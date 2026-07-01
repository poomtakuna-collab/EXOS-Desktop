from __future__ import annotations

import json
import sqlite3
import unittest

from src.outcome_tracking import (
    OutcomeRecord,
    OutcomeStatus,
    evaluate_saved_signal_outcomes,
)
from src.outcome_tracking.sqlite_repository import SQLiteOutcomeRepository
from src.signal_ledger import SignalRecord, SignalSnapshotReference, SignalType
from src.signal_ledger.sqlite_repository import SQLiteSignalLedgerRepository


class OutcomeEvaluationTest(unittest.TestCase):
    def test_signal_with_enough_future_rows_gets_outcome_persisted(self) -> None:
        with _repositories() as repositories:
            signal_repository, outcome_repository = repositories
            signal_repository.save_signal(_signal("signal-1"))

            summary = evaluate_saved_signal_outcomes(
                signal_repository=signal_repository,
                outcome_repository=outcome_repository,
                future_rows_by_signal_id={
                    "signal-1": (
                        _row("2026-07-01", 101.0),
                        _row("2026-07-02", 102.0),
                        _row("2026-07-03", 104.0),
                    )
                },
            )

            outcomes = outcome_repository.list_outcomes_for_signal("signal-1")

            self.assertEqual(summary.evaluated, 1)
            self.assertEqual(summary.skipped_insufficient_future_rows, 0)
            self.assertEqual(len(outcomes), 1)
            self.assertEqual(outcomes[0].symbol, "AAPL")
            self.assertEqual(outcomes[0].signal_date, "2026-07-01")
            self.assertEqual(outcomes[0].evaluation_date, "2026-07-03")
            self.assertEqual(outcomes[0].horizon_days, 2)
            self.assertEqual(outcomes[0].entry_price, 100.0)
            self.assertEqual(outcomes[0].close_price, 104.0)
            self.assertEqual(outcomes[0].return_pct, 4.0)
            self.assertEqual(outcomes[0].outcome_status, OutcomeStatus.POSITIVE)
            json.dumps(summary.to_dict(), sort_keys=True)

    def test_signal_without_enough_future_rows_is_skipped_safely(self) -> None:
        with _repositories() as repositories:
            signal_repository, outcome_repository = repositories
            signal_repository.save_signal(_signal("signal-1"))

            summary = evaluate_saved_signal_outcomes(
                signal_repository=signal_repository,
                outcome_repository=outcome_repository,
                future_rows_by_signal_id={
                    "signal-1": (_row("2026-07-02", 102.0),)
                },
            )

            self.assertEqual(summary.evaluated, 0)
            self.assertEqual(summary.skipped_insufficient_future_rows, 1)
            self.assertEqual(outcome_repository.list_outcomes_for_signal("signal-1"), ())

    def test_existing_outcome_is_not_duplicated_or_overwritten(self) -> None:
        with _repositories() as repositories:
            signal_repository, outcome_repository = repositories
            signal_repository.save_signal(_signal("signal-1"))
            existing = OutcomeRecord(
                symbol="AAPL",
                signal_date="2026-07-01",
                evaluation_date="2026-07-03",
                horizon_days=2,
                entry_price=100.0,
                close_price=101.0,
                return_pct=1.0,
                max_runup_pct=1.0,
                max_drawdown_pct=0.0,
                outcome_status=OutcomeStatus.POSITIVE,
                notes=("existing",),
            )
            outcome_repository.save_outcome("signal-1", existing)

            summary = evaluate_saved_signal_outcomes(
                signal_repository=signal_repository,
                outcome_repository=outcome_repository,
                future_rows_by_signal_id={
                    "signal-1": (
                        _row("2026-07-02", 90.0),
                        _row("2026-07-03", 80.0),
                    )
                },
            )

            outcomes = outcome_repository.list_outcomes_for_signal("signal-1")

            self.assertEqual(summary.evaluated, 0)
            self.assertEqual(summary.skipped_existing, 1)
            self.assertEqual(outcomes, (existing,))


class _repositories:
    def __enter__(self) -> tuple[SQLiteSignalLedgerRepository, SQLiteOutcomeRepository]:
        self.connection = sqlite3.connect(":memory:")
        self.signal_repository = SQLiteSignalLedgerRepository(self.connection)
        self.outcome_repository = SQLiteOutcomeRepository(self.connection)
        self.signal_repository.initialize_schema()
        self.outcome_repository.initialize_schema()
        return self.signal_repository, self.outcome_repository

    def __exit__(self, *args: object) -> None:
        del args
        self.connection.close()


def _signal(signal_id: str) -> SignalRecord:
    return SignalRecord(
        signal_id=signal_id,
        symbol="AAPL",
        signal_date="2026-07-01",
        snapshot_reference=SignalSnapshotReference(
            snapshot_id="snapshot-1",
            snapshot_date="2026-07-01",
            timeframe="1D",
            source="fixture",
        ),
        strategy_summary={
            "entry_price": 100.0,
            "horizon_days": 2,
            "target_price": 110.0,
            "stop_price": 95.0,
        },
        signal_type=SignalType.SETUP,
        confidence=80.0,
        notes=("fixture",),
    )


def _row(row_date: str, close: float) -> dict[str, object]:
    return {
        "date": row_date,
        "open": close - 1.0,
        "high": close + 1.0,
        "low": close - 2.0,
        "close": close,
        "volume": 1000,
    }


if __name__ == "__main__":
    unittest.main()
