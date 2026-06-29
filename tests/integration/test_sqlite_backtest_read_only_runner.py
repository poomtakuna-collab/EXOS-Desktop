from __future__ import annotations

import http.client
import json
import socket
import sqlite3
import sys
import unittest
import urllib.request
from collections.abc import Iterator
from contextlib import ExitStack, closing, contextmanager
from unittest.mock import patch

from src.backtest import SimulationConfig, run_sqlite_backtest_read_only
from src.backtest.data import SnapshotQuery


class SQLiteBacktestReadOnlyRunnerIntegrationTest(unittest.TestCase):
    def test_db_rows_flow_to_dataset_backtest_result_and_report(self) -> None:
        with closing(_runner_connection()) as connection:
            schema_before = _schema_sql(connection)
            changes_before = connection.total_changes

            with _blocked_external_access():
                run = run_sqlite_backtest_read_only(
                    connection=connection,
                    query=SnapshotQuery(symbol="AAPL", timeframe="1D"),
                    config=SimulationConfig(horizon_days=2),
                )

            self.assertEqual(connection.total_changes, changes_before)
            self.assertEqual(_schema_sql(connection), schema_before)

        self.assertEqual(
            [item.snapshot["snapshot_id"] for item in run.dataset.inputs],
            ["snapshot-a", "snapshot-b", "snapshot-c"],
        )
        self.assertEqual(run.result.attempted_trades, 3)
        self.assertEqual(run.result.completed_trades, 2)
        self.assertEqual(run.result.total_trades, 2)
        self.assertEqual(run.result.skipped_trades, 1)
        self.assertEqual(run.result.breakeven_trades, 1)
        self.assertEqual(run.result.winning_trades, 1)
        self.assertEqual(run.result.losing_trades, 0)

        self.assertEqual(run.report.attempted_trades, 3)
        self.assertEqual(run.report.completed_trades, 2)
        self.assertEqual(run.report.total_trades, 2)
        self.assertEqual(run.report.skipped_trades, 1)
        self.assertEqual(run.report.breakeven_trades, 1)

    def test_skipped_records_are_preserved_deterministically(self) -> None:
        with closing(_runner_connection()) as connection:
            run = run_sqlite_backtest_read_only(
                connection=connection,
                query=SnapshotQuery(symbol="AAPL", timeframe="1D"),
                config=SimulationConfig(horizon_days=2),
            )

        self.assertEqual(
            run.skipped_records,
            [
                {
                    "sequence_number": 3,
                    "snapshot_id": "snapshot-c",
                    "symbol": "AAPL",
                    "timeframe": "1D",
                    "date": "2026-01-03",
                    "reason": "Missing outcome",
                },
                {
                    "sequence_number": 3,
                    "snapshot_id": "snapshot-c",
                    "symbol": "AAPL",
                    "timeframe": "1D",
                    "date": "2026-01-03",
                    "reason": "Insufficient future rows",
                },
            ],
        )

    def test_output_does_not_contain_trade_recommendations(self) -> None:
        with closing(_runner_connection()) as connection:
            run = run_sqlite_backtest_read_only(
                connection=connection,
                query=SnapshotQuery(symbol="AAPL", timeframe="1D"),
                config=SimulationConfig(horizon_days=2),
            )

        output_text = str(
            {
                "dataset": run.dataset,
                "result": run.result,
                "report": run.report,
                "skipped_records": run.skipped_records,
            }
        ).lower()
        for recommendation in ("buy", "sell", "hold"):
            self.assertNotIn(recommendation, output_text)


@contextmanager
def _blocked_external_access() -> Iterator[None]:
    with ExitStack() as stack:
        stack.enter_context(
            patch.object(
                socket,
                "create_connection",
                side_effect=AssertionError("integration test must not access the network"),
            )
        )
        stack.enter_context(
            patch.object(
                urllib.request,
                "urlopen",
                side_effect=AssertionError("integration test must not access live data"),
            )
        )
        stack.enter_context(
            patch.object(
                http.client.HTTPConnection,
                "connect",
                side_effect=AssertionError("integration test must not access HTTP"),
            )
        )
        before_modules = set(sys.modules)
        yield
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
        forbidden_imports = {
            module_name
            for module_name in imported_modules
            if module_name.startswith(forbidden_prefixes)
        }
        if forbidden_imports:
            raise AssertionError(f"forbidden imports: {sorted(forbidden_imports)}")


def _runner_connection() -> sqlite3.Connection:
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
    target_strategy_json = json.dumps(
        {
            "strategy_score": 70.0,
            "trade_grade": "Good",
            "entry_quality": "Good",
            "risk_rating": "Medium",
            "reward_risk_estimate": {
                "expected_reward_percent": 5.0,
                "expected_risk_percent": 5.0,
                "reward_risk_ratio": 1.0,
                "target_zone": {"low": 105.0, "high": 107.0},
                "risk_zone": {"low": 95.0, "high": 98.0},
            },
            "notes": ["Persisted strategy fixture"],
        }
    )
    timeout_strategy_json = json.dumps(
        {
            "strategy_score": 70.0,
            "trade_grade": "Good",
            "entry_quality": "Good",
            "risk_rating": "Medium",
            "reward_risk_estimate": {
                "expected_reward_percent": 10.0,
                "expected_risk_percent": 5.0,
                "reward_risk_ratio": 2.0,
                "target_zone": {"low": 110.0, "high": 112.0},
                "risk_zone": {"low": 95.0, "high": 98.0},
            },
            "notes": ["Persisted strategy fixture"],
        }
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
            ("snapshot-b", "AAPL", "1D", "2026-01-02", 100.0, "{}", "{}", "{}", timeout_strategy_json, "2026-01-02T00:00:00"),
            ("snapshot-a", "AAPL", "1D", "2026-01-01", 100.0, "{}", "{}", "{}", target_strategy_json, "2026-01-01T00:00:00"),
            ("snapshot-c", "AAPL", "1D", "2026-01-03", 100.0, "{}", "{}", "{}", target_strategy_json, "2026-01-03T00:00:00"),
        ],
    )
    connection.executemany(
        """
        INSERT INTO outcomes (outcome_id, snapshot_id, forward_10d_return, label_10d, calculated_at)
        VALUES (?, ?, ?, ?, ?)
        """,
        [
            ("outcome-a", "snapshot-a", 5.0, "Bull", "2026-01-11"),
            ("outcome-b", "snapshot-b", 0.0, "Sideway", "2026-01-12"),
        ],
    )
    connection.executemany(
        """
        INSERT INTO ohlcv_daily (symbol, date, open, high, low, close, volume, source)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            ("AAPL", "2026-01-02", 100.0, 104.0, 99.0, 103.0, 1_000_000, "fixture"),
            ("AAPL", "2026-01-03", 100.0, 105.0, 100.0, 105.0, 1_100_000, "fixture"),
            ("AAPL", "2026-01-04", 100.0, 104.0, 99.0, 100.0, 1_200_000, "fixture"),
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
