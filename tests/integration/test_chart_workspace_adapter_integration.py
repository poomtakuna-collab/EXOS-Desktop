from __future__ import annotations

import sys
import types
import unittest

from src.data import HistoricalDataResult
from src.data_source import MemoryDataSource
from src.gui.chart_data_adapter import ChartDataAdapter


def _install_fake_pyside() -> None:
    if "PySide6" in sys.modules:
        return

    pyside_module = types.ModuleType("PySide6")
    qtcore_module = types.ModuleType("PySide6.QtCore")
    qtgui_module = types.ModuleType("PySide6.QtGui")
    qtwidgets_module = types.ModuleType("PySide6.QtWidgets")

    class _Qt:
        AlignCenter = 1
        AlignRight = 2
        AlignVCenter = 4
        AlignLeft = 8
        DashLine = 16

    class _Signal:
        def __init__(self) -> None:
            self._callbacks: list[object] = []

        def connect(self, callback: object) -> None:
            self._callbacks.append(callback)

        def emit(self) -> None:
            for callback in self._callbacks:
                if callable(callback):
                    callback()

    class _Widget:
        def __init__(self, *args: object, **kwargs: object) -> None:
            del args, kwargs
            self._layout = None
            self._minimum_height = 0
            self._mouse_tracking = False
            self._updated = False

        def setLayout(self, layout: object) -> None:  # noqa: N802
            self._layout = layout

        def setMinimumHeight(self, height: int) -> None:  # noqa: N802
            self._minimum_height = height

        def setMouseTracking(self, enabled: bool) -> None:  # noqa: N802
            self._mouse_tracking = enabled

        def update(self) -> None:
            self._updated = True

        def width(self) -> int:
            return 800

        def height(self) -> int:
            return 600

    class _Label(_Widget):
        def __init__(self, text: str = "", *args: object, **kwargs: object) -> None:
            super().__init__(*args, **kwargs)
            self._text = text
            self._alignment = None

        def setText(self, text: str) -> None:  # noqa: N802
            self._text = text

        def text(self) -> str:
            return self._text

        def setAlignment(self, alignment: object) -> None:  # noqa: N802
            self._alignment = alignment

    class _Button(_Widget):
        def __init__(self, text: str = "", *args: object, **kwargs: object) -> None:
            super().__init__(*args, **kwargs)
            self._text = text
            self.clicked = _Signal()
            self._checked = False

        def setCheckable(self, checkable: bool) -> None:  # noqa: N802
            del checkable

        def setFixedWidth(self, width: int) -> None:  # noqa: N802
            del width

        def setChecked(self, checked: bool) -> None:  # noqa: N802
            self._checked = checked

    class _ButtonGroup:
        def __init__(self, *args: object, **kwargs: object) -> None:
            del args, kwargs
            self.buttons: list[object] = []

        def addButton(self, button: object) -> None:  # noqa: N802
            self.buttons.append(button)

    class _Layout:
        def __init__(self, *args: object, **kwargs: object) -> None:
            del args, kwargs
            self.items: list[object] = []

        def addStretch(self) -> None:  # noqa: N802
            self.items.append("stretch")

        def addWidget(self, widget: object, *args: object) -> None:  # noqa: N802
            del args
            self.items.append(widget)

        def addLayout(self, layout: object) -> None:  # noqa: N802
            self.items.append(layout)

    class _Color:
        def __init__(self, *args: object, **kwargs: object) -> None:
            del args, kwargs

    class _Point:
        def __init__(self, *args: object, **kwargs: object) -> None:
            del args, kwargs

    class _Rect:
        def __init__(self, *args: object, **kwargs: object) -> None:
            del args, kwargs

    class _Painter:
        Antialiasing = 1

    class _Pen:
        def __init__(self, *args: object, **kwargs: object) -> None:
            del args, kwargs

    class _ToolTip:
        @staticmethod
        def hideText() -> None:  # noqa: N802
            return None

        @staticmethod
        def showText(*args: object, **kwargs: object) -> None:  # noqa: N802
            del args, kwargs

    qtcore_module.Qt = _Qt
    qtcore_module.Signal = _Signal
    qtcore_module.QPointF = _Point
    qtcore_module.QRectF = _Rect
    qtgui_module.QColor = _Color
    qtgui_module.QPainter = _Painter
    qtgui_module.QPen = _Pen
    qtwidgets_module.QButtonGroup = _ButtonGroup
    qtwidgets_module.QHBoxLayout = _Layout
    qtwidgets_module.QLabel = _Label
    qtwidgets_module.QPushButton = _Button
    qtwidgets_module.QVBoxLayout = _Layout
    qtwidgets_module.QWidget = _Widget
    qtwidgets_module.QToolTip = _ToolTip

    sys.modules["PySide6"] = pyside_module
    sys.modules["PySide6.QtCore"] = qtcore_module
    sys.modules["PySide6.QtGui"] = qtgui_module
    sys.modules["PySide6.QtWidgets"] = qtwidgets_module


