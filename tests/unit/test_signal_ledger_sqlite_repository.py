from __future__ import annotations

import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

from src.outcome_tracking import OutcomeRecord, OutcomeStatus
from src.signal_ledger import SignalRecord, SignalSnapshotReference, SignalType
from src.signal_ledger.sqlite_repository import (
    SQLiteSignalLedgerRepository,
    initialize_signal_ledger_schema,
)


class SQLiteSignalLedgerRepositoryTest(unittest.TestCase):
    def test_schema_initialization_creates_tables(self) -> None:
        with _connection() as connection:
            initialize_signal_ledger_schema(connection)

            table_names = {
                row[0]
                for row in connection.execute(
                    """
                    SELECT name
                    FROM sqlite_master
                    WHERE type = 'table'
                    """
                ).fetchall()
            }

            self.assertIn("signal_ledger_signals", table_names)
            self.assertIn("signal_ledger_outcomes", table_names)

    def test_save_and_load_signal(self) -> None:
        with _connection() as connection:
            repository = SQLiteSignalLedgerRepository(connection)
            repository.initialize_schema()
            signal = _signal(signal_id="signal-1", symbol="AAPL")

            saved = repository.save_signal(signal)
            loaded = repository.load_signal("signal-1")

            self.assertEqual(saved, signal)
            self.assertEqual(loaded, signal)

    def test_list_signals_preserves_insert_order_and_filters_by_symbol(self) -> None:
        with _connection() as connection:
            repository = SQLiteSignalLedgerRepository(connection)
            repository.initialize_schema()
            first = _signal(signal_id="signal-1", symbol="AAPL")
            second = _signal(signal_id="signal-2", symbol="MSFT")
            third = _signal(signal_id="signal-3", symbol="AAPL")

            repository.save_signal(first)
            repository.save_signal(second)
            repository.save_signal(third)

            self.assertEqual(repository.list_signals(), (first, second, third))
            self.assertEqual(repository.list_signals(symbol="AAPL"), (first, third))

    def test_save_and_list_outcomes_for_signal(self) -> None:
        with _connection() as connection:
            repository = SQLiteSignalLedgerRepository(connection)
            repository.initialize_schema()
            first = _outcome("AAPL", "2026-07-11", 5.0)
            second = _outcome("AAPL", "2026-07-21", -2.5)

            saved_first = repository.save_outcome("signal-1", first)
            saved_second = repository.save_outcome("signal-1", second)

            self.assertEqual(saved_first, first)
            self.assertEqual(saved_second, second)
            self.assertEqual(repository.list_outcomes_for_signal("signal-1"), (first, second))

    def test_persistence_across_repository_instances(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "signal-ledger.db"
            first_connection = sqlite3.connect(db_path)
            try:
                first_repository = SQLiteSignalLedgerRepository(first_connection)
                first_repository.initialize_schema()
                first_repository.save_signal(_signal(signal_id="signal-1", symbol="AAPL"))
                first_repository.save_outcome(
                    "signal-1",
                    _outcome("AAPL", "2026-07-11", 5.0),
                )
            finally:
                first_connection.close()

            second_connection = sqlite3.connect(db_path)
            try:
                second_repository = SQLiteSignalLedgerRepository(second_connection)

                self.assertEqual(
                    second_repository.load_signal("signal-1"),
                    _signal(signal_id="signal-1", symbol="AAPL"),
                )
                self.assertEqual(
                    second_repository.list_outcomes_for_signal("signal-1"),
                    (_outcome("AAPL", "2026-07-11", 5.0),),
                )
            finally:
                second_connection.close()

    def test_missing_signal_lookup_returns_none(self) -> None:
        with _connection() as connection:
            repository = SQLiteSignalLedgerRepository(connection)
            repository.initialize_schema()

            self.assertIsNone(repository.load_signal("missing"))

    def test_missing_signal_outcomes_are_empty(self) -> None:
        with _connection() as connection:
            repository = SQLiteSignalLedgerRepository(connection)
            repository.initialize_schema()

            self.assertEqual(repository.list_outcomes_for_signal("missing"), ())

    def test_save_signal_replaces_existing_signal_id(self) -> None:
        with _connection() as connection:
            repository = SQLiteSignalLedgerRepository(connection)
            repository.initialize_schema()
            original = _signal(signal_id="signal-1", symbol="AAPL")
            updated = _signal(signal_id="signal-1", symbol="MSFT")

            repository.save_signal(original)
            repository.save_signal(updated)

            self.assertEqual(repository.load_signal("signal-1"), updated)
            self.assertEqual(repository.list_signals(), (updated,))

    def test_save_signal_requires_signal_id(self) -> None:
        with _connection() as connection:
            repository = SQLiteSignalLedgerRepository(connection)
            repository.initialize_schema()

            with self.assertRaises(ValueError):
                repository.save_signal(SignalRecord())

    def test_save_outcome_requires_signal_id(self) -> None:
        with _connection() as connection:
            repository = SQLiteSignalLedgerRepository(connection)
            repository.initialize_schema()

            with self.assertRaises(ValueError):
                repository.save_outcome("", _outcome("AAPL", "2026-07-11", 5.0))

    def test_nested_fields_are_json_serialized_safely(self) -> None:
        with _connection() as connection:
            repository = SQLiteSignalLedgerRepository(connection)
            repository.initialize_schema()
            signal = _signal(
                signal_id="signal-1",
                symbol="AAPL",
                context_summary={
                    "market": {"trend": "up"},
                    "tags": ["context", "fixture"],
                },
            )
            outcome = _outcome("AAPL", "2026-07-11", 5.0)

            repository.save_signal(signal)
            repository.save_outcome("signal-1", outcome)

            signal_row = connection.execute(
                """
                SELECT context_summary_json, strategy_summary_json, notes_json
                FROM signal_ledger_signals
                WHERE signal_id = ?
                """,
                ("signal-1",),
            ).fetchone()
            outcome_row = connection.execute(
                """
                SELECT notes_json
                FROM signal_ledger_outcomes
                WHERE signal_id = ?
                """,
                ("signal-1",),
            ).fetchone()

            self.assertEqual(
                json.loads(signal_row[0]),
                {"market": {"trend": "up"}, "tags": ["context", "fixture"]},
            )
            self.assertEqual(json.loads(signal_row[1]), {"strategy_score": 72.5})
            self.assertEqual(json.loads(signal_row[2]), ["fixture"])
            self.assertEqual(json.loads(outcome_row[0]), ["fixture"])


def _connection() -> sqlite3.Connection:
    return sqlite3.connect(":memory:")


def _signal(
    *,
    signal_id: str,
    symbol: str,
    context_summary: dict[str, object] | None = None,
) -> SignalRecord:
    return SignalRecord(
        signal_id=signal_id,
        symbol=symbol,
        signal_date="2026-07-01",
        snapshot_reference=SignalSnapshotReference(
            snapshot_id="snapshot-1",
            snapshot_date="2026-07-01",
            timeframe="1D",
            source="fixture",
        ),
        context_summary=context_summary or {"market": {"trend": "up"}},
        strategy_summary={"strategy_score": 72.5},
        signal_type=SignalType.SETUP,
        confidence=75.0,
        notes=("fixture",),
    )


def _outcome(symbol: str, evaluation_date: str, return_pct: float) -> OutcomeRecord:
    return OutcomeRecord(
        symbol=symbol,
        signal_date="2026-07-01",
        evaluation_date=evaluation_date,
        horizon_days=10,
        entry_price=100.0,
        close_price=100.0 + return_pct,
        return_pct=return_pct,
        max_runup_pct=max(return_pct, 0.0),
        max_drawdown_pct=min(return_pct, 0.0),
        hit_target=False,
        hit_stop=False,
        outcome_status=OutcomeStatus.POSITIVE if return_pct > 0 else OutcomeStatus.NEGATIVE,
        notes=("fixture",),
    )


if __name__ == "__main__":
    unittest.main()
