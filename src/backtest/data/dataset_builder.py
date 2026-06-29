from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from src.backtest.contracts import BacktestInput, SimulationConfig
from src.backtest.data.future_rows_loader import FutureRowsLoader
from src.backtest.data.outcome_loader import OutcomeLoader
from src.backtest.data.snapshot_loader import SnapshotLoader, SnapshotQuery


@dataclass(frozen=True)
class BacktestDataset:
    inputs: list[BacktestInput]
    metadata: dict[str, Any] = field(default_factory=dict)
    skipped_records: list[dict[str, Any]] = field(default_factory=list)


class BacktestDatasetBuilder:
    """Public interface for constructing Backtest datasets from stored records."""

    def __init__(
        self,
        snapshot_loader: SnapshotLoader,
        outcome_loader: OutcomeLoader,
        future_rows_loader: FutureRowsLoader,
    ) -> None:
        self.snapshot_loader = snapshot_loader
        self.outcome_loader = outcome_loader
        self.future_rows_loader = future_rows_loader

    def build_dataset(
        self,
        query: SnapshotQuery,
        config: SimulationConfig,
    ) -> BacktestDataset:
        """Build a deterministic `BacktestDataset` for the supplied query/config.

        Implementations should coordinate snapshot, outcome, and future-row loaders
        to create `BacktestInput` records. They must not run replay, aggregate
        metrics, execute trades, call AI, or mutate source data.
        """
        raise NotImplementedError("BacktestDatasetBuilder.build_dataset is not implemented yet")
