from __future__ import annotations

import json
import unittest
from unittest.mock import patch

from src.application.evidence_loop_runner import run_manual_evidence_loop
from src.application.signal_backfill_service import (
    SignalBackfillProgress,
    SignalBackfillSummary,
)
from src.data_source import MemoryDataSource
from src.outcome_tracking import OutcomeEvaluationSummary
from src.outcome_tracking.repository import InMemoryOutcomeRepository
from src.signal_ledger import InMemorySignalLedgerRepository


class ManualEvidenceLoopRunnerTest(unittest.TestCase):
    def test_backfill_runs_before_outcome_evaluation(self) -> None:
        calls: list[str] = []

        def backfill(**kwargs: object) -> SignalBackfillSummary:
            del kwargs
            calls.append("backfill")
            return SignalBackfillSummary(symbol="AAPL", saved=1)

        def evaluate(**kwargs: object) -> OutcomeEvaluationSummary:
            del kwargs
            calls.append("evaluate")
            return OutcomeEvaluationSummary(evaluated=1)

        with patch(
            "src.application.evidence_loop_runner.backfill_missing_research_signals",
            side_effect=backfill,
        ), patch(
            "src.application.evidence_loop_runner.evaluate_saved_signal_outcomes",
            side_effect=evaluate,
        ):
            run_manual_evidence_loop(
                symbol="AAPL",
                data_source=MemoryDataSource([]),
                signal_repository=InMemorySignalLedgerRepository(),
                outcome_repository=InMemoryOutcomeRepository(),
                future_rows_by_signal_id={},
            )

        self.assertEqual(calls, ["backfill", "evaluate"])

    def test_summary_reports_signals_created_and_outcomes_evaluated_or_skipped(self) -> None:
        with patch(
            "src.application.evidence_loop_runner.backfill_missing_research_signals",
            return_value=SignalBackfillSummary(
                symbol="AAPL",
                saved=2,
                skipped_existing=3,
                skipped_failed=1,
            ),
        ), patch(
            "src.application.evidence_loop_runner.evaluate_saved_signal_outcomes",
            return_value=OutcomeEvaluationSummary(
                evaluated=1,
                skipped_existing=1,
                skipped_insufficient_future_rows=2,
            ),
        ):
            summary = run_manual_evidence_loop(
                symbol="aapl",
                data_source=MemoryDataSource([]),
                signal_repository=InMemorySignalLedgerRepository(),
                outcome_repository=InMemoryOutcomeRepository(),
                future_rows_by_signal_id={},
            )

        self.assertEqual(summary.symbol, "AAPL")
        self.assertEqual(summary.signals_created, 2)
        self.assertEqual(summary.snapshots_processed, 6)
        self.assertEqual(summary.outcomes_evaluated, 1)
        self.assertEqual(summary.outcome_evaluation.skipped_existing, 1)
        self.assertEqual(summary.outcome_evaluation.skipped_insufficient_future_rows, 2)
        json.dumps(summary.to_dict(), sort_keys=True)

    def test_safe_when_no_missing_signals(self) -> None:
        with patch(
            "src.application.evidence_loop_runner.backfill_missing_research_signals",
            return_value=SignalBackfillSummary(symbol="AAPL", saved=0, skipped_existing=3),
        ), patch(
            "src.application.evidence_loop_runner.evaluate_saved_signal_outcomes",
            return_value=OutcomeEvaluationSummary(evaluated=0, skipped_existing=3),
        ):
            summary = run_manual_evidence_loop(
                symbol="AAPL",
                data_source=MemoryDataSource([]),
                signal_repository=InMemorySignalLedgerRepository(),
                outcome_repository=InMemoryOutcomeRepository(),
                future_rows_by_signal_id={},
            )

        self.assertEqual(summary.signals_created, 0)
        self.assertEqual(summary.backfill.skipped_existing, 3)
        self.assertEqual(summary.outcomes_evaluated, 0)

    def test_safe_when_no_evaluable_outcomes(self) -> None:
        with patch(
            "src.application.evidence_loop_runner.backfill_missing_research_signals",
            return_value=SignalBackfillSummary(symbol="AAPL", saved=1),
        ), patch(
            "src.application.evidence_loop_runner.evaluate_saved_signal_outcomes",
            return_value=OutcomeEvaluationSummary(
                evaluated=0,
                skipped_insufficient_future_rows=1,
                skipped_unavailable_inputs=1,
            ),
        ):
            summary = run_manual_evidence_loop(
                symbol="AAPL",
                data_source=MemoryDataSource([]),
                signal_repository=InMemorySignalLedgerRepository(),
                outcome_repository=InMemoryOutcomeRepository(),
                future_rows_by_signal_id={},
            )

        self.assertEqual(summary.signals_created, 1)
        self.assertEqual(summary.outcomes_evaluated, 0)
        self.assertEqual(summary.outcome_evaluation.skipped_insufficient_future_rows, 1)
        self.assertEqual(summary.outcome_evaluation.skipped_unavailable_inputs, 1)

    def test_progress_callback_is_forwarded_to_backfill(self) -> None:
        progress_events: list[SignalBackfillProgress] = []

        def backfill(**kwargs: object) -> SignalBackfillSummary:
            callback = kwargs["progress_callback"]
            self.assertTrue(callable(callback))
            callback(
                SignalBackfillProgress(
                    symbol="AAPL",
                    current=1,
                    total=2,
                    market_date="2026-06-29",
                )
            )
            return SignalBackfillSummary(symbol="AAPL", saved=1)

        with patch(
            "src.application.evidence_loop_runner.backfill_missing_research_signals",
            side_effect=backfill,
        ), patch(
            "src.application.evidence_loop_runner.evaluate_saved_signal_outcomes",
            return_value=OutcomeEvaluationSummary(evaluated=0),
        ):
            run_manual_evidence_loop(
                symbol="AAPL",
                data_source=MemoryDataSource([]),
                signal_repository=InMemorySignalLedgerRepository(),
                outcome_repository=InMemoryOutcomeRepository(),
                future_rows_by_signal_id={},
                progress_callback=progress_events.append,
            )

        self.assertEqual(
            [progress.to_dict() for progress in progress_events],
            [
                {
                    "symbol": "AAPL",
                    "current": 1,
                    "total": 2,
                    "market_date": "2026-06-29",
                }
            ],
        )


if __name__ == "__main__":
    unittest.main()
