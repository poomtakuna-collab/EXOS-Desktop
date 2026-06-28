from __future__ import annotations

from time import perf_counter

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from src.core.state_manager import StateManager
from src.data import DataLoadError, DataManager, HistoricalDataResult, MarketDataRow
from src.gui.candlestick_chart import CandlestickChart


SAMPLE_FALLBACK_SOURCE = "Sample Fallback"


class ChartWorkspace(QWidget):
    def __init__(
        self,
        data_manager: DataManager | None = None,
        state_manager: StateManager | None = None,
        dev_sample_fallback_enabled: bool = False,
    ) -> None:
        super().__init__()
        self._data_manager = data_manager or DataManager()
        self._state_manager = state_manager or StateManager()
        self._dev_sample_fallback_enabled = dev_sample_fallback_enabled
        self._title_label = QLabel("No symbol selected", self)
        self._market_header_label = QLabel("", self)
        self._detail_label = QLabel("", self)
        self._chart = CandlestickChart()

        self._title_label.setAlignment(Qt.AlignCenter)
        self._market_header_label.setAlignment(Qt.AlignCenter)
        self._detail_label.setAlignment(Qt.AlignCenter)

        layout = QVBoxLayout()
        layout.addWidget(self._title_label)
        layout.addWidget(self._market_header_label)
        layout.addWidget(self._detail_label)
        layout.addWidget(self._chart, 1)
        self.setLayout(layout)

    def refresh_from_state(self) -> None:
        symbol = self._state_manager.current_symbol
        if not symbol:
            self._title_label.setText("No symbol selected")
            self._market_header_label.setText("")
            self._detail_label.setText("")
            self._chart.clear()
            self._state_manager.clear_market_data_state()
            return

        self._title_label.setText("")

        start_time = perf_counter()
        try:
            historical_data = self._data_manager.get_cached_historical_data(symbol)
        except DataLoadError as error:
            self._handle_load_error(str(error))
            return

        last_load_time = perf_counter() - start_time
        if historical_data.rows:
            self._show_historical_data(historical_data, last_load_time)
            return

        if self._dev_sample_fallback_enabled:
            sample_data = HistoricalDataResult(
                rows=self._sample_ohlc_data(), source=SAMPLE_FALLBACK_SOURCE
            )
            self._show_historical_data(sample_data, last_load_time)
            return

        self._state_manager.set_market_data_state(
            rows=0,
            source=historical_data.source,
            last_load_time=last_load_time,
        )
        self._chart.clear()
        self._market_header_label.setText("")
        self._detail_label.setText(
            self._get_display_status(
                symbol=symbol,
                source=historical_data.source,
                cached_rows=0,
                rendered_rows=[],
                extra_status="Data status: No cached OHLC data",
            )
        )

    def _show_historical_data(
        self, historical_data: HistoricalDataResult, last_load_time: float
    ) -> None:
        self._state_manager.set_market_data_state(
            rows=len(historical_data.rows),
            source=historical_data.source,
            last_load_time=last_load_time,
        )
        self._chart.set_ohlc_data(historical_data.rows)
        self._market_header_label.setText(
            self._get_market_header(
                symbol=self._state_manager.current_symbol or "",
                rows=historical_data.rows,
            )
        )
        self._detail_label.setText(
            self._get_display_status(
                symbol=self._state_manager.current_symbol or "",
                source=historical_data.source,
                cached_rows=len(historical_data.rows),
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
                rendered_rows=[],
                extra_status=f"Data status: {message}",
            )
        )

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
        rendered_rows: list[MarketDataRow],
        extra_status: str = "",
    ) -> str:
        first_rendered_date = self._row_date(rendered_rows[0]) if rendered_rows else ""
        last_rendered_date = self._row_date(rendered_rows[-1]) if rendered_rows else ""
        lines = [
            (
                f"Source {source}  |  "
                f"Cached {cached_rows}  |  "
                f"Rendered {len(rendered_rows)}  |  "
                f"{first_rendered_date} -> {last_rendered_date}"
            )
        ]
        if extra_status:
            lines.append(extra_status)
        return "\n".join(lines)

    def _row_date(self, row: MarketDataRow) -> str:
        return str(row.get("date", ""))

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
