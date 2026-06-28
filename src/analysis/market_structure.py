from __future__ import annotations

from dataclasses import asdict, dataclass

from src.data import MarketDataRow


PIVOT_LEFT = 2
PIVOT_RIGHT = 2
MINIMUM_ROWS = PIVOT_LEFT + PIVOT_RIGHT + 6


@dataclass(frozen=True)
class MarketStructureAnalysis:
    structure_state: str
    structure_score: float
    swing_high: float
    swing_low: float
    last_pivot_high: float
    last_pivot_low: float
    bos: str
    choch: str
    confidence: float

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def analyze_market_structure(rows: list[MarketDataRow]) -> MarketStructureAnalysis:
    if len(rows) < MINIMUM_ROWS:
        return _default_analysis()

    pivot_highs = _pivot_highs(rows)
    pivot_lows = _pivot_lows(rows)
    if len(pivot_highs) < 2 or len(pivot_lows) < 2:
        return _default_analysis()

    last_close = float(rows[-1]["close"])
    recent_highs = pivot_highs[-2:]
    recent_lows = pivot_lows[-2:]
    last_pivot_high = recent_highs[-1][1]
    last_pivot_low = recent_lows[-1][1]
    swing_high = max(high for _, high in recent_highs)
    swing_low = min(low for _, low in recent_lows)

    trend_state = _trend_state(recent_highs, recent_lows)
    prior_trend_state = _prior_trend_state(pivot_highs, pivot_lows)
    bos = _bos(last_close, last_pivot_high, last_pivot_low)
    choch = _choch(prior_trend_state, bos)
    structure_state = _structure_state(
        trend_state=trend_state,
        bos=bos,
        choch=choch,
    )

    return MarketStructureAnalysis(
        structure_state=structure_state,
        structure_score=_structure_score(structure_state),
        swing_high=round(swing_high, 4),
        swing_low=round(swing_low, 4),
        last_pivot_high=round(last_pivot_high, 4),
        last_pivot_low=round(last_pivot_low, 4),
        bos=bos,
        choch=choch,
        confidence=_confidence(pivot_highs, pivot_lows),
    )


def calculate_market_structure_snapshot(
    rows: list[MarketDataRow],
) -> dict[str, object]:
    return analyze_market_structure(rows).to_dict()


def _pivot_highs(rows: list[MarketDataRow]) -> list[tuple[int, float]]:
    pivots: list[tuple[int, float]] = []
    for index in range(PIVOT_LEFT, len(rows) - PIVOT_RIGHT):
        high = float(rows[index]["high"])
        left_highs = [
            float(rows[left_index]["high"])
            for left_index in range(index - PIVOT_LEFT, index)
        ]
        right_highs = [
            float(rows[right_index]["high"])
            for right_index in range(index + 1, index + PIVOT_RIGHT + 1)
        ]
        if high > max(left_highs) and high >= max(right_highs):
            pivots.append((index, high))
    return pivots


def _pivot_lows(rows: list[MarketDataRow]) -> list[tuple[int, float]]:
    pivots: list[tuple[int, float]] = []
    for index in range(PIVOT_LEFT, len(rows) - PIVOT_RIGHT):
        low = float(rows[index]["low"])
        left_lows = [
            float(rows[left_index]["low"])
            for left_index in range(index - PIVOT_LEFT, index)
        ]
        right_lows = [
            float(rows[right_index]["low"])
            for right_index in range(index + 1, index + PIVOT_RIGHT + 1)
        ]
        if low < min(left_lows) and low <= min(right_lows):
            pivots.append((index, low))
    return pivots


def _trend_state(
    recent_highs: list[tuple[int, float]], recent_lows: list[tuple[int, float]]
) -> str:
    previous_high, current_high = recent_highs[-2][1], recent_highs[-1][1]
    previous_low, current_low = recent_lows[-2][1], recent_lows[-1][1]
    if current_high > previous_high and current_low > previous_low:
        return "HH_HL"
    if current_high < previous_high and current_low < previous_low:
        return "LH_LL"
    return "RANGE"


def _prior_trend_state(
    pivot_highs: list[tuple[int, float]], pivot_lows: list[tuple[int, float]]
) -> str:
    if len(pivot_highs) < 3 or len(pivot_lows) < 3:
        return "UNKNOWN"
    return _trend_state(pivot_highs[-3:-1], pivot_lows[-3:-1])


def _bos(last_close: float, last_pivot_high: float, last_pivot_low: float) -> str:
    if last_close > last_pivot_high:
        return "up"
    if last_close < last_pivot_low:
        return "down"
    return "none"


def _choch(prior_trend_state: str, bos: str) -> str:
    if prior_trend_state == "LH_LL" and bos == "up":
        return "up"
    if prior_trend_state == "HH_HL" and bos == "down":
        return "down"
    return "none"


def _structure_state(trend_state: str, bos: str, choch: str) -> str:
    if choch == "up":
        return "CHOCH_UP"
    if choch == "down":
        return "CHOCH_DOWN"
    if bos == "up":
        return "BREAKOUT_UP"
    if bos == "down":
        return "BREAKOUT_DOWN"
    return trend_state


def _structure_score(structure_state: str) -> float:
    scores = {
        "UNKNOWN": 0.0,
        "HH_HL": 70.0,
        "LH_LL": 30.0,
        "RANGE": 50.0,
        "BREAKOUT_UP": 80.0,
        "BREAKOUT_DOWN": 20.0,
        "CHOCH_UP": 85.0,
        "CHOCH_DOWN": 15.0,
    }
    return scores.get(structure_state, 0.0)


def _confidence(
    pivot_highs: list[tuple[int, float]], pivot_lows: list[tuple[int, float]]
) -> float:
    pivot_count = min(len(pivot_highs), len(pivot_lows))
    return round(min(pivot_count / 4, 1.0), 2)


def _default_analysis() -> MarketStructureAnalysis:
    return MarketStructureAnalysis(
        structure_state="UNKNOWN",
        structure_score=0.0,
        swing_high=0.0,
        swing_low=0.0,
        last_pivot_high=0.0,
        last_pivot_low=0.0,
        bos="none",
        choch="none",
        confidence=0.0,
    )
