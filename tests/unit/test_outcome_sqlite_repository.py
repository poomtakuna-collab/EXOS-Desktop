from __future__ import annotations

from contextlib import closing
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

from src.outcome_tracking import OutcomeRecord, OutcomeStatus
from src.outcome_tracking.sqlite_repository import (
    SQLiteOutcomeRepository,
    initialize_outcome_schema,
)


class SQLiteOutcomeRepositoryTest(unittest.TestCase):
    def test_schema_initialization_creates_outcome_table(self) -> None:
        with closing(_connection()) as connection:
            initialize_outcome_schema(connection)

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

            self.assertIn("outcome_records", table_names)

    def test_save_and_load_outcome(self) -> None:
        with closing(_connection()) as connection:
            repository = SQLiteOutcomeRepository(connection)
            repository.initialize_schema()
            outcome = _outcome("AAPL", "2026-07-11", 5.0)

            saved = repository.save_outcome("signal-1", outcome, outcome_id="outcome-1")
            loaded = repository.load_outcome("outcome-1")

            self.assertEqual(saved, outcome)
            self.assertEqual(loaded, outcome)

    def test_missing_outcome_lookup_returns_none(self) -> None:
        with closing(_connection()) as connection:
            repository = SQLiteOutcomeRepository(connection)
            repository.initialize_schema()

            self.assertIsNone(repository.load_outcome("missing"))

    def test_list_outcomes_preserves_insert_order_and_filters_by_symbol(self) -> None:
        with closing(_connection()) as connection:
            repository = SQLiteOutcomeRepository(connection)
            repository.initialize_schema()
            first = _outcome("AAPL", "2026-07-11", 5.0)
            second = _outcome("MSFT", "2026-07-12", 2.0)
            third = _outcome("AAPL", "2026-07-21", -2.5)

            repository.save_outcome("signal-1", first, outcome_id="outcome-1")
            repository.save_outcome("signal-2", second, outcome_id="outcome-2")
            repository.save_outcome("signal-1", third, outcome_id="outcome-3")

            self.assertEqual(repository.list_outcomes(), (first, second, third))
            self.assertEqual(repository.list_outcomes(symbol="AAPL"), (first, third))

    def test_list_outcomes_for_signal_preserves_insert_order(self) -> None:
        with closing(_connection()) as connection:
            repository = SQLiteOutcomeRepository(connection)
            repository.initialize_schema()
            first = _outcome("AAPL", "2026-07-11", 5.0)
            second = _outcome("AAPL", "2026-07-21", -2.5)

            repository.save_outcome("signal-1", first, outcome_id="outcome-1")
            repository.save_outcome("signal-2", _outcome("MSFT", "2026-07-12", 2.0), outcome_id="outcome-2")
            repository.save_outcome("signal-1", second, outcome_id="outcome-3")

            self.assertEqual(repository.list_outcomes_for_signal("signal-1"), (first, second))

    def test_save_outcome_replaces_existing_outcome_id_without_reordering(self) -> None:
        with closing(_connection()) as connection:
            repository = SQLiteOutcomeRepository(connection)
            repository.initialize_schema()
            original = _outcome("AAPL", "2026-07-11", 5.0)
            middle = _outcome("MSFT", "2026-07-12", 2.0)
            updated = _outcome("AAPL", "2026-07-15", -1.5)

            repository.save_outcome("signal-1", original, outcome_id="outcome-1")
            repository.save_outcome("signal-2", middle, outcome_id="outcome-2")
            repository.save_outcome("signal-1", updated, outcome_id="outcome-1")

            self.assertEqual(repository.load_outcome("outcome-1"), updated)
            self.assertEqual(repository.list_outcomes(), (updated, middle))

    def test_save_outcome_requires_signal_id_and_outcome_id_when_supplied(self) -> None:
        with closing(_connection()) as connection:
            repository = SQLiteOutcomeRepository(connection)
            repository.initialize_schema()

            with self.assertRaises(ValueError):
                repository.save_outcome("", _outcome("AAPL", "2026-07-11", 5.0))
            with self.assertRaises(ValueError):
                repository.save_outcome("signal-1", _outcome("AAPL", "2026-07-11", 5.0), outcome_id="")

    def test_default_outcome_id_is_deterministic(self) -> None:
        with closing(_connection()) as connection:
            repository = SQLiteOutcomeRepository(connection)
            repository.initialize_schema()
            outcome = _outcome("AAPL", "2026-07-11", 5.0)

            repository.save_outcome("signal-1", outcome)

            self.assertEqual(
                repository.load_outcome("signal-1:AAPL:2026-07-01:2026-07-11:10"),
                outcome,
            )

    def test_json_serializes_notes_safely(self) -> None:
        with closing(_connection()) as connection:
            repository = SQLiteOutcomeRepository(connection)
            repository.initialize_schema()
            outcome = _outcome(
                "AAPL",
                "2026-07-11",
                5.0,
                notes=("target reached", "closed at horizon"),
            )

            repository.save_outcome("signal-1", outcome, outcome_id="outcome-1")

            row = connection.execute(
                """
                SELECT notes_json
                FROM outcome_records
                WHERE outcome_id = ?
                """,
                ("outcome-1",),
            ).fetchone()
            self.assertEqual(json.loads(row[0]), ["target reached", "closed at horizon"])

    def test_custom_status_round_trips_without_validation_side_effects(self) -> None:
        with closing(_connection()) as connection:
            repository = SQLiteOutcomeRepository(connection)
            repository.initialize_schema()
            outcome = _outcome("AAPL", "2026-07-11", 5.0, status="custom-status")

            repository.save_outcome("signal-1", outcome, outcome_id="outcome-1")

            self.assertEqual(repository.load_outcome("outcome-1"), outcome)

    def test_persistence_across_repository_instances(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "outcomes.db"
            first_connection = sqlite3.connect(db_path)
            try:
                first_repository = SQLiteOutcomeRepository(first_connection)
                first_repository.initialize_schema()
                first_repository.save_outcome(
                    "signal-1",
                    _outcome("AAPL", "2026-07-11", 5.0),
                    outcome_id="outcome-1",
                )
            finally:
                first_connection.close()

            second_connection = sqlite3.connect(db_path)
            try:
                second_repository = SQLiteOutcomeRepository(second_connection)

                self.assertEqual(
                    second_repository.load_outcome("outcome-1"),
                    _outcome("AAPL", "2026-07-11", 5.0),
                )
                self.assertEqual(
                    second_repository.list_outcomes_for_signal("signal-1"),
                    (_outcome("AAPL", "2026-07-11", 5.0),),
                )
            finally:
                second_connection.close()


def _connection() -> sqlite3.Connection:
    return sqlite3.connect(":memory:")


def _outcome(
    symbol: str,
    evaluation_date: str,
    return_pct: float,
    *,
    notes: tuple[str, ...] = ("fixture",),
    status: OutcomeStatus | str | None = None,
) -> OutcomeRecord:
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
        outcome_status=(
            status
            if status is not None
            else OutcomeStatus.POSITIVE if return_pct > 0 else OutcomeStatus.NEGATIVE
        ),
        notes=notes,
    )


if __name__ == "__main__":
    unittest.main()
