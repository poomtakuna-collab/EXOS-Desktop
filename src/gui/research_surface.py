from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from src.canonical_result import CanonicalResultV1
from src.core.state_manager import StateManager
from src.gui.research_signal_save import save_manual_signal_candidate
from src.gui.research_view_model import (
    build_research_view_model,
    load_desktop_research_view_model,
)


class ResearchPanel(QWidget):
    signal_saved = Signal()

    def __init__(self, state_manager: StateManager) -> None:
        super().__init__()
        self._state_manager = state_manager
        self._status_label = QLabel(self)
        self._save_signal_button = QPushButton("Save Snapshot", self)
        self._card_rows: dict[str, list[tuple[QLabel, QLabel]]] = {}
        self._current_canonical_result: CanonicalResultV1 | None = None

        self._create_layout()
        self.refresh()

    def refresh(self) -> None:
        view_model = load_desktop_research_view_model(
            selected_symbol=self._state_manager.current_symbol,
            indicator_snapshot=self._state_manager.indicator_snapshot,
        )
        candidate = view_model.get("canonical_result")
        self._current_canonical_result = (
            candidate if isinstance(candidate, CanonicalResultV1) else None
        )
        self._save_signal_button.setEnabled(bool(view_model.get("can_save_signal")))
        self._status_label.setText(str(view_model["status"]))

        cards = view_model["cards"]
        if not isinstance(cards, tuple):
            return

        for card in cards:
            if not isinstance(card, dict):
                continue
            card_id = str(card.get("id", ""))
            rows = self._card_rows.get(card_id, [])
            items = card.get("items")
            if not isinstance(items, tuple):
                continue
            for index, item in enumerate(items):
                if index >= len(rows) or not isinstance(item, dict):
                    continue
                label_widget, value_widget = rows[index]
                label_widget.setText(str(item.get("label", "")))
                value_widget.setText(str(item.get("value", "")))
                _apply_value_style(
                    value_widget,
                    bool(item.get("is_placeholder", False)),
                )

    def _save_signal(self) -> None:
        result = save_manual_signal_candidate(self._current_canonical_result)
        self._status_label.setText(result.message)
        if result.saved:
            self.signal_saved.emit()

    def _create_layout(self) -> None:
        root_layout = QVBoxLayout()
        grid = QGridLayout()
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(12)

        view_model = build_research_view_model()
        cards = view_model["cards"]
        if isinstance(cards, tuple):
            for index, card in enumerate(cards):
                if not isinstance(card, dict):
                    continue
                row = index // 3
                column = index % 3
                grid.addWidget(self._card_widget(card), row, column)

        root_layout.addLayout(grid)
        self._save_signal_button.clicked.connect(self._save_signal)
        self._save_signal_button.setEnabled(False)
        root_layout.addWidget(self._save_signal_button)
        root_layout.addWidget(self._status_label)
        root_layout.addStretch()
        self.setLayout(root_layout)

    def _card_widget(self, card: dict[str, object]) -> QFrame:
        card_id = str(card.get("id", ""))
        title = str(card.get("title", ""))
        items = card.get("items")
        safe_items = items if isinstance(items, tuple) else ()

        frame = QFrame(self)
        frame.setFrameShape(QFrame.StyledPanel)
        frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)

        layout = QVBoxLayout()
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(6)

        title_label = QLabel(title, frame)
        title_label.setStyleSheet("font-weight: 600;")
        layout.addWidget(title_label)

        rows: list[tuple[QLabel, QLabel]] = []
        values_layout = QGridLayout()
        values_layout.setHorizontalSpacing(10)
        values_layout.setVerticalSpacing(4)
        for row, item in enumerate(safe_items):
            label = QLabel(str(item.get("label", "")), frame)
            value = QLabel(str(item.get("value", "")), frame)
            label.setStyleSheet("color: #9aa0a6;")
            value.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            value.setWordWrap(True)
            _apply_value_style(value, bool(item.get("is_placeholder", False)))
            values_layout.addWidget(label, row, 0)
            values_layout.addWidget(value, row, 1)
            rows.append((label, value))

        layout.addLayout(values_layout)
        frame.setLayout(layout)
        self._card_rows[card_id] = rows
        return frame


def _apply_value_style(label: QLabel, is_placeholder: bool) -> None:
    if is_placeholder:
        label.setStyleSheet("color: #777d86;")
    else:
        label.setStyleSheet("color: #f1f3f4;")
