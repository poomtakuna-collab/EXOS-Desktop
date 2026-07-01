from __future__ import annotations

import sqlite3
import tempfile
import unittest
from pathlib import Path

from src.gui.signal_history_view_model import (
    SIGNAL_HISTORY_COLUMNS,
    build_signal_history_view_model,
    load_desktop_signal_history_view_model,
)
from src.outcome_tracking import OutcomeRecord, OutcomeStatus
from src.signal_ledger import SignalRecord, SignalSnapshotReference, SignalType
from src.signal_ledger.sqlite_repository import (
    CREATE_SIGNAL_LEDGER_SIGNALS_TABLE_SQL,
    SQLiteSignalLedgerRepository,
)


class SignalHistorySurfaceTest(unittest.TestCase):
    def test_no_selected_symbol_returns_empty_state(self) -> None:
        view_model = build_signal_history_view_model()

        self.assertEqual(view_model["selected_symbol"], "No symbol selected")
        self.assertEqual(view_model["columns"], SIGNAL_HISTORY_COLUMNS)
        self.assertEqual(view_model["rows"], ())
        self.assertEqual(
            view_model["status"],
            "Select a dashboard symbol to view saved signal history.",
        )

    def test_missing_database_returns_empty_selected_symbol_without_creating_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "missing.db"

            view_model = load_desktop_signal_history_view_model(
                db_path,
                selected_symbol="aapl",
            )

            self.assertFalse(db_path.exists())
            self.assertEqual(view_model["selected_symbol"], "AAPL")
            self.assertEqual(view_model["rows"], ())
            self.assertEqual(view_model["status"], "No saved signals found for AAPL.")

    def test_database_without_signal_ledger_tables_returns_empty_state(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "exos.db"
            connection = sqlite3.connect(db_path)
            try:
                connection.execute("CREATE TABLE unrelated (id INTEGER PRIMARY KEY)")
                connection.commit()
            finally:
                connection.close()

            view_model = load_desktop_signal_history_view_model(
                db_path,
                selected_symbol="MSFT",
            )

            self.assertEqual(view_model["rows"], ())
            self.assertEqual(view_model["status"], "No saved signals found for MSFT.")

    def test_loads_selected_symbol_signals_and_linked_outcomes(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "exos.db"
            connection = sqlite3.connect(db_path)
            try:
                repository = SQLiteSignalLedgerRepository(connection)
                repository.initialize_schema()
                repository.save_signal(_signal("signal-1", "AAPL", SignalType.SETUP, 75.0))
                repository.save_signal(_signal("signal-2", "MSFT", SignalType.BREAKOUT, 85.0))
                repository.save_signal(_signal("signal-3", "AAPL", SignalType.RISK, None))
                repository.save_outcome(
                    "signal-1",
                    _outcome(OutcomeStatus.POSITIVE, 5.0),
                )
                repository.save_outcome(
                    "signal-1",
                    _outcome(OutcomeStatus.TARGET_HIT, 8.25),
                )
                repository.save_outcome(
                    "signal-2",
                    _outcome(OutcomeStatus.NEGATIVE, -3.0, symbol="MSFT"),
                )
            finally:
                connection.close()

            view_model = load_desktop_signal_history_view_model(
                db_path,
                selected_symbol="aapl",
            )

            self.assertEqual(view_model["selected_symbol"], "AAPL")
            self.assertEqual(view_model["status"], "Read-only signal history for AAPL.")
            self.assertEqual(len(view_model["rows"]), 2)
            first_row = view_model["rows"][0]
            second_row = view_model["rows"][1]
            self.assertEqual(first_row["signal_date"], "2026-07-01")
            self.assertEqual(first_row["signal_type"], "Setup")
            self.assertEqual(first_row["confidence"], "75.00%")
            self.assertEqual(first_row["snapshot"], "2026-07-01 / snapshot-signal-1")
            self.assertEqual(first_row["linked_outcome_count"], "2")
            self.assertEqual(first_row["latest_outcome"], "Target Hit / 8.25%")
            self.assertEqual(second_row["signal_type"], "Risk")
            self.assertEqual(second_row["confidence"], "-")
            self.assertEqual(second_row["linked_outcome_count"], "0")
            self.assertEqual(second_row["latest_outcome"], "-")

    def test_signal_table_without_outcome_table_still_lists_signals(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "exos.db"
            connection = sqlite3.connect(db_path)
            try:
                connection.execute(CREATE_SIGNAL_LEDGER_SIGNALS_TABLE_SQL)
                connection.execute(
                    """
                    INSERT INTO signal_ledger_signals (
                        signal_id,
                        symbol,
                        signal_date,
                        snapshot_id,
                        snapshot_date,
                        timeframe,
                        snapshot_source,
                        context_summary_json,
                        strategy_summary_json,
                        signal_type,
                        confidence,
                        notes_json
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        "signal-1",
                        "AAPL",
                        "2026-07-01",
                        "snapshot-1",
                        "2026-07-01",
                        "1D",
                        "fixture",
                        "{}",
                        "{}",
                        "setup",
                        75.0,
                        "[]",
                    ),
                )
                connection.commit()
            finally:
                connection.close()

            view_model = load_desktop_signal_history_view_model(
                db_path,
                selected_symbol="AAPL",
            )

            self.assertEqual(len(view_model["rows"]), 1)
            self.assertEqual(view_model["rows"][0]["linked_outcome_count"], "0")
            self.assertEqual(view_model["rows"][0]["latest_outcome"], "-")

    def test_builder_formats_custom_signal_and_outcome_values(self) -> None:
        signal = _signal("signal-1", "AAPL", "custom-signal", None)
        outcome = _outcome("custom-outcome", None)

        view_model = build_signal_history_view_model(
            selected_symbol="AAPL",
            signals=(signal,),
            outcomes_by_signal_id={"signal-1": (outcome,)},
        )

        row = view_model["rows"][0]
        self.assertEqual(row["signal_type"], "Custom Signal")
        self.assertEqual(row["latest_outcome"], "Custom Outcome")


def _signal(
    signal_id: str,
    symbol: str,
    signal_type: SignalType | str,
    confidence: float | None,
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
    status: OutcomeStatus | str,
    return_pct: float | None,
    *,
    symbol: str = "AAPL",
) -> OutcomeRecord:
    return OutcomeRecord(
        symbol=symbol,
        signal_date="2026-07-01",
        evaluation_date="2026-07-11",
        horizon_days=10,
        entry_price=100.0,
        close_price=100.0 + return_pct if return_pct is not None else None,
        return_pct=return_pct,
        max_runup_pct=max(return_pct, 0.0) if return_pct is not None else None,
        max_drawdown_pct=min(return_pct, 0.0) if return_pct is not None else None,
        outcome_status=status,
    )


if __name__ == "__main__":
    unittest.main()
