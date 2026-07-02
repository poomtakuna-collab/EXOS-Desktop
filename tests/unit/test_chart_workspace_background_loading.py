from __future__ import annotations

import ast
import unittest
from pathlib import Path


class ChartWorkspaceBackgroundLoadingTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tree = ast.parse(Path("src/gui/chart_workspace.py").read_text(encoding="utf-8"))
        self.chart_tree = ast.parse(Path("src/gui/candlestick_chart.py").read_text(encoding="utf-8"))

    def test_refresh_from_state_starts_background_symbol_load(self) -> None:
        method = _class_method(self.tree, "ChartWorkspace", "refresh_from_state")
        called_names = {
            _call_name(call)
            for call in ast.walk(method)
            if isinstance(call, ast.Call)
        }

        self.assertIn("self.is_loading", called_names)
        self.assertIn("self._chart.set_projection_overlay", called_names)
        self.assertIn("self._start_symbol_load", called_names)
        self.assertNotIn("self._chart_data_loader.get_cached_historical_data", called_names)
        self.assertNotIn("self._chart_data_loader.get_historical_data", called_names)

    def test_chart_workspace_uses_chart_projection_indicator_layout(self) -> None:
        init_method = _class_method(self.tree, "ChartWorkspace", "__init__")
        source = ast.unparse(init_method)
        called_names = {
            _call_name(call)
            for call in ast.walk(init_method)
            if isinstance(call, ast.Call)
        }

        self.assertIn("QSplitter", called_names)
        self.assertIn("main_splitter.addWidget", called_names)
        self.assertIn("chart_layout.addWidget(self._chart, 1)", source)
        self.assertNotIn("_action_overlay", source)
        self.assertIn("main_splitter.setStretchFactor(0, 6)", source)
        self.assertIn("main_splitter.setStretchFactor(1, 1)", source)
        self.assertIn("dashboard_widget", source)

    def test_chart_workspace_forwards_action_overlay_to_chart_canvas(self) -> None:
        method = _class_method(self.tree, "ChartWorkspace", "_handle_symbol_sidebar_ready")
        source = ast.unparse(method)
        called_names = {
            _call_name(call)
            for call in ast.walk(method)
            if isinstance(call, ast.Call)
        }

        self.assertIn("self._chart.set_projection_overlay", called_names)
        self.assertIn("view_model.get('chart_action_overlay')", source)

    def test_symbol_load_worker_uses_qthread_and_progress_signals(self) -> None:
        method = _class_method(self.tree, "ChartWorkspace", "_start_symbol_load")
        called_names = {
            _call_name(call)
            for call in ast.walk(method)
            if isinstance(call, ast.Call)
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

        self.assertIn("QThread", called_names)
        self.assertIn("_SymbolLoadWorker", called_names)
        self.assertIn("worker.moveToThread", called_names)
        self.assertIn("thread.start", called_names)
        self.assertIn(("worker.progress", "self._handle_symbol_load_progress"), connections)
        self.assertIn(("worker.chart_ready", "self._handle_symbol_chart_ready"), connections)
        self.assertIn(("worker.sidebar_ready", "self._handle_symbol_sidebar_ready"), connections)
        self.assertIn(("worker.finished", "self._handle_symbol_load_finished"), connections)
        self.assertIn(("worker.failed", "self._handle_symbol_load_failed"), connections)

    def test_symbol_load_worker_reports_required_progress_stages(self) -> None:
        method = _class_method(self.tree, "_SymbolLoadWorker", "run")
        string_constants = {
            node.value
            for node in ast.walk(method)
            if isinstance(node, ast.Constant)
            and isinstance(node.value, str)
        }

        self.assertIn("Reading OHLCV...", string_constants)
        self.assertIn("Building Indicators...", string_constants)
        self.assertIn("Loading Snapshot...", string_constants)
        self.assertIn("Loading POOM Combo...", string_constants)
        self.assertIn("Loading Statistics...", string_constants)
        self.assertIn("Loading Historical Edge...", string_constants)
        self.assertIn("Loading Research Summary...", string_constants)

    def test_symbol_load_worker_completion_and_failure_signals(self) -> None:
        method = _class_method(self.tree, "_SymbolLoadWorker", "run")
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
        self.assertIn("self.finished.emit", called_names)
        self.assertIn("self.failed.emit", called_names)

    def test_sidebar_progressive_updates_use_prepared_view_models(self) -> None:
        method = _class_method(self.tree, "_SymbolLoadWorker", "_emit_sidebar_stage")
        called_names = {
            _call_name(call)
            for call in ast.walk(method)
            if isinstance(call, ast.Call)
        }

        self.assertIn("self.progress.emit", called_names)
        self.assertIn("empty_chart_research_sidebar_view_model", called_names)
        self.assertIn("self.sidebar_ready.emit", called_names)

    def test_candlestick_chart_renders_projection_as_chart_layer(self) -> None:
        source = Path("src/gui/candlestick_chart.py").read_text(encoding="utf-8")
        draw_method = _class_method(self.chart_tree, "CandlestickChart", "_draw_candles")
        called_names = {
            _call_name(call)
            for call in ast.walk(draw_method)
            if isinstance(call, ast.Call)
        }

        self.assertIn("PROJECTION_FUTURE_SLOTS = 30", source)
        self.assertIn("def set_projection_overlay", source)
        self.assertIn("self._draw_projection_background", called_names)
        self.assertIn("self._draw_projection_foreground", called_names)
        self.assertIn("candle_count + future_slots", source)

    def test_projection_area_suppresses_historical_hover_tooltip(self) -> None:
        source = Path("src/gui/candlestick_chart.py").read_text(encoding="utf-8")
        hover_method = _class_method(self.chart_tree, "CandlestickChart", "_update_hover_tooltip")
        crosshair_method = _class_method(self.chart_tree, "CandlestickChart", "_draw_crosshair")
        nearest_method = _class_method(self.chart_tree, "CandlestickChart", "_nearest_row_index")
        hover_source = ast.unparse(hover_method)
        crosshair_source = ast.unparse(crosshair_method)
        nearest_source = ast.unparse(nearest_method)

        self.assertIn("def _historical_chart_right", source)
        self.assertIn("def _is_projection_area", source)
        self.assertIn("self._is_projection_area(x, price_rect)", hover_source)
        self.assertIn("QToolTip.hideText()", hover_source)
        self.assertIn("self._is_projection_area(x, price_rect)", crosshair_source)
        self.assertIn("self._historical_chart_right(price_rect)", nearest_source)

    def test_chart_workspace_does_not_use_action_overlay_side_panel(self) -> None:
        workspace_source = Path("src/gui/chart_workspace.py").read_text(encoding="utf-8")
        sidebar_source = Path("src/gui/chart_research_sidebar.py").read_text(encoding="utf-8")

        self.assertNotIn("ChartActionOverlayPanel", workspace_source)
        self.assertNotIn("ChartActionOverlayPanel", sidebar_source)


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
