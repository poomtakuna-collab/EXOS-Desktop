from __future__ import annotations

from dataclasses import asdict, dataclass
from math import sqrt
from typing import Any, Mapping, Sequence


EW_FAST = 5
EW_SLOW = 35
SCALE_FACTOR = 200
VP_LEN = 20
VP_SMOOTH1 = 5
VP_SMOOTH2 = 8
TS_LEN = 20
TS_LOOKBACK = 10
TS_SMOOTH = 5
TS_SCALE = 1.5
BB_LEN = 20
BB_MULT = 2.0
KC_MULT = 1.5
MSB_LEFT = 2
MSB_RIGHT = 2


@dataclass(frozen=True)
class POOMComboParameters:
    ewFast: int = EW_FAST
    ewSlow: int = EW_SLOW
    scaleFactor: float = SCALE_FACTOR
    vpLen: int = VP_LEN
    vpSmooth1: int = VP_SMOOTH1
    vpSmooth2: int = VP_SMOOTH2
    tsLen: int = TS_LEN
    tsLookback: int = TS_LOOKBACK
    tsSmooth: int = TS_SMOOTH
    tsScale: float = TS_SCALE
    bbLen: int = BB_LEN
    bbMult: float = BB_MULT
    kcMult: float = KC_MULT
    msbLeft: int = MSB_LEFT
    msbRight: int = MSB_RIGHT


@dataclass(frozen=True)
class POOMComboResult:
    ew_norm: float
    volume_pressure: float
    trend_slope: float
    in_squeeze: bool
    squeeze_up: bool
    squeeze_down: bool
    bos_up: bool
    bos_down: bool
    choch_up: bool
    choch_down: bool
    msb_last_high: float | None
    msb_last_low: float | None
    msb_dir: int
    signal_summary: dict[str, object]

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def calculate_poom_combo_snapshot(
    rows: Sequence[Mapping[str, Any]],
    parameters: POOMComboParameters | None = None,
) -> dict[str, object]:
    return analyze_poom_combo(rows, parameters).to_dict()


def analyze_poom_combo(
    rows: Sequence[Mapping[str, Any]],
    parameters: POOMComboParameters | None = None,
) -> POOMComboResult:
    params = parameters or POOMComboParameters()
    safe_rows = [_plain_row(row) for row in rows]
    closes = [row["close"] for row in safe_rows]
    volumes = [row["volume"] for row in safe_rows]

    ew_norm = _ew_norm(closes, params)
    volume_pressure = _volume_pressure(safe_rows, volumes, params)
    trend_slope = _trend_slope(closes, params)
    in_squeeze, squeeze_up, squeeze_down = _squeeze_state(safe_rows, params)
    msb = _market_structure(safe_rows, params)

    summary = {
        "ew_state": _signed_state(ew_norm),
        "volume_pressure_state": _signed_state(volume_pressure),
        "trend_slope_state": _signed_state(trend_slope),
        "squeeze": _squeeze_summary(in_squeeze, squeeze_up, squeeze_down),
        "structure": _structure_summary(msb),
    }
    return POOMComboResult(
        ew_norm=round(ew_norm, 4),
        volume_pressure=round(volume_pressure, 4),
        trend_slope=round(trend_slope, 4),
        in_squeeze=in_squeeze,
        squeeze_up=squeeze_up,
        squeeze_down=squeeze_down,
        bos_up=msb["bos_up"],
        bos_down=msb["bos_down"],
        choch_up=msb["choch_up"],
        choch_down=msb["choch_down"],
        msb_last_high=msb["last_high"],
        msb_last_low=msb["last_low"],
        msb_dir=msb["dir"],
        signal_summary=summary,
    )


def _plain_row(row: Mapping[str, Any]) -> dict[str, float]:
    return {
        "open": _number(row.get("open")),
        "high": _number(row.get("high")),
        "low": _number(row.get("low")),
        "close": _number(row.get("close")),
        "volume": _number(row.get("volume")),
    }


def _ew_norm(closes: list[float], params: POOMComboParameters) -> float:
    if not closes:
        return 0.0
    fast = _sma(closes, params.ewFast)
    slow = _sma(closes, params.ewSlow)
    base = closes[-1]
    return ((fast - slow) / base) * params.scaleFactor if base else 0.0


def _volume_pressure(
    rows: list[dict[str, float]],
    volumes: list[float],
    params: POOMComboParameters,
) -> float:
    if not rows:
        return 0.0
    delta = [
        row["volume"] if row["close"] > row["open"] else -row["volume"] if row["close"] < row["open"] else 0.0
        for row in rows
    ]
    raw = _ema_values(delta, params.vpLen)
    base = _ema_values(volumes, params.vpLen)
    normalized = [
        (raw_value / base_value) * 100 if base_value else 0.0
        for raw_value, base_value in zip(raw, base)
    ]
    return _last(_ema_values(_ema_values(normalized, params.vpSmooth1), params.vpSmooth2))


def _trend_slope(closes: list[float], params: POOMComboParameters) -> float:
    if not closes:
        return 0.0
    base_values = _ema_values(closes, params.tsLen)
    normalized: list[float] = []
    for index, base in enumerate(base_values):
        if index < params.tsLookback:
            normalized.append(0.0)
            continue
        raw = base - base_values[index - params.tsLookback]
        normalized.append(((raw / base) * 100 if base else 0.0) * params.tsScale)
    return _last(_ema_values(normalized, params.tsSmooth))


