from __future__ import annotations

from src.data import MarketDataRow


VP_LENGTH = 20
VP_SMOOTH1 = 5
VP_SMOOTH2 = 8


def calculate_volume_pressure_snapshot(
    rows: list[MarketDataRow],
) -> dict[str, object] | None:
    if not rows:
        return None

    buy_sell_delta = [_buy_sell_delta(row) for row in rows]
    volumes = [float(row["volume"]) for row in rows]

    vp_raw_values = _ema_values(buy_sell_delta, VP_LENGTH)
    vp_norm_base_values = _ema_values(volumes, VP_LENGTH)
    vp_norm_values = [
        (raw / base) * 100 if base != 0 else 0.0
        for raw, base in zip(vp_raw_values, vp_norm_base_values)
    ]
    vp_core_values = _ema_values(vp_norm_values, VP_SMOOTH1)
    vp_values = _ema_values(vp_core_values, VP_SMOOTH2)
    vp = round(vp_values[-1], 4) if vp_values else 0.0

    return {
        "volume_pressure": vp,
        "vp_state": _vp_state(vp),
    }


def _buy_sell_delta(row: MarketDataRow) -> float:
    close = float(row["close"])
    open_price = float(row["open"])
    volume = float(row["volume"])
    if close > open_price:
        return volume
    if close < open_price:
        return -volume
    return 0.0


def _ema_values(values: list[float], period: int) -> list[float]:
    if not values:
        return []

    multiplier = 2 / (period + 1)
    ema_values = [values[0]]
    for value in values[1:]:
        ema_values.append((value - ema_values[-1]) * multiplier + ema_values[-1])
    return ema_values


def _vp_state(vp: float) -> str:
    if vp > 0:
        return "buy"
    if vp < 0:
        return "sell"
    return "neutral"
