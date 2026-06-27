from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from src.data import DataManager


class ChartWorkspace(QWidget):
    def __init__(self, data_manager: DataManager | None = None) -> None:
        super().__init__()
        self._data_manager = data_manager or DataManager()
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

    def set_current_symbol(self, symbol: str | None) -> None:
        if symbol:
            historical_data = self._data_manager.get_historical_data(symbol)
            self._title_label.setText(f"Current Symbol: {symbol}")
            self._detail_label.setText(self._get_data_status(historical_data))
            return

        self._title_label.setText("No symbol selected")
        self._detail_label.setText("")

    def _get_data_status(self, historical_data: list[dict[str, object]]) -> str:
        if historical_data:
            return "Data status: Market data loaded"

        return "Data status: No market data loaded yet"
