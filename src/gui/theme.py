from __future__ import annotations

from PySide6.QtWidgets import QApplication


def apply_dark_theme(app: QApplication) -> None:
    app.setStyleSheet(DARK_THEME_STYLESHEET)


DARK_THEME_STYLESHEET = """
QMainWindow,
QWidget {
    background-color: #1f242a;
    color: #d8dee6;
    font-size: 13px;
}

QDockWidget {
    background-color: #242a31;
    color: #e2e8f0;
    titlebar-close-icon: none;
    titlebar-normal-icon: none;
}

QDockWidget::title {
    background-color: #2b323a;
    color: #e2e8f0;
    padding: 6px 8px;
    border-bottom: 1px solid #3a4450;
}

QMenuBar {
    background-color: #252b32;
    color: #d8dee6;
    border-bottom: 1px solid #343d47;
}

QMenuBar::item {
    background: transparent;
    padding: 5px 10px;
}

QMenuBar::item:selected {
    background-color: #343d47;
}

QMenu {
    background-color: #252b32;
    color: #d8dee6;
    border: 1px solid #3a4450;
}

QMenu::item {
    padding: 6px 24px 6px 12px;
}

QMenu::item:selected {
    background-color: #3a4653;
}

QToolBar {
    background-color: #242a31;
    border: 0;
    border-bottom: 1px solid #343d47;
    spacing: 6px;
    padding: 4px;
}

QStatusBar {
    background-color: #252b32;
    color: #b8c2cc;
    border-top: 1px solid #343d47;
}

QPushButton {
    background-color: #303841;
    color: #e2e8f0;
    border: 1px solid #4b5563;
    border-radius: 4px;
    padding: 5px 10px;
}

QPushButton:hover {
    background-color: #394450;
    border-color: #5d6b7a;
}

QPushButton:pressed {
    background-color: #26313a;
}

QPushButton:checked {
    background-color: #2f6f8f;
    color: #ffffff;
    border-color: #4aa3c7;
}

QListWidget {
    background-color: #20262d;
    color: #d8dee6;
    border: 1px solid #3a4450;
    outline: 0;
}

QListWidget::item {
    padding: 5px 6px;
}

QListWidget::item:selected {
    background-color: #2f6f8f;
    color: #ffffff;
}

QLabel {
    color: #d8dee6;
}

QLineEdit {
    background-color: #20262d;
    color: #e2e8f0;
    border: 1px solid #4b5563;
    border-radius: 4px;
    padding: 5px 7px;
    selection-background-color: #2f6f8f;
}

QInputDialog {
    background-color: #1f242a;
    color: #d8dee6;
}

QToolTip {
    background-color: #252b32;
    color: #e2e8f0;
    border: 1px solid #4b5563;
    padding: 5px;
}
"""
