from __future__ import annotations

from contextlib import closing
import sqlite3
import sys
import unittest

from src.backtest.data import SQLiteSnapshotLoader, SnapshotQuery


class SQLiteSnapshotLoaderTest(unittest.TestCase):
    def test_load_snapshot_by_id_reads_existing_record(self) -> None:
        with closing(_snapshot_connection()) as connection:
            loader = SQLiteSnapshotLoader(connection)

            row = loader.load_snapshot("snapshot-b")

            self.assertIsNotNone(row)
            self.assertEqual(row["snapshot_id"], "snapshot-b")
            self.assertEqual(row["symbol"], "AAPL")
            self.assertEqual(row["date"], "2026-01-02")

    def test_symbol_timeframe_date_and_limit_filters_work(self) -> None:
        with closing(_snapshot_connection()) as connection:
            loader = SQLiteSnapshotLoader(connection)

            rows = loader.load_snapshots(
                SnapshotQuery(
                    symbol="AAPL",
                    timeframe="1D",
                    start_date="2026-01-02",
                    end_date="2026-01-03",
                    limit=1,
                )
            )

            self.assertEqual([row["snapshot_id"] for row in rows], ["snapshot-b"])

    def test_symbols_tuple_filter_is_supported_for_backward_compatibility(self) -> None:
        with closing(_snapshot_connection()) as connection:
            loader = SQLiteSnapshotLoader(connection)

            rows = loader.load_snapshots(SnapshotQuery(symbols=("MSFT",)))

            self.assertEqual([row["snapshot_id"] for row in rows], ["snapshot-c"])

    def test_ordering_is_stable(self) -> None:
        with closing(_snapshot_connection()) as connection:
            loader = SQLiteSnapshotLoader(connection)

            rows = loader.load_snapshots(SnapshotQuery())

            self.assertEqual(
                [row["snapshot_id"] for row in rows],
                ["snapshot-b", "snapshot-a", "snapshot-d", "snapshot-c"],
            )

    def test_missing_snapshots_table_fails_clearly(self) -> None:
        with closing(sqlite3.connect(":memory:")) as connection:
            loader = SQLiteSnapshotLoader(connection)

            with self.assertRaisesRegex(RuntimeError, "snapshots table is required"):
                loader.load_snapshots(SnapshotQuery())

    def test_loader_does_not_write_to_database(self) -> None:
        with closing(_snapshot_connection()) as connection:
            loader = SQLiteSnapshotLoader(connection)
            changes_before = connection.total_changes
            schema_before = _schema_sql(connection)

            loader.load_snapshot("snapshot-a")
            loader.load_snapshots(SnapshotQuery(symbol="AAPL", limit=2))

            self.assertEqual(connection.total_changes, changes_before)
            self.assertEqual(_schema_sql(connection), schema_before)

    def test_loader_does_not_import_live_data_ai_network_or_broker_modules(self) -> None:
        before_modules = set(sys.modules)
        with closing(_snapshot_connection()) as connection:
            loader = SQLiteSnapshotLoader(connection)
            loader.load_snapshots(SnapshotQuery(symbol="AAPL"))

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


def _snapshot_connection() -> sqlite3.Connection:
    connection = sqlite3.connect(":memory:")
    connection.execute(
        """
        CREATE TABLE snapshots (
            snapshot_id TEXT PRIMARY KEY,
            symbol TEXT NOT NULL,
            timeframe TEXT NOT NULL,
            date TEXT NOT NULL,
            close REAL,
            exos_score REAL,
            trend_state TEXT,
            squeeze_state TEXT,
            market_structure_state TEXT,
            snapshot_json TEXT NOT NULL,
            created_at TEXT NOT NULL
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
            exos_score,
            trend_state,
            squeeze_state,
            market_structure_state,
            snapshot_json,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            (
                "snapshot-a",
                "AAPL",
                "1D",
                "2026-01-03",
                103.0,
                70.0,
                "Bull",
                "Released",
                "Breakout",
                "{}",
                "2026-01-03T00:00:00",
            ),
            (
                "snapshot-b",
                "AAPL",
                "1D",
                "2026-01-02",
                102.0,
                68.0,
                "Bull",
                "Released",
                "Breakout",
                "{}",
                "2026-01-02T00:00:00",
            ),
            (
                "snapshot-c",
                "MSFT",
                "1D",
                "2026-01-01",
                201.0,
                65.0,
                "Sideway",
                "Compression",
                "Range",
                "{}",
                "2026-01-01T00:00:00",
            ),
            (
                "snapshot-d",
                "AAPL",
                "1W",
                "2026-01-01",
                101.0,
                72.0,
                "Bull",
                "Released",
                "Breakout",
                "{}",
                "2026-01-01T00:00:00",
            ),
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
