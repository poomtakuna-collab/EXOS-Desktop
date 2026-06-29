from __future__ import annotations

import json
import sqlite3
import sys
import unittest

from src.backtest import SimulationConfig
from src.backtest.data import SQLiteBacktestDatasetBuilder, SnapshotQuery


class SQLiteBacktestDatasetBuilderTest(unittest.TestCase):
    def test_build_dataset_loads_snapshots_outcomes_and_future_rows(self) -> None:
        with _dataset_connection() as connection:
            builder = SQLiteBacktestDatasetBuilder(connection)

            dataset = builder.build_dataset(
                SnapshotQuery(symbol="AAPL", timeframe="1D"),
                SimulationConfig(horizon_days=2),
            )

            self.assertEqual(
                [item.snapshot["snapshot_id"] for item in dataset.inputs],
                ["snapshot-a", "snapshot-b", "snapshot-c"],
            )
            self.assertEqual(dataset.inputs[0].outcome["outcome_id"], "outcome-a")
            self.assertEqual(dataset.inputs[1].outcome, {})
            self.assertEqual(dataset.inputs[2].outcome["outcome_id"], "outcome-c")
            self.assertEqual(
                [row["date"] for row in dataset.inputs[0].future_rows],
                ["2026-01-02", "2026-01-03"],
            )
            self.assertEqual(
                [row["date"] for row in dataset.inputs[2].future_rows],
                ["2026-01-06"],
            )

    def test_missing_outcomes_and_future_rows_are_represented_deterministically(self) -> None:
        with _dataset_connection() as connection:
            builder = SQLiteBacktestDatasetBuilder(connection)

            dataset = builder.build_dataset(
                SnapshotQuery(symbol="AAPL", timeframe="1D"),
                SimulationConfig(horizon_days=2),
            )

            self.assertEqual(dataset.metadata["snapshot_count"], 3)
            self.assertEqual(dataset.metadata["outcome_count"], 2)
            self.assertEqual(dataset.metadata["missing_outcome_count"], 1)
            self.assertEqual(dataset.metadata["missing_future_rows_count"], 1)
            self.assertEqual(
                dataset.skipped_records,
                [
                    {
                        "sequence_number": 2,
                        "snapshot_id": "snapshot-b",
                        "symbol": "AAPL",
                        "timeframe": "1D",
                        "date": "2026-01-02",
                        "reason": "Missing outcome",
                    },
                    {
                        "sequence_number": 3,
                        "snapshot_id": "snapshot-c",
                        "symbol": "AAPL",
                        "timeframe": "1D",
                        "date": "2026-01-05",
                        "reason": "Insufficient future rows",
                    },
                ],
            )

    def test_strategy_probability_and_prediction_json_are_parsed_without_execution(self) -> None:
        with _dataset_connection() as connection:
            builder = SQLiteBacktestDatasetBuilder(connection)

            dataset = builder.build_dataset(
                SnapshotQuery(symbol="AAPL", timeframe="1D", limit=1),
                SimulationConfig(horizon_days=1),
            )

            item = dataset.inputs[0]
            self.assertEqual(item.probability["confidence"], 70.0)
            self.assertEqual(item.prediction["expected_return"], 5.0)
            self.assertEqual(item.strategy_result.strategy_score, 72.0)
            self.assertEqual(item.strategy_result.reward_risk_estimate["target_zone"]["low"], 105.0)

    def test_snapshot_order_is_preserved(self) -> None:
        with _dataset_connection() as connection:
            builder = SQLiteBacktestDatasetBuilder(connection)

            dataset = builder.build_dataset(SnapshotQuery(), SimulationConfig(horizon_days=1))

            self.assertEqual(
                [item.snapshot["snapshot_id"] for item in dataset.inputs],
                ["snapshot-a", "snapshot-b", "snapshot-c", "snapshot-msft"],
            )

    def test_builder_does_not_write_to_database(self) -> None:
        with _dataset_connection() as connection:
            builder = SQLiteBacktestDatasetBuilder(connection)
            changes_before = connection.total_changes
            schema_before = _schema_sql(connection)

            builder.build_dataset(
                SnapshotQuery(symbol="AAPL", timeframe="1D"),
                SimulationConfig(horizon_days=2),
            )

            self.assertEqual(connection.total_changes, changes_before)
            self.assertEqual(_schema_sql(connection), schema_before)

    def test_builder_does_not_import_live_data_ai_network_or_broker_modules(self) -> None:
        before_modules = set(sys.modules)
        with _dataset_connection() as connection:
            builder = SQLiteBacktestDatasetBuilder(connection)
            builder.build_dataset(
                SnapshotQuery(symbol="AAPL", timeframe="1D"),
                SimulationConfig(horizon_days=1),
            )

        imported_modules = set(sys.modules) - before_modules
        forbidden_prefixes = (
            "src.ai",
            "src.data",
            "src.database",
            "urllib",
            "http",
            "socket",
            "yfinance",
            "broker",
        )
        self.assertFalse(
            {
                module_name
                for module_name in imported_modules
                if module_name.startswith(forbidden_prefixes)
            }
        )


