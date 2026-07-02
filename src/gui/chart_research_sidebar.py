from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QGridLayout, QGroupBox, QLabel, QScrollArea, QVBoxLayout, QWidget

from src.gui.chart_research_sidebar_view_model import (
    empty_chart_research_sidebar_view_model,
    load_chart_research_sidebar_view_model,
)
from src.gui.performance_view_model import DEFAULT_PERFORMANCE_DATABASE_PATH


class ChartResearchSidebar(QWidget):
    """Legacy full sidebar kept for tests and fallback research-detail rendering."""

    def __init__(
        self,
        *,
        database_path: Path | str = DEFAULT_PERFORMANCE_DATABASE_PATH,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._database_path = database_path
        self._identity_labels: dict[str, QLabel] = {}
        self._bias_labels: dict[str, QLabel] = {}
        self._poom_labels: dict[str, QLabel] = {}
        self._trend_labels: dict[str, QLabel] = {}
        self._edge_labels: dict[str, QLabel] = {}
        self._zone_labels: dict[str, QLabel] = {}
        self._reasoning_group: QGroupBox | None = None
        self._reasoning_layout: QVBoxLayout | None = None
        self._summary_layout: QVBoxLayout | None = None
        self._details_layout: QVBoxLayout | None = None
        self._status_label = QLabel(self)

        self.setMinimumWidth(360)
        self._create_layout()
        self.refresh(None)

    def refresh(self, symbol: str | None) -> None:
        view_model = load_chart_research_sidebar_view_model(
            symbol=symbol,
            database_path=self._database_path,
        )
        self.apply_view_model(view_model)

    def show_loading(self, symbol: str | None, stage: str) -> None:
        self.apply_view_model(
            empty_chart_research_sidebar_view_model(
                stage,
                symbol=str(symbol or "").strip().upper(),
            )
        )

    def apply_view_model(self, view_model: dict[str, object]) -> None:
        if isinstance(view_model.get("summary_cards"), tuple):
            _update_card_layout(self._summary_layout, view_model.get("summary_cards"), expanded_default=True)
            _update_card_layout(self._details_layout, view_model.get("detail_sections"), expanded_default=False)
            self._status_label.setText(str(view_model.get("status", "")))
            return

        _update_label_map(self._identity_labels, view_model.get("identity"))
        _update_label_map(
            self._bias_labels,
            view_model.get("overall_assessment", view_model.get("bias")),
        )
        _update_label_map(self._poom_labels, view_model.get("poom_combo"))
        _update_label_map(self._trend_labels, view_model.get("trend_structure"))
        _update_label_map(self._edge_labels, view_model.get("historical_edge"))
        _update_reasoning(self._reasoning_group, self._reasoning_layout, view_model.get("reasoning"))
        _update_zones(self._zone_labels, view_model.get("zones"))
        self._status_label.setText(str(view_model.get("status", "")))

    def _create_layout(self) -> None:
        content = QWidget(self)
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(8)
        title = QLabel("Research Summary", content)
        title.setAlignment(Qt.AlignLeft)
        title.setStyleSheet("font-weight: 700;")
        layout.addWidget(title)
        self._summary_layout = QVBoxLayout()
        self._summary_layout.setSpacing(8)
        layout.addLayout(self._summary_layout)

        details_title = QLabel("Details", content)
        details_title.setStyleSheet("font-weight: 700; color: #9ca3af;")
        layout.addWidget(details_title)
        self._details_layout = QVBoxLayout()
        self._details_layout.setSpacing(6)
        layout.addLayout(self._details_layout)
        self._status_label.setWordWrap(True)
        self._status_label.setStyleSheet("color: #6b7280;")
        layout.addWidget(self._status_label)
        layout.addStretch(1)
        content.setLayout(layout)

        scroll_area = QScrollArea(self)
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)
        scroll_area.setWidget(content)

        root_layout = QVBoxLayout()
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.addWidget(scroll_area)
        self.setLayout(root_layout)


def _section_group(title: str, labels: dict[str, QLabel], parent: QWidget) -> QGroupBox:
    group = QGroupBox(title, parent)
    layout = QGridLayout()
    layout.setContentsMargins(8, 6, 8, 8)
    layout.setVerticalSpacing(3)
    for row, label in enumerate(_labels_for_section(title)):
        name = QLabel(label, group)
        value = QLabel("-", group)
        value.setAlignment(Qt.AlignRight | Qt.AlignTop)
        value.setWordWrap(True)
        labels[label] = value
        layout.addWidget(name, row, 0)
        layout.addWidget(value, row, 1)
    layout.setColumnStretch(1, 1)
    group.setLayout(layout)
    return group


