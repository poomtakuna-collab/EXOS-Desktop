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
        self.assertEqual(_attribute_name(keywords["data_manager"]), "self._data_manager")
        self.assertEqual(_attribute_name(keywords["state_manager"]), "self._state_manager")

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
        }

        self.assertIn("run_manual_evidence_loop", called_names)
        self.assertIn("self.finished.emit", called_names)
        self.assertIn("self.failed.emit", called_names)

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

        self.assertIn("self._signal_history_panel.refresh", called_names)
        self.assertIn("self._performance_panel.refresh", called_names)
        self.assertIn("self._evidence_loop_action.setEnabled", called_names)
        self.assertIn("self.statusBar().showMessage", called_names)

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
    raise AssertionError(f"Unexpected AST node: {ast.dump(node)}")


def _call_name(node: ast.Call) -> str:
    return _attribute_name(node.func)


def _method(tree: ast.Module, name: str) -> ast.FunctionDef:
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return node
    raise AssertionError(f"Missing method: {name}")


if __name__ == "__main__":
    unittest.main()
