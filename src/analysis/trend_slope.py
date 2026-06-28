from __future__ import annotations

from src.data import MarketDataRow


TS_LEN = 20
TS_LOOKBACK = 10
TS_SMOOTH = 5
TS_SCALE = 1.5


def calculate_trend_slope_snapshot(
    rows: list[MarketDataRow],
) -> dict[str, object] | None:
    if not rows:
        return None

    closes = [float(row["close"]) for row in rows]
    ts_base_values = _ema_values(closes, TS_LEN)
    ts_norm_values: list[float] = []

    for index, ts_base in enumerate(ts_base_values):
        if index < TS_LOOKBACK:
            ts_norm_values.append(0.0)
            continue

        ts_raw = ts_base - ts_base_values[index - TS_LOOKBACK]
        ts_norm = (ts_raw / ts_base) * 100 if ts_base != 0 else 0.0
        ts_norm_values.append(ts_norm * TS_SCALE)

    trend_slope_values = _ema_values(ts_norm_values, TS_SMOOTH)
    trend_slope = round(trend_slope_values[-1], 4) if trend_slope_values else 0.0

    return {
        "trend_slope": trend_slope,
        "trend_slope_state": _trend_slope_state(trend_slope),
    }


def _ema_values(values: list[float], period: int) -> list[float]:
    if not values:
        return []

    multiplier = 2 / (period + 1)
    ema_values = [values[0]]
    for value in values[1:]:
        ema_values.append((value - ema_values[-1]) * multiplier + ema_values[-1])
    return ema_values


def _trend_slope_state(trend_slope: float) -> str:
    if trend_slope > 0:
        return "up"
    if trend_slope < 0:
        return "down"
    return "flat"
