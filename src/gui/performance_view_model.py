from __future__ import annotations

import sqlite3
from pathlib import Path

from src.outcome_tracking import InMemoryOutcomeRepository
from src.outcome_tracking.sqlite_repository import SQLiteOutcomeRepository
from src.performance_report import PerformanceReport, build_performance_report
from src.signal_ledger import InMemorySignalLedgerRepository
from src.signal_ledger.sqlite_repository import SQLiteSignalLedgerRepository


DEFAULT_PERFORMANCE_DATABASE_PATH = Path("database") / "exos.db"


def load_desktop_performance_report(
    database_path: Path | str | None = None,
) -> PerformanceReport:
    safe_database_path = Path(database_path or DEFAULT_PERFORMANCE_DATABASE_PATH)
    if not safe_database_path.exists():
        return build_performance_report(
            InMemorySignalLedgerRepository(),
            InMemoryOutcomeRepository(),
        )

    uri = safe_database_path.resolve().as_uri() + "?mode=ro"
    connection = sqlite3.connect(uri, uri=True)
    try:
        signal_repository = (
            SQLiteSignalLedgerRepository(connection)
            if _has_table(connection, "signal_ledger_signals")
            else InMemorySignalLedgerRepository()
        )
        outcome_repository = (
            SQLiteOutcomeRepository(connection)
            if _has_table(connection, "outcome_records")
            else InMemoryOutcomeRepository()
        )
        return build_performance_report(signal_repository, outcome_repository)
    finally:
        connection.close()


def build_performance_view_model(report: PerformanceReport) -> dict[str, object]:
    return {
        "summary": {
            "total_signals": str(report.total_signals),
            "total_outcomes": str(report.total_outcomes),
            "win_rate": _format_percent(report.win_rate),
            "average_return": _format_percent(report.average_return),
            "average_max_drawdown": _format_percent(report.average_max_drawdown),
        },
        "outcome_status_distribution": _format_distribution(
            report.outcome_status_distribution
        ),
        "signal_type_breakdown": _format_distribution(report.signal_type_breakdown),
        "confidence_bucket_breakdown": _format_distribution(
            report.confidence_bucket_breakdown
        ),
        "status": _status_text(report),
    }


def _has_table(connection: sqlite3.Connection, table_name: str) -> bool:
    row = connection.execute(
        """
        SELECT 1
        FROM sqlite_master
        WHERE type = 'table'
          AND name = ?
        """,
        (table_name,),
    ).fetchone()
    return row is not None


def _format_distribution(distribution: dict[str, int]) -> str:
    if not distribution:
        return "No data"
    return "\n".join(
        f"{_format_label(label)}: {count}"
        for label, count in distribution.items()
    )


def _format_label(value: str) -> str:
    return str(value or "unknown").replace("_", " ").replace("-", " ").title()


def _format_percent(value: float) -> str:
    return f"{float(value):.2f}%"


def _status_text(report: PerformanceReport) -> str:
    if report.total_signals == 0 and report.total_outcomes == 0:
        return "No saved signal or outcome records found."
    return "Read-only performance report."
