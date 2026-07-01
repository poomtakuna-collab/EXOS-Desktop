from __future__ import annotations

from collections import OrderedDict
from datetime import date
from time import perf_counter

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QButtonGroup, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

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
from src.gui.candlestick_chart import CandlestickChart
from src.indicators import build_indicator_snapshot


SAMPLE_FALLBACK_SOURCE = "Sample Fallback"
DEFAULT_TIMEFRAME = "1D"
TIMEFRAMES = ("1D", "1W", "1M")
DEFAULT_VISIBLE_ROWS = 120
VISIBLE_ROW_OPTIONS = (60, 120, 240, None)


class ChartWorkspace(QWidget):
    data_changed = Signal()

    def __init__(
        self,
        data_manager: DataManager | None = None,
        chart_data_loader: LegacyChartDataLoader | None = None,
        state_manager: StateManager | None = None,
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

        self._title_label.setAlignment(Qt.AlignCenter)
        self._market_header_label.setAlignment(Qt.AlignCenter)
        self._detail_label.setAlignment(Qt.AlignCenter)

        layout = QVBoxLayout()
        layout.addLayout(self._create_timeframe_controls())
        layout.addLayout(self._create_visible_rows_controls())
        layout.addWidget(self._title_label)
        layout.addWidget(self._market_header_label)
        layout.addWidget(self._detail_label)
        layout.addWidget(self._chart, 1)
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

        self._title_label.setText("")

        start_time = perf_counter()
        try:
            historical_data = self._chart_data_loader.get_cached_historical_data(symbol)
        except DataLoadError as error:
            self._handle_load_error(str(error))
            return

        last_load_time = perf_counter() - start_time
        if (
            len(historical_data.rows) >= REQUIRED_ROW_COUNT
            and is_historical_data_fresh(historical_data)
        ):
            self._show_historical_data(historical_data, last_load_time)
            return

        if self._dev_sample_fallback_enabled:
            sample_data = HistoricalDataResult(
                rows=self._sample_ohlc_data(), source=SAMPLE_FALLBACK_SOURCE
            )
            self._show_historical_data(sample_data, last_load_time)
            return

        self._detail_label.setText(
            self._get_display_status(
                symbol=symbol,
                source=historical_data.source,
                cached_rows=len(historical_data.rows),
                timeframe_rows=len(self._rows_for_timeframe(historical_data.rows)),
                rendered_rows=[],
                extra_status="Data status: Refreshing OHLC cache...",
            )
        )
        self._load_and_show_cached_data(symbol, last_load_time)

    def _load_and_show_cached_data(
        self, symbol: str, cache_check_time: float
    ) -> None:
        start_time = perf_counter()
        try:
            fetched_data = self._chart_data_loader.get_historical_data(symbol)
        except DataLoadError as error:
            self._show_no_data_status(
                symbol=symbol,
                source="SQLite Cache",
                load_time=cache_check_time,
                message=f"Data status: {error}",
            )
            return

        cached_data = self._chart_data_loader.get_cached_historical_data(symbol)
        load_time = cache_check_time + (perf_counter() - start_time)
        if cached_data.rows:
            self._show_historical_data(cached_data, load_time)
            return

        source = fetched_data.source or cached_data.source
        self._show_no_data_status(
            symbol=symbol,
            source=source,
            load_time=load_time,
            message="Data status: No OHLC data returned",
        )

    def _show_no_data_status(
        self, symbol: str, source: str, load_time: float, message: str
    ) -> None:
        self._state_manager.set_market_data_state(
            rows=0,
            source=source,
            last_load_time=load_time,
        )
        self._state_manager.set_indicator_snapshot(None)
        self._chart.clear()
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
        self.data_changed.emit()

    def _show_historical_data(
        self, historical_data: HistoricalDataResult, last_load_time: float
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

    def _handle_load_error(self, message: str) -> None:
        if self._dev_sample_fallback_enabled:
            sample_data = HistoricalDataResult(
                rows=self._sample_ohlc_data(), source=SAMPLE_FALLBACK_SOURCE
            )
            self._show_historical_data(sample_data, 0.0)
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
