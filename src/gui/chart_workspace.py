from __future__ import annotations

from time import perf_counter

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from src.core.state_manager import StateManager
from src.data import DataLoadError, DataManager, HistoricalDataResult


class ChartWorkspace(QWidget):
    def __init__(
        self,
        data_manager: DataManager | None = None,
        state_manager: StateManager | None = None,
    ) -> None:
        super().__init__()
        self._data_manager = data_manager or DataManager()
        self._state_manager = state_manager or StateManager()
        self._title_label = QLabel("No symbol selected", self)
        self._detail_label = QLabel("", self)

        self._title_label.setAlignment(Qt.AlignCenter)
        self._detail_label.setAlignment(Qt.AlignCenter)

        layout = QVBoxLayout()
        layout.addStretch()
        layout.addWidget(self._title_label)
        layout.addWidget(self._detail_label)
        layout.addStretch()
        self.setLayout(layout)

    def refresh_from_state(self) -> None:
        symbol = self._state_manager.current_symbol
        if not symbol:
            self._title_label.setText("No symbol selected")
            self._detail_label.setText("")
            self._state_manager.clear_market_data_state()
            return

        self._title_label.setText(f"Current Symbol: {symbol}")

        start_time = perf_counter()
        try:
            historical_data = self._data_manager.get_historical_data(symbol)
        except DataLoadError as error:
            self._state_manager.set_error_status(str(error))
            self._detail_label.setText(f"Data status: {error}")
            return

        last_load_time = perf_counter() - start_time
        self._state_manager.set_market_data_state(
            rows=len(historical_data.rows),
            source=historical_data.source,
            last_load_time=last_load_time,
        )
        self._detail_label.setText(self._get_data_status(historical_data))

    def _get_data_status(self, historical_data: HistoricalDataResult) -> str:
        if not historical_data.rows:
            return "Data status: No market data loaded yet"

        return f"Rows: {len(historical_data.rows)}\nSource: {historical_data.source}"
