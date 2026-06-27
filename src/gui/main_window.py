from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QDockWidget, QListWidget, QMainWindow, QToolBar, QWidget


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("EXOS Desktop")
        self.resize(1200, 800)

        self._create_menu_bar()
        self._create_toolbar()
        self._create_central_workspace()
        self._create_watchlist_dock()
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

    def _create_watchlist_dock(self) -> None:
        watchlist_dock = QDockWidget("Watchlist", self)
        watchlist_dock.setAllowedAreas(Qt.RightDockWidgetArea)
        watchlist_dock.setWidget(QListWidget(watchlist_dock))
        self.addDockWidget(Qt.RightDockWidgetArea, watchlist_dock)
