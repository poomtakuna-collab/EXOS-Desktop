from __future__ import annotations

from typing import Any

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QDockWidget,
    QHBoxLayout,
    QInputDialog,
    QListWidget,
    QMainWindow,
    QPushButton,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from src.core.dashboard_manager import DashboardManager


class MainWindow(QMainWindow):
    def __init__(self, dashboard_symbols: list[dict[str, Any]] | None = None) -> None:
        super().__init__()
        self._dashboard_manager = DashboardManager()
        self._dashboard_symbols = dashboard_symbols or self._dashboard_manager.load_symbols()
        self._dashboard_list = QListWidget(self)

        self.setWindowTitle("EXOS Desktop")
        self.resize(1200, 800)

        self._create_menu_bar()
        self._create_toolbar()
        self._create_central_workspace()
        self._create_dashboard_dock()
        self.statusBar().showMessage("Ready")

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
        workspace = QWidget(self)
        workspace.setObjectName("centralWorkspace")
        self.setCentralWidget(workspace)

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
            self._refresh_dashboard_list()

    def _refresh_dashboard_list(self) -> None:
        self._dashboard_list.clear()
        for item in self._dashboard_symbols:
            symbol = str(item.get("symbol", "")).strip().upper()
            if symbol:
                self._dashboard_list.addItem(symbol)
