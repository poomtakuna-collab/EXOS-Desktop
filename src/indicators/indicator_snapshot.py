from __future__ import annotations

from src.analysis import calculate_indicator_snapshot
from src.core.market_scope import MARKET_SCOPE
from src.data import MarketDataRow


def build_indicator_snapshot(
    symbol: str, timeframe: str, rows: list[MarketDataRow]
) -> dict[str, object] | None:
    if not rows:
        return None

    latest_row = rows[-1]
    indicator_snapshot = calculate_indicator_snapshot(rows)
    if indicator_snapshot is None:
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
        **indicator_snapshot,
    }
