from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from typing import Any

from src.backtest.contracts import BacktestReport, BacktestResult, SimulationConfig
from src.backtest.data import BacktestDataset, SQLiteBacktestDatasetBuilder, SnapshotQuery
from src.backtest.pipeline import run_backtest
from src.backtest.report import build_backtest_report


@dataclass(frozen=True)
class SQLiteBacktestRun:
    dataset: BacktestDataset
    result: BacktestResult
    report: BacktestReport
    skipped_records: list[dict[str, Any]]


def run_sqlite_backtest_read_only(
    connection: sqlite3.Connection,
    query: SnapshotQuery,
    config: SimulationConfig | None = None,
) -> SQLiteBacktestRun:
    simulation_config = config or SimulationConfig()
    dataset = SQLiteBacktestDatasetBuilder(connection).build_dataset(
        query,
        simulation_config,
    )
    result = run_backtest(dataset.inputs, simulation_config)
    report = build_backtest_report(result)

    return SQLiteBacktestRun(
        dataset=dataset,
        result=result,
        report=report,
        skipped_records=list(dataset.skipped_records),
    )
