from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import (
    QGridLayout,
    QGroupBox,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from src.gui.performance_view_model import (
    DEFAULT_PERFORMANCE_DATABASE_PATH,
    build_performance_view_model,
    load_desktop_performance_report,
)
from src.core.state_manager import StateManager


class PerformancePanel(QWidget):
    def __init__(
        self,
        database_path: Path | None = None,
        state_manager: StateManager | None = None,
    ) -> None:
        super().__init__()
        self._database_path = database_path or DEFAULT_PERFORMANCE_DATABASE_PATH
        self._state_manager = state_manager
        self._scope_label = QLabel(self)
        self._global_summary_label = QLabel(self)
        self._summary_labels: dict[str, QLabel] = {}
        self._performance_analytics_labels: dict[str, QLabel] = {}
        self._snapshot_health_labels: dict[str, QLabel] = {}
        self._outcome_distribution_label = QLabel(self)
        self._signal_breakdown_label = QLabel(self)
        self._confidence_breakdown_label = QLabel(self)
        self._status_label = QLabel(self)

        self._create_layout()
        self.refresh()

    def refresh(self) -> None:
        selected_symbol = self._state_manager.current_symbol if self._state_manager else None
        global_report = load_desktop_performance_report(self._database_path)
        report = load_desktop_performance_report(
            self._database_path,
            symbol=selected_symbol,
        )
        view_model = build_performance_view_model(
            report,
            selected_symbol=selected_symbol,
            global_report=global_report,
        )

        self._scope_label.setText(str(view_model["scope"]))
        self._global_summary_label.setText(str(view_model["global_summary"]))

        for key, value in view_model["summary"].items():
            self._summary_labels[key].setText(value)
        for key, value in view_model["performance_analytics"].items():
            self._performance_analytics_labels[key].setText(value)
        for key, value in view_model["snapshot_health"].items():
            self._snapshot_health_labels[key].setText(value)

        self._outcome_distribution_label.setText(view_model["outcome_status_distribution"])
        self._signal_breakdown_label.setText(view_model["signal_type_breakdown"])
        self._confidence_breakdown_label.setText(view_model["confidence_bucket_breakdown"])
        self._status_label.setText(view_model["status"])

    def _create_layout(self) -> None:
        refresh_button = QPushButton("Refresh", self)
        refresh_button.clicked.connect(self.refresh)

        summary_group = QGroupBox("Summary", self)
        summary_layout = QGridLayout()
        for row, (key, label) in enumerate(
            (
                ("total_signals", "Total Snapshots"),
                ("total_outcomes", "Total Outcomes"),
                ("win_rate", "Win Rate"),
                ("average_return", "Average Return"),
                ("average_max_drawdown", "Average Max Drawdown"),
            )
        ):
            name_label = QLabel(label, summary_group)
            value_label = QLabel("", summary_group)
            summary_layout.addWidget(name_label, row, 0)
            summary_layout.addWidget(value_label, row, 1)
            self._summary_labels[key] = value_label
        summary_group.setLayout(summary_layout)

        performance_analytics_group = QGroupBox("Performance Analytics", self)
        performance_analytics_layout = QGridLayout()
        for row, (key, label) in enumerate(
            (
                ("average_return", "Average Return"),
                ("median_return", "Median Return"),
                ("win_rate", "Win Rate"),
                ("average_drawdown", "Average Drawdown"),
                ("best_outcome", "Best Outcome"),
                ("worst_outcome", "Worst Outcome"),
            )
        ):
            name_label = QLabel(label, performance_analytics_group)
            value_label = QLabel("", performance_analytics_group)
            performance_analytics_layout.addWidget(name_label, row, 0)
            performance_analytics_layout.addWidget(value_label, row, 1)
            self._performance_analytics_labels[key] = value_label
        performance_analytics_group.setLayout(performance_analytics_layout)

        snapshot_health_group = QGroupBox("Snapshot Health", self)
        snapshot_health_layout = QGridLayout()
        for row, (key, label) in enumerate(
            (
                ("total_snapshots", "Total Snapshots"),
                ("completed_outcomes", "Completed Outcomes"),
                ("pending_outcomes", "Pending Outcomes"),
                ("outcome_coverage", "Outcome Coverage"),
                ("duplicate_snapshots", "Duplicate Snapshots"),
                ("last_snapshot_date", "Last Snapshot Date"),
                ("last_outcome_evaluation_date", "Last Outcome Evaluation Date"),
            )
        ):
            name_label = QLabel(label, snapshot_health_group)
            value_label = QLabel("", snapshot_health_group)
            snapshot_health_layout.addWidget(name_label, row, 0)
            snapshot_health_layout.addWidget(value_label, row, 1)
            self._snapshot_health_labels[key] = value_label
        snapshot_health_group.setLayout(snapshot_health_layout)

        outcome_group = _text_group(
            "Outcome Status Distribution",
            self._outcome_distribution_label,
            self,
        )
        signal_group = _text_group(
            "Snapshot Type Breakdown",
            self._signal_breakdown_label,
            self,
        )
        confidence_group = _text_group(
            "Confidence Bucket Breakdown",
            self._confidence_breakdown_label,
            self,
        )

        layout = QVBoxLayout()
        layout.addWidget(refresh_button)
        layout.addWidget(self._scope_label)
        layout.addWidget(self._global_summary_label)
        layout.addWidget(summary_group)
        layout.addWidget(performance_analytics_group)
        layout.addWidget(snapshot_health_group)
        layout.addWidget(outcome_group)
        layout.addWidget(signal_group)
        layout.addWidget(confidence_group)
        layout.addWidget(self._status_label)
        layout.addStretch()
        self.setLayout(layout)


def _text_group(title: str, label: QLabel, parent: QWidget) -> QGroupBox:
    label.setWordWrap(True)
    group = QGroupBox(title, parent)
    layout = QVBoxLayout()
    layout.addWidget(label)
    group.setLayout(layout)
    return group
