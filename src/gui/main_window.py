from __future__ import annotations

from pathlib import Path
import sqlite3
import traceback
from typing import Any

from PySide6.QtCore import QObject, Qt, QThread, Signal
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QDialog,
    QDockWidget,
    QHBoxLayout,
    QGridLayout,
    QGroupBox,
    QInputDialog,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from src.application import run_manual_evidence_loop
from src.application.signal_backfill_service import EVIDENCE_LOOP_LOG_PATH
from src.core.dashboard_manager import DashboardManager
from src.core.market_scope import MARKET_SCOPE
from src.core.state_manager import StateManager
from src.data import DataManager
from src.data_source import SQLiteDataSource
from src.daily_research_snapshot import SQLiteDailyResearchSnapshotRepository
from src.developer import reset_snapshots
from src.gui.chart_workspace import ChartWorkspace
from src.gui.developer_panel import DeveloperPanel
from src.gui.performance_view_model import DEFAULT_PERFORMANCE_DATABASE_PATH
from src.gui.performance_surface import PerformancePanel
from src.gui.pattern_statistics_view_model import load_pattern_statistics_view_model
from src.gui.research_surface import ResearchPanel
from src.gui.signal_history_surface import SignalHistoryPanel
from src.gui.statistics_report_view_model import load_statistics_report_view_model
from src.outcome_tracking.sqlite_repository import SQLiteOutcomeRepository
from src.signal_ledger.sqlite_repository import SQLiteSignalLedgerRepository


