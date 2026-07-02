from __future__ import annotations

from collections import OrderedDict
from datetime import date
from time import perf_counter

from PySide6.QtCore import QObject, QThread, Qt, Signal
from PySide6.QtWidgets import QButtonGroup, QHBoxLayout, QLabel, QPushButton, QSplitter, QVBoxLayout, QWidget

from src.core.state_manager import StateManager
from src.data import (
    REQUIRED_ROW_COUNT,
    DataLoadError,
    DataManager,
    HistoricalDataResult,
    MarketDataRow,
    is_historical_data_fresh,
)
from src.gui.chart_data_adapter import ChartDataAdapter, LegacyChartDataLoader
from src.gui.chart_research_sidebar_view_model import (
    empty_chart_research_sidebar_view_model,
    load_chart_research_sidebar_view_model,
)
from src.gui.candlestick_chart import CandlestickChart
from src.indicators import build_indicator_snapshot


SAMPLE_FALLBACK_SOURCE = "Sample Fallback"
DEFAULT_TIMEFRAME = "1D"
TIMEFRAMES = ("1D", "1W", "1M")
DEFAULT_VISIBLE_ROWS = 120
VISIBLE_ROW_OPTIONS = (60, 120, 240, None)


class ChartWorkspace(QWidget):
    data_changed = Signal()
    loading_started = Signal(str)
    loading_progress = Signal(str)
    loading_finished = Signal(str, float)
    loading_failed = Signal(str, str)

    def __init__(
        self,
        data_manager: DataManager | None = None,
        chart_data_loader: LegacyChartDataLoader | None = None,
        state_manager: StateManager | None = None,
        dashboard_widget: QWidget | None = None,
        dev_sample_fallback_enabled: bool = False,
    ) -> None:
        super().__init__()
        self._data_manager = data_manager or DataManager()
        self._chart_data_loader = chart_data_loader or ChartDataAdapter(
            legacy_data_loader=self._data_manager
        )
        self._state_manager = state_manager or StateManager()
        self._dev_sample_fallback_enabled = dev_sample_fallback_enabled
        self._timeframe = DEFAULT_TIMEFRAME
        self._timeframe_buttons = QButtonGroup(self)
        self._visible_rows: int | None = DEFAULT_VISIBLE_ROWS
        self._visible_rows_buttons = QButtonGroup(self)
        self._title_label = QLabel("No symbol selected", self)
        self._market_header_label = QLabel("", self)
        self._detail_label = QLabel("", self)
        self._chart = CandlestickChart()
        self._dashboard_widget = dashboard_widget or QWidget(self)
        self._load_thread: QThread | None = None
        self._load_worker: _SymbolLoadWorker | None = None

        self._title_label.setAlignment(Qt.AlignCenter)
        self._market_header_label.setAlignment(Qt.AlignCenter)
        self._detail_label.setAlignment(Qt.AlignCenter)

        chart_panel = QWidget(self)
        chart_layout = QVBoxLayout()
        chart_layout.setContentsMargins(0, 0, 0, 0)
        chart_layout.addLayout(self._create_timeframe_controls())
        chart_layout.addLayout(self._create_visible_rows_controls())
        chart_layout.addWidget(self._title_label)
        chart_layout.addWidget(self._market_header_label)
        chart_layout.addWidget(self._detail_label)
        chart_layout.addWidget(self._chart, 1)
        chart_panel.setLayout(chart_layout)

        main_splitter = QSplitter(Qt.Horizontal, self)
        main_splitter.addWidget(chart_panel)
        main_splitter.addWidget(self._dashboard_widget)
        main_splitter.setStretchFactor(0, 6)
        main_splitter.setStretchFactor(1, 1)
        main_splitter.setChildrenCollapsible(False)

        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(main_splitter)
        self.setLayout(layout)

    def _create_timeframe_controls(self) -> QHBoxLayout:
        layout = QHBoxLayout()
        layout.addStretch()
        for timeframe in TIMEFRAMES:
            button = QPushButton(timeframe, self)
            button.setCheckable(True)
            button.setFixedWidth(42)
            button.clicked.connect(lambda checked, value=timeframe: self._set_timeframe(value))
            self._timeframe_buttons.addButton(button)
            layout.addWidget(button)
            if timeframe == DEFAULT_TIMEFRAME:
                button.setChecked(True)
        layout.addStretch()
        return layout

    def _set_timeframe(self, timeframe: str) -> None:
        self._timeframe = timeframe
        self.refresh_from_state()

    def _create_visible_rows_controls(self) -> QHBoxLayout:
        layout = QHBoxLayout()
        layout.addStretch()
        layout.addWidget(QLabel("Rows", self))
        for option in VISIBLE_ROW_OPTIONS:
            text = str(option) if option is not None else "All"
            button = QPushButton(text, self)
            button.setCheckable(True)
            button.setFixedWidth(48)
            button.clicked.connect(lambda checked, value=option: self._set_visible_rows(value))
            self._visible_rows_buttons.addButton(button)
            layout.addWidget(button)
            if option == DEFAULT_VISIBLE_ROWS:
                button.setChecked(True)
        layout.addStretch()
        return layout

    def _set_visible_rows(self, visible_rows: int | None) -> None:
        self._visible_rows = visible_rows
        self.refresh_from_state()

    def is_loading(self) -> bool:
        return self._load_thread is not None

    def refresh_from_state(self) -> None:
        symbol = self._state_manager.current_symbol
        if not symbol:
            self._title_label.setText("No symbol selected")
            self._market_header_label.setText("")
            self._detail_label.setText("")
            self._chart.clear()
            self._state_manager.clear_market_data_state()
            self.data_changed.emit()
            return

        if self.is_loading():
            self.loading_progress.emit(f"Loading {symbol} already in progress...")
            return

        self._title_label.setText("")
        self._market_header_label.setText("")
        self._detail_label.setText("")
        self._chart.set_projection_overlay(None)
        self._start_symbol_load(symbol)

    def _start_symbol_load(self, symbol: str) -> None:
        sample_rows = self._sample_ohlc_data() if self._dev_sample_fallback_enabled else None
        thread = QThread(self)
        worker = _SymbolLoadWorker(
            symbol=symbol,
            chart_data_loader=self._chart_data_loader,
            dev_sample_fallback_enabled=self._dev_sample_fallback_enabled,
            sample_rows=sample_rows,
        )
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        worker.progress.connect(self._handle_symbol_load_progress)
        worker.chart_ready.connect(self._handle_symbol_chart_ready)
        worker.no_data.connect(self._handle_symbol_no_data)
        worker.sidebar_ready.connect(self._handle_symbol_sidebar_ready)
        worker.finished.connect(self._handle_symbol_load_finished)
        worker.failed.connect(self._handle_symbol_load_failed)
        worker.finished.connect(thread.quit)
        worker.failed.connect(thread.quit)
        worker.finished.connect(worker.deleteLater)
        worker.failed.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)
        thread.finished.connect(self._clear_symbol_load_worker)
        self._load_thread = thread
        self._load_worker = worker
        self.loading_started.emit(symbol)
        self.loading_progress.emit(f"Loading {symbol}...")
        thread.start()

    def _handle_symbol_load_progress(self, message: str) -> None:
        self.loading_progress.emit(message)

    def _handle_symbol_chart_ready(self, payload: object) -> None:
        if not isinstance(payload, dict):
            return
        historical_data = payload.get("historical_data")
        if not isinstance(historical_data, HistoricalDataResult):
            return
        self._show_historical_data(
            historical_data,
            float(payload.get("last_load_time", 0.0)),
            refresh_sidebar=False,
        )

    def _handle_symbol_no_data(self, payload: object) -> None:
        if not isinstance(payload, dict):
            return
        self._show_no_data_status(
            symbol=str(payload.get("symbol", "")),
            source=str(payload.get("source", "SQLite Cache")),
            load_time=float(payload.get("last_load_time", 0.0)),
            message=str(payload.get("message", "Data status: No OHLC data returned")),
            refresh_sidebar=False,
        )

    def _handle_symbol_sidebar_ready(self, view_model: object) -> None:
        if isinstance(view_model, dict):
            self._chart.set_projection_overlay(view_model.get("chart_action_overlay"))

    def _handle_symbol_load_finished(self, symbol: str, elapsed_seconds: float) -> None:
        self.loading_finished.emit(symbol, elapsed_seconds)

    def _handle_symbol_load_failed(self, symbol: str, message: str) -> None:
        self._handle_load_error(message, refresh_sidebar=False)
        self._chart.set_projection_overlay(None)
        self.loading_failed.emit(symbol, message)

    def _clear_symbol_load_worker(self) -> None:
        self._load_thread = None
        self._load_worker = None

    def _show_no_data_status(
        self,
        symbol: str,
        source: str,
        load_time: float,
        message: str,
        *,
        refresh_sidebar: bool = True,
    ) -> None:
        self._state_manager.set_market_data_state(
            rows=0,
            source=source,
            last_load_time=load_time,
        )
        self._state_manager.set_indicator_snapshot(None)
        self._chart.clear()
        self._chart.set_projection_overlay(None)
        self._market_header_label.setText("")
        self._detail_label.setText(
            self._get_display_status(
                symbol=symbol,
                source=source,
                cached_rows=0,
                timeframe_rows=0,
                rendered_rows=[],
                extra_status=message,
            )
        )
        if refresh_sidebar:
            view_model = load_chart_research_sidebar_view_model(symbol=symbol)
            self._chart.set_projection_overlay(view_model.get("chart_action_overlay"))
        self.data_changed.emit()

    def _show_historical_data(
        self,
        historical_data: HistoricalDataResult,
        last_load_time: float,
        *,
        refresh_sidebar: bool = True,
    ) -> None:
        timeframe_rows = self._rows_for_timeframe(historical_data.rows)
        visible_rows = self._rows_for_visible_count(timeframe_rows)
        self._state_manager.set_market_data_state(
            rows=len(visible_rows),
            source=historical_data.source,
            last_load_time=last_load_time,
        )
        self._state_manager.set_indicator_snapshot(
            build_indicator_snapshot(
                symbol=self._state_manager.current_symbol or "",
                timeframe=self._timeframe,
                rows=timeframe_rows,
            )
        )
        self._chart.set_ohlc_data(visible_rows)
        self._market_header_label.setText(
            self._get_market_header(
                symbol=self._state_manager.current_symbol or "",
                rows=visible_rows,
            )
        )
        self.data_changed.emit()
        if refresh_sidebar:
            view_model = load_chart_research_sidebar_view_model(symbol=self._state_manager.current_symbol)
            self._chart.set_projection_overlay(view_model.get("chart_action_overlay"))
        self._detail_label.setText(
            self._get_display_status(
                symbol=self._state_manager.current_symbol or "",
                source=historical_data.source,
                cached_rows=len(historical_data.rows),
                timeframe_rows=len(timeframe_rows),
                visible_row_label=self._visible_row_label(),
                rendered_rows=self._chart.rendered_rows(),
            )
        )

    def _handle_load_error(self, message: str, *, refresh_sidebar: bool = True) -> None:
        if self._dev_sample_fallback_enabled:
            sample_data = HistoricalDataResult(
                rows=self._sample_ohlc_data(), source=SAMPLE_FALLBACK_SOURCE
            )
            self._show_historical_data(sample_data, 0.0, refresh_sidebar=refresh_sidebar)
            self._detail_label.setText(
                self._get_display_status(
                    symbol=self._state_manager.current_symbol or "",
                    source=SAMPLE_FALLBACK_SOURCE,
                    cached_rows=len(sample_data.rows),
                    timeframe_rows=len(self._rows_for_timeframe(sample_data.rows)),
                    visible_row_label=self._visible_row_label(),
                    rendered_rows=self._chart.rendered_rows(),
                    extra_status=f"Data status: {message}",
                )
            )
            return

        self._state_manager.set_error_status(message)
        self._chart.clear()
        self._chart.set_projection_overlay(None)
        self._market_header_label.setText("")
        self._detail_label.setText(
            self._get_display_status(
                symbol=self._state_manager.current_symbol or "",
                source="SQLite Cache",
                cached_rows=0,
                timeframe_rows=0,
                rendered_rows=[],
                extra_status=f"Data status: {message}",
            )
        )
        self.data_changed.emit()
        if refresh_sidebar:
            view_model = load_chart_research_sidebar_view_model(symbol=self._state_manager.current_symbol)
            self._chart.set_projection_overlay(view_model.get("chart_action_overlay"))

    def _get_market_header(self, symbol: str, rows: list[MarketDataRow]) -> str:
        if not rows:
            return ""

        latest_row = rows[-1]
        previous_row = rows[-2] if len(rows) >= 2 else None
        latest_close = float(latest_row["close"])
        previous_close = float(previous_row["close"]) if previous_row else latest_close
        change = latest_close - previous_close
        change_percent = (change / previous_close * 100) if previous_close else 0.0
        return (
            f"{symbol}  |  "
            f"Close {latest_close:.2f}  |  "
            f"Change {change:+.2f} ({change_percent:+.2f}%)  |  "
            f"O {float(latest_row['open']):.2f}  |  "
            f"H {float(latest_row['high']):.2f}  |  "
            f"L {float(latest_row['low']):.2f}  |  "
            f"Vol {self._format_volume(int(latest_row['volume']))}  |  "
            f"{self._row_date(latest_row)}"
        )

    def _get_display_status(
        self,
        symbol: str,
        source: str,
        cached_rows: int,
        timeframe_rows: int,
        rendered_rows: list[MarketDataRow],
        visible_row_label: str = "",
        extra_status: str = "",
    ) -> str:
        first_rendered_date = self._row_date(rendered_rows[0]) if rendered_rows else ""
        last_rendered_date = self._row_date(rendered_rows[-1]) if rendered_rows else ""
        lines = [
            (
                f"Source {source}  |  "
                f"TF {self._timeframe}  |  "
                f"Cached {cached_rows}  |  "
                f"TF Rows {timeframe_rows}  |  "
                f"Visible {visible_row_label or self._visible_row_label()}  |  "
                f"Rendered {len(rendered_rows)}  |  "
                f"{first_rendered_date} -> {last_rendered_date}"
            )
        ]
        if extra_status:
            lines.append(extra_status)
        return "\n".join(lines)

    def _row_date(self, row: MarketDataRow) -> str:
        return str(row.get("date", ""))

    def _rows_for_timeframe(self, rows: list[MarketDataRow]) -> list[MarketDataRow]:
        if self._timeframe == "1D":
            return rows
        return self._resample_rows(rows, self._timeframe)

    def _rows_for_visible_count(
        self, rows: list[MarketDataRow]
    ) -> list[MarketDataRow]:
        if self._visible_rows is None:
            return rows
        return rows[-self._visible_rows :]

    def _visible_row_label(self) -> str:
        return str(self._visible_rows) if self._visible_rows is not None else "All"

    def _resample_rows(
        self, rows: list[MarketDataRow], timeframe: str
    ) -> list[MarketDataRow]:
        groups: OrderedDict[str, list[MarketDataRow]] = OrderedDict()
        for row in rows:
            group_key = self._timeframe_group_key(str(row["date"]), timeframe)
            groups.setdefault(group_key, []).append(row)

        return [
            self._aggregate_rows(group_key=group_key, rows=group_rows)
            for group_key, group_rows in groups.items()
        ]

    def _timeframe_group_key(self, row_date: str, timeframe: str) -> str:
        try:
            parsed_date = date.fromisoformat(row_date)
        except ValueError:
            return row_date

        if timeframe == "1W":
            year, week, _ = parsed_date.isocalendar()
            return f"{year}-W{week:02d}"
        if timeframe == "1M":
            return f"{parsed_date.year}-{parsed_date.month:02d}"
        return row_date

    def _aggregate_rows(
        self, group_key: str, rows: list[MarketDataRow]
    ) -> MarketDataRow:
        first_row = rows[0]
        last_row = rows[-1]
        return {
            "date": group_key,
            "open": float(first_row["open"]),
            "high": max(float(row["high"]) for row in rows),
            "low": min(float(row["low"]) for row in rows),
            "close": float(last_row["close"]),
            "volume": sum(int(row["volume"]) for row in rows),
            "source": first_row.get("source", ""),
        }

    def _format_volume(self, volume: int) -> str:
        if volume >= 1_000_000:
            return f"{volume / 1_000_000:.2f}M"
        if volume >= 1_000:
            return f"{volume / 1_000:.2f}K"
        return str(volume)

    def _sample_ohlc_data(self) -> list[MarketDataRow]:
        closes = [
            102.4,
            104.1,
            103.2,
            105.8,
            108.0,
            107.2,
            109.5,
            111.1,
            110.4,
            112.6,
            114.2,
            113.7,
            115.4,
            117.1,
            116.5,
            118.8,
            120.2,
            119.4,
            121.6,
            123.0,
        ]
        rows: list[MarketDataRow] = []
        previous_close = 101.8
        for index, close in enumerate(closes, start=1):
            open_price = previous_close + (0.6 if index % 2 == 0 else -0.4)
            high = max(open_price, close) + 1.2
            low = min(open_price, close) - 1.0
            rows.append(
                {
                    "date": f"sample-{index:02d}",
                    "open": round(open_price, 2),
                    "high": round(high, 2),
                    "low": round(low, 2),
                    "close": round(close, 2),
                    "volume": 0,
                    "source": SAMPLE_FALLBACK_SOURCE,
                }
            )
            previous_close = close

        return rows


