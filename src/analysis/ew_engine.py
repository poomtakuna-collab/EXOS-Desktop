from __future__ import annotations

from src.data import MarketDataRow


EW_FAST = 5
EW_SLOW = 35


def calculate_ew_snapshot(rows: list[MarketDataRow]) -> dict[str, object] | None:
    if not rows:
        return None

    closes = [float(row["close"]) for row in rows]
    ew_raw = _sma(closes, EW_FAST) - _sma(closes, EW_SLOW)
    base_price = _latest_ema(closes, EW_SLOW)
    ew = round((ew_raw / base_price) * 200, 4) if base_price != 0 else 0.0

    return {
        "ew": ew,
        "ew_fast": EW_FAST,
        "ew_slow": EW_SLOW,
        "ew_state": _ew_state(ew),
    }


def _sma(values: list[float], period: int) -> float:
    if not values:
        return 0.0

    window = values[-period:]
    return sum(window) / len(window)


def _latest_ema(values: list[float], period: int) -> float:
    if not values:
        return 0.0

    multiplier = 2 / (period + 1)
    ema = values[0]
    for value in values[1:]:
        ema = (value - ema) * multiplier + ema
    return ema


def _ew_state(ew: float) -> str:
    if ew > 0:
        return "positive"
    if ew < 0:
        return "negative"
    return "neutral"
