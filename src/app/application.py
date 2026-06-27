from __future__ import annotations

from PySide6.QtWidgets import QApplication

from src.gui import MainWindow


class Application:
    def __init__(self, argv: list[str] | None = None) -> None:
        self._qt_app = QApplication(argv or [])
        self._main_window = MainWindow()

    def run(self) -> int:
        self._main_window.show()
        return self._qt_app.exec()
