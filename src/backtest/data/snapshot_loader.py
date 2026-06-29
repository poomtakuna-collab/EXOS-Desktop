from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class SnapshotQuery:
    symbols: tuple[str, ...] = ()
    timeframe: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    minimum_exos_score: float | None = None
    trend_state: str | None = None
    squeeze_state: str | None = None
    market_structure_state: str | None = None


class SnapshotLoader:
    """Public interface for loading stored snapshot records for Backtest."""

    def load_snapshot(self, snapshot_id: str) -> dict[str, Any] | None:
        """Load one stored snapshot by its stable `snapshot_id`.

        Implementations must return the stored snapshot record without recalculating
        indicators, mutating source data, or opening live market-data paths.
        """
        raise NotImplementedError("SnapshotLoader.load_snapshot is not implemented yet")

    def load_snapshots(self, query: SnapshotQuery) -> list[dict[str, Any]]:
        """Load stored snapshots matching `query` in deterministic order.

        Implementations must preserve `snapshot_id` and return records ordered by
        the Backtest Data Layer contract without executing strategy logic.
        """
        raise NotImplementedError("SnapshotLoader.load_snapshots is not implemented yet")
