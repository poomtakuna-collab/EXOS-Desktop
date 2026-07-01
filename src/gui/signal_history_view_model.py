from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Protocol

from src.outcome_tracking import OutcomeRecord, OutcomeStatus
from src.signal_ledger import SignalRecord, SignalType
from src.signal_ledger.sqlite_repository import SQLiteSignalLedgerRepository


DEFAULT_SIGNAL_HISTORY_DATABASE_PATH = Path("database") / "exos.db"
SIGNAL_HISTORY_COLUMNS = (
    "Snapshot Date",
    "Snapshot Type",
    "Confidence",
    "Snapshot",
    "Outcomes",
    "Latest Outcome",
)


class SignalHistoryRepository(Protocol):
    def list_signals(
        self,
        *,
        symbol: str | None = None,
    ) -> tuple[SignalRecord, ...]:
        """List saved signals."""

    def list_outcomes_for_signal(self, signal_id: str) -> tuple[OutcomeRecord, ...]:
        """List outcomes linked to a signal."""


def load_desktop_signal_history_view_model(
    database_path: Path | str | None = None,
    *,
    selected_symbol: str | None = None,
) -> dict[str, object]:
    symbol = _normalize_symbol(selected_symbol)
    if not symbol:
        return build_signal_history_view_model(selected_symbol=symbol)

    safe_database_path = Path(database_path or DEFAULT_SIGNAL_HISTORY_DATABASE_PATH)
    if not safe_database_path.exists():
        return build_signal_history_view_model(selected_symbol=symbol)

    uri = safe_database_path.resolve().as_uri() + "?mode=ro"
    connection = sqlite3.connect(uri, uri=True)
    try:
        if not _has_table(connection, "signal_ledger_signals"):
            return build_signal_history_view_model(selected_symbol=symbol)

        repository = SQLiteSignalLedgerRepository(connection)
        signals = repository.list_signals(symbol=symbol)
        outcomes_by_signal_id = (
            _outcomes_by_signal_id(repository, signals)
            if _has_table(connection, "signal_ledger_outcomes")
            else {}
        )
        return build_signal_history_view_model(
            selected_symbol=symbol,
            signals=signals,
            outcomes_by_signal_id=outcomes_by_signal_id,
        )
    finally:
        connection.close()


def build_signal_history_view_model(
    *,
    selected_symbol: str | None = None,
    signals: tuple[SignalRecord, ...] = (),
    outcomes_by_signal_id: dict[str, tuple[OutcomeRecord, ...]] | None = None,
) -> dict[str, object]:
    symbol = _normalize_symbol(selected_symbol)
    outcomes_by_signal_id = outcomes_by_signal_id or {}
    rows = tuple(
        _signal_row(signal, outcomes_by_signal_id.get(signal.signal_id, ()))
        for signal in signals
    )
    return {
        "selected_symbol": symbol or "No symbol selected",
        "columns": SIGNAL_HISTORY_COLUMNS,
        "rows": rows,
        "status": _status_text(symbol=symbol, row_count=len(rows)),
    }


def _outcomes_by_signal_id(
    repository: SignalHistoryRepository,
    signals: tuple[SignalRecord, ...],
) -> dict[str, tuple[OutcomeRecord, ...]]:
    return {
        signal.signal_id: repository.list_outcomes_for_signal(signal.signal_id)
        for signal in signals
        if signal.signal_id
    }


def _signal_row(
    signal: SignalRecord,
    outcomes: tuple[OutcomeRecord, ...],
) -> dict[str, str]:
    latest_outcome = outcomes[-1] if outcomes else None
    return {
        "signal_date": signal.signal_date or "-",
        "signal_type": _format_label(_signal_type_value(signal.signal_type)),
        "confidence": _format_percent(signal.confidence),
        "snapshot": _format_snapshot(signal),
        "linked_outcome_count": str(len(outcomes)),
        "latest_outcome": _format_latest_outcome(latest_outcome),
    }


def _format_snapshot(signal: SignalRecord) -> str:
    snapshot = signal.snapshot_reference
    snapshot_id = snapshot.snapshot_id.strip()
    snapshot_date = snapshot.snapshot_date.strip()
    if snapshot_date and snapshot_id:
        return f"{snapshot_date} / {snapshot_id}"
    return snapshot_date or snapshot_id or "-"


def _format_latest_outcome(outcome: OutcomeRecord | None) -> str:
    if outcome is None:
        return "-"
    status = _format_label(_outcome_status_value(outcome.outcome_status))
    return_value = _format_percent(outcome.return_pct)
    if return_value == "-":
        return status
    return f"{status} / {return_value}"


def _status_text(*, symbol: str, row_count: int) -> str:
    if not symbol:
        return "Select a dashboard symbol to view saved snapshot history."
    if row_count == 0:
        return f"No saved snapshots found for {symbol}."
    return f"Read-only snapshot history for {symbol}."


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


def _normalize_symbol(symbol: str | None) -> str:
    return str(symbol or "").strip().upper()


def _format_percent(value: float | None) -> str:
    if value is None:
        return "-"
    return f"{float(value):.2f}%"


def _format_label(value: str) -> str:
    safe_value = str(value or "").strip()
    if not safe_value:
        return "-"
    return safe_value.replace("_", " ").replace("-", " ").title()


def _signal_type_value(signal_type: SignalType | str) -> str:
    if isinstance(signal_type, SignalType):
        return signal_type.value
    return str(signal_type or SignalType.UNKNOWN.value)


def _outcome_status_value(outcome_status: OutcomeStatus | str) -> str:
    if isinstance(outcome_status, OutcomeStatus):
        return outcome_status.value
    return str(outcome_status or OutcomeStatus.UNKNOWN.value)
