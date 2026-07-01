from __future__ import annotations

import sqlite3
import tempfile
import unittest
from pathlib import Path

from src.gui.performance_view_model import (
    build_performance_view_model,
    load_desktop_performance_report,
)
from src.outcome_tracking import OutcomeRecord, OutcomeStatus
from src.outcome_tracking.sqlite_repository import SQLiteOutcomeRepository
from src.performance_report import PerformanceReport
from src.signal_ledger import SignalRecord, SignalSnapshotReference, SignalType
from src.signal_ledger.sqlite_repository import SQLiteSignalLedgerRepository


class PerformanceSurfaceTest(unittest.TestCase):
    def test_view_model_formats_summary_and_distributions(self) -> None:
        report = PerformanceReport(
            total_signals=3,
            total_outcomes=2,
            completed_outcomes=2,
            pending_outcomes=1,
            outcome_coverage=66.6667,
            duplicate_snapshots=1,
            last_snapshot_date="2026-07-03",
            last_outcome_evaluation_date="2026-07-11",
            win_rate=50.0,
            average_return=1.25,
            average_max_drawdown=-3.5,
            outcome_status_distribution={"negative": 1, "target_hit": 1},
            signal_type_breakdown={"breakout": 1, "setup": 2},
            confidence_bucket_breakdown={
                "unknown": 0,
                "0-20": 0,
                "20-40": 0,
                "40-60": 1,
                "60-80": 1,
                "80-100": 1,
            },
        )

        view_model = build_performance_view_model(report)

        self.assertEqual(view_model["scope"], "Global Performance")
        self.assertEqual(
            view_model["summary"],
            {
                "total_signals": "3",
                "total_outcomes": "2",
                "win_rate": "50.00%",
                "average_return": "1.25%",
                "average_max_drawdown": "-3.50%",
            },
        )
        self.assertEqual(
            view_model["snapshot_health"],
            {
                "total_snapshots": "3",
                "completed_outcomes": "2",
                "pending_outcomes": "1",
                "outcome_coverage": "66.67%",
                "duplicate_snapshots": "1",
                "last_snapshot_date": "2026-07-03",
                "last_outcome_evaluation_date": "2026-07-11",
            },
        )
        self.assertEqual(
            view_model["outcome_status_distribution"],
            "Negative: 1\nTarget Hit: 1",
        )
        self.assertEqual(
            view_model["signal_type_breakdown"],
            "Breakout: 1\nSetup: 2",
        )
        self.assertIn("80 100: 1", view_model["confidence_bucket_breakdown"])
        self.assertEqual(view_model["global_summary"], "")
        self.assertEqual(view_model["status"], "Read-only global performance report.")

    def test_view_model_formats_selected_symbol_scope_and_global_reference(self) -> None:
        selected_report = PerformanceReport(
            total_signals=1,
            total_outcomes=1,
            win_rate=100.0,
            average_return=5.0,
            average_max_drawdown=-2.0,
            outcome_status_distribution={"positive": 1},
            signal_type_breakdown={"setup": 1},
        )
        global_report = PerformanceReport(total_signals=3, total_outcomes=2, win_rate=50.0)

        view_model = build_performance_view_model(
            selected_report,
            selected_symbol="aapl",
            global_report=global_report,
        )

        self.assertEqual(view_model["scope"], "Selected Symbol: AAPL")
        self.assertEqual(
            view_model["global_summary"],
            "Global: 3 snapshots, 2 outcomes, 50.00% win rate",
        )
        self.assertEqual(view_model["status"], "Read-only performance report for AAPL.")

    def test_view_model_handles_empty_report(self) -> None:
        view_model = build_performance_view_model(PerformanceReport())

        self.assertEqual(
            view_model["snapshot_health"],
            {
                "total_snapshots": "0",
                "completed_outcomes": "0",
                "pending_outcomes": "0",
                "outcome_coverage": "0.00%",
                "duplicate_snapshots": "0",
                "last_snapshot_date": "-",
                "last_outcome_evaluation_date": "-",
            },
        )
        self.assertEqual(view_model["outcome_status_distribution"], "No data")
        self.assertEqual(view_model["signal_type_breakdown"], "No data")
        self.assertIn("Unknown: 0", view_model["confidence_bucket_breakdown"])
        self.assertEqual(
            view_model["status"],
            "No saved snapshot or outcome records found.",
        )

    def test_view_model_handles_empty_selected_symbol_report(self) -> None:
        view_model = build_performance_view_model(
            PerformanceReport(),
            selected_symbol="MSFT",
            global_report=PerformanceReport(total_signals=2, total_outcomes=1),
        )

        self.assertEqual(view_model["scope"], "Selected Symbol: MSFT")
        self.assertEqual(
            view_model["status"],
            "No saved snapshot or outcome records found for MSFT.",
        )

    def test_missing_database_path_returns_empty_report_without_creating_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "missing.db"

            report = load_desktop_performance_report(db_path)

            self.assertFalse(db_path.exists())
            self.assertEqual(report.total_signals, 0)
            self.assertEqual(report.total_outcomes, 0)

    def test_existing_database_without_performance_tables_returns_empty_report(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "exos.db"
            connection = sqlite3.connect(db_path)
            try:
                connection.execute("CREATE TABLE unrelated (id INTEGER PRIMARY KEY)")
                connection.commit()
            finally:
                connection.close()

            report = load_desktop_performance_report(db_path)

            self.assertEqual(report.total_signals, 0)
            self.assertEqual(report.total_outcomes, 0)

    def test_existing_performance_tables_are_loaded_read_only(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "exos.db"
            connection = sqlite3.connect(db_path)
            try:
                signal_repository = SQLiteSignalLedgerRepository(connection)
                outcome_repository = SQLiteOutcomeRepository(connection)
                signal_repository.initialize_schema()
                outcome_repository.initialize_schema()
                signal_repository.save_signal(_signal("signal-1", SignalType.SETUP, 75.0))
                signal_repository.save_signal(_signal("signal-2", SignalType.BREAKOUT, 85.0))
                outcome_repository.save_outcome(
                    "signal-1",
                    _outcome(OutcomeStatus.POSITIVE, 5.0, -2.0),
                    outcome_id="outcome-1",
                )
                outcome_repository.save_outcome(
                    "signal-2",
                    _outcome(OutcomeStatus.NEGATIVE, -3.0, -6.0),
                    outcome_id="outcome-2",
                )
            finally:
                connection.close()

            report = load_desktop_performance_report(db_path)

            self.assertEqual(report.total_signals, 2)
            self.assertEqual(report.total_outcomes, 2)
            self.assertEqual(report.win_rate, 50.0)
            self.assertEqual(report.average_return, 1.0)
            self.assertEqual(report.average_max_drawdown, -4.0)

    def test_existing_performance_tables_can_be_filtered_by_symbol(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "exos.db"
            connection = sqlite3.connect(db_path)
            try:
                signal_repository = SQLiteSignalLedgerRepository(connection)
                outcome_repository = SQLiteOutcomeRepository(connection)
                signal_repository.initialize_schema()
                outcome_repository.initialize_schema()
                signal_repository.save_signal(_signal("signal-1", SignalType.SETUP, 75.0, symbol="AAPL"))
                signal_repository.save_signal(_signal("signal-2", SignalType.BREAKOUT, 85.0, symbol="MSFT"))
                outcome_repository.save_outcome(
                    "signal-1",
                    _outcome(OutcomeStatus.POSITIVE, 5.0, -2.0, symbol="AAPL"),
                    outcome_id="outcome-1",
                )
                outcome_repository.save_outcome(
                    "signal-2",
                    _outcome(OutcomeStatus.NEGATIVE, -3.0, -6.0, symbol="MSFT"),
                    outcome_id="outcome-2",
                )
            finally:
                connection.close()

            report = load_desktop_performance_report(db_path, symbol="msft")

            self.assertEqual(report.total_signals, 1)
            self.assertEqual(report.total_outcomes, 1)
            self.assertEqual(report.win_rate, 0.0)
            self.assertEqual(report.average_return, -3.0)


def _signal(
    signal_id: str,
    signal_type: SignalType,
    confidence: float,
    *,
    symbol: str = "AAPL",
) -> SignalRecord:
    return SignalRecord(
        signal_id=signal_id,
        symbol=symbol,
        signal_date="2026-07-01",
        snapshot_reference=SignalSnapshotReference(
            snapshot_id=f"snapshot-{signal_id}",
            snapshot_date="2026-07-01",
            timeframe="1D",
            source="fixture",
        ),
        signal_type=signal_type,
        confidence=confidence,
    )


def _outcome(
    status: OutcomeStatus,
    return_pct: float,
    max_drawdown_pct: float,
    *,
    symbol: str = "AAPL",
) -> OutcomeRecord:
    return OutcomeRecord(
        symbol=symbol,
        signal_date="2026-07-01",
        evaluation_date="2026-07-11",
        horizon_days=10,
        entry_price=100.0,
        close_price=100.0 + return_pct,
        return_pct=return_pct,
        max_runup_pct=max(return_pct, 0.0),
        max_drawdown_pct=max_drawdown_pct,
        hit_target=False,
        hit_stop=False,
        outcome_status=status,
    )


if __name__ == "__main__":
    unittest.main()