class MainWindow(QMainWindow):
    def __init__(self, dashboard_symbols: list[dict[str, Any]] | None = None) -> None:
        super().__init__()
        self._dashboard_manager = DashboardManager()
        self._state_manager = StateManager()
        self._data_manager = DataManager()
        self._dashboard_symbols = dashboard_symbols or self._dashboard_manager.load_symbols()
        self._dashboard_list = QListWidget(self)
        self._dashboard_panel = self._create_dashboard_panel()
        self._chart_workspace = ChartWorkspace(
            data_manager=self._data_manager,
            state_manager=self._state_manager,
            dashboard_widget=self._dashboard_panel,
        )
        self._research_panel = ResearchPanel(self._state_manager)
        self._performance_panel = PerformancePanel(state_manager=self._state_manager)
        self._signal_history_panel = SignalHistoryPanel(self._state_manager)
        self._developer_panel = DeveloperPanel(self._state_manager)
        self._developer_dock = QDockWidget("Developer Panel", self)
        self._developer_mode_action: QAction | None = None
        self._reset_snapshots_action: QAction | None = None
        self._statistics_report_action: QAction | None = None
        self._pattern_statistics_action: QAction | None = None
        self._evidence_loop_action: QAction | None = None
        self._evidence_loop_thread: QThread | None = None
        self._evidence_loop_worker: _EvidenceLoopWorker | None = None
        self._statistics_report_dialog: StatisticsReportDialog | None = None
        self._pattern_statistics_dialog: PatternStatisticsDialog | None = None

        self.setWindowTitle("EXOS Desktop")
        self.resize(1200, 800)

        self._create_menu_bar()
        self._create_toolbar()
        self._create_central_workspace()
        self._create_developer_dock()
        self._chart_workspace.data_changed.connect(self._developer_panel.refresh)
        self._chart_workspace.data_changed.connect(self._research_panel.refresh)
        self._chart_workspace.loading_started.connect(self._handle_symbol_loading_started)
        self._chart_workspace.loading_progress.connect(self.statusBar().showMessage)
        self._chart_workspace.loading_finished.connect(self._handle_symbol_loading_finished)
        self._chart_workspace.loading_failed.connect(self._handle_symbol_loading_failed)
        self._research_panel.signal_saved.connect(self._signal_history_panel.refresh)
        self._research_panel.signal_saved.connect(self._performance_panel.refresh)
        self._update_current_symbol_views()

    def _create_menu_bar(self) -> None:
        file_menu = self.menuBar().addMenu("File")

        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        view_menu = self.menuBar().addMenu("View")
        self._developer_mode_action = QAction("Developer Panel", self)
        self._developer_mode_action.setCheckable(True)
        self._developer_mode_action.toggled.connect(self._set_developer_mode_visible)
        view_menu.addAction(self._developer_mode_action)

        developer_menu = self.menuBar().addMenu("Developer")
        self._reset_snapshots_action = QAction("Reset Snapshots...", self)
        self._reset_snapshots_action.triggered.connect(self._confirm_and_reset_snapshots)
        developer_menu.addAction(self._reset_snapshots_action)
        self._statistics_report_action = QAction("Statistics Report...", self)
        self._statistics_report_action.triggered.connect(self._show_statistics_report)
        developer_menu.addAction(self._statistics_report_action)
        self._pattern_statistics_action = QAction("Pattern Statistics...", self)
        self._pattern_statistics_action.triggered.connect(self._show_pattern_statistics)
        developer_menu.addAction(self._pattern_statistics_action)

    def _create_toolbar(self) -> None:
        toolbar = QToolBar("Main Toolbar", self)
        toolbar.setMovable(False)
        self._evidence_loop_action = QAction("Run Evidence Loop", self)
        self._evidence_loop_action.triggered.connect(self._run_manual_evidence_loop)
        toolbar.addAction(self._evidence_loop_action)
        self.addToolBar(Qt.TopToolBarArea, toolbar)

    def _create_central_workspace(self) -> None:
        tabs = QTabWidget(self)
        tabs.addTab(self._chart_workspace, "Chart")
        tabs.addTab(self._research_panel, "Research")
        tabs.addTab(self._performance_panel, "Performance")
        tabs.addTab(self._signal_history_panel, "Snapshot History")
        self.setCentralWidget(tabs)

    def _create_dashboard_panel(self) -> QWidget:
        dashboard_widget = QWidget(self)

        title = QLabel(f"Dashboard ({MARKET_SCOPE})", dashboard_widget)
        title.setStyleSheet("font-weight: 700;")

        add_button = QPushButton("+", dashboard_widget)
        add_button.setFixedWidth(32)
        add_button.clicked.connect(self._add_dashboard_symbol)

        remove_button = QPushButton("-", dashboard_widget)
        remove_button.setFixedWidth(32)
        remove_button.clicked.connect(self._remove_selected_dashboard_symbol)

        button_layout = QHBoxLayout()
        button_layout.addWidget(add_button)
        button_layout.addWidget(remove_button)
        button_layout.addStretch()

        dashboard_layout = QVBoxLayout()
        dashboard_layout.addLayout(button_layout)
        dashboard_layout.addWidget(self._dashboard_list)
        dashboard_layout.setContentsMargins(8, 6, 8, 8)
        dashboard_layout.setSpacing(6)
        dashboard_layout.insertWidget(0, title)

        dashboard_widget.setLayout(dashboard_layout)

        self._dashboard_list.currentItemChanged.connect(self._select_dashboard_symbol)
        self._refresh_dashboard_list()
        return dashboard_widget

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
        if self._chart_workspace.is_loading():
            self.statusBar().showMessage("Symbol load already in progress...")
            return

        if current is None:
            self._state_manager.clear_current_symbol()
        else:
            self._state_manager.set_current_symbol(current.text())

        self._update_current_symbol_views()

    def _update_current_symbol_views(self) -> None:
        self._chart_workspace.refresh_from_state()

        if self._state_manager.current_symbol:
            return

        self._research_panel.refresh()
        self._performance_panel.refresh()
        self._signal_history_panel.refresh()
        self._developer_panel.refresh()
        self.statusBar().showMessage("Ready")

    def _handle_symbol_loading_started(self, symbol: str) -> None:
        self._dashboard_list.setEnabled(False)
        self.statusBar().showMessage(f"Loading {symbol}...")

    def _handle_symbol_loading_finished(
        self,
        symbol: str,
        elapsed_seconds: float,
    ) -> None:
        self._dashboard_list.setEnabled(True)
        self._research_panel.refresh()
        self._performance_panel.refresh()
        self._signal_history_panel.refresh()
        self._developer_panel.refresh()
        self.statusBar().showMessage(f"Loaded {symbol} in {elapsed_seconds:.1f}s")

    def _handle_symbol_loading_failed(self, symbol: str, message: str) -> None:
        self._dashboard_list.setEnabled(True)
        if symbol:
            self.statusBar().showMessage(f"Failed to load {symbol}: {message}")
        else:
            self.statusBar().showMessage(f"Symbol load failed: {message}")

    def _run_manual_evidence_loop(self) -> None:
        symbol = str(self._state_manager.current_symbol or "").strip().upper()
        if not symbol:
            self.statusBar().showMessage("Select a symbol before running Evidence Loop.")
            return
        if self._evidence_loop_thread is not None:
            self.statusBar().showMessage("Evidence Loop already running...")
            return

        database_path = Path(DEFAULT_PERFORMANCE_DATABASE_PATH)
        if not database_path.exists():
            self.statusBar().showMessage("Evidence Loop unavailable: database not found.")
            return

        if self._evidence_loop_action is not None:
            self._evidence_loop_action.setEnabled(False)
        self.statusBar().showMessage("Evidence Loop running...")
        thread = QThread(self)
        worker = _EvidenceLoopWorker(symbol=symbol, database_path=database_path)
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        worker.progress.connect(self._handle_evidence_loop_progress)
        worker.finished.connect(self._handle_evidence_loop_finished)
        worker.failed.connect(self._handle_evidence_loop_failed)
        worker.finished.connect(thread.quit)
        worker.failed.connect(thread.quit)
        worker.finished.connect(worker.deleteLater)
        worker.failed.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)
        thread.finished.connect(self._clear_evidence_loop_worker)
        self._evidence_loop_thread = thread
        self._evidence_loop_worker = worker
        thread.start()

    def _handle_evidence_loop_progress(self, progress: object) -> None:
        current = getattr(progress, "current", 0)
        total = getattr(progress, "total", 0)
        symbol = str(getattr(progress, "symbol", "") or "").strip().upper()
        market_date = str(getattr(progress, "market_date", "") or "").strip()
        detail = " ".join(value for value in (symbol, market_date) if value)
        message = f"Evidence Loop running: {current} / {total} snapshots"
        if detail:
            message = f"{message} | {detail}"
        self.statusBar().showMessage(message)

    def _handle_evidence_loop_finished(self, summary: object) -> None:
        try:
            self._signal_history_panel.refresh()
            self._performance_panel.refresh()
            snapshots_processed = getattr(
                summary,
                "snapshots_processed",
                getattr(summary, "signals_created", 0),
            )
            outcomes_evaluated = getattr(summary, "outcomes_evaluated", 0)
            self.statusBar().showMessage(
                "Evidence Loop complete: "
                f"{snapshots_processed} snapshots, "
                f"{outcomes_evaluated} outcomes."
            )
        except Exception as error:
            self.statusBar().showMessage(
                f"Evidence Loop complete, but refresh failed: {error}"
            )
        finally:
            if self._evidence_loop_action is not None:
                self._evidence_loop_action.setEnabled(True)

    def _handle_evidence_loop_failed(self, message: str) -> None:
        self.statusBar().showMessage(f"Evidence Loop failed: {message}")
        if self._evidence_loop_action is not None:
            self._evidence_loop_action.setEnabled(True)

    def _clear_evidence_loop_worker(self) -> None:
        self._evidence_loop_thread = None
        self._evidence_loop_worker = None

    def _set_developer_mode_visible(self, visible: bool) -> None:
        self._developer_dock.setVisible(visible)
        if visible:
            self._developer_panel.refresh()

    def _sync_developer_mode_action(self, visible: bool) -> None:
        if self._developer_mode_action is not None:
            self._developer_mode_action.setChecked(visible)

    def _confirm_and_reset_snapshots(self) -> None:
        response = QMessageBox.warning(
            self,
            "Reset Snapshot Test Data",
            "Delete saved snapshot test data from the development database?\n\n"
            "This clears snapshot records only. Market data, settings, outcomes, "
            "performance records, and other tables are left unchanged.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if response != QMessageBox.Yes:
            self.statusBar().showMessage("Snapshot reset cancelled.")
            return

        try:
            result = reset_snapshots(
                DEFAULT_PERFORMANCE_DATABASE_PATH,
                confirm=True,
            )
        except Exception as error:
            self.statusBar().showMessage(f"Snapshot reset failed: {error}")
            return

        self._signal_history_panel.refresh()
        self._performance_panel.refresh()
        self._developer_panel.refresh()
        self.statusBar().showMessage(
            f"Snapshot reset complete: {result.total_deleted} rows deleted."
        )

    def _show_statistics_report(self) -> None:
        self._open_statistics_report(
            "current_symbol" if self._state_manager.current_symbol else "all_symbols"
        )

    def _open_statistics_report(self, scope_mode: str) -> None:
        current_symbol = str(self._state_manager.current_symbol or "").strip().upper()
        self.statusBar().showMessage("Building Statistics Report...")
        try:
            view_model = load_statistics_report_view_model(
                DEFAULT_PERFORMANCE_DATABASE_PATH,
                scope_mode=scope_mode,
                current_symbol=current_symbol,
            )
        except Exception as error:
            self.statusBar().showMessage(f"Statistics Report failed: {error}")
            return

        self._statistics_report_dialog = StatisticsReportDialog(
            view_model,
            self,
            scope_callback=self._open_statistics_report,
        )
        self._statistics_report_dialog.show()
        self.statusBar().showMessage(str(view_model.get("status", "")))

    def _show_pattern_statistics(self) -> None:
        self._open_pattern_statistics(
            "current_symbol" if self._state_manager.current_symbol else "all_symbols"
        )

    def _open_pattern_statistics(self, scope_mode: str) -> None:
        current_symbol = str(self._state_manager.current_symbol or "").strip().upper()
        self.statusBar().showMessage("Building Pattern Statistics...")
        try:
            view_model = load_pattern_statistics_view_model(
                DEFAULT_PERFORMANCE_DATABASE_PATH,
                scope_mode=scope_mode,
                current_symbol=current_symbol,
            )
        except Exception as error:
            self.statusBar().showMessage(f"Pattern Statistics failed: {error}")
            return

        self._pattern_statistics_dialog = PatternStatisticsDialog(
            view_model,
            self,
            scope_callback=self._open_pattern_statistics,
        )
        self._pattern_statistics_dialog.show()
        self.statusBar().showMessage(str(view_model.get("status", "")))


class StatisticsReportDialog(QDialog):
    def __init__(
        self,
        view_model: dict[str, object],
        parent: QWidget | None = None,
        scope_callback: object | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle(str(view_model.get("title", "Statistics Report")))
        self.setMinimumWidth(920)
        self.setMinimumHeight(640)

        layout = QVBoxLayout()
        layout.addLayout(_scope_button_layout(scope_callback))
        layout.addWidget(_statistics_summary_group(view_model.get("scope_summary"), self))
        layout.addWidget(_statistics_summary_group(view_model.get("summary"), self))
        layout.addWidget(_statistics_table_group("Top Buckets by Sample Count", view_model.get("top_by_sample_count"), self))
        layout.addWidget(_statistics_table_group("Top Buckets by Win Rate", view_model.get("top_by_win_rate"), self))
        layout.addWidget(_statistics_table_group("Top Buckets by Expectancy", view_model.get("top_by_expectancy"), self))
        layout.addWidget(QLabel(str(view_model.get("status", "")), self))
        self.setLayout(layout)


def _statistics_summary_group(value: object, parent: QWidget) -> QGroupBox:
    group = QGroupBox("Summary", parent)
    layout = QGridLayout()
    if isinstance(value, tuple):
        for row, item in enumerate(value):
            if not isinstance(item, tuple) or len(item) != 2:
                continue
            layout.addWidget(QLabel(str(item[0]), group), row, 0)
            layout.addWidget(QLabel(str(item[1]), group), row, 1)
    group.setLayout(layout)
    return group


def _statistics_table_group(title: str, value: object, parent: QWidget) -> QGroupBox:
    group = QGroupBox(title, parent)
    layout = QVBoxLayout()
    table = QTableWidget(group)
    columns = (
        "Feature",
        "Bucket",
        "Samples",
        "Win Rate",
        "Avg Return",
        "Median Return",
        "Avg Max Gain",
        "Avg Drawdown",
        "Expectancy",
    )
    rows = value if isinstance(value, tuple) else ()
    table.setColumnCount(len(columns))
    table.setHorizontalHeaderLabels(list(columns))
    table.setRowCount(len(rows))
    for row_index, row in enumerate(rows):
        if not isinstance(row, dict):
            continue
        values = (
            row.get("feature", ""),
            row.get("bucket", ""),
            row.get("sample_count", ""),
            row.get("win_rate", ""),
            row.get("average_return", ""),
            row.get("median_return", ""),
            row.get("average_max_gain", ""),
            row.get("average_drawdown", ""),
            row.get("expectancy", ""),
        )
        for column_index, item in enumerate(values):
            table.setItem(row_index, column_index, QTableWidgetItem(str(item)))
    table.resizeColumnsToContents()
    layout.addWidget(table)
    group.setLayout(layout)
    return group


class PatternStatisticsDialog(QDialog):
    def __init__(
        self,
        view_model: dict[str, object],
        parent: QWidget | None = None,
        scope_callback: object | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle(str(view_model.get("title", "Pattern Statistics")))
        self.setMinimumWidth(980)
        self.setMinimumHeight(720)

        layout = QVBoxLayout()
        layout.addLayout(_scope_button_layout(scope_callback))
        layout.addWidget(_statistics_summary_group(view_model.get("scope_summary"), self))
        layout.addWidget(_statistics_summary_group(view_model.get("summary"), self))
        for title, rows in _named_sections(view_model.get("rankings")):
            layout.addWidget(_pattern_statistics_table_group(title, rows, self))
        for title, rows in _named_sections(view_model.get("insights")):
            layout.addWidget(_pattern_statistics_table_group(title, rows, self))
        layout.addWidget(QLabel(str(view_model.get("status", "")), self))
        self.setLayout(layout)


def _scope_button_layout(scope_callback: object | None) -> QHBoxLayout:
    layout = QHBoxLayout()
    current_button = QPushButton("Current Symbol")
    all_button = QPushButton("All Symbols")
    if callable(scope_callback):
        current_button.clicked.connect(lambda: scope_callback("current_symbol"))
        all_button.clicked.connect(lambda: scope_callback("all_symbols"))
    else:
        current_button.setEnabled(False)
        all_button.setEnabled(False)
    layout.addWidget(current_button)
    layout.addWidget(all_button)
    layout.addStretch()
    return layout


def _named_sections(value: object) -> tuple[tuple[str, object], ...]:
    if not isinstance(value, tuple):
        return ()
    return tuple(
        (str(item[0]), item[1])
        for item in value
        if isinstance(item, tuple) and len(item) == 2
    )


def _pattern_statistics_table_group(title: str, value: object, parent: QWidget) -> QGroupBox:
    group = QGroupBox(title, parent)
    layout = QVBoxLayout()
    table = QTableWidget(group)
    columns = (
        "Bucket",
        "Samples",
        "Win Rate",
        "Avg Return",
        "Expectancy",
        "Avg Drawdown",
        "Interpretation",
    )
    rows = value if isinstance(value, tuple) else ()
    table.setColumnCount(len(columns))
    table.setHorizontalHeaderLabels(list(columns))
    table.setRowCount(len(rows))
    for row_index, row in enumerate(rows):
        if not isinstance(row, dict):
            continue
        values = (
            row.get("bucket_name", ""),
            row.get("sample_count", ""),
            row.get("win_rate", ""),
            row.get("average_return_10d", ""),
            row.get("expectancy", ""),
            row.get("average_drawdown", ""),
            row.get("interpretation", ""),
        )
        for column_index, item in enumerate(values):
            table.setItem(row_index, column_index, QTableWidgetItem(str(item)))
    table.resizeColumnsToContents()
    layout.addWidget(table)
    group.setLayout(layout)
    return group


class _EvidenceLoopWorker(QObject):
    progress = Signal(object)
    finished = Signal(object)
    failed = Signal(str)

    def __init__(self, *, symbol: str, database_path: Path) -> None:
        super().__init__()
        self._symbol = symbol
        self._database_path = database_path
        self._last_progress: object | None = None

    def _emit_progress(self, progress: object) -> None:
        self._last_progress = progress
        self.progress.emit(progress)

    def run(self) -> None:
        try:
            connection = sqlite3.connect(self._database_path)
            try:
                signal_repository = SQLiteSignalLedgerRepository(connection)
                outcome_repository = SQLiteOutcomeRepository(connection)
                snapshot_repository = SQLiteDailyResearchSnapshotRepository(connection)
                signal_repository.initialize_schema()
                outcome_repository.initialize_schema()
                snapshot_repository.initialize_schema()
                summary = run_manual_evidence_loop(
                    symbol=self._symbol,
                    data_source=SQLiteDataSource(connection),
                    signal_repository=signal_repository,
                    outcome_repository=outcome_repository,
                    snapshot_repository=snapshot_repository,
                    progress_callback=self._emit_progress,
                )
            finally:
                connection.close()
        except Exception as error:
            _log_evidence_loop_exception(
                symbol=self._symbol,
                progress=self._last_progress,
                error=error,
            )
            self.failed.emit(_evidence_loop_failure_message(error, self._last_progress))
            return

        self.finished.emit(summary)


def _evidence_loop_failure_message(error: BaseException, progress: object | None) -> str:
    error_symbol = str(getattr(error, "symbol", "") or "").strip().upper()
    error_market_date = str(getattr(error, "market_date", "") or "").strip()
    if error_symbol or error_market_date:
        return str(error)

    symbol = str(getattr(progress, "symbol", "") or "").strip().upper()
    market_date = str(getattr(progress, "market_date", "") or "").strip()
    detail = " ".join(value for value in (symbol, market_date) if value)
    if detail:
        return f"{detail}: {error}"
    return str(error)


def _log_evidence_loop_exception(
    *,
    symbol: str,
    progress: object | None,
    error: BaseException,
) -> None:
    market_date = str(getattr(error, "market_date", "") or "").strip()
    if not market_date:
        market_date = str(getattr(progress, "market_date", "") or "").strip()
    try:
        EVIDENCE_LOOP_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with EVIDENCE_LOOP_LOG_PATH.open("a", encoding="utf-8") as handle:
            handle.write(
                "\n"
                f"Evidence Loop worker failure: {symbol}"
                f"{(' ' + market_date) if market_date else ''}\n"
            )
            handle.writelines(
                traceback.format_exception(type(error), error, error.__traceback__)
            )
    except Exception:
        return
