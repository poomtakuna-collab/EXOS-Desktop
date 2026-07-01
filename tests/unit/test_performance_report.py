from __future__ import annotations

import ast
import inspect
import json
import sys
import unittest

import src.performance_report.report as report_module
from src.outcome_tracking import InMemoryOutcomeRepository, OutcomeRecord, OutcomeStatus
from src.performance_report import (
    CONFIDENCE_BUCKETS,
    PerformanceReport,
    build_performance_report,
)
from src.signal_ledger import (
    InMemorySignalLedgerRepository,
    SignalRecord,
    SignalSnapshotReference,
    SignalType,
)


class PerformanceReportTest(unittest.TestCase):
    def test_empty_repositories_return_safe_report(self) -> None:
        report = build_performance_report(
            InMemorySignalLedgerRepository(),
            InMemoryOutcomeRepository(),
        )

        self.assertEqual(report.total_signals, 0)
        self.assertEqual(report.total_outcomes, 0)
        self.assertEqual(report.win_rate, 0.0)
        self.assertEqual(report.average_return, 0.0)
        self.assertEqual(report.average_max_drawdown, 0.0)
        self.assertEqual(report.outcome_status_distribution, {})
        self.assertEqual(report.signal_type_breakdown, {})
        self.assertEqual(
            report.confidence_bucket_breakdown,
            {bucket: 0 for bucket in CONFIDENCE_BUCKETS},
        )
        json.dumps(report.to_dict(), sort_keys=True)

    def test_builds_core_performance_metrics(self) -> None:
        signal_repository = InMemorySignalLedgerRepository()
        outcome_repository = InMemoryOutcomeRepository()
        signal_repository.save_signal(_signal("signal-1", SignalType.SETUP, 75.0))
        signal_repository.save_signal(_signal("signal-2", SignalType.BREAKOUT, 85.0))
        signal_repository.save_signal(_signal("signal-3", SignalType.SETUP, None))
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
        outcome_repository.save_outcome(
            "signal-3",
            _outcome(OutcomeStatus.NEUTRAL, 0.0, -1.0),
            outcome_id="outcome-3",
        )

        report = build_performance_report(signal_repository, outcome_repository)

        self.assertEqual(report.total_signals, 3)
        self.assertEqual(report.total_outcomes, 3)
        self.assertEqual(report.win_rate, 33.3333)
        self.assertEqual(report.average_return, 0.6667)
        self.assertEqual(report.average_max_drawdown, -3.0)

    def test_outcome_status_distribution_is_deterministic(self) -> None:
        signal_repository = InMemorySignalLedgerRepository()
        outcome_repository = InMemoryOutcomeRepository()
        outcome_repository.save_outcome(
            "signal-1",
            _outcome(OutcomeStatus.POSITIVE, 5.0, -2.0),
            outcome_id="outcome-1",
        )
        outcome_repository.save_outcome(
            "signal-2",
            _outcome("custom-status", None, None),
            outcome_id="outcome-2",
        )
        outcome_repository.save_outcome(
            "signal-3",
            _outcome(OutcomeStatus.NEGATIVE, -3.0, -6.0),
            outcome_id="outcome-3",
        )

        report = build_performance_report(signal_repository, outcome_repository)

        self.assertEqual(
            list(report.outcome_status_distribution),
            ["custom-status", "negative", "positive"],
        )
        self.assertEqual(
            report.outcome_status_distribution,
            {"custom-status": 1, "negative": 1, "positive": 1},
        )

    def test_signal_type_breakdown_is_deterministic(self) -> None:
        signal_repository = InMemorySignalLedgerRepository()
        outcome_repository = InMemoryOutcomeRepository()
        signal_repository.save_signal(_signal("signal-1", SignalType.SETUP, 75.0))
        signal_repository.save_signal(_signal("signal-2", SignalType.BREAKOUT, 85.0))
        signal_repository.save_signal(_signal("signal-3", "custom-type", 45.0))
        signal_repository.save_signal(_signal("signal-4", SignalType.SETUP, 55.0))

        report = build_performance_report(signal_repository, outcome_repository)

        self.assertEqual(
            list(report.signal_type_breakdown),
            ["breakout", "custom-type", "setup"],
        )
        self.assertEqual(
            report.signal_type_breakdown,
            {"breakout": 1, "custom-type": 1, "setup": 2},
        )

    def test_confidence_bucket_breakdown_clamps_and_handles_unknowns(self) -> None:
        signal_repository = InMemorySignalLedgerRepository()
        outcome_repository = InMemoryOutcomeRepository()
        signal_repository.save_signal(_signal("signal-1", SignalType.SETUP, None))
        signal_repository.save_signal(_signal("signal-2", SignalType.SETUP, -10.0))
        signal_repository.save_signal(_signal("signal-3", SignalType.SETUP, 20.0))
        signal_repository.save_signal(_signal("signal-4", SignalType.SETUP, 40.0))
        signal_repository.save_signal(_signal("signal-5", SignalType.SETUP, 60.0))
        signal_repository.save_signal(_signal("signal-6", SignalType.SETUP, 80.0))
        signal_repository.save_signal(_signal("signal-7", SignalType.SETUP, 150.0))

        report = build_performance_report(signal_repository, outcome_repository)

        self.assertEqual(
            report.confidence_bucket_breakdown,
            {
                "unknown": 1,
                "0-20": 1,
                "20-40": 1,
                "40-60": 1,
                "60-80": 1,
                "80-100": 2,
            },
        )

    def test_win_rate_uses_status_fallback_when_return_is_missing(self) -> None:
        signal_repository = InMemorySignalLedgerRepository()
        outcome_repository = InMemoryOutcomeRepository()
        outcome_repository.save_outcome(
            "signal-1",
            _outcome(OutcomeStatus.TARGET_HIT, None, -1.0),
            outcome_id="outcome-1",
        )
        outcome_repository.save_outcome(
            "signal-2",
            _outcome(OutcomeStatus.STOP_HIT, None, -5.0),
            outcome_id="outcome-2",
        )

        report = build_performance_report(signal_repository, outcome_repository)

        self.assertEqual(report.win_rate, 50.0)
        self.assertEqual(report.average_return, 0.0)
        self.assertEqual(report.average_max_drawdown, -3.0)

    def test_to_dict_is_json_safe_and_stable(self) -> None:
        report = PerformanceReport(
            total_signals=1,
            total_outcomes=1,
            win_rate=100.0,
            average_return=5.0,
            average_max_drawdown=-2.0,
            outcome_status_distribution={"positive": 1},
            signal_type_breakdown={"setup": 1},
            confidence_bucket_breakdown={bucket: 0 for bucket in CONFIDENCE_BUCKETS},
        )

        output = report.to_dict()

        self.assertEqual(
            set(output),
            {
                "total_signals",
                "total_outcomes",
                "win_rate",
                "average_return",
                "average_max_drawdown",
                "outcome_status_distribution",
                "signal_type_breakdown",
                "confidence_bucket_breakdown",
            },
        )
        json.dumps(output, sort_keys=True)

    def test_report_is_deterministic(self) -> None:
        signal_repository = InMemorySignalLedgerRepository()
        outcome_repository = InMemoryOutcomeRepository()
        signal_repository.save_signal(_signal("signal-1", SignalType.SETUP, 75.0))
        outcome_repository.save_outcome(
            "signal-1",
            _outcome(OutcomeStatus.POSITIVE, 5.0, -2.0),
            outcome_id="outcome-1",
        )

        first = build_performance_report(signal_repository, outcome_repository)
        second = build_performance_report(signal_repository, outcome_repository)

        self.assertEqual(first, second)
        self.assertEqual(first.to_dict(), second.to_dict())

    def test_performance_report_does_not_import_ai_network_broker_or_database_modules(self) -> None:
        blocked_module_roots = {
            "openai",
            "anthropic",
            "yfinance",
            "requests",
            "httpx",
            "urllib3",
            "alpaca",
            "ib_insync",
            "sqlite3",
        }
        imported_roots: set[str] = set()

        tree = ast.parse(inspect.getsource(report_module))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported_roots.update(alias.name.split(".")[0] for alias in node.names)
            if isinstance(node, ast.ImportFrom) and node.module:
                imported_roots.add(node.module.split(".")[0])

        self.assertTrue(blocked_module_roots.isdisjoint(imported_roots))

    def test_running_report_does_not_load_database_modules(self) -> None:
        before = set(sys.modules)

        build_performance_report(
            InMemorySignalLedgerRepository(),
            InMemoryOutcomeRepository(),
        )

        imported = set(sys.modules) - before
        imported_roots = {name.split(".")[0] for name in imported}
        self.assertNotIn("sqlite3", imported_roots)


def _signal(
    signal_id: str,
    signal_type: SignalType | str,
    confidence: float | None,
) -> SignalRecord:
    return SignalRecord(
        signal_id=signal_id,
        symbol="AAPL",
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
    status: OutcomeStatus | str,
    return_pct: float | None,
    max_drawdown_pct: float | None,
) -> OutcomeRecord:
    return OutcomeRecord(
        symbol="AAPL",
        signal_date="2026-07-01",
        evaluation_date="2026-07-11",
        horizon_days=10,
        entry_price=100.0,
        close_price=100.0 + return_pct if return_pct is not None else None,
        return_pct=return_pct,
        max_runup_pct=max(return_pct, 0.0) if return_pct is not None else None,
        max_drawdown_pct=max_drawdown_pct,
        hit_target=status == OutcomeStatus.TARGET_HIT,
        hit_stop=status == OutcomeStatus.STOP_HIT,
        outcome_status=status,
        notes=("fixture",),
    )


if __name__ == "__main__":
    unittest.main()
