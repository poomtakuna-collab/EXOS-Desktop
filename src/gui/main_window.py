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
    QTabWidget,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from src.core.dashboard_manager import DashboardManager
from src.core.market_scope import MARKET_SCOPE
from src.core.state_manager import StateManager
from src.data import DataManager
from src.gui.chart_workspace import ChartWorkspace
from src.gui.developer_panel import DeveloperPanel
from src.gui.performance_surface import PerformancePanel
from src.gui.research_surface import ResearchPanel


class MainWindow(QMainWindow):
    def __init__(self, dashboard_symbols: list[dict[str, Any]] | None = None) -> None:
        super().__init__()
        self._dashboard_manager = DashboardManager()
        self._state_manager = StateManager()
        self._data_manager = DataManager()
        self._dashboard_symbols = dashboard_symbols or self._dashboard_manager.load_symbols()
        self._dashboard_list = QListWidget(self)
        self._chart_workspace = ChartWorkspace(self._data_manager, self._state_manager)
        self._research_panel = ResearchPanel(self._state_manager)
        self._performance_panel = PerformancePanel(state_manager=self._state_manager)
        self._developer_panel = DeveloperPanel(self._state_manager)
        self._developer_dock = QDockWidget("Developer Panel", self)
        self._developer_mode_action: QAction | None = None

        self.setWindowTitle("EXOS Desktop")
        self.resize(1200, 800)

        self._create_menu_bar()
        self._create_toolbar()
        self._create_central_workspace()
        self._create_dashboard_dock()
        self._create_developer_dock()
        self._chart_workspace.data_changed.connect(self._developer_panel.refresh)
        self._chart_workspace.data_changed.connect(self._research_panel.refresh)
        self._update_current_symbol_views()

    def _create_menu_bar(self) -> None:
        file_menu = self.menuBar().addMenu("File")

        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        view_menu = self.menuBar().addMenu("View")
        self._developer_mode_action = QAction("Developer Mode", self)
        self._developer_mode_action.setCheckable(True)
        self._developer_mode_action.toggled.connect(self._set_developer_mode_visible)
        view_menu.addAction(self._developer_mode_action)

    def _create_toolbar(self) -> None:
        toolbar = QToolBar("Main Toolbar", self)
        toolbar.setMovable(False)
        self.addToolBar(Qt.TopToolBarArea, toolbar)

    def _create_central_workspace(self) -> None:
        tabs = QTabWidget(self)
        tabs.addTab(self._chart_workspace, "Chart")
        tabs.addTab(self._research_panel, "Research")
        tabs.addTab(self._performance_panel, "Performance")
        self.setCentralWidget(tabs)

    def _create_dashboard_dock(self) -> None:
        dashboard_dock = QDockWidget(f"Dashboard ({MARKET_SCOPE})", self)
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

    def _create_developer_dock(self) -> None:
        self._developer_dock.setAllowedAreas(
            Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea | Qt.BottomDockWidgetArea
        )
        self._developer_dock.setWidget(self._developer_panel)
        self.addDockWidget(Qt.BottomDockWidgetArea, self._developer_dock)
        self._developer_dock.setVisible(False)
        self._developer_dock.visibilityChanged.connect(self._sync_developer_mode_action)

    def _add_dashboard_symbol(self) -> None:
        symbol, accepted = QInputDialog.getText(
            self, "Add Symbol", f"{MARKET_SCOPE} Symbol:"
        )
        if not accepted:
            return

        if self._dashboard_manager.add_symbol(symbol):
            self._dashboard_symbols = self._dashboard_manager.load_symbols()
            self._refresh_dashboard_list()
            self._select_dashboard_list_symbol(symbol)

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

    def _select_dashboard_list_symbol(self, symbol: str) -> None:
        normalized_symbol = symbol.strip().upper()
        matching_items = self._dashboard_list.findItems(normalized_symbol, Qt.MatchExactly)
        if matching_items:
            self._dashboard_list.setCurrentItem(matching_items[0])

    def _select_dashboard_symbol(
        self, current: QListWidgetItem | None, previous: QListWidgetItem | None
    ) -> None:
        if current is None:
            self._state_manager.clear_current_symbol()
        else:
            self._state_manager.set_current_symbol(current.text())

        self._update_current_symbol_views()

    def _update_current_symbol_views(self) -> None:
        self._chart_workspace.refresh_from_state()
        self._research_panel.refresh()
        self._performance_panel.refresh()
        self._developer_panel.refresh()

        if self._state_manager.current_symbol:
            self.statusBar().showMessage(f"Selected: {self._state_manager.current_symbol}")
        else:
            self.statusBar().showMessage("Ready")

    def _set_developer_mode_visible(self, visible: bool) -> None:
        self._developer_dock.setVisible(visible)
        if visible:
            self._developer_panel.refresh()

    def _sync_developer_mode_action(self, visible: bool) -> None:
        if self._developer_mode_action is not None:
            self._developer_mode_action.setChecked(visible)