_install_fake_pyside()

import src.gui.chart_workspace as chart_workspace_module  # noqa: E402
from src.core.state_manager import StateManager  # noqa: E402
from src.gui.chart_workspace import ChartWorkspace  # noqa: E402


class ChartWorkspaceAdapterIntegrationTest(unittest.TestCase):
    def setUp(self) -> None:
        self._original_required_count = chart_workspace_module.REQUIRED_ROW_COUNT
        chart_workspace_module.REQUIRED_ROW_COUNT = 2

    def tearDown(self) -> None:
        chart_workspace_module.REQUIRED_ROW_COUNT = self._original_required_count

    def test_successful_adapter_load_updates_chart_model(self) -> None:
        state = StateManager()
        state.set_current_symbol("aapl")
        legacy = _LegacyLoader()
        adapter = ChartDataAdapter(
            legacy_data_loader=legacy,
            data_source=MemoryDataSource(
                [
                    _row("AAPL", "2026-01-01", 100.0),
                    _row("AAPL", "2026-01-02", 101.0),
                ]
            ),
            required_row_count=2,
        )
        workspace = ChartWorkspace(
            data_manager=_UnusedDataManager(),
            chart_data_loader=adapter,
            state_manager=state,
        )

        workspace.refresh_from_state()

        self.assertEqual(
            [row["date"] for row in workspace._chart.rendered_rows()],
            ["2026-01-01", "2026-01-02"],
        )
        self.assertEqual(state.market_data_rows, 2)
        self.assertEqual(state.market_data_source, "memory")
        self.assertEqual(legacy.cached_calls, 0)
        self.assertEqual(legacy.historical_calls, 0)

    def test_empty_adapter_response_uses_legacy_fallback_path(self) -> None:
        state = StateManager()
        state.set_current_symbol("AAPL")
        legacy = _LegacyLoader(
            cached_sequence=(
                HistoricalDataResult(rows=[], source="legacy-cache"),
                HistoricalDataResult(
                    rows=[_chart_row("legacy-1", 90.0), _chart_row("legacy-2", 91.0)],
                    source="legacy-cache",
                ),
            ),
            historical=HistoricalDataResult(
                rows=[_chart_row("legacy-live", 92.0)],
                source="legacy-live",
            ),
        )
        adapter = ChartDataAdapter(
            legacy_data_loader=legacy,
            data_source=MemoryDataSource([]),
            required_row_count=2,
        )
        workspace = ChartWorkspace(
            data_manager=_UnusedDataManager(),
            chart_data_loader=adapter,
            state_manager=state,
        )

        workspace.refresh_from_state()

        self.assertEqual(
            [row["date"] for row in workspace._chart.rendered_rows()],
            ["legacy-1", "legacy-2"],
        )
        self.assertEqual(legacy.cached_calls, 2)
        self.assertEqual(legacy.historical_calls, 1)

    def test_adapter_exception_uses_legacy_fallback_inside_adapter(self) -> None:
        state = StateManager()
        state.set_current_symbol("AAPL")
        legacy = _LegacyLoader(
            cached_sequence=(
                HistoricalDataResult(
                    rows=[_chart_row("legacy-1", 90.0), _chart_row("legacy-2", 91.0)],
                    source="legacy-cache",
                ),
            ),
        )
        adapter = ChartDataAdapter(
            legacy_data_loader=legacy,
            data_source=_FailingDataSource(),
            required_row_count=2,
        )
        workspace = ChartWorkspace(
            data_manager=_UnusedDataManager(),
            chart_data_loader=adapter,
            state_manager=state,
        )

        workspace.refresh_from_state()

        self.assertEqual(
            [row["date"] for row in workspace._chart.rendered_rows()],
            ["legacy-1", "legacy-2"],
        )
        self.assertEqual(state.market_data_source, "legacy-cache")
        self.assertEqual(legacy.cached_calls, 1)

    def test_symbol_switching_triggers_adapter_reloads(self) -> None:
        state = StateManager()
        loader = _SymbolAwareLoader()
        workspace = ChartWorkspace(
            data_manager=_UnusedDataManager(),
            chart_data_loader=loader,
            state_manager=state,
        )

        state.set_current_symbol("AAPL")
        workspace.refresh_from_state()
        state.set_current_symbol("MSFT")
        workspace.refresh_from_state()

        self.assertEqual(loader.cached_symbols, ["AAPL", "MSFT"])
        self.assertEqual(workspace._chart.rendered_rows()[-1]["date"], "MSFT-2")
        self.assertEqual(state.market_data_source, "adapter:MSFT")

    def test_repeated_refresh_requests_adapter_each_time(self) -> None:
        state = StateManager()
        state.set_current_symbol("AAPL")
        loader = _SymbolAwareLoader()
        workspace = ChartWorkspace(
            data_manager=_UnusedDataManager(),
            chart_data_loader=loader,
            state_manager=state,
        )

        workspace.refresh_from_state()
        workspace.refresh_from_state()

        self.assertEqual(loader.cached_symbols, ["AAPL", "AAPL"])
        self.assertEqual(len(workspace._chart.rendered_rows()), 2)


