from __future__ import annotations

import ast
import unittest
from pathlib import Path


class MainWindowWiringTest(unittest.TestCase):
    def test_chart_workspace_receives_shared_state_manager_by_keyword(self) -> None:
        tree = ast.parse(Path("src/gui/main_window.py").read_text(encoding="utf-8"))
        calls = [
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "ChartWorkspace"
        ]

        self.assertEqual(len(calls), 1)
        call = calls[0]
        keywords = {keyword.arg: keyword.value for keyword in call.keywords}

        self.assertEqual(call.args, [])
        self.assertIn("data_manager", keywords)
        self.assertIn("state_manager", keywords)
        self.assertIn("dashboard_widget", keywords)
        self.assertEqual(_attribute_name(keywords["data_manager"]), "self._data_manager")
        self.assertEqual(_attribute_name(keywords["state_manager"]), "self._state_manager")
        self.assertEqual(_attribute_name(keywords["dashboard_widget"]), "self._dashboard_panel")

    def test_dashboard_is_embedded_in_chart_workspace_not_right_dock(self) -> None:
        source = Path("src/gui/main_window.py").read_text(encoding="utf-8")

        self.assertIn("self._dashboard_panel = self._create_dashboard_panel()", source)
        self.assertIn("dashboard_widget=self._dashboard_panel", source)
        self.assertNotIn("def _create_dashboard_dock", source)
        self.assertNotIn("self._create_dashboard_dock()", source)
        self.assertIn("Dashboard ({MARKET_SCOPE})", source)

    def test_research_signal_save_refreshes_signal_history_and_performance(self) -> None:
        tree = ast.parse(Path("src/gui/main_window.py").read_text(encoding="utf-8"))
        calls = [
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "connect"
        ]

        connections = {
            (
                _attribute_name(call.func.value),
                _attribute_name(call.args[0]) if call.args else "",
            )
            for call in calls
        }

        self.assertIn(
            (
                "self._research_panel.signal_saved",
                "self._signal_history_panel.refresh",
            ),
            connections,
        )
        self.assertIn(
            (
                "self._research_panel.signal_saved",
                "self._performance_panel.refresh",
            ),
            connections,
        )

    def test_chart_workspace_symbol_load_signals_are_wired_to_main_window(self) -> None:
        tree = ast.parse(Path("src/gui/main_window.py").read_text(encoding="utf-8"))
        calls = [
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "connect"
        ]

        connections = {
            (
                _attribute_name(call.func.value),
                _attribute_name(call.args[0]) if call.args else "",
            )
            for call in calls
        }

        self.assertIn(
            (
                "self._chart_workspace.loading_started",
                "self._handle_symbol_loading_started",
            ),
            connections,
        )
        self.assertIn(
            (
                "self._chart_workspace.loading_progress",
                "self.statusBar().showMessage",
            ),
            connections,
        )
        self.assertIn(
            (
                "self._chart_workspace.loading_finished",
                "self._handle_symbol_loading_finished",
            ),
            connections,
        )
        self.assertIn(
            (
                "self._chart_workspace.loading_failed",
                "self._handle_symbol_loading_failed",
            ),
            connections,
        )

    def test_symbol_selection_is_ignored_while_background_load_is_active(self) -> None:
        tree = ast.parse(Path("src/gui/main_window.py").read_text(encoding="utf-8"))
        method = _method(tree, "_select_dashboard_symbol")
        called_names = {
            _call_name(call)
            for call in ast.walk(method)
            if isinstance(call, ast.Call)
        }
        string_constants = {
            node.value
            for node in ast.walk(method)
            if isinstance(node, ast.Constant)
            and isinstance(node.value, str)
        }

        self.assertIn("self._chart_workspace.is_loading", called_names)
        self.assertIn("self.statusBar().showMessage", called_names)
        self.assertIn("Symbol load already in progress...", string_constants)

    def test_symbol_load_completion_refreshes_views_and_reenables_dashboard(self) -> None:
        tree = ast.parse(Path("src/gui/main_window.py").read_text(encoding="utf-8"))
        method = _method(tree, "_handle_symbol_loading_finished")
        called_names = {
            _call_name(call)
            for call in ast.walk(method)
            if isinstance(call, ast.Call)
        }

        self.assertIn("self._dashboard_list.setEnabled", called_names)
        self.assertIn("self._research_panel.refresh", called_names)
        self.assertIn("self._performance_panel.refresh", called_names)
        self.assertIn("self._signal_history_panel.refresh", called_names)
        self.assertIn("self._developer_panel.refresh", called_names)
        self.assertIn("self.statusBar().showMessage", called_names)

    def test_symbol_load_failure_reenables_dashboard_and_reports_status(self) -> None:
        tree = ast.parse(Path("src/gui/main_window.py").read_text(encoding="utf-8"))
        method = _method(tree, "_handle_symbol_loading_failed")
        called_names = {
            _call_name(call)
            for call in ast.walk(method)
            if isinstance(call, ast.Call)
        }

        self.assertIn("self._dashboard_list.setEnabled", called_names)
        self.assertIn("self.statusBar().showMessage", called_names)

    def test_evidence_loop_action_triggers_manual_runner_method(self) -> None:
        tree = ast.parse(Path("src/gui/main_window.py").read_text(encoding="utf-8"))
        calls = [
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "connect"
        ]

        connections = {
            (
                _attribute_name(call.func.value),
                _attribute_name(call.args[0]) if call.args else "",
            )
            for call in calls
        }

        self.assertIn(
            (
                "self._evidence_loop_action.triggered",
                "self._run_manual_evidence_loop",
            ),
            connections,
        )

    def test_developer_menu_reset_snapshots_action_triggers_confirmed_reset(self) -> None:
        tree = ast.parse(Path("src/gui/main_window.py").read_text(encoding="utf-8"))
        calls = [
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "connect"
        ]
        connections = {
            (
                _attribute_name(call.func.value),
                _attribute_name(call.args[0]) if call.args else "",
            )
            for call in calls
        }

        self.assertIn(
            (
                "self._reset_snapshots_action.triggered",
                "self._confirm_and_reset_snapshots",
            ),
            connections,
        )
        self.assertIn(
            (
                "self._statistics_report_action.triggered",
                "self._show_statistics_report",
            ),
            connections,
        )
        self.assertIn(
            (
                "self._pattern_statistics_action.triggered",
                "self._show_pattern_statistics",
            ),
            connections,
        )

    def test_view_menu_can_open_developer_panel(self) -> None:
        tree = ast.parse(Path("src/gui/main_window.py").read_text(encoding="utf-8"))
        calls = [
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "connect"
        ]
        connections = {
            (
                _attribute_name(call.func.value),
                _attribute_name(call.args[0]) if call.args else "",
            )
            for call in calls
        }

        self.assertIn(
            (
                "self._developer_mode_action.toggled",
                "self._set_developer_mode_visible",
            ),
            connections,
        )

    def test_developer_reset_snapshots_menu_labels_are_visible(self) -> None:
        tree = ast.parse(Path("src/gui/main_window.py").read_text(encoding="utf-8"))
        string_constants = {
            node.value
            for node in ast.walk(tree)
            if isinstance(node, ast.Constant)
            and isinstance(node.value, str)
        }

        self.assertIn("View", string_constants)
        self.assertIn("Developer Panel", string_constants)
        self.assertIn("Developer", string_constants)
        self.assertIn("Reset Snapshots...", string_constants)
        self.assertIn("Statistics Report...", string_constants)
        self.assertIn("Pattern Statistics...", string_constants)

    def test_developer_panel_does_not_add_reset_button_clutter(self) -> None:
        tree = ast.parse(Path("src/gui/developer_panel.py").read_text(encoding="utf-8"))
        imported_names: set[str] = set()
        string_constants = {
            node.value
            for node in ast.walk(tree)
            if isinstance(node, ast.Constant)
            and isinstance(node.value, str)
        }

        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                imported_names.update(alias.name for alias in node.names)

        self.assertNotIn("QPushButton", imported_names)
        self.assertNotIn("Reset Snapshot Test Data", string_constants)

    def test_confirmed_snapshot_reset_shows_dialog_and_refreshes_views(self) -> None:
        tree = ast.parse(Path("src/gui/main_window.py").read_text(encoding="utf-8"))
        method = _method(tree, "_confirm_and_reset_snapshots")
        called_names = {
            _call_name(call)
            for call in ast.walk(method)
            if isinstance(call, ast.Call)
            and not (
                isinstance(call.func, ast.Attribute)
                and isinstance(call.func.value, ast.Constant)
            )
        }
        keyword_pairs = {
            (
                _call_name(call),
                keyword.arg,
                _attribute_name(keyword.value)
                if isinstance(keyword.value, ast.Attribute)
                else keyword.value.value
                if isinstance(keyword.value, ast.Constant)
                else "",
            )
            for call in ast.walk(method)
            if isinstance(call, ast.Call)
            for keyword in call.keywords
        }

        self.assertIn("QMessageBox.warning", called_names)
        self.assertIn("reset_snapshots", called_names)
        self.assertIn(("reset_snapshots", "confirm", True), keyword_pairs)
        self.assertIn("self._signal_history_panel.refresh", called_names)
        self.assertIn("self._performance_panel.refresh", called_names)
        self.assertIn("self._developer_panel.refresh", called_names)

    def test_statistics_report_action_loads_view_model_and_opens_dialog(self) -> None:
        tree = ast.parse(Path("src/gui/main_window.py").read_text(encoding="utf-8"))
        method = _method(tree, "_open_statistics_report")
        called_names = {
            _call_name(call)
            for call in ast.walk(method)
            if isinstance(call, ast.Call)
        }

        self.assertIn("load_statistics_report_view_model", called_names)
        self.assertIn("StatisticsReportDialog", called_names)
        self.assertIn("self._statistics_report_dialog.show", called_names)
        self.assertIn("self.statusBar().showMessage", called_names)
        self.assertIn("Building Statistics Report...", {
            node.value
            for node in ast.walk(method)
            if isinstance(node, ast.Constant)
            and isinstance(node.value, str)
        })

    def test_statistics_report_dialog_shows_required_sections(self) -> None:
        tree = ast.parse(Path("src/gui/main_window.py").read_text(encoding="utf-8"))
        string_constants = {
            node.value
            for node in ast.walk(tree)
            if isinstance(node, ast.Constant)
            and isinstance(node.value, str)
        }
        dialog_init = _class_method(tree, "StatisticsReportDialog", "__init__")
        source = ast.unparse(dialog_init)

        self.assertIn("Top Buckets by Sample Count", string_constants)
        self.assertIn("Top Buckets by Win Rate", string_constants)
        self.assertIn("Top Buckets by Expectancy", string_constants)
        self.assertIn("Current Symbol", string_constants)
        self.assertIn("All Symbols", string_constants)
        self.assertIn("top_by_sample_count", source)
        self.assertIn("top_by_win_rate", source)
        self.assertIn("top_by_expectancy", source)

    def test_pattern_statistics_action_loads_view_model_and_opens_dialog(self) -> None:
        tree = ast.parse(Path("src/gui/main_window.py").read_text(encoding="utf-8"))
        method = _method(tree, "_open_pattern_statistics")
        called_names = {
            _call_name(call)
            for call in ast.walk(method)
            if isinstance(call, ast.Call)
        }

        self.assertIn("load_pattern_statistics_view_model", called_names)
        self.assertIn("PatternStatisticsDialog", called_names)
        self.assertIn("self._pattern_statistics_dialog.show", called_names)
        self.assertIn("self.statusBar().showMessage", called_names)
        self.assertIn("Building Pattern Statistics...", {
            node.value
            for node in ast.walk(method)
            if isinstance(node, ast.Constant)
            and isinstance(node.value, str)
        })

    def test_pattern_statistics_dialog_shows_required_sections(self) -> None:
        tree = ast.parse(Path("src/gui/main_window.py").read_text(encoding="utf-8"))
        string_constants = {
            node.value
            for node in ast.walk(tree)
            if isinstance(node, ast.Constant)
            and isinstance(node.value, str)
        }
        dialog_init = _class_method(tree, "PatternStatisticsDialog", "__init__")
        source = ast.unparse(dialog_init)

        self.assertIn("Pattern Statistics", string_constants)
        self.assertIn("Bucket", string_constants)
        self.assertIn("Interpretation", string_constants)
        self.assertIn("rankings", source)
        self.assertIn("insights", source)

    def test_manual_evidence_loop_starts_background_worker_without_sync_runner_call(self) -> None:
        tree = ast.parse(Path("src/gui/main_window.py").read_text(encoding="utf-8"))
        method = _method(tree, "_run_manual_evidence_loop")
        calls = [
            node
            for node in ast.walk(method)
            if isinstance(node, ast.Call)
        ]
        called_names = {
            _call_name(call)
            for call in calls
        }

        self.assertNotIn("run_manual_evidence_loop", called_names)
        self.assertIn("QThread", called_names)
        self.assertIn("_EvidenceLoopWorker", called_names)
        self.assertIn("worker.moveToThread", called_names)
        self.assertIn("worker.progress.connect", called_names)
        self.assertIn("thread.start", called_names)
        self.assertIn("self._evidence_loop_action.setEnabled", called_names)
        self.assertIn("self.statusBar().showMessage", called_names)

    def test_evidence_loop_worker_calls_runner(self) -> None:
        tree = ast.parse(Path("src/gui/main_window.py").read_text(encoding="utf-8"))
        method = _method(tree, "run")
        called_names = {
            _call_name(call)
            for call in ast.walk(method)
            if isinstance(call, ast.Call)
            and not (
                isinstance(call.func, ast.Attribute)
                and isinstance(call.func.value, ast.Constant)
            )
        }

        self.assertIn("run_manual_evidence_loop", called_names)
        self.assertIn("self.finished.emit", called_names)
        self.assertIn("self.failed.emit", called_names)

    def test_evidence_loop_worker_forwards_progress_callback_to_runner(self) -> None:
        tree = ast.parse(Path("src/gui/main_window.py").read_text(encoding="utf-8"))
        method = _method(tree, "run")
        runner_calls = [
            call
            for call in ast.walk(method)
            if isinstance(call, ast.Call)
            and _call_name(call) == "run_manual_evidence_loop"
        ]

        self.assertEqual(len(runner_calls), 1)
        keywords = {keyword.arg: keyword.value for keyword in runner_calls[0].keywords}
        self.assertEqual(
            _attribute_name(keywords["progress_callback"]),
            "self._emit_progress",
        )
        self.assertEqual(
            _attribute_name(keywords["snapshot_repository"]),
            "snapshot_repository",
        )

    def test_evidence_loop_worker_initializes_daily_snapshot_repository(self) -> None:
        tree = ast.parse(Path("src/gui/main_window.py").read_text(encoding="utf-8"))
        method = _method(tree, "run")
        assignments = {
            _attribute_name(target): _attribute_name(node.value)
            for node in ast.walk(method)
            if isinstance(node, ast.Assign)
            for target in node.targets
        }
        called_names = {
            _call_name(call)
            for call in ast.walk(method)
            if isinstance(call, ast.Call)
        }

        self.assertEqual(
            assignments["snapshot_repository"],
            "SQLiteDailyResearchSnapshotRepository()",
        )
        self.assertIn("snapshot_repository.initialize_schema", called_names)

    def test_evidence_loop_worker_records_last_progress_before_emitting(self) -> None:
        tree = ast.parse(Path("src/gui/main_window.py").read_text(encoding="utf-8"))
        method = _method(tree, "_emit_progress")
        assigned_names = {
            _attribute_name(target): _attribute_name(node.value)
            for node in ast.walk(method)
            if isinstance(node, ast.Assign)
            for target in node.targets
        }
        called_names = {
            _call_name(call)
            for call in ast.walk(method)
            if isinstance(call, ast.Call)
        }

        self.assertEqual(assigned_names["self._last_progress"], "progress")
        self.assertIn("self.progress.emit", called_names)

    def test_evidence_loop_progress_updates_status_bar_with_count_and_symbol_date(
        self,
    ) -> None:
        tree = ast.parse(Path("src/gui/main_window.py").read_text(encoding="utf-8"))
        method = _method(tree, "_handle_evidence_loop_progress")
        called_names = {
            _call_name(call)
            for call in ast.walk(method)
            if isinstance(call, ast.Call)
            and not (
                isinstance(call.func, ast.Attribute)
                and isinstance(call.func.value, ast.Constant)
            )
        }
        string_constants = {
            node.value
            for node in ast.walk(method)
            if isinstance(node, ast.Constant)
            and isinstance(node.value, str)
        }

        self.assertIn("getattr", called_names)
        self.assertIn("self.statusBar().showMessage", called_names)
        self.assertIn("current", string_constants)
        self.assertIn("total", string_constants)
        self.assertIn("symbol", string_constants)
        self.assertIn("market_date", string_constants)
        self.assertIn(" snapshots", string_constants)

    def test_evidence_loop_worker_catches_unexpected_exceptions(self) -> None:
        tree = ast.parse(Path("src/gui/main_window.py").read_text(encoding="utf-8"))
        method = _method(tree, "run")
        handlers = [
            handler
            for handler in ast.walk(method)
            if isinstance(handler, ast.ExceptHandler)
        ]

        handled_names = {
            handler.type.id
            for handler in handlers
            if isinstance(handler.type, ast.Name)
        }
        called_names = {
            _call_name(call)
            for call in ast.walk(method)
            if isinstance(call, ast.Call)
        }

        self.assertIn("Exception", handled_names)
        self.assertIn("_log_evidence_loop_exception", called_names)
        self.assertIn("_evidence_loop_failure_message", called_names)
        self.assertIn("self.failed.emit", called_names)

    def test_evidence_loop_worker_references_are_retained_until_thread_finishes(self) -> None:
        tree = ast.parse(Path("src/gui/main_window.py").read_text(encoding="utf-8"))
        method = _method(tree, "_run_manual_evidence_loop")
        assignments = {
            _attribute_name(target): _attribute_name(node.value)
            for node in ast.walk(method)
            if isinstance(node, ast.Assign)
            for target in node.targets
        }
        connections = {
            (
                _attribute_name(call.func.value),
                _attribute_name(call.args[0]) if call.args else "",
            )
            for call in ast.walk(method)
            if isinstance(call, ast.Call)
            and isinstance(call.func, ast.Attribute)
            and call.func.attr == "connect"
        }

        self.assertEqual(assignments["self._evidence_loop_thread"], "thread")
        self.assertEqual(assignments["self._evidence_loop_worker"], "worker")
        self.assertIn(
            ("thread.finished", "self._clear_evidence_loop_worker"),
            connections,
        )

    def test_evidence_loop_worker_references_are_cleared_after_finish_or_error(self) -> None:
        tree = ast.parse(Path("src/gui/main_window.py").read_text(encoding="utf-8"))
        method = _method(tree, "_clear_evidence_loop_worker")
        cleared_names = {
            _attribute_name(target)
            for node in ast.walk(method)
            if isinstance(node, ast.Assign)
            and isinstance(node.value, ast.Constant)
            and node.value.value is None
            for target in node.targets
        }

        self.assertIn("self._evidence_loop_thread", cleared_names)
        self.assertIn("self._evidence_loop_worker", cleared_names)

    def test_evidence_loop_success_refreshes_views_and_reenables_action(self) -> None:
        tree = ast.parse(Path("src/gui/main_window.py").read_text(encoding="utf-8"))
        method = _method(tree, "_handle_evidence_loop_finished")
        called_names = {
            _call_name(call)
            for call in ast.walk(method)
            if isinstance(call, ast.Call)
        }
        string_constants = {
            node.value
            for node in ast.walk(method)
            if isinstance(node, ast.Constant)
            and isinstance(node.value, str)
        }

        self.assertIn("self._signal_history_panel.refresh", called_names)
        self.assertIn("self._performance_panel.refresh", called_names)
        self.assertIn("self._evidence_loop_action.setEnabled", called_names)
        self.assertIn("self.statusBar().showMessage", called_names)
        self.assertIn("snapshots_processed", string_constants)

    def test_evidence_loop_error_reenables_action_and_shows_status(self) -> None:
        tree = ast.parse(Path("src/gui/main_window.py").read_text(encoding="utf-8"))
        method = _method(tree, "_handle_evidence_loop_failed")
        called_names = {
            _call_name(call)
            for call in ast.walk(method)
            if isinstance(call, ast.Call)
        }

        self.assertIn("self._evidence_loop_action.setEnabled", called_names)
        self.assertIn("self.statusBar().showMessage", called_names)

    def test_research_surface_keeps_persistence_out_of_qt_widget(self) -> None:
        tree = ast.parse(Path("src/gui/research_surface.py").read_text(encoding="utf-8"))
        imported_names: set[str] = set()

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported_names.update(alias.name for alias in node.names)
            if isinstance(node, ast.ImportFrom) and node.module:
                imported_names.add(node.module)

        self.assertNotIn("sqlite3", imported_names)
        self.assertNotIn("src.signal_ledger.sqlite_repository", imported_names)


def _attribute_name(node: ast.AST) -> str:
    if isinstance(node, ast.Attribute):
        return f"{_attribute_name(node.value)}.{node.attr}"
    if isinstance(node, ast.Call):
        return f"{_attribute_name(node.func)}()"
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Lambda):
        return "lambda"
    raise AssertionError(f"Unexpected AST node: {ast.dump(node)}")


def _call_name(node: ast.Call) -> str:
    return _attribute_name(node.func)


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