def _zone_group(labels: dict[str, QLabel], parent: QWidget) -> QGroupBox:
    group = QGroupBox("Zones", parent)
    layout = QVBoxLayout()
    layout.setContentsMargins(8, 6, 8, 8)
    layout.setSpacing(6)
    for title, tone in (
        ("Target / Upside Zone", "upside"),
        ("Neutral / Decision Zone", "neutral"),
        ("Risk / Downside Zone", "risk"),
    ):
        card = QFrame(group)
        card.setObjectName(f"{tone}_zone_card")
        card.setStyleSheet(_zone_style(tone))
        card_layout = QVBoxLayout()
        card_layout.setContentsMargins(8, 5, 8, 5)
        title_label = QLabel(title, card)
        title_label.setStyleSheet("font-weight: 700;")
        value_label = QLabel("Not available", card)
        value_label.setWordWrap(True)
        labels[title] = value_label
        card_layout.addWidget(title_label)
        card_layout.addWidget(value_label)
        card.setLayout(card_layout)
        layout.addWidget(card)
    group.setLayout(layout)
    return group


def _reasoning_group(parent: QWidget) -> tuple[QGroupBox, QVBoxLayout]:
    group = QGroupBox("Reasoning / Why", parent)
    layout = QVBoxLayout()
    layout.setContentsMargins(8, 6, 8, 8)
    layout.setSpacing(8)
    group.setLayout(layout)
    group.setVisible(False)
    return group, layout


def _update_card_layout(
    layout: QVBoxLayout | None,
    value: object,
    *,
    expanded_default: bool,
) -> None:
    if layout is None:
        return
    _clear_layout(layout)
    if not isinstance(value, tuple):
        return
    for card in value:
        if not isinstance(card, dict):
            continue
        title = str(card.get("title", "")).strip()
        if not title:
            continue
        expanded = bool(card.get("expanded", expanded_default))
        group = _card_group(title, card, expanded=expanded)
        if group is not None:
            layout.addWidget(group)


def _card_group(title: str, card: dict[str, object], *, expanded: bool) -> QGroupBox | None:
    has_items = isinstance(card.get("items"), tuple) and bool(card.get("items"))
    has_body = bool(str(card.get("body", "")).strip())
    has_zones = isinstance(card.get("zones"), tuple) and bool(card.get("zones"))
    if not has_items and not has_body and not has_zones:
        return None

    group = QGroupBox(title)
    group.setCheckable(not expanded)
    group.setChecked(expanded)
    outer_layout = QVBoxLayout()
    outer_layout.setContentsMargins(8, 6, 8, 8)
    body_container = QWidget(group)
    body_layout = QVBoxLayout()
    body_layout.setContentsMargins(0, 0, 0, 0)
    body_layout.setSpacing(5)

    if has_items:
        body_layout.addLayout(_items_layout(card.get("items")))
    if has_body:
        body = QLabel(str(card.get("body", "")), body_container)
        body.setWordWrap(True)
        body.setTextInteractionFlags(Qt.TextSelectableByMouse)
        body_layout.addWidget(body)
    if has_zones:
        for zone in card.get("zones", ()):
            if isinstance(zone, dict):
                body_layout.addWidget(_zone_card(zone, body_container))

    body_container.setLayout(body_layout)
    body_container.setVisible(expanded)
    if not expanded:
        group.toggled.connect(body_container.setVisible)
    outer_layout.addWidget(body_container)
    group.setLayout(outer_layout)
    return group


def _items_layout(value: object) -> QGridLayout:
    layout = QGridLayout()
    layout.setVerticalSpacing(3)
    rows = value if isinstance(value, tuple) else ()
    for row, item in enumerate(rows):
        if not isinstance(item, tuple) or len(item) != 2:
            continue
        label = QLabel(str(item[0]))
        text = QLabel(str(item[1]))
        text.setAlignment(Qt.AlignRight | Qt.AlignTop)
        text.setWordWrap(True)
        text.setTextInteractionFlags(Qt.TextSelectableByMouse)
        layout.addWidget(label, row, 0)
        layout.addWidget(text, row, 1)
    layout.setColumnStretch(1, 1)
    return layout


