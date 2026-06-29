from __future__ import annotations

import inspect
import unittest

from src.backtest import SimulationConfig
from src.backtest.data import (
    BacktestDataset,
    BacktestDatasetBuilder,
    FutureRowsLoader,
    OutcomeLoader,
    SQLiteBacktestDatasetBuilder,
    SQLiteFutureRowsLoader,
    SQLiteOutcomeLoader,
    SQLiteSnapshotLoader,
    SnapshotLoader,
    SnapshotQuery,
)


class BacktestDataSkeletonTest(unittest.TestCase):
    def test_public_imports_are_available(self) -> None:
        self.assertIs(SnapshotLoader, SnapshotLoader)
        self.assertIs(OutcomeLoader, OutcomeLoader)
        self.assertIs(FutureRowsLoader, FutureRowsLoader)
        self.assertIs(SQLiteFutureRowsLoader, SQLiteFutureRowsLoader)
        self.assertIs(SQLiteOutcomeLoader, SQLiteOutcomeLoader)
        self.assertIs(SQLiteSnapshotLoader, SQLiteSnapshotLoader)
        self.assertIs(SQLiteBacktestDatasetBuilder, SQLiteBacktestDatasetBuilder)
        self.assertIs(BacktestDatasetBuilder, BacktestDatasetBuilder)
        self.assertIs(BacktestDataset, BacktestDataset)
        self.assertIs(SnapshotQuery, SnapshotQuery)

    def test_snapshot_query_defaults_are_stable(self) -> None:
        query = SnapshotQuery()

        self.assertIsNone(query.symbol)
        self.assertEqual(query.symbols, ())
        self.assertIsNone(query.timeframe)
        self.assertIsNone(query.start_date)
        self.assertIsNone(query.end_date)
        self.assertIsNone(query.limit)
        self.assertIsNone(query.minimum_exos_score)
        self.assertIsNone(query.trend_state)
        self.assertIsNone(query.squeeze_state)
        self.assertIsNone(query.market_structure_state)

    def test_backtest_dataset_defaults_are_stable(self) -> None:
        dataset = BacktestDataset(inputs=[])

        self.assertEqual(dataset.inputs, [])
        self.assertEqual(dataset.metadata, {})
        self.assertEqual(dataset.skipped_records, [])

    def test_loader_methods_raise_not_implemented(self) -> None:
        with self.assertRaises(NotImplementedError):
            SnapshotLoader().load_snapshot("snapshot-1")

        with self.assertRaises(NotImplementedError):
            SnapshotLoader().load_snapshots(SnapshotQuery())

        with self.assertRaises(NotImplementedError):
            OutcomeLoader().load_outcome("snapshot-1")

        with self.assertRaises(NotImplementedError):
            OutcomeLoader().load_outcomes(["snapshot-1"])

        with self.assertRaises(NotImplementedError):
            FutureRowsLoader().load_future_rows(
                symbol="AAPL",
                timeframe="1D",
                snapshot_date="2026-01-01",
                horizon_days=10,
            )

    def test_dataset_builder_signature_is_stable(self) -> None:
        builder = BacktestDatasetBuilder(
            snapshot_loader=SnapshotLoader(),
            outcome_loader=OutcomeLoader(),
            future_rows_loader=FutureRowsLoader(),
        )

        self.assertIsInstance(builder.snapshot_loader, SnapshotLoader)
        self.assertIsInstance(builder.outcome_loader, OutcomeLoader)
        self.assertIsInstance(builder.future_rows_loader, FutureRowsLoader)

        with self.assertRaises(NotImplementedError):
            builder.build_dataset(SnapshotQuery(), SimulationConfig())

    def test_public_methods_exist(self) -> None:
        self.assertTrue(hasattr(SnapshotLoader, "load_snapshot"))
        self.assertTrue(hasattr(SnapshotLoader, "load_snapshots"))
        self.assertTrue(hasattr(OutcomeLoader, "load_outcome"))
        self.assertTrue(hasattr(OutcomeLoader, "load_outcomes"))
        self.assertTrue(hasattr(FutureRowsLoader, "load_future_rows"))
        self.assertTrue(hasattr(BacktestDatasetBuilder, "build_dataset"))

    def test_loader_signatures_are_stable(self) -> None:
        self.assertEqual(
            list(inspect.signature(SnapshotLoader.load_snapshot).parameters),
            ["self", "snapshot_id"],
        )
        self.assertEqual(
            list(inspect.signature(SnapshotLoader.load_snapshots).parameters),
            ["self", "query"],
        )
        self.assertEqual(
            list(inspect.signature(OutcomeLoader.load_outcome).parameters),
            ["self", "snapshot_id"],
        )
        self.assertEqual(
            list(inspect.signature(OutcomeLoader.load_outcomes).parameters),
            ["self", "snapshot_ids"],
        )
        self.assertEqual(
            list(inspect.signature(FutureRowsLoader.load_future_rows).parameters),
            ["self", "symbol", "timeframe", "snapshot_date", "horizon_days"],
        )
        self.assertEqual(
            list(inspect.signature(BacktestDatasetBuilder.build_dataset).parameters),
            ["self", "query", "config"],
        )

    def test_public_methods_have_docstrings(self) -> None:
        self.assertIsNotNone(SnapshotLoader.load_snapshot.__doc__)
        self.assertIsNotNone(SnapshotLoader.load_snapshots.__doc__)
        self.assertIsNotNone(OutcomeLoader.load_outcome.__doc__)
        self.assertIsNotNone(OutcomeLoader.load_outcomes.__doc__)
        self.assertIsNotNone(FutureRowsLoader.load_future_rows.__doc__)
        self.assertIsNotNone(BacktestDatasetBuilder.build_dataset.__doc__)


if __name__ == "__main__":
    unittest.main()
