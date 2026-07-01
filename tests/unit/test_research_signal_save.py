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
from src.gui.research_signal_save import save_manual_signal_candidate
from src.signal_ledger import SignalRecord, SignalType
from src.signal_ledger.sqlite_repository import SQLiteSignalLedgerRepository


class ResearchSignalSaveTest(unittest.TestCase):
    def test_successful_save_persists_signal_to_sqlite_repository(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "exos.db"

            result = save_manual_signal_candidate(
                _canonical_result(),
                database_path=db_path,
            )

            self.assertTrue(result.saved)
            self.assertIsNotNone(result.signal)
            self.assertTrue(result.signal.signal_id)
            self.assertIn("Signal saved:", result.message)

            connection = sqlite3.connect(db_path)
            try:
                repository = SQLiteSignalLedgerRepository(connection)
                saved = repository.load_signal(result.signal.signal_id)
            finally:
                connection.close()

            self.assertIsNotNone(saved)
            self.assertEqual(saved.symbol, "AAPL")
            self.assertEqual(saved.signal_date, "2026-07-02")
            self.assertEqual(saved.snapshot_reference.snapshot_id, "snapshot-1")
            self.assertEqual(saved.snapshot_reference.snapshot_date, "2026-07-01")
            self.assertEqual(saved.snapshot_reference.timeframe, "1D")
            self.assertEqual(saved.signal_type, SignalType.SETUP)
            self.assertEqual(saved.confidence, 81.0)
            self.assertEqual(saved.context_summary["market"]["trend"], "up")
            self.assertEqual(saved.strategy_summary["strategy_score"], 77.0)
            self.assertIn("prediction_summary", saved.strategy_summary)

    def test_duplicate_save_is_idempotent(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "exos.db"

            first = save_manual_signal_candidate(_canonical_result(), database_path=db_path)
            second = save_manual_signal_candidate(_canonical_result(), database_path=db_path)

            self.assertTrue(first.saved)
            self.assertTrue(second.duplicate)
            self.assertEqual(second.signal.signal_id, first.signal.signal_id)
            self.assertIn("already saved", second.message)

            connection = sqlite3.connect(db_path)
            try:
                repository = SQLiteSignalLedgerRepository(connection)
                signals = repository.list_signals(symbol="AAPL")
            finally:
                connection.close()

            self.assertEqual(len(signals), 1)

    def test_missing_analysis_returns_unavailable_without_repository_call(self) -> None:
        repository = _CountingRepository()

        result = save_manual_signal_candidate(None, repository=repository)

        self.assertEqual(result.status, "unavailable")
        self.assertFalse(result.saved)
        self.assertEqual(repository.load_calls, 0)
        self.assertEqual(repository.save_calls, 0)

    def test_repository_failure_is_reported_without_raising(self) -> None:
        result = save_manual_signal_candidate(
            _canonical_result(),
            repository=_FailingRepository(),
        )

        self.assertEqual(result.status, "error")
        self.assertIn("Unable to save signal", result.message)
        self.assertIsNone(result.signal)

    def test_signal_serialization_is_deterministic(self) -> None:
        first = save_manual_signal_candidate(
            _canonical_result(),
            repository=_CountingRepository(),
        ).signal
        second = save_manual_signal_candidate(
            _canonical_result(),
            repository=_CountingRepository(),
        ).signal

        self.assertEqual(first.to_dict(), second.to_dict())


class _CountingRepository:
    def __init__(self) -> None:
        self.signals: dict[str, SignalRecord] = {}
        self.load_calls = 0
        self.save_calls = 0

    def load_signal(self, signal_id: str) -> SignalRecord | None:
        self.load_calls += 1
        return self.signals.get(signal_id)

    def save_signal(self, signal: SignalRecord) -> SignalRecord:
        self.save_calls += 1
        self.signals[signal.signal_id] = signal
        return signal


class _FailingRepository:
    def load_signal(self, signal_id: str) -> SignalRecord | None:
        del signal_id
        return None

    def save_signal(self, signal: SignalRecord) -> SignalRecord:
        del signal
        raise RuntimeError("repository unavailable")


def _canonical_result() -> CanonicalResultV1:
    return CanonicalResultV1(
        identity=CanonicalIdentityV1(
            symbol="AAPL",
            timeframe="1D",
            snapshot_id="snapshot-1",
            snapshot_date="2026-07-01",
            analysis_date="2026-07-02",
            source="analysis_pipeline_v2",
        ),
        signal_summary=CanonicalSignalSummaryV1(
            symbol="AAPL",
            signal_date="2026-07-02",
            timeframe="1D",
            signal_type="setup",
            confidence=81.0,
            snapshot_id="snapshot-1",
            snapshot_date="2026-07-01",
            context_summary={"market": {"trend": "up"}},
            strategy_summary={"strategy_score": 77.0},
            prediction_summary={"confidence": 81.0, "evidence_count": 12},
            notes=("manual save candidate",),
        ),
    )


if __name__ == "__main__":
    unittest.main()
