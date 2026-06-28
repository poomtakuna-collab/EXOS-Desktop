from __future__ import annotations

from PySide6.QtWidgets import QApplication

from src.core.dashboard_manager import DashboardManager
from src.gui import MainWindow
from src.gui.theme import apply_dark_theme


class Application:
    def __init__(self, argv: list[str] | None = None) -> None:
        self._qt_app = QApplication(argv or [])
        apply_dark_theme(self._qt_app)
        self._dashboard_manager = DashboardManager()
        self._main_window = MainWindow(
            dashboard_symbols=self._dashboard_manager.load_symbols()
        )

    def run(self) -> int:
        self._main_window.show()
        return self._qt_app.exec()
