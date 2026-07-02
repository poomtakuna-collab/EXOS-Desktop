from __future__ import annotations

import sqlite3
import tempfile
import unittest
from pathlib import Path

from src.canonical_result import (
    CanonicalIdentityV1,
    CanonicalResultV1,
    CanonicalSignalSummaryV1,
)
from src.developer import SNAPSHOT_RESET_TABLES, reset_snapshots
from src.gui.research_signal_save import save_manual_signal_candidate
from src.signal_ledger.sqlite_repository import initialize_signal_ledger_schema
from src.statistics.schema import (
    CREATE_OUTCOMES_TABLE_SQL,
    CREATE_PATTERNS_TABLE_SQL,
    CREATE_SNAPSHOTS_TABLE_SQL,
)


class DeveloperResetSnapshotsTest(unittest.TestCase):
    def test_reset_requires_explicit_confirmation(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "exos.db"
            _seed_database(db_path)

            with self.assertRaisesRegex(ValueError, "confirm=True"):
                reset_snapshots(db_path)

            self.assertEqual(_count(db_path, "daily_research_snapshots"), 1)
            self.assertEqual(_count(db_path, "signal_ledger_signals"), 1)
            self.assertEqual(_count(db_path, "snapshots"), 1)

    def test_reset_removes_snapshot_owned_tables_only(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "exos.db"
            _seed_database(db_path)

            result = reset_snapshots(db_path, confirm=True)

            self.assertEqual(
                result.deleted_by_table,
                {
                    "daily_research_snapshots": 1,
                    "signal_ledger_signals": 1,
                    "snapshots": 1,
                },
            )
            self.assertEqual(result.total_deleted, 3)
            for table_name in SNAPSHOT_RESET_TABLES:
                self.assertEqual(_count(db_path, table_name), 0)
            self.assertEqual(_count(db_path, "ohlcv_daily"), 1)
            self.assertEqual(_count(db_path, "settings"), 1)
            self.assertEqual(_count(db_path, "outcome_records"), 1)
            self.assertEqual(_count(db_path, "signal_ledger_outcomes"), 1)
            self.assertEqual(_count(db_path, "outcomes"), 1)
            self.assertEqual(_count(db_path, "patterns"), 1)
            self.assertEqual(_count(db_path, "backtest_runs"), 1)

    def test_missing_database_is_safe_noop(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "missing.db"

            result = reset_snapshots(db_path, confirm=True)

            self.assertEqual(result.total_deleted, 0)
            self.assertFalse(db_path.exists())

    def test_normal_manual_snapshot_save_does_not_reset_existing_snapshots(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "exos.db"
            _seed_market_learning_snapshot(db_path)

            result = save_manual_signal_candidate(
                _canonical_result(),
                database_path=db_path,
            )

            self.assertTrue(result.saved)
            self.assertEqual(_count(db_path, "daily_research_snapshots"), 1)
            self.assertEqual(_count(db_path, "signal_ledger_signals"), 1)
            self.assertEqual(_count(db_path, "snapshots"), 1)


def _seed_database(db_path: Path) -> None:
    connection = sqlite3.connect(db_path)
    try:
        initialize_signal_ledger_schema(connection)
        connection.execute(CREATE_SNAPSHOTS_TABLE_SQL)
        connection.execute(CREATE_OUTCOMES_TABLE_SQL)
        connection.execute(CREATE_PATTERNS_TABLE_SQL)
        connection.execute(
            """
            CREATE TABLE daily_research_snapshots (
                snapshot_record_id TEXT PRIMARY KEY,
                symbol TEXT NOT NULL,
                market_date TEXT NOT NULL,
                timeframe TEXT NOT NULL,
                canonical_schema_version TEXT NOT NULL,
                persistence_version TEXT NOT NULL,
                canonical_snapshot_json TEXT NOT NULL,
                signal_id TEXT,
                payload_hash TEXT NOT NULL,
                source TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE outcome_records (
                outcome_row_id INTEGER PRIMARY KEY AUTOINCREMENT,
                outcome_id TEXT NOT NULL UNIQUE,
                signal_id TEXT NOT NULL,
                symbol TEXT NOT NULL,
                signal_date TEXT NOT NULL,
                evaluation_date TEXT NOT NULL,
                horizon_days INTEGER,
                entry_price REAL,
                close_price REAL,
                return_pct REAL,
                max_runup_pct REAL,
                max_drawdown_pct REAL,
                hit_target INTEGER,
                hit_stop INTEGER,
                outcome_status TEXT NOT NULL,
                notes_json TEXT NOT NULL
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE ohlcv_daily (
                symbol TEXT NOT NULL,
                date TEXT NOT NULL,
                open REAL,
                high REAL,
                low REAL,
                close REAL,
                volume INTEGER
            )
            """
        )
        connection.execute("CREATE TABLE settings (key TEXT PRIMARY KEY, value TEXT)")
        connection.execute("CREATE TABLE backtest_runs (run_id TEXT PRIMARY KEY)")
        _insert_snapshot_rows(connection)
        connection.execute(
            """
            INSERT INTO daily_research_snapshots (
                snapshot_record_id,
                symbol,
                market_date,
                timeframe,
                canonical_schema_version,
                persistence_version,
                canonical_snapshot_json,
                signal_id,
                payload_hash,
                source,
                created_at
            )
            VALUES ('snapshot-v2-1', 'AAPL', '2026-07-02', '1D', 'canonical_result_v1',
                    'daily_research_snapshot_v2', '{}', 'signal-1', 'hash', 'test', '2026-07-02')
            """
        )
        connection.execute(
            """
            INSERT INTO signal_ledger_signals (
                signal_id,
                symbol,
                signal_date,
                snapshot_id,
                snapshot_date,
                timeframe,
                snapshot_source,
                context_summary_json,
                strategy_summary_json,
                signal_type,
                confidence,
                notes_json
            )
            VALUES ('signal-1', 'AAPL', '2026-07-02', 'snapshot-1', '2026-07-02',
                    '1D', 'test', '{}', '{}', 'setup', 70.0, '[]')
            """
        )
        connection.execute(
            """
            INSERT INTO signal_ledger_outcomes (
                signal_id,
                symbol,
                signal_date,
                evaluation_date,
                horizon_days,
                outcome_status,
                notes_json
            )
            VALUES ('signal-1', 'AAPL', '2026-07-02', '2026-07-12', 10, 'complete', '[]')
            """
        )
        connection.execute(
            """
            INSERT INTO outcome_records (
                outcome_id,
                signal_id,
                symbol,
                signal_date,
                evaluation_date,
                horizon_days,
                outcome_status,
                notes_json
            )
            VALUES ('outcome-record-1', 'signal-1', 'AAPL', '2026-07-02',
                    '2026-07-12', 10, 'complete', '[]')
            """
        )
        connection.execute(
            """
            INSERT INTO outcomes (outcome_id, snapshot_id, forward_10d_return, label_10d, calculated_at)
            VALUES ('outcome-1', 'snapshot-1', 4.0, 'Bull', '2026-07-12')
            """
        )
        connection.execute(
            """
            INSERT INTO patterns (
                pattern_id,
                sample_count,
                confidence,
                created_at,
                updated_at
            )
            VALUES ('pattern-1', 1, 50.0, '2026-07-02', '2026-07-02')
            """
        )
        connection.execute(
            """
            INSERT INTO ohlcv_daily (symbol, date, open, high, low, close, volume)
            VALUES ('AAPL', '2026-07-02', 100.0, 101.0, 99.0, 100.5, 1000)
            """
        )
        connection.execute("INSERT INTO settings (key, value) VALUES ('theme', 'dark')")
        connection.execute("INSERT INTO backtest_runs (run_id) VALUES ('run-1')")
        connection.commit()
    finally:
        connection.close()


def _seed_market_learning_snapshot(db_path: Path) -> None:
    connection = sqlite3.connect(db_path)
    try:
        connection.execute(CREATE_SNAPSHOTS_TABLE_SQL)
        _insert_snapshot_rows(connection)
        connection.commit()
    finally:
        connection.close()


def _insert_snapshot_rows(connection: sqlite3.Connection) -> None:
    connection.execute(
        """
        INSERT INTO snapshots (
            snapshot_id,
            symbol,
            timeframe,
            date,
            close,
            snapshot_json,
            created_at
        )
        VALUES ('snapshot-1', 'AAPL', '1D', '2026-07-02', 100.5, '{}', '2026-07-02')
        """
    )


def _count(db_path: Path, table_name: str) -> int:
    connection = sqlite3.connect(db_path)
    try:
        row = connection.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()
        return int(row[0] or 0)
    finally:
        connection.close()


def _canonical_result() -> CanonicalResultV1:
    return CanonicalResultV1(
        identity=CanonicalIdentityV1(
            symbol="MSFT",
            timeframe="1D",
            snapshot_id="snapshot-save-flow",
            snapshot_date="2026-07-02",
            analysis_date="2026-07-03",
            source="analysis_pipeline_v2",
        ),
        signal_summary=CanonicalSignalSummaryV1(
            symbol="MSFT",
            signal_date="2026-07-03",
            timeframe="1D",
            signal_type="setup",
            confidence=77.0,
            snapshot_id="snapshot-save-flow",
            snapshot_date="2026-07-02",
            notes=("manual save candidate",),
        ),
    )


if __name__ == "__main__":
    unittest.main()
