from __future__ import annotations

import ast
import sqlite3
import tempfile
import unittest
from pathlib import Path

from src.canonical_result import (
    CanonicalBrainResultV1,
    CanonicalIdentityV1,
    CanonicalPredictionResultV1,
    CanonicalResultV1,
)
from src.daily_research_snapshot import SQLiteDailyResearchSnapshotRepository
from src.gui.signal_history_view_model import (
    SIGNAL_HISTORY_COLUMNS,
    build_snapshot_detail_view_model,
    build_signal_history_view_model,
    load_desktop_snapshot_detail_view_model,
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
            "Select a dashboard symbol to view saved snapshot history.",
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
            self.assertEqual(view_model["status"], "No saved snapshots found for AAPL.")

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
            self.assertEqual(view_model["status"], "No saved snapshots found for MSFT.")

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
            self.assertEqual(view_model["status"], "Read-only snapshot history for AAPL.")
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

    def test_snapshot_detail_view_model_handles_empty_fields_safely(self) -> None:
        view_model = build_snapshot_detail_view_model()

        self.assertEqual(view_model["title"], "Snapshot Detail")
        self.assertEqual(view_model["raw_json"], "{}")
        self.assertEqual(view_model["status"], "Snapshot detail is not available.")
        header = view_model["header"]
        self.assertEqual(header[0]["value"], "-")

    def test_snapshot_detail_view_model_formats_groups_and_json_deterministically(self) -> None:
        signal = SignalRecord(
            signal_id="signal-1",
            symbol="AAPL",
            signal_date="2026-07-01",
            snapshot_reference=SignalSnapshotReference(
                snapshot_id="snapshot-1",
                snapshot_date="2026-07-01",
                timeframe="1D",
                source="fixture",
            ),
            context_summary={
                "brain_version": "brain-v1",
                "indicators": {"rsi": 55.1234},
                "market": {"regime": "risk_on"},
                "prediction_summary": {"confidence": 0.75},
            },
            strategy_summary={"grade": "A", "score": 82},
            signal_type=SignalType.SETUP,
            confidence=75.0,
            notes=("first",),
        )
        outcome = _outcome(OutcomeStatus.POSITIVE, 5.0)

        view_model = build_snapshot_detail_view_model(
            signal=signal,
            outcomes=(outcome,),
        )

        self.assertEqual(view_model["title"], "Snapshot Detail - AAPL")
        header = view_model["header"]
        self.assertEqual(header[0]["value"], "AAPL")
        self.assertEqual(header[1]["value"], "2026-07-01")
        self.assertEqual(header[2]["value"], "snapshot-1")
        self.assertEqual(header[3]["value"], "brain-v1")
        self.assertEqual(header[4]["value"], "Positive / 5.00%")
        raw_json = view_model["raw_json"]
        self.assertIn('  "confidence": 75.0', raw_json)
        self.assertIn('  "linked_outcome_count": 1', raw_json)
        self.assertLess(raw_json.index('"confidence"'), raw_json.index('"context_summary"'))

    def test_load_snapshot_detail_view_model_loads_exact_snapshot_id(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "exos.db"
            connection = sqlite3.connect(db_path)
            try:
                repository = SQLiteSignalLedgerRepository(connection)
                repository.initialize_schema()
                repository.save_signal(_signal("signal-1", "AAPL", SignalType.SETUP, 75.0))
                repository.save_signal(_signal("signal-2", "AAPL", SignalType.RISK, None))
                repository.save_outcome(
                    "signal-2",
                    _outcome(OutcomeStatus.NEGATIVE, -4.0),
                )
            finally:
                connection.close()

            view_model = load_desktop_snapshot_detail_view_model(
                db_path,
                signal_id="signal-2",
            )

            header = view_model["header"]
            self.assertEqual(header[2]["value"], "snapshot-signal-2")
            self.assertEqual(header[4]["value"], "Negative / -4.00%")
            self.assertIn('"signal_id": "signal-2"', view_model["raw_json"])

    def test_snapshot_detail_prefers_v2_canonical_payload(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "exos.db"
            canonical = _canonical_result()
            connection = sqlite3.connect(db_path)
            try:
                signal_repository = SQLiteSignalLedgerRepository(connection)
                signal_repository.initialize_schema()
                signal_repository.save_signal(_signal("signal-1", "AAPL", SignalType.SETUP, 75.0))
                snapshot_repository = SQLiteDailyResearchSnapshotRepository(connection)
                snapshot_repository.initialize_schema()
                snapshot_repository.save_snapshot(
                    canonical,
                    signal_id="signal-1",
                    created_at="2026-07-01",
                )
            finally:
                connection.close()

            view_model = load_desktop_snapshot_detail_view_model(
                db_path,
                signal_id="signal-1",
            )

            self.assertEqual(view_model["status"], "Snapshot Payload v2")
            header = view_model["header"]
            self.assertEqual(header[0]["value"], "AAPL")
            self.assertEqual(header[1]["value"], "2026-07-01")
            self.assertEqual(header[2]["value"], "canonical-snapshot-1")
            self.assertEqual(header[3]["value"], "analysis_pipeline_v2")
            self.assertEqual(
                [tab["title"] for tab in view_model["tabs"]],
                [
                    "Identity",
                    "Provenance",
                    "Input",
                    "Analysis",
                    "Context",
                    "Strategy",
                    "Diagnostics",
                    "Compatibility",
                ],
            )
            identity_items = view_model["tabs"][0]["items"]
            self.assertIn(
                {"label": "Payload Schema Version", "value": "snapshot_payload_v2"},
                identity_items,
            )
            self.assertIn('"payload_schema_version": "snapshot_payload_v2"', view_model["raw_json"])
            self.assertIn('"resolver_output"', view_model["raw_json"])

    def test_snapshot_detail_falls_back_to_legacy_when_v2_missing(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "exos.db"
            connection = sqlite3.connect(db_path)
            try:
                repository = SQLiteSignalLedgerRepository(connection)
                repository.initialize_schema()
                repository.save_signal(_signal("signal-1", "AAPL", SignalType.SETUP, 75.0))
            finally:
                connection.close()

            view_model = load_desktop_snapshot_detail_view_model(
                db_path,
                signal_id="signal-1",
            )

            self.assertEqual(view_model["status"], "Legacy Compatibility Projection")
            self.assertIn('"signal_id": "signal-1"', view_model["raw_json"])

    def test_snapshot_detail_missing_v2_table_is_safe(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "exos.db"
            connection = sqlite3.connect(db_path)
            try:
                repository = SQLiteSignalLedgerRepository(connection)
                repository.initialize_schema()
                repository.save_signal(_signal("signal-1", "AAPL", SignalType.SETUP, 75.0))
            finally:
                connection.close()

            view_model = load_desktop_snapshot_detail_view_model(
                db_path,
                signal_id="signal-1",
            )

            self.assertEqual(view_model["status"], "Legacy Compatibility Projection")

    def test_snapshot_detail_can_find_v2_by_symbol_market_date_and_timeframe(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "exos.db"
            canonical = _canonical_result()
            connection = sqlite3.connect(db_path)
            try:
                signal_repository = SQLiteSignalLedgerRepository(connection)
                signal_repository.initialize_schema()
                signal_repository.save_signal(_signal("signal-1", "AAPL", SignalType.SETUP, 75.0))
                snapshot_repository = SQLiteDailyResearchSnapshotRepository(connection)
                snapshot_repository.initialize_schema()
                snapshot_repository.save_snapshot(canonical, created_at="2026-07-01")
            finally:
                connection.close()

            view_model = load_desktop_snapshot_detail_view_model(
                db_path,
                signal_id="signal-1",
            )

            self.assertEqual(view_model["status"], "Snapshot Payload v2")
            self.assertIn('"payload_schema_version": "snapshot_payload_v2"', view_model["raw_json"])

    def test_history_rows_include_hidden_signal_id_for_detail_loading(self) -> None:
        signal = _signal("signal-1", "AAPL", SignalType.SETUP, 75.0)

        view_model = build_signal_history_view_model(
            selected_symbol="AAPL",
            signals=(signal,),
        )

        self.assertEqual(view_model["rows"][0]["signal_id"], "signal-1")

    def test_snapshot_history_double_click_opens_detail_viewer(self) -> None:
        tree = ast.parse(Path("src/gui/signal_history_surface.py").read_text(encoding="utf-8"))
        connections = {
            (
                _attribute_name(call.func.value),
                _attribute_name(call.args[0]) if call.args else "",
            )
            for call in ast.walk(tree)
            if isinstance(call, ast.Call)
            and isinstance(call.func, ast.Attribute)
            and call.func.attr == "connect"
        }
        open_method = _method(tree, "_open_snapshot_detail")
        called_names = {
            _attribute_name(call.func)
            for call in ast.walk(open_method)
            if isinstance(call, ast.Call)
        }

        self.assertIn(
            ("self._table.cellDoubleClicked", "self._open_snapshot_detail"),
            connections,
        )
        self.assertIn("load_desktop_snapshot_detail_view_model", called_names)
        self.assertIn("SnapshotDetailDialog", called_names)

    def test_snapshot_detail_dialog_prefers_v2_tabs_when_available(self) -> None:
        tree = ast.parse(Path("src/gui/signal_history_surface.py").read_text(encoding="utf-8"))
        dialog_init = _class_method(tree, "SnapshotDetailDialog", "__init__")
        source = ast.unparse(dialog_init)

        self.assertIn("detail_tabs = view_model.get('tabs')", source)
        self.assertIn("detail_tabs if isinstance(detail_tabs, tuple) else view_model.get('groups')", source)


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


def _canonical_result() -> CanonicalResultV1:
    return CanonicalResultV1(
        identity=CanonicalIdentityV1(
            symbol="AAPL",
            timeframe="1D",
            snapshot_id="canonical-snapshot-1",
            snapshot_date="2026-07-01",
            analysis_date="2026-07-01",
            source="analysis_pipeline_v2",
            pipeline_version="pipeline-v2",
        ),
        brain=CanonicalBrainResultV1(
            snapshot={"indicators": {"rsi": 55.0}},
            resolver_output={"matches": [{"pattern_id": "pattern-1"}]},
            prediction_summary={"confidence": 72.0, "evidence_count": 12},
            metadata={"brain_version": "brain-v1"},
        ),
        prediction=CanonicalPredictionResultV1(
            confidence=72.0,
            evidence_count=12,
            expected_return_10d=4.5,
            best_pattern_id="pattern-1",
        ),
    )


def _json_pretty(value: object) -> str:
    import json

    return json.dumps(value, indent=2, sort_keys=True, default=str)


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


def _attribute_name(node: ast.AST) -> str:
    if isinstance(node, ast.Attribute):
        return f"{_attribute_name(node.value)}.{node.attr}"
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Call):
        return f"{_attribute_name(node.func)}()"
    if isinstance(node, ast.Subscript):
        return f"{_attribute_name(node.value)}[]"
    raise AssertionError(f"Unexpected AST node: {ast.dump(node)}")


def _method(tree: ast.Module, name: str) -> ast.FunctionDef:
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return node
    raise AssertionError(f"Missing method: {name}")


def _class_method(tree: ast.Module, class_name: str, method_name: str) -> ast.FunctionDef:
    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef) or node.name != class_name:
            continue
        for item in node.body:
            if isinstance(item, ast.FunctionDef) and item.name == method_name:
                return item
    raise AssertionError(f"Missing method: {class_name}.{method_name}")


if __name__ == "__main__":
    unittest.main()
