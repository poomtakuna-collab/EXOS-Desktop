from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import (
    QDialog,
    QGridLayout,
    QGroupBox,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from src.core.state_manager import StateManager
from src.gui.signal_history_view_model import (
    DEFAULT_SIGNAL_HISTORY_DATABASE_PATH,
    load_desktop_snapshot_detail_view_model,
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
        self._rows: tuple[dict[str, object], ...] = ()
        self._detail_dialog: SnapshotDetailDialog | None = None

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
        self._rows = tuple(row for row in rows if isinstance(row, dict))

        self._table.setColumnCount(len(columns))
        self._table.setHorizontalHeaderLabels([str(column) for column in columns])
        self._table.setRowCount(len(self._rows))
        for row_index, row in enumerate(self._rows):
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

    def _open_snapshot_detail(self, row: int, column: int) -> None:
        del column
        if row < 0 or row >= len(self._rows):
            return
        signal_id = str(self._rows[row].get("signal_id", "")).strip()
        if not signal_id:
            return
        selected_row = self._rows[row]
        view_model = load_desktop_snapshot_detail_view_model(
            self._database_path,
            signal_id=signal_id,
            snapshot_record_id=str(selected_row.get("snapshot_record_id", "")).strip(),
            symbol=str(selected_row.get("symbol", "")).strip(),
            market_date=str(selected_row.get("market_date", "")).strip(),
            timeframe=str(selected_row.get("timeframe", "")).strip(),
        )
        self._detail_dialog = SnapshotDetailDialog(view_model, self)
        self._detail_dialog.show()

    def _create_layout(self) -> None:
        refresh_button = QPushButton("Refresh", self)
        refresh_button.clicked.connect(self.refresh)
        self._table.cellDoubleClicked.connect(self._open_snapshot_detail)

        layout = QVBoxLayout()
        layout.addWidget(refresh_button)
        layout.addWidget(self._symbol_label)
        layout.addWidget(self._table)
        layout.addWidget(self._status_label)
        self.setLayout(layout)


class SnapshotDetailDialog(QDialog):
    def __init__(self, view_model: dict[str, object], parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle(str(view_model.get("title", "Snapshot Detail")))
        self.setMinimumWidth(760)
        self.setMinimumHeight(560)

        layout = QVBoxLayout()
        layout.addWidget(_header_group(view_model.get("header"), self))

        tabs = QTabWidget(self)
        detail_tabs = view_model.get("tabs")
        groups = detail_tabs if isinstance(detail_tabs, tuple) else view_model.get("groups")
        if isinstance(groups, tuple):
            for group in groups:
                if isinstance(group, dict):
                    tabs.addTab(_group_widget(group, self), str(group.get("title", "")))

        raw_json = QTextEdit(self)
        raw_json.setReadOnly(True)
        raw_json.setPlainText(str(view_model.get("raw_json", "{}")))
        tabs.addTab(raw_json, "Raw JSON")
        layout.addWidget(tabs)

        status = QLabel(str(view_model.get("status", "")), self)
        layout.addWidget(status)
        self.setLayout(layout)


def _header_group(value: object, parent: QWidget) -> QGroupBox:
    group = QGroupBox("Header", parent)
    layout = QGridLayout()
    if isinstance(value, tuple):
        for row, item in enumerate(value):
            if not isinstance(item, dict):
                continue
            layout.addWidget(QLabel(str(item.get("label", "")), group), row, 0)
            layout.addWidget(QLabel(str(item.get("value", "")), group), row, 1)
    group.setLayout(layout)
    return group


def _group_widget(group_model: dict[str, object], parent: QWidget) -> QGroupBox:
    group = QGroupBox(str(group_model.get("title", "")), parent)
    layout = QGridLayout()
    items = group_model.get("items")
    if isinstance(items, tuple):
        for row, item in enumerate(items):
            if not isinstance(item, dict):
                continue
            layout.addWidget(QLabel(str(item.get("label", "")), group), row, 0)
            value = QLabel(str(item.get("value", "")), group)
            value.setWordWrap(True)
            layout.addWidget(value, row, 1)
    group.setLayout(layout)
    return group
