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
from src.daily_research_snapshot import SQLiteDailyResearchSnapshotRepository
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
            self.assertIn("Snapshot saved:", result.message)

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

    def test_successful_save_persists_v2_snapshot_and_compatibility_record(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "exos.db"

            result = save_manual_signal_candidate(
                _canonical_result(),
                database_path=db_path,
            )

            self.assertTrue(result.saved)
            connection = sqlite3.connect(db_path)
            try:
                signal_repository = SQLiteSignalLedgerRepository(connection)
                snapshot_repository = SQLiteDailyResearchSnapshotRepository(connection)
                saved_signal = signal_repository.load_signal(result.signal.signal_id)
                saved_snapshot = snapshot_repository.load_snapshot(
                    symbol="AAPL",
                    market_date="2026-07-02",
                    timeframe="1D",
                )
            finally:
                connection.close()

            self.assertIsNotNone(saved_signal)
            self.assertIsNotNone(saved_snapshot)
            self.assertEqual(saved_snapshot.signal_id, result.signal.signal_id)
            self.assertEqual(saved_snapshot.canonical_snapshot, _canonical_result().to_dict())

    def test_v2_conflict_does_not_create_compatibility_record(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "exos.db"
            connection = sqlite3.connect(db_path)
            try:
                snapshot_repository = SQLiteDailyResearchSnapshotRepository(connection)
                snapshot_repository.initialize_schema()
                snapshot_repository.save_snapshot(_canonical_result(confidence=90.0))
            finally:
                connection.close()

            result = save_manual_signal_candidate(
                _canonical_result(confidence=81.0),
                database_path=db_path,
            )

            self.assertEqual(result.status, "error")
            self.assertIn("Unable to save snapshot", result.message)
            self.assertEqual(_signals(db_path, "AAPL"), ())

    def test_duplicate_save_is_idempotent(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "exos.db"

            first = save_manual_signal_candidate(_canonical_result(), database_path=db_path)
            second = save_manual_signal_candidate(_canonical_result(), database_path=db_path)

            self.assertTrue(first.saved)
            self.assertTrue(second.duplicate)
            self.assertEqual(second.signal.signal_id, first.signal.signal_id)
            self.assertIn("Snapshot already exists", second.message)

            connection = sqlite3.connect(db_path)
            try:
                repository = SQLiteSignalLedgerRepository(connection)
                signals = repository.list_signals(symbol="AAPL")
            finally:
                connection.close()

            self.assertEqual(len(signals), 1)

    def test_same_symbol_and_market_date_with_different_signal_id_is_duplicate(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "exos.db"

            first = save_manual_signal_candidate(
                _canonical_result(confidence=81.0, notes=("first",)),
                database_path=db_path,
            )
            second = save_manual_signal_candidate(
                _canonical_result(confidence=77.0, notes=("changed payload",)),
                database_path=db_path,
            )

            self.assertTrue(first.saved)
            self.assertTrue(second.duplicate)
            self.assertNotEqual(
                _signal_id_for(_canonical_result(confidence=81.0, notes=("first",))),
                _signal_id_for(_canonical_result(confidence=77.0, notes=("changed payload",))),
            )
            self.assertEqual(second.signal.signal_id, first.signal.signal_id)
            self.assertEqual(_signals(db_path, "AAPL"), (first.signal,))

    def test_same_symbol_different_market_date_can_create_new_signal(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "exos.db"

            first = save_manual_signal_candidate(
                _canonical_result(signal_date="2026-07-02", snapshot_date="2026-07-01"),
                database_path=db_path,
            )
            second = save_manual_signal_candidate(
                _canonical_result(signal_date="2026-07-03", snapshot_date="2026-07-03"),
                database_path=db_path,
            )

            self.assertTrue(first.saved)
            self.assertTrue(second.saved)
            self.assertEqual(len(_signals(db_path, "AAPL")), 2)

    def test_same_market_date_different_symbol_can_create_new_signal(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "exos.db"

            first = save_manual_signal_candidate(
                _canonical_result(symbol="AAPL"),
                database_path=db_path,
            )
            second = save_manual_signal_candidate(
                _canonical_result(symbol="MSFT"),
                database_path=db_path,
            )

            self.assertTrue(first.saved)
            self.assertTrue(second.saved)
            self.assertEqual(len(_signals(db_path, "AAPL")), 1)
            self.assertEqual(len(_signals(db_path, "MSFT")), 1)

    def test_duplicate_detection_checks_snapshot_date_when_signal_date_differs(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "exos.db"

            first = save_manual_signal_candidate(
                _canonical_result(signal_date="2026-07-02", snapshot_date="2026-07-01"),
                database_path=db_path,
            )
            second = save_manual_signal_candidate(
                _canonical_result(signal_date="2026-07-05", snapshot_date="2026-07-01"),
                database_path=db_path,
            )

            self.assertTrue(first.saved)
            self.assertTrue(second.duplicate)
            self.assertEqual(len(_signals(db_path, "AAPL")), 1)

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
        self.assertIn("Unable to save snapshot", result.message)
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
        self.list_calls = 0
        self.save_calls = 0

    def load_signal(self, signal_id: str) -> SignalRecord | None:
        self.load_calls += 1
        return self.signals.get(signal_id)

    def list_signals(self, *, symbol: str | None = None) -> tuple[SignalRecord, ...]:
        self.list_calls += 1
        signals = tuple(self.signals.values())
        if symbol is not None:
            signals = tuple(signal for signal in signals if signal.symbol == symbol)
        return signals

    def save_signal(self, signal: SignalRecord) -> SignalRecord:
        self.save_calls += 1
        self.signals[signal.signal_id] = signal
        return signal


class _FailingRepository:
    def list_signals(self, *, symbol: str | None = None) -> tuple[SignalRecord, ...]:
        del symbol
        return ()

    def load_signal(self, signal_id: str) -> SignalRecord | None:
        del signal_id
        return None

    def save_signal(self, signal: SignalRecord) -> SignalRecord:
        del signal
        raise RuntimeError("repository unavailable")


def _canonical_result(
    *,
    symbol: str = "AAPL",
    signal_date: str = "2026-07-02",
    snapshot_date: str = "2026-07-01",
    confidence: float = 81.0,
    notes: tuple[str, ...] = ("manual save candidate",),
) -> CanonicalResultV1:
    return CanonicalResultV1(
        identity=CanonicalIdentityV1(
            symbol=symbol,
            timeframe="1D",
            snapshot_id="snapshot-1",
            snapshot_date=snapshot_date,
            analysis_date=signal_date,
            source="analysis_pipeline_v2",
        ),
        signal_summary=CanonicalSignalSummaryV1(
            symbol=symbol,
            signal_date=signal_date,
            timeframe="1D",
            signal_type="setup",
            confidence=confidence,
            snapshot_id="snapshot-1",
            snapshot_date=snapshot_date,
            context_summary={"market": {"trend": "up"}},
            strategy_summary={"strategy_score": 77.0},
            prediction_summary={"confidence": confidence, "evidence_count": 12},
            notes=notes,
        ),
    )


def _signals(db_path: Path, symbol: str) -> tuple[SignalRecord, ...]:
    connection = sqlite3.connect(db_path)
    try:
        repository = SQLiteSignalLedgerRepository(connection)
        return repository.list_signals(symbol=symbol)
    finally:
        connection.close()


def _signal_id_for(canonical_result: CanonicalResultV1) -> str:
    with tempfile.TemporaryDirectory() as temp_dir:
        result = save_manual_signal_candidate(
            canonical_result,
            database_path=Path(temp_dir) / "exos.db",
        )
        return result.signal.signal_id


if __name__ == "__main__":
    unittest.main()