def _squeeze_state(
    rows: list[dict[str, float]],
    params: POOMComboParameters,
) -> tuple[bool, bool, bool]:
    if len(rows) < params.bbLen + 1:
        return False, False, False
    current = _squeeze_on(rows, params)
    previous = _squeeze_on(rows[:-1], params)
    if current is None:
        return False, False, False
    previous_state = previous if previous is not None else current
    released = previous_state and not current
    close = rows[-1]["close"]
    previous_close = rows[-2]["close"]
    return current, released and close >= previous_close, released and close < previous_close


def _squeeze_on(rows: list[dict[str, float]], params: POOMComboParameters) -> bool | None:
    if len(rows) < params.bbLen:
        return None
    window = rows[-params.bbLen :]
    closes = [row["close"] for row in window]
    basis = _sma(closes, params.bbLen)
    deviation = _standard_deviation(closes)
    bb_upper = basis + params.bbMult * deviation
    bb_lower = basis - params.bbMult * deviation
    true_range = _sma(_true_ranges(window), params.bbLen)
    kc_upper = basis + params.kcMult * true_range
    kc_lower = basis - params.kcMult * true_range
    return bb_upper < kc_upper and bb_lower > kc_lower


def _market_structure(
    rows: list[dict[str, float]],
    params: POOMComboParameters,
) -> dict[str, Any]:
    pivot_highs = _pivot_highs(rows, params.msbLeft, params.msbRight)
    pivot_lows = _pivot_lows(rows, params.msbLeft, params.msbRight)
    last_high = pivot_highs[-1][1] if pivot_highs else None
    last_low = pivot_lows[-1][1] if pivot_lows else None
    close = rows[-1]["close"] if rows else 0.0
    bos_up = last_high is not None and close > last_high
    bos_down = last_low is not None and close < last_low
    prior_dir = _structure_dir(pivot_highs[:-1], pivot_lows[:-1])
    current_dir = _structure_dir(pivot_highs, pivot_lows)
    direction = 1 if bos_up else -1 if bos_down else current_dir
    return {
        "last_high": round(last_high, 4) if last_high is not None else None,
        "last_low": round(last_low, 4) if last_low is not None else None,
        "dir": direction,
        "bos_up": bos_up,
        "bos_down": bos_down,
        "choch_up": prior_dir < 0 and bos_up,
        "choch_down": prior_dir > 0 and bos_down,
    }


def _pivot_highs(
    rows: list[dict[str, float]],
    left: int,
    right: int,
) -> list[tuple[int, float]]:
    pivots: list[tuple[int, float]] = []
    for index in range(left, len(rows) - right):
        high = rows[index]["high"]
        left_highs = [rows[item]["high"] for item in range(index - left, index)]
        right_highs = [rows[item]["high"] for item in range(index + 1, index + right + 1)]
        if high > max(left_highs) and high >= max(right_highs):
            pivots.append((index, high))
    return pivots


def _pivot_lows(
    rows: list[dict[str, float]],
    left: int,
    right: int,
) -> list[tuple[int, float]]:
    pivots: list[tuple[int, float]] = []
    for index in range(left, len(rows) - right):
        low = rows[index]["low"]
        left_lows = [rows[item]["low"] for item in range(index - left, index)]
        right_lows = [rows[item]["low"] for item in range(index + 1, index + right + 1)]
        if low < min(left_lows) and low <= min(right_lows):
            pivots.append((index, low))
    return pivots


def _structure_dir(
    pivot_highs: list[tuple[int, float]],
    pivot_lows: list[tuple[int, float]],
) -> int:
    if len(pivot_highs) < 2 or len(pivot_lows) < 2:
        return 0
    high_up = pivot_highs[-1][1] > pivot_highs[-2][1]
    low_up = pivot_lows[-1][1] > pivot_lows[-2][1]
    high_down = pivot_highs[-1][1] < pivot_highs[-2][1]
    low_down = pivot_lows[-1][1] < pivot_lows[-2][1]
    if high_up and low_up:
        return 1
    if high_down and low_down:
        return -1
    return 0


def _sma(values: list[float], period: int) -> float:
    if not values:
        return 0.0
    window = values[-period:]
    return sum(window) / len(window)


def _ema_values(values: list[float], period: int) -> list[float]:
    if not values:
        return []
    multiplier = 2 / (period + 1)
    output = [values[0]]
    for value in values[1:]:
        output.append((value - output[-1]) * multiplier + output[-1])
    return output


def _true_ranges(rows: list[dict[str, float]]) -> list[float]:
    output: list[float] = []
    previous_close: float | None = None
    for row in rows:
        high = row["high"]
        low = row["low"]
        if previous_close is None:
            output.append(high - low)
        else:
            output.append(max(high - low, abs(high - previous_close), abs(low - previous_close)))
        previous_close = row["close"]
    return output


def _standard_deviation(values: list[float]) -> float:
    if not values:
        return 0.0
    mean = sum(values) / len(values)
    return sqrt(sum((value - mean) ** 2 for value in values) / len(values))


def _number(value: object) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _last(values: list[float]) -> float:
    return values[-1] if values else 0.0


def _signed_state(value: float) -> str:
    if value > 0:
        return "positive"
    if value < 0:
        return "negative"
    return "neutral"


def _squeeze_summary(in_squeeze: bool, squeeze_up: bool, squeeze_down: bool) -> str:
    if squeeze_up:
        return "release_up"
    if squeeze_down:
        return "release_down"
    if in_squeeze:
        return "in_squeeze"
    return "none"


def _structure_summary(msb: Mapping[str, Any]) -> str:
    if msb["choch_up"]:
        return "choch_up"
    if msb["choch_down"]:
        return "choch_down"
    if msb["bos_up"]:
        return "bos_up"
    if msb["bos_down"]:
        return "bos_down"
    if msb["dir"] > 0:
        return "bullish"
    if msb["dir"] < 0:
        return "bearish"
    return "neutral"