class _UnusedDataManager:
    pass


class _LegacyLoader:
    def __init__(
        self,
        *,
        cached_sequence: tuple[HistoricalDataResult, ...] = (),
        historical: HistoricalDataResult | None = None,
    ) -> None:
        self._cached_sequence = list(cached_sequence)
        self._last_cached = (
            cached_sequence[-1]
            if cached_sequence
            else HistoricalDataResult(rows=[], source="legacy-cache")
        )
        self._historical = historical or HistoricalDataResult(
            rows=[],
            source="legacy-live",
        )
        self.cached_calls = 0
        self.historical_calls = 0

    def get_cached_historical_data(self, symbol: str) -> HistoricalDataResult:
        del symbol
        self.cached_calls += 1
        if self._cached_sequence:
            self._last_cached = self._cached_sequence.pop(0)
        return self._last_cached

    def get_historical_data(self, symbol: str) -> HistoricalDataResult:
        del symbol
        self.historical_calls += 1
        return self._historical


class _SymbolAwareLoader:
    def __init__(self) -> None:
        self.cached_symbols: list[str] = []

    def get_cached_historical_data(self, symbol: str) -> HistoricalDataResult:
        safe_symbol = symbol.strip().upper()
        self.cached_symbols.append(safe_symbol)
        return HistoricalDataResult(
            rows=[
                _chart_row(f"{safe_symbol}-1", 100.0),
                _chart_row(f"{safe_symbol}-2", 101.0),
            ],
            source=f"adapter:{safe_symbol}",
        )

    def get_historical_data(self, symbol: str) -> HistoricalDataResult:
        raise AssertionError(f"Unexpected historical fallback for {symbol}")


class _FailingDataSource:
    def load_ohlcv(self, request: object) -> object:
        del request
        raise RuntimeError("fixture failure")

    def load_future_rows(self, request: object) -> object:
        del request
        raise RuntimeError("fixture failure")


def _row(
    symbol: str,
    row_date: str,
    close: float,
) -> dict[str, object]:
    return {
        "symbol": symbol,
        "timeframe": "1D",
        "date": row_date,
        "open": close - 1.0,
        "high": close + 1.0,
        "low": close - 2.0,
        "close": close,
        "volume": 1000,
        "source": "fixture",
    }


def _chart_row(row_date: str, close: float) -> dict[str, object]:
    return {
        "date": row_date,
        "open": close - 1.0,
        "high": close + 1.0,
        "low": close - 2.0,
        "close": close,
        "volume": 1000,
        "source": "fixture",
    }


if __name__ == "__main__":
    unittest.main()