def _zone_card(zone: dict[str, object], parent: QWidget) -> QFrame:
    tone = str(zone.get("tone", "neutral"))
    card = QFrame(parent)
    card.setStyleSheet(_zone_style(tone))
    card_layout = QVBoxLayout()
    card_layout.setContentsMargins(8, 5, 8, 5)
    title_label = QLabel(str(zone.get("title", "")), card)
    title_label.setStyleSheet("font-weight: 700;")
    value_label = QLabel(str(zone.get("value", "Not available")), card)
    value_label.setWordWrap(True)
    card_layout.addWidget(title_label)
    card_layout.addWidget(value_label)
    card.setLayout(card_layout)
    return card


def _clear_layout(layout: QVBoxLayout) -> None:
    while layout.count():
        item = layout.takeAt(0)
        widget = item.widget()
        child_layout = item.layout()
        if widget is not None:
            widget.deleteLater()
        if child_layout is not None:
            _clear_child_layout(child_layout)


def _clear_child_layout(layout: object) -> None:
    while layout.count():
        item = layout.takeAt(0)
        widget = item.widget()
        child_layout = item.layout()
        if widget is not None:
            widget.deleteLater()
        if child_layout is not None:
            _clear_child_layout(child_layout)


def _labels_for_section(title: str) -> tuple[str, ...]:
    if title == "Snapshot":
        return ("Symbol", "Latest Snapshot Date", "Timeframe")
    if title == "Overall Assessment":
        return ("Rating", "Recommendation", "Confidence")
    if title == "POOM Combo":
        return ("EW", "Volume Pressure", "POOM Trend Slope", "Squeeze", "BOS / CHoCH")
    if title == "Trend && Structure":
        return ("Trend", "EMA Alignment", "Market Structure", "Support", "Resistance")
    if title == "Historical Edge":
        return ("Matched Pattern", "Sample Count", "Win Rate", "Average Return", "Expectancy", "Average Drawdown")
    return ()


def _update_label_map(labels: dict[str, QLabel], value: object) -> None:
    if not isinstance(value, tuple):
        return
    values = {
        str(item[0]): str(item[1])
        for item in value
        if isinstance(item, tuple) and len(item) == 2
    }
    for label, widget in labels.items():
        text = values.get(label, "-")
        widget.setText(text)
        widget.setStyleSheet(_value_style(label, text))


def _update_reasoning(group: QGroupBox | None, layout: QVBoxLayout | None, value: object) -> None:
    if group is None or layout is None:
        return
    while layout.count():
        item = layout.takeAt(0)
        widget = item.widget()
        if widget is not None:
            widget.deleteLater()
    if not isinstance(value, tuple) or not value:
        group.setVisible(False)
        return
    for label, text in value:
        if not str(text).strip():
            continue
        title = QLabel(str(label), group)
        title.setStyleSheet("font-weight: 700;")
        body = QLabel(str(text), group)
        body.setWordWrap(True)
        body.setTextInteractionFlags(Qt.TextSelectableByMouse)
        layout.addWidget(title)
        layout.addWidget(body)
    group.setVisible(layout.count() > 0)


def _update_zones(labels: dict[str, QLabel], value: object) -> None:
    if not isinstance(value, tuple):
        return
    for zone in value:
        if not isinstance(zone, dict):
            continue
        title = str(zone.get("title", ""))
        label = labels.get(title)
        if label is not None:
            label.setText(str(zone.get("value", "Not available")))


def _zone_style(tone: str) -> str:
    colors = {
        "upside": ("#14532d", "#dcfce7"),
        "neutral": ("#713f12", "#fef3c7"),
        "risk": ("#7f1d1d", "#fee2e2"),
    }
    border, text = colors.get(tone, ("#374151", "#e5e7eb"))
    return (
        f"QFrame {{ border: 1px solid {border}; border-radius: 6px; }}"
        f"QLabel {{ color: {text}; }}"
    )


def _value_style(label: str, text: str) -> str:
    if label not in {"EW", "Volume Pressure", "POOM Trend Slope"}:
        return ""
    try:
        number = float(text)
    except ValueError:
        return "color: #facc15; font-weight: 700;"
    if number > 0:
        return "color: #22c55e; font-weight: 700;"
    if number < 0:
        return "color: #ef4444; font-weight: 700;"
    return "color: #facc15; font-weight: 700;"
