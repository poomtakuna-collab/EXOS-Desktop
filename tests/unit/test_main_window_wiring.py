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

    def test_research_signal_save_refreshes_signal_history(self) -> None:
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
    if isinstance(node, ast.Name):
        return node.id
    raise AssertionError(f"Unexpected AST node: {ast.dump(node)}")


if __name__ == "__main__":
    unittest.main()
