from __future__ import annotations

from typing import Any

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QDockWidget,
    QHBoxLayout,
    QInputDialog,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QPushButton,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from src.core.dashboard_manager import DashboardManager
from src.core.state_manager import StateManager
from src.data import DataManager
from src.gui.chart_workspace import ChartWorkspace


class MainWindow(QMainWindow):
    def __init__(self, dashboard_symbols: list[dict[str, Any]] | None = None) -> None:
        super().__init__()
        self._dashboard_manager = DashboardManager()
        self._state_manager = StateManager()
        self._data_manager = DataManager()
        self._dashboard_symbols = dashboard_symbols or self._dashboard_manager.load_symbols()
        self._dashboard_list = QListWidget(self)
        self._chart_workspace = ChartWorkspace(self._data_manager)

        self.setWindowTitle("EXOS Desktop")
        self.resize(1200, 800)

        self._create_menu_bar()
        self._create_toolbar()
        self._create_central_workspace()
        self._create_dashboard_dock()
        self._update_current_symbol_views()

    def _create_menu_bar(self) -> None:
        file_menu = self.menuBar().addMenu("File")

        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        self.menuBar().addMenu("View")

    def _create_toolbar(self) -> None:
        toolbar = QToolBar("Main Toolbar", self)
        toolbar.setMovable(False)
        self.addToolBar(Qt.TopToolBarArea, toolbar)

    def _create_central_workspace(self) -> None:
        self.setCentralWidget(self._chart_workspace)

    def _create_dashboard_dock(self) -> None:
        dashboard_dock = QDockWidget("Dashboard", self)
        dashboard_dock.setAllowedAreas(Qt.RightDockWidgetArea)

        add_button = QPushButton("+", dashboard_dock)
        add_button.setFixedWidth(32)
        add_button.clicked.connect(self._add_dashboard_symbol)

        remove_button = QPushButton("-", dashboard_dock)
        remove_button.setFixedWidth(32)
        remove_button.clicked.connect(self._remove_selected_dashboard_symbol)

        button_layout = QHBoxLayout()
        button_layout.addWidget(add_button)
        button_layout.addWidget(remove_button)
        button_layout.addStretch()

        dashboard_layout = QVBoxLayout()
        dashboard_layout.addLayout(button_layout)
        dashboard_layout.addWidget(self._dashboard_list)

        dashboard_widget = QWidget(dashboard_dock)
        dashboard_widget.setLayout(dashboard_layout)

        dashboard_dock.setWidget(dashboard_widget)
        self.addDockWidget(Qt.RightDockWidgetArea, dashboard_dock)
        self._dashboard_list.currentItemChanged.connect(self._select_dashboard_symbol)
        self._refresh_dashboard_list()

    def _add_dashboard_symbol(self) -> None:
        symbol, accepted = QInputDialog.getText(self, "Add Symbol", "Symbol:")
        if not accepted:
            return

        if self._dashboard_manager.add_symbol(symbol):
            self._dashboard_symbols = self._dashboard_manager.load_symbols()
            self._refresh_dashboard_list()

    def _remove_selected_dashboard_symbol(self) -> None:
        selected_item = self._dashboard_list.currentItem()
        if selected_item is None:
            return

        if self._dashboard_manager.remove_symbol(selected_item.text()):
            self._dashboard_symbols = self._dashboard_manager.load_symbols()
            self._state_manager.clear_current_symbol()
            self._refresh_dashboard_list()
            self._update_current_symbol_views()

    def _refresh_dashboard_list(self) -> None:
        self._dashboard_list.clear()
        for item in self._dashboard_symbols:
            symbol = str(item.get("symbol", "")).strip().upper()
            if symbol:
                self._dashboard_list.addItem(symbol)

    def _select_dashboard_symbol(
        self, current: QListWidgetItem | None, previous: QListWidgetItem | None
    ) -> None:
        if current is None:
            self._state_manager.clear_current_symbol()
        else:
            self._state_manager.set_current_symbol(current.text())

        self._update_current_symbol_views()

    def _update_current_symbol_views(self) -> None:
        current_symbol = self._state_manager.current_symbol
        self._chart_workspace.set_current_symbol(current_symbol)

        if current_symbol:
            self.statusBar().showMessage(f"Selected: {current_symbol}")
        else:
            self.statusBar().showMessage("Ready")
