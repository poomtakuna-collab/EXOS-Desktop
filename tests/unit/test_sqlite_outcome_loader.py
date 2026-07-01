from __future__ import annotations

from contextlib import closing
import sqlite3
import sys
import unittest

from src.backtest.data import SQLiteOutcomeLoader


class SQLiteOutcomeLoaderTest(unittest.TestCase):
    def test_load_outcome_by_snapshot_id_reads_existing_record(self) -> None:
        with closing(_outcome_connection()) as connection:
            loader = SQLiteOutcomeLoader(connection)

            row = loader.load_outcome("snapshot-b")

            self.assertIsNotNone(row)
            self.assertEqual(row["snapshot_id"], "snapshot-b")
            self.assertEqual(row["outcome_id"], "outcome-b")

    def test_load_outcomes_returns_matching_snapshot_ids_only(self) -> None:
        with closing(_outcome_connection()) as connection:
            loader = SQLiteOutcomeLoader(connection)

            rows = loader.load_outcomes(["snapshot-c", "snapshot-a"])

            self.assertEqual(set(rows), {"snapshot-a", "snapshot-c"})
            self.assertEqual(rows["snapshot-a"]["outcome_id"], "outcome-a")
            self.assertEqual(rows["snapshot-c"]["outcome_id"], "outcome-c")
            self.assertNotIn("snapshot-b", rows)

    def test_empty_snapshot_id_list_returns_empty_dict_without_table_access(self) -> None:
        with closing(sqlite3.connect(":memory:")) as connection:
            loader = SQLiteOutcomeLoader(connection)

            self.assertEqual(loader.load_outcomes([]), {})

    def test_ordering_is_stable(self) -> None:
        with closing(_outcome_connection()) as connection:
            loader = SQLiteOutcomeLoader(connection)

            rows = loader.load_outcomes(["snapshot-c", "snapshot-a", "snapshot-b"])

            self.assertEqual(list(rows), ["snapshot-a", "snapshot-b", "snapshot-c"])

    def test_duplicate_snapshot_id_uses_first_outcome_by_outcome_id(self) -> None:
        with closing(_outcome_connection()) as connection:
            connection.execute(
                """
                INSERT INTO outcomes (
                    outcome_id,
                    snapshot_id,
                    forward_10d_return,
                    label_10d,
                    calculated_at
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                ("outcome-a-duplicate", "snapshot-a", 99.0, "Duplicate", "2026-01-07"),
            )
            connection.commit()
            loader = SQLiteOutcomeLoader(connection)

            rows = loader.load_outcomes(["snapshot-a"])

            self.assertEqual(rows["snapshot-a"]["outcome_id"], "outcome-a")

    def test_missing_outcomes_table_fails_clearly(self) -> None:
        with closing(sqlite3.connect(":memory:")) as connection:
            loader = SQLiteOutcomeLoader(connection)

            with self.assertRaisesRegex(RuntimeError, "outcomes table is required"):
                loader.load_outcomes(["snapshot-a"])

    def test_loader_does_not_write_to_database(self) -> None:
        with closing(_outcome_connection()) as connection:
            loader = SQLiteOutcomeLoader(connection)
            changes_before = connection.total_changes
            schema_before = _schema_sql(connection)

            loader.load_outcome("snapshot-a")
            loader.load_outcomes(["snapshot-a", "snapshot-c"])

            self.assertEqual(connection.total_changes, changes_before)
            self.assertEqual(_schema_sql(connection), schema_before)

    def test_loader_does_not_import_live_data_ai_network_or_broker_modules(self) -> None:
        before_modules = set(sys.modules)
        with closing(_outcome_connection()) as connection:
            loader = SQLiteOutcomeLoader(connection)
            loader.load_outcomes(["snapshot-a"])

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


def _outcome_connection() -> sqlite3.Connection:
    connection = sqlite3.connect(":memory:")
    connection.execute(
        """
        CREATE TABLE outcomes (
            outcome_id TEXT PRIMARY KEY,
            snapshot_id TEXT NOT NULL,
            forward_5d_return REAL,
            forward_10d_return REAL,
            forward_20d_return REAL,
            max_gain_10d REAL,
            max_drawdown_10d REAL,
            hit_5pct_10d INTEGER,
            hit_10pct_10d INTEGER,
            label_10d TEXT,
            calculated_at TEXT NOT NULL
        )
        """
    )
    connection.executemany(
        """
        INSERT INTO outcomes (
            outcome_id,
            snapshot_id,
            forward_5d_return,
            forward_10d_return,
            forward_20d_return,
            max_gain_10d,
            max_drawdown_10d,
            hit_5pct_10d,
            hit_10pct_10d,
            label_10d,
            calculated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            ("outcome-b", "snapshot-b", 1.0, 2.0, 3.0, 4.0, -1.0, 0, 0, "Bull", "2026-01-02"),
            ("outcome-a", "snapshot-a", 2.0, 3.0, 4.0, 5.0, -2.0, 1, 0, "Bull", "2026-01-01"),
            ("outcome-c", "snapshot-c", -1.0, -2.0, -3.0, 1.0, -5.0, 0, 0, "Bear", "2026-01-03"),
            ("outcome-z", "snapshot-z", 9.0, 9.0, 9.0, 9.0, -1.0, 1, 1, "Ignored", "2026-01-04"),
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
