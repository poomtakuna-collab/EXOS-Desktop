from __future__ import annotations

from contextlib import closing
from pathlib import Path
import sqlite3
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from src.application.signal_backfill_service import (
    SignalBackfillSnapshotError,
    backfill_missing_research_signals,
)
from src.data_source import MemoryDataSource
from src.daily_research_snapshot import SQLiteDailyResearchSnapshotRepository
from src.signal_ledger import (
    InMemorySignalLedgerRepository,
    SignalRecord,
    SignalSnapshotReference,
    SignalType,
)


class SignalBackfillServiceTest(unittest.TestCase):
    def test_backfill_excludes_latest_current_row_and_saves_missing_dates(self) -> None:
        repository = InMemorySignalLedgerRepository()

        with patch(
            "src.application.signal_backfill_service.analyze_symbol_v2",
            side_effect=_fake_analysis,
        ):
            summary = backfill_missing_research_signals(
                symbol="aapl",
                data_source=MemoryDataSource(
                    [
                        _row("AAPL", "2026-06-29", 100.0),
                        _row("AAPL", "2026-06-30", 101.0),
                        _row("AAPL", "2026-07-01", 102.0),
                    ]
                ),
                signal_repository=repository,
                as_of_date="2026-07-01",
            )

        saved_dates = [signal.signal_date for signal in repository.list_signals(symbol="AAPL")]

        self.assertEqual(summary.chart_latest_date, "2026-07-01")
        self.assertEqual(summary.analysis_cutoff_date, "2026-06-30")
        self.assertEqual(summary.saved, 2)
        self.assertEqual(saved_dates, ["2026-06-29", "2026-06-30"])
        self.assertNotIn("2026-07-01", saved_dates)

    def test_each_missing_date_analyzes_rows_through_that_date_only(self) -> None:
        repository = InMemorySignalLedgerRepository()
        observed_dates_by_call: list[list[str]] = []

        def fake_analysis(request: object) -> object:
            observed_dates_by_call.append([row["date"] for row in request.ohlcv_rows])
            return _fake_analysis(request)

        with patch(
            "src.application.signal_backfill_service.analyze_symbol_v2",
            side_effect=fake_analysis,
        ):
            summary = backfill_missing_research_signals(
                symbol="AAPL",
                data_source=MemoryDataSource(
                    [
                        _row("AAPL", "2026-06-29", 100.0),
                        _row("AAPL", "2026-06-30", 101.0),
                        _row("AAPL", "2026-07-02", 102.0),
                    ]
                ),
                signal_repository=repository,
                as_of_date="2026-07-03",
            )

        self.assertEqual(summary.saved, 3)
        self.assertEqual(
            observed_dates_by_call,
            [
                ["2026-06-29"],
                ["2026-06-29", "2026-06-30"],
                ["2026-06-29", "2026-06-30", "2026-07-02"],
            ],
        )

    def test_existing_market_date_is_skipped_without_duplicate_signal(self) -> None:
        repository = InMemorySignalLedgerRepository()
        repository.save_signal(
            _signal(
                signal_id="existing-custom-id",
                symbol="AAPL",
                signal_date="2026-06-30",
                snapshot_date="2026-06-30",
            )
        )

        with patch(
            "src.application.signal_backfill_service.analyze_symbol_v2",
            side_effect=_fake_analysis,
        ):
            summary = backfill_missing_research_signals(
                symbol="AAPL",
                data_source=MemoryDataSource(
                    [
                        _row("AAPL", "2026-06-29", 100.0),
                        _row("AAPL", "2026-06-30", 101.0),
                    ]
                ),
                signal_repository=repository,
                as_of_date="2026-07-01",
            )

        signals = repository.list_signals(symbol="AAPL")

        self.assertEqual(summary.saved, 1)
        self.assertEqual(summary.skipped_existing, 1)
        self.assertEqual(summary.skipped_dates, ("2026-06-30",))
        self.assertEqual(len(signals), 2)
        self.assertEqual(
            [signal.signal_date for signal in signals],
            ["2026-06-30", "2026-06-29"],
        )

    def test_backfill_persists_v2_snapshot_for_each_saved_market_date(self) -> None:
        signal_repository = InMemorySignalLedgerRepository()
        with closing(sqlite3.connect(":memory:")) as connection:
            snapshot_repository = SQLiteDailyResearchSnapshotRepository(connection)
            snapshot_repository.initialize_schema()

            with patch(
                "src.application.signal_backfill_service.analyze_symbol_v2",
                side_effect=_fake_analysis,
            ):
                summary = backfill_missing_research_signals(
                    symbol="AAPL",
                    data_source=MemoryDataSource(
                        [
                            _row("AAPL", "2026-06-29", 100.0),
                            _row("AAPL", "2026-06-30", 101.0),
                            _row("AAPL", "2026-07-01", 102.0),
                        ]
                    ),
                    signal_repository=signal_repository,
                    snapshot_repository=snapshot_repository,
                    as_of_date="2026-07-01",
                )

            snapshots = snapshot_repository.list_snapshots(symbol="AAPL")

        self.assertEqual(summary.saved, 2)
        self.assertEqual(
            [snapshot.market_date for snapshot in snapshots],
            ["2026-06-29", "2026-06-30"],
        )
        self.assertEqual(
            [snapshot.signal_id for snapshot in snapshots],
            list(summary.saved_signal_ids),
        )
        self.assertEqual(
            [snapshot.canonical_snapshot["identity"]["payload_schema_version"] for snapshot in snapshots],
            ["snapshot_payload_v2", "snapshot_payload_v2"],
        )
        self.assertEqual(
            [snapshot.canonical_snapshot["identity"]["market_date"] for snapshot in snapshots],
            ["2026-06-29", "2026-06-30"],
        )
        self.assertEqual(
            [
                snapshot.canonical_snapshot["compatibility"]["legacy_signal_record_projection"]["signal_id"]
                for snapshot in snapshots
            ],
            list(summary.saved_signal_ids),
        )

    def test_backfill_reports_progress_for_each_eligible_market_date(self) -> None:
        repository = InMemorySignalLedgerRepository()
        observed_progress: list[dict[str, object]] = []

        with patch(
            "src.application.signal_backfill_service.analyze_symbol_v2",
            side_effect=_fake_analysis,
        ):
            summary = backfill_missing_research_signals(
                symbol="aapl",
                data_source=MemoryDataSource(
                    [
                        _row("AAPL", "2026-06-29", 100.0),
                        _row("AAPL", "2026-06-30", 101.0),
                        _row("AAPL", "2026-07-01", 102.0),
                    ]
                ),
                signal_repository=repository,
                as_of_date="2026-07-01",
                progress_callback=lambda progress: observed_progress.append(
                    progress.to_dict()
                ),
            )

        self.assertEqual(summary.saved, 2)
        self.assertEqual(
            observed_progress,
            [
                {
                    "symbol": "AAPL",
                    "current": 1,
                    "total": 2,
                    "market_date": "2026-06-29",
                },
                {
                    "symbol": "AAPL",
                    "current": 2,
                    "total": 2,
                    "market_date": "2026-06-30",
                },
            ],
        )

    def test_backfill_logs_and_raises_failed_snapshot_with_symbol_and_date(self) -> None:
        repository = InMemorySignalLedgerRepository()

        def fake_analysis(request: object) -> object:
            if request.ohlcv_rows[-1]["date"] == "2026-06-30":
                raise RuntimeError("fixture analysis failure")
            return _fake_analysis(request)

        with TemporaryDirectory() as temporary_directory:
            log_path = Path(temporary_directory) / "evidence_loop.log"
            with patch(
                "src.application.signal_backfill_service.analyze_symbol_v2",
                side_effect=fake_analysis,
            ):
                with self.assertRaises(SignalBackfillSnapshotError) as raised:
                    backfill_missing_research_signals(
                        symbol="aapl",
                        data_source=MemoryDataSource(
                            [
                                _row("AAPL", "2026-06-29", 100.0),
                                _row("AAPL", "2026-06-30", 101.0),
                                _row("AAPL", "2026-07-01", 102.0),
                            ]
                        ),
                        signal_repository=repository,
                        as_of_date="2026-07-01",
                        error_log_path=log_path,
                    )

            self.assertEqual(raised.exception.symbol, "AAPL")
            self.assertEqual(raised.exception.market_date, "2026-06-30")
            self.assertEqual(raised.exception.current, 2)
            self.assertEqual(raised.exception.total, 2)
            self.assertIn("AAPL 2026-06-30", str(raised.exception))
            log_text = log_path.read_text(encoding="utf-8")
            self.assertIn("Evidence Loop snapshot failure: AAPL 2026-06-30", log_text)
            self.assertIn("fixture analysis failure", log_text)


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


def _signal(
    *,
    signal_id: str,
    symbol: str,
    signal_date: str,
    snapshot_date: str,
) -> SignalRecord:
    return SignalRecord(
        signal_id=signal_id,
        symbol=symbol,
        signal_date=signal_date,
        snapshot_reference=SignalSnapshotReference(
            snapshot_date=snapshot_date,
            timeframe="1D",
            source="fixture",
        ),
        signal_type=SignalType.SETUP,
        confidence=80.0,
    )


if __name__ == "__main__":
    unittest.main()
