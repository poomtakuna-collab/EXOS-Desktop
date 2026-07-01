from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import (
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from src.core.state_manager import StateManager
from src.gui.signal_history_view_model import (
    DEFAULT_SIGNAL_HISTORY_DATABASE_PATH,
    load_desktop_signal_history_view_model,
)


class SignalHistoryPanel(QWidget):
    def __init__(
        self,
        state_manager: StateManager,
        database_path: Path | None = None,
    ) -> None:
        super().__init__()
        self._state_manager = state_manager
        self._database_path = database_path or DEFAULT_SIGNAL_HISTORY_DATABASE_PATH
        self._symbol_label = QLabel(self)
        self._status_label = QLabel(self)
        self._table = QTableWidget(self)

        self._create_layout()
        self.refresh()

    def refresh(self) -> None:
        view_model = load_desktop_signal_history_view_model(
            self._database_path,
            selected_symbol=self._state_manager.current_symbol,
        )
        columns = view_model["columns"]
        rows = view_model["rows"]

        self._symbol_label.setText(str(view_model["selected_symbol"]))
        self._status_label.setText(str(view_model["status"]))

        if not isinstance(columns, tuple) or not isinstance(rows, tuple):
            return

        self._table.setColumnCount(len(columns))
        self._table.setHorizontalHeaderLabels([str(column) for column in columns])
        self._table.setRowCount(len(rows))
        for row_index, row in enumerate(rows):
            if not isinstance(row, dict):
                continue
            values = (
                row.get("signal_date", ""),
                row.get("signal_type", ""),
                row.get("confidence", ""),
                row.get("snapshot", ""),
                row.get("linked_outcome_count", ""),
                row.get("latest_outcome", ""),
            )
            for column_index, value in enumerate(values):
                self._table.setItem(
                    row_index,
                    column_index,
                    QTableWidgetItem(str(value)),
                )
        self._table.resizeColumnsToContents()

    def _create_layout(self) -> None:
        refresh_button = QPushButton("Refresh", self)
        refresh_button.clicked.connect(self.refresh)

        layout = QVBoxLayout()
        layout.addWidget(refresh_button)
        layout.addWidget(self._symbol_label)
        layout.addWidget(self._table)
        layout.addWidget(self._status_label)
        self.setLayout(layout)
