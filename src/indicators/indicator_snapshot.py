from __future__ import annotations

from src.analysis import (
    build_exos_snapshot,
    calculate_ew_snapshot,
    calculate_indicator_snapshot,
    calculate_market_structure_snapshot,
    calculate_squeeze_snapshot,
    calculate_trend_slope_snapshot,
    calculate_volume_pressure_snapshot,
)
from src.core.market_scope import MARKET_SCOPE
from src.data import MarketDataRow


def build_indicator_snapshot(
    symbol: str, timeframe: str, rows: list[MarketDataRow]
) -> dict[str, object] | None:
    if not rows:
        return None

    latest_row = rows[-1]
    exos_snapshot = build_exos_snapshot(rows, symbol=symbol, timeframe=timeframe)
    indicator_snapshot = calculate_indicator_snapshot(rows)
    ew_snapshot = calculate_ew_snapshot(rows)
    market_structure_snapshot = calculate_market_structure_snapshot(rows)
    market_structure_snapshot = {
        **market_structure_snapshot,
        "market_structure_confidence": market_structure_snapshot["confidence"],
    }
    squeeze_snapshot = calculate_squeeze_snapshot(rows)
    trend_slope_snapshot = calculate_trend_slope_snapshot(rows)
    volume_pressure_snapshot = calculate_volume_pressure_snapshot(rows)
    if (
        indicator_snapshot is None
        or ew_snapshot is None
        or market_structure_snapshot is None
        or squeeze_snapshot is None
        or trend_slope_snapshot is None
        or volume_pressure_snapshot is None
    ):
        return None

    return {
        "symbol": symbol,
        "market": MARKET_SCOPE,
        "timeframe": timeframe,
        "latest_date": str(latest_row["date"]),
        "open": float(latest_row["open"]),
        "high": float(latest_row["high"]),
        "low": float(latest_row["low"]),
        "close": float(latest_row["close"]),
        "volume": int(latest_row["volume"]),
        "exos_snapshot": exos_snapshot,
        **indicator_snapshot,
        **ew_snapshot,
        **market_structure_snapshot,
        **squeeze_snapshot,
        **trend_slope_snapshot,
        **volume_pressure_snapshot,
    }
