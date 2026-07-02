from __future__ import annotations

from contextlib import closing
import json
import sqlite3
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from src.application.evidence_loop_runner import run_manual_evidence_loop
from src.application.signal_backfill_service import (
    SignalBackfillProgress,
    SignalBackfillSummary,
)
from src.data_source import MemoryDataSource
from src.daily_research_snapshot import SQLiteDailyResearchSnapshotRepository
from src.outcome_tracking import OutcomeEvaluationSummary
from src.outcome_tracking.repository import InMemoryOutcomeRepository
from src.outcome_tracking.sqlite_repository import SQLiteOutcomeRepository
from src.signal_ledger import InMemorySignalLedgerRepository
from src.signal_ledger.sqlite_repository import SQLiteSignalLedgerRepository


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

    def test_error_log_path_is_forwarded_to_backfill_when_supplied(self) -> None:
        observed_error_log_paths: list[object] = []

        def backfill(**kwargs: object) -> SignalBackfillSummary:
            observed_error_log_paths.append(kwargs["error_log_path"])
            return SignalBackfillSummary(symbol="AAPL", saved=0)

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
                error_log_path="logs/test-evidence-loop.log",
            )

        self.assertEqual(observed_error_log_paths, ["logs/test-evidence-loop.log"])

    def test_evidence_loop_persists_daily_snapshots_and_compatibility_signals(self) -> None:
        with closing(sqlite3.connect(":memory:")) as connection:
            signal_repository = SQLiteSignalLedgerRepository(connection)
            outcome_repository = SQLiteOutcomeRepository(connection)
            snapshot_repository = SQLiteDailyResearchSnapshotRepository(connection)
            signal_repository.initialize_schema()
            outcome_repository.initialize_schema()
            snapshot_repository.initialize_schema()

            with patch(
                "src.application.signal_backfill_service.analyze_symbol_v2",
                side_effect=_fake_analysis,
            ):
                summary = run_manual_evidence_loop(
                    symbol="aapl",
                    data_source=MemoryDataSource(
                        [
                            _row("AAPL", "2026-06-29", 100.0),
                            _row("AAPL", "2026-06-30", 101.0),
                            _row("AAPL", "2026-07-01", 102.0),
                        ]
                    ),
                    signal_repository=signal_repository,
                    outcome_repository=outcome_repository,
                    snapshot_repository=snapshot_repository,
                    as_of_date="2026-07-01",
                    future_rows_by_signal_id={"unused": []},
                )

            snapshot_rows = connection.execute(
                """
                SELECT snapshot_record_id, market_date, canonical_snapshot_json, signal_id
                FROM daily_research_snapshots
                ORDER BY market_date ASC
                """
            ).fetchall()
            signal_count = connection.execute(
                "SELECT COUNT(*) FROM signal_ledger_signals"
            ).fetchone()[0]

        self.assertEqual(summary.signals_created, 2)
        self.assertEqual(len(snapshot_rows), 2)
        self.assertEqual(signal_count, 2)
        self.assertEqual([row[1] for row in snapshot_rows], ["2026-06-29", "2026-06-30"])
        for expected_count, row in enumerate(snapshot_rows, start=1):
            payload = json.loads(row[2])
            self.assertIn("identity", payload)
            self.assertEqual(
                payload["identity"]["payload_schema_version"],
                "snapshot_payload_v2",
            )
            self.assertEqual(payload["input"]["ohlcv_window"]["row_count"], expected_count)
            self.assertEqual(payload["input"]["ohlcv_window"]["last_date"], row[1])
            self.assertEqual(len(payload["input"]["ohlcv_window"]["rows"]), expected_count)
            self.assertEqual(payload["input"]["query"]["symbol"], "AAPL")
            self.assertEqual(payload["input"]["query"]["end_date"], row[1])
            self.assertEqual(payload["input"]["query"]["limit"], expected_count)
            self.assertTrue(payload["analysis"]["brain_snapshot"]["indicators"])
            self.assertIn("ema20", payload["analysis"]["brain_snapshot"]["indicators"])
            self.assertTrue(payload["context"]["market"])
            self.assertTrue(payload["context"]["volume"])
            self.assertTrue(payload["context"]["support_resistance"])
            self.assertTrue(payload["provenance"]["analysis_cutoff"])
            self.assertEqual(
                payload["provenance"]["analysis_cutoff"]["analysis_cutoff_date"],
                "2026-06-30",
            )
            self.assertTrue(payload["provenance"]["data_source"])
            self.assertIn("compatibility", payload)
            self.assertTrue(str(row[0]).startswith("snapshot-v2:aapl:"))
            self.assertTrue(str(row[3]).strip())


def _fake_analysis(request: object) -> object:
    del request
    return SimpleNamespace(
        canonical_brain=SimpleNamespace(
            snapshot={},
            resolver_output={},
            probability={},
            projection={},
            target_zone={},
            risk_zone={},
            prediction_summary={"confidence": 50.0},
            metadata={},
            notes=(),
        ),
        metadata={"entry_point": "fake_analysis"},
        notes=[],
    )


def _row(symbol: str, row_date: str, close: float) -> dict[str, object]:
    return {
        "symbol": symbol,
        "timeframe": "1D",
        "date": row_date,
        "open": close - 1.0,
        "high": close + 1.0,
        "low": close - 2.0,
        "close": close,
        "volume": 1000,
    }


if __name__ == "__main__":
    unittest.main()