class _SymbolLoadWorker(QObject):
    progress = Signal(str)
    chart_ready = Signal(object)
    no_data = Signal(object)
    sidebar_ready = Signal(object)
    finished = Signal(str, float)
    failed = Signal(str, str)

    def __init__(
        self,
        *,
        symbol: str,
        chart_data_loader: LegacyChartDataLoader,
        dev_sample_fallback_enabled: bool,
        sample_rows: list[MarketDataRow] | None = None,
    ) -> None:
        super().__init__()
        self._symbol = symbol
        self._chart_data_loader = chart_data_loader
        self._dev_sample_fallback_enabled = dev_sample_fallback_enabled
        self._sample_rows = sample_rows or []

    def run(self) -> None:
        start_time = perf_counter()
        try:
            self.progress.emit(f"Loading {self._symbol}...")
            self.progress.emit("Reading OHLCV...")
            historical_data = self._chart_data_loader.get_cached_historical_data(
                self._symbol
            )
            if (
                len(historical_data.rows) < REQUIRED_ROW_COUNT
                or not is_historical_data_fresh(historical_data)
            ):
                historical_data = self._load_refreshed_or_fallback(historical_data)
            if historical_data.rows:
                self.progress.emit("Building Indicators...")
                self.chart_ready.emit(
                    {
                        "historical_data": historical_data,
                        "last_load_time": perf_counter() - start_time,
                    }
                )
            else:
                self.no_data.emit(
                    {
                        "symbol": self._symbol,
                        "source": historical_data.source,
                        "last_load_time": perf_counter() - start_time,
                        "message": "Data status: No OHLC data returned",
                    }
                )

            self._emit_sidebar_stage("Loading Snapshot...")
            self._emit_sidebar_stage("Loading POOM Combo...")
            self._emit_sidebar_stage("Loading Statistics...")
            self._emit_sidebar_stage("Loading Historical Edge...")
            self.progress.emit("Loading Research Summary...")
            self.sidebar_ready.emit(
                load_chart_research_sidebar_view_model(symbol=self._symbol)
            )
        except Exception as error:
            self.failed.emit(self._symbol, str(error))
            return

        self.finished.emit(self._symbol, perf_counter() - start_time)

    def _load_refreshed_or_fallback(
        self,
        historical_data: HistoricalDataResult,
    ) -> HistoricalDataResult:
        if self._dev_sample_fallback_enabled:
            return HistoricalDataResult(
                rows=self._sample_rows,
                source=SAMPLE_FALLBACK_SOURCE,
            )

        self.progress.emit("Refreshing OHLC cache...")
        try:
            fetched_data = self._chart_data_loader.get_historical_data(self._symbol)
        except DataLoadError:
            if historical_data.rows:
                return historical_data
            raise

        cached_data = self._chart_data_loader.get_cached_historical_data(self._symbol)
        if cached_data.rows:
            return cached_data
        return fetched_data

    def _emit_sidebar_stage(self, message: str) -> None:
        self.progress.emit(message)
        self.sidebar_ready.emit(
            empty_chart_research_sidebar_view_model(message, symbol=self._symbol)
        )