def _dataset_connection() -> sqlite3.Connection:
    connection = sqlite3.connect(":memory:")
    connection.execute(
        """
        CREATE TABLE snapshots (
            snapshot_id TEXT PRIMARY KEY,
            symbol TEXT NOT NULL,
            timeframe TEXT NOT NULL,
            date TEXT NOT NULL,
            close REAL,
            snapshot_json TEXT NOT NULL,
            probability_json TEXT,
            prediction_json TEXT,
            strategy_result_json TEXT,
            created_at TEXT NOT NULL
        )
        """
    )
    connection.execute(
        """
        CREATE TABLE outcomes (
            outcome_id TEXT PRIMARY KEY,
            snapshot_id TEXT NOT NULL,
            forward_10d_return REAL,
            label_10d TEXT,
            calculated_at TEXT NOT NULL
        )
        """
    )
    connection.execute(
        """
        CREATE TABLE ohlcv_daily (
            symbol TEXT NOT NULL,
            date TEXT NOT NULL,
            open REAL NOT NULL,
            high REAL NOT NULL,
            low REAL NOT NULL,
            close REAL NOT NULL,
            volume INTEGER NOT NULL,
            source TEXT NOT NULL
        )
        """
    )
    connection.executemany(
        """
        INSERT INTO snapshots (
            snapshot_id,
            symbol,
            timeframe,
            date,
            close,
            snapshot_json,
            probability_json,
            prediction_json,
            strategy_result_json,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            (
                "snapshot-b",
                "AAPL",
                "1D",
                "2026-01-02",
                102.0,
                "{}",
                "{}",
                "{}",
                "",
                "2026-01-02T00:00:00",
            ),
            (
                "snapshot-a",
                "AAPL",
                "1D",
                "2026-01-01",
                100.0,
                "{}",
                json.dumps({"confidence": 70.0}),
                json.dumps({"expected_return": 5.0}),
                json.dumps(
                    {
                        "strategy_score": 72.0,
                        "trade_grade": "Good",
                        "entry_quality": "Good",
                        "risk_rating": "Medium",
                        "reward_risk_estimate": {
                            "expected_reward_percent": 5.0,
                            "expected_risk_percent": 3.0,
                            "reward_risk_ratio": 1.6667,
                            "target_zone": {"low": 105.0, "high": 108.0},
                            "risk_zone": {"low": 97.0, "high": 99.0},
                        },
                        "notes": ["Persisted strategy fixture"],
                    }
                ),
                "2026-01-01T00:00:00",
            ),
            (
                "snapshot-c",
                "AAPL",
                "1D",
                "2026-01-05",
                105.0,
                "{}",
                "{}",
                "{}",
                "",
                "2026-01-05T00:00:00",
            ),
            (
                "snapshot-msft",
                "MSFT",
                "1D",
                "2026-01-01",
                200.0,
                "{}",
                "{}",
                "{}",
                "",
                "2026-01-01T00:00:00",
            ),
        ],
    )
    connection.executemany(
        """
        INSERT INTO outcomes (outcome_id, snapshot_id, forward_10d_return, label_10d, calculated_at)
        VALUES (?, ?, ?, ?, ?)
        """,
        [
            ("outcome-a", "snapshot-a", 4.0, "Bull", "2026-01-11"),
            ("outcome-c", "snapshot-c", -1.0, "Sideway", "2026-01-15"),
            ("outcome-msft", "snapshot-msft", 2.0, "Bull", "2026-01-11"),
        ],
    )
    connection.executemany(
        """
        INSERT INTO ohlcv_daily (symbol, date, open, high, low, close, volume, source)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            ("AAPL", "2026-01-02", 101.0, 102.0, 100.0, 101.5, 1_000_000, "fixture"),
            ("AAPL", "2026-01-03", 102.0, 103.0, 101.0, 102.5, 1_100_000, "fixture"),
            ("AAPL", "2026-01-04", 103.0, 104.0, 102.0, 103.5, 1_200_000, "fixture"),
            ("AAPL", "2026-01-06", 104.0, 105.0, 103.0, 104.5, 1_300_000, "fixture"),
            ("MSFT", "2026-01-02", 201.0, 202.0, 200.0, 201.5, 2_000_000, "fixture"),
        ],
    )
    connection.commit()
    return connection


def _schema_sql(connection: sqlite3.Connection) -> dict[str, str]:
    rows = connection.execute(
        """
        SELECT name, sql
        FROM sqlite_master
        WHERE type IN ('index', 'table')
          AND name NOT LIKE 'sqlite_autoindex_%'
        ORDER BY type, name
        """
    ).fetchall()
    return {str(name): str(sql) for name, sql in rows}


if __name__ == "__main__":
    unittest.main()
