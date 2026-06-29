from __future__ import annotations

from typing import Any


class FutureRowsLoader:
    """Public interface for loading future OHLCV rows for Backtest replay."""

    def load_future_rows(
        self,
        symbol: str,
        timeframe: str,
        snapshot_date: str,
        horizon_days: int,
    ) -> list[dict[str, Any]]:
        """Load future OHLCV rows after `snapshot_date` for one replay window.

        Implementations must return deterministic rows for replay only. They must
        not fetch live data, calculate indicators, run Strategy, or mutate source
        records.
        """
        raise NotImplementedError("FutureRowsLoader.load_future_rows is not implemented yet")
