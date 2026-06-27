from __future__ import annotations

from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from src.core.state_manager import StateManager


class DeveloperPanel(QWidget):
    def __init__(self, state_manager: StateManager) -> None:
        super().__init__()
        self._state_manager = state_manager
        self._content_label = QLabel(self)
        self._content_label.setTextInteractionFlags(self._content_label.textInteractionFlags())

        layout = QVBoxLayout()
        layout.addWidget(self._content_label)
        layout.addStretch()
        self.setLayout(layout)

        self.refresh()

    def refresh(self) -> None:
        current_symbol = self._state_manager.current_symbol or ""
        rows = self._state_manager.market_data_rows
        source = self._state_manager.market_data_source
        last_load_time = self._format_load_time(self._state_manager.last_load_time)
        status = self._state_manager.status

        self._content_label.setText(
            "Developer Panel\n\n"
            "Application\n"
            "--------------------------------\n"
            f"{self._format_row('Current Symbol', current_symbol)}\n\n"
            "Database\n"
            "--------------------------------\n"
            f"{self._format_row('Rows', str(rows))}\n"
            f"{self._format_row('Source', source)}\n"
            f"{self._format_row('Last Update', '')}\n"
            f"{self._format_row('Cache', '')}\n\n"
            "Performance\n"
            "--------------------------------\n"
            f"{self._format_row('Load Time', last_load_time)}\n\n"
            "Status\n"
            "--------------------------------\n"
            f"{status}"
        )

    def _format_row(self, label: str, value: str) -> str:
        return f"{label:<14} : {value}"

    def _format_load_time(self, last_load_time: float | None) -> str:
        if last_load_time is None:
            return ""

        return f"{last_load_time:.3f} sec"
