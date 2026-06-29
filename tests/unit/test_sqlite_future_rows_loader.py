from __future__ import annotations

import sqlite3
import sys
import unittest

from src.backtest.data import SQLiteFutureRowsLoader


class SQLiteFutureRowsLoaderTest(unittest.TestCase):
    def test_load_future_rows_after_snapshot_date_only(self) -> None:
        with _market_connection() as connection:
            loader = SQLiteFutureRowsLoader(connection)

            rows = loader.load_future_rows("AAPL", "1D", "2026-01-02", 10)

            self.assertEqual([row["date"] for row in rows], ["2026-01-03", "2026-01-04"])
            self.assertTrue(all(row["symbol"] == "AAPL" for row in rows))

    def test_horizon_limits_rows(self) -> None:
        with _market_connection() as connection:
            loader = SQLiteFutureRowsLoader(connection)

            rows = loader.load_future_rows("AAPL", "1D", "2026-01-01", 1)

            self.assertEqual([row["date"] for row in rows], ["2026-01-02"])

    def test_groups_rows_by_snapshot_id(self) -> None:
        with _market_connection() as connection:
            loader = SQLiteFutureRowsLoader(connection)
            snapshots = _snapshot_rows(connection)

            rows_by_snapshot = loader.load_future_rows_for_snapshots(
                snapshots=snapshots,
                horizon_days=2,
            )

            self.assertEqual(
                list(rows_by_snapshot),
                ["snapshot-a", "snapshot-b", "snapshot-c"],
            )
            self.assertEqual(
                [row["date"] for row in rows_by_snapshot["snapshot-a"]],
                ["2026-01-02", "2026-01-03"],
            )
            self.assertEqual(
                [row["date"] for row in rows_by_snapshot["snapshot-b"]],
                ["2026-01-03", "2026-01-04"],
            )
            self.assertEqual(
                [row["date"] for row in rows_by_snapshot["snapshot-c"]],
                ["2026-01-02", "2026-01-03"],
            )

    def test_zero_horizon_returns_empty_rows_without_table_access(self) -> None:
        with sqlite3.connect(":memory:") as connection:
            loader = SQLiteFutureRowsLoader(connection)

            self.assertEqual(loader.load_future_rows("AAPL", "1D", "2026-01-01", 0), [])

    def test_missing_ohlcv_table_fails_clearly(self) -> None:
        with sqlite3.connect(":memory:") as connection:
            loader = SQLiteFutureRowsLoader(connection)

            with self.assertRaisesRegex(RuntimeError, "ohlcv_daily table is required"):
                loader.load_future_rows("AAPL", "1D", "2026-01-01", 2)

    def test_non_daily_timeframe_fails_clearly(self) -> None:
        with _market_connection() as connection:
            loader = SQLiteFutureRowsLoader(connection)

            with self.assertRaisesRegex(ValueError, "1D timeframe only"):
                loader.load_future_rows("AAPL", "1W", "2026-01-01", 2)

    def test_loader_does_not_write_to_database(self) -> None:
        with _market_connection() as connection:
            loader = SQLiteFutureRowsLoader(connection)
            changes_before = connection.total_changes
            schema_before = _schema_sql(connection)

            loader.load_future_rows("AAPL", "1D", "2026-01-01", 2)
            loader.load_future_rows_for_snapshots(_snapshot_rows(connection), 1)

            self.assertEqual(connection.total_changes, changes_before)
            self.assertEqual(_schema_sql(connection), schema_before)

    def test_loader_does_not_import_live_data_ai_network_or_broker_modules(self) -> None:
        before_modules = set(sys.modules)
        with _market_connection() as connection:
            loader = SQLiteFutureRowsLoader(connection)
            loader.load_future_rows("AAPL", "1D", "2026-01-01", 2)

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


def _market_connection() -> sqlite3.Connection:
    connection = sqlite3.connect(":memory:")
    connection.execute(
        """
        CREATE TABLE snapshots (
            snapshot_id TEXT PRIMARY KEY,
            symbol TEXT NOT NULL,
            timeframe TEXT NOT NULL,
            date TEXT NOT NULL
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
        INSERT INTO snapshots (snapshot_id, symbol, timeframe, date)
        VALUES (?, ?, ?, ?)
        """,
        [
            ("snapshot-b", "AAPL", "1D", "2026-01-02"),
            ("snapshot-c", "MSFT", "1D", "2026-01-01"),
            ("snapshot-a", "AAPL", "1D", "2026-01-01"),
        ],
    )
    connection.executemany(
        """
        INSERT INTO ohlcv_daily (symbol, date, open, high, low, close, volume, source)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            ("AAPL", "2026-01-01", 100.0, 101.0, 99.0, 100.5, 1_000_000, "fixture"),
            ("AAPL", "2026-01-02", 101.0, 102.0, 100.0, 101.5, 1_100_000, "fixture"),
            ("AAPL", "2026-01-03", 102.0, 103.0, 101.0, 102.5, 1_200_000, "fixture"),
            ("AAPL", "2026-01-04", 103.0, 104.0, 102.0, 103.5, 1_300_000, "fixture"),
            ("MSFT", "2026-01-01", 200.0, 201.0, 199.0, 200.5, 2_000_000, "fixture"),
            ("MSFT", "2026-01-02", 201.0, 202.0, 200.0, 201.5, 2_100_000, "fixture"),
            ("MSFT", "2026-01-03", 202.0, 203.0, 201.0, 202.5, 2_200_000, "fixture"),
        ],
    )
    connection.commit()
    return connection


def _snapshot_rows(connection: sqlite3.Connection) -> list[dict[str, object]]:
    rows = connection.execute(
        """
        SELECT snapshot_id, symbol, timeframe, date
        FROM snapshots
        """
    ).fetchall()
    return [
        {
            "snapshot_id": row[0],
            "symbol": row[1],
            "timeframe": row[2],
            "date": row[3],
        }
        for row in rows
    ]


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
