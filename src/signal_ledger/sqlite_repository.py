from __future__ import annotations

import json
import sqlite3
from typing import Any

from src.outcome_tracking import OutcomeRecord, OutcomeStatus
from src.signal_ledger.contracts import (
    SignalRecord,
    SignalSnapshotReference,
    SignalType,
)


CREATE_SIGNAL_LEDGER_SIGNALS_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS signal_ledger_signals (
    signal_id TEXT PRIMARY KEY,
    symbol TEXT NOT NULL,
    signal_date TEXT NOT NULL,
    snapshot_id TEXT NOT NULL,
    snapshot_date TEXT NOT NULL,
    timeframe TEXT NOT NULL,
    snapshot_source TEXT NOT NULL,
    context_summary_json TEXT NOT NULL,
    strategy_summary_json TEXT NOT NULL,
    signal_type TEXT NOT NULL,
    confidence REAL,
    notes_json TEXT NOT NULL
)
"""


CREATE_SIGNAL_LEDGER_OUTCOMES_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS signal_ledger_outcomes (
    outcome_row_id INTEGER PRIMARY KEY AUTOINCREMENT,
    signal_id TEXT NOT NULL,
    symbol TEXT NOT NULL,
    signal_date TEXT NOT NULL,
    evaluation_date TEXT NOT NULL,
    horizon_days INTEGER,
    entry_price REAL,
    close_price REAL,
    return_pct REAL,
    max_runup_pct REAL,
    max_drawdown_pct REAL,
    hit_target INTEGER,
    hit_stop INTEGER,
    outcome_status TEXT NOT NULL,
    notes_json TEXT NOT NULL
)
"""


SIGNAL_LEDGER_SCHEMA_SQL = (
    CREATE_SIGNAL_LEDGER_SIGNALS_TABLE_SQL,
    CREATE_SIGNAL_LEDGER_OUTCOMES_TABLE_SQL,
)


def initialize_signal_ledger_schema(connection: sqlite3.Connection) -> None:
    for statement in SIGNAL_LEDGER_SCHEMA_SQL:
        connection.execute(statement)
    connection.commit()


class SQLiteSignalLedgerRepository:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self.connection = connection

    def initialize_schema(self) -> None:
        initialize_signal_ledger_schema(self.connection)

    def save_signal(self, signal: SignalRecord) -> SignalRecord:
        signal_id = _required_id(signal.signal_id, "signal.signal_id")
        snapshot = signal.snapshot_reference
        self.connection.execute(
            """
            INSERT OR REPLACE INTO signal_ledger_signals (
                signal_id,
                symbol,
                signal_date,
                snapshot_id,
                snapshot_date,
                timeframe,
                snapshot_source,
                context_summary_json,
                strategy_summary_json,
                signal_type,
                confidence,
                notes_json
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                signal_id,
                signal.symbol,
                signal.signal_date,
                snapshot.snapshot_id,
                snapshot.snapshot_date,
                snapshot.timeframe,
                snapshot.source,
                _json_dumps(signal.context_summary),
                _json_dumps(signal.strategy_summary),
                _signal_type_value(signal.signal_type),
                signal.confidence,
                _json_dumps(list(signal.notes)),
            ),
        )
        self.connection.commit()
        return signal

    def load_signal(self, signal_id: str) -> SignalRecord | None:
        row = self.connection.execute(
            """
            SELECT
                signal_id,
                symbol,
                signal_date,
                snapshot_id,
                snapshot_date,
                timeframe,
                snapshot_source,
                context_summary_json,
                strategy_summary_json,
                signal_type,
                confidence,
                notes_json
            FROM signal_ledger_signals
            WHERE signal_id = ?
            """,
            (signal_id,),
        ).fetchone()
        if row is None:
            return None
        return _signal_from_row(row)

    def list_signals(
        self,
        *,
        symbol: str | None = None,
    ) -> tuple[SignalRecord, ...]:
        if symbol is None:
            cursor = self.connection.execute(
                """
                SELECT
                    signal_id,
                    symbol,
                    signal_date,
                    snapshot_id,
                    snapshot_date,
                    timeframe,
                    snapshot_source,
                    context_summary_json,
                    strategy_summary_json,
                    signal_type,
                    confidence,
                    notes_json
                FROM signal_ledger_signals
                ORDER BY rowid ASC
                """
            )
        else:
            cursor = self.connection.execute(
                """
                SELECT
                    signal_id,
                    symbol,
                    signal_date,
                    snapshot_id,
                    snapshot_date,
                    timeframe,
                    snapshot_source,
                    context_summary_json,
                    strategy_summary_json,
                    signal_type,
                    confidence,
                    notes_json
                FROM signal_ledger_signals
                WHERE symbol = ?
                ORDER BY rowid ASC
                """,
                (symbol,),
            )
        return tuple(_signal_from_row(row) for row in cursor.fetchall())

    def save_outcome(self, signal_id: str, outcome: OutcomeRecord) -> OutcomeRecord:
        safe_signal_id = _required_id(signal_id, "signal_id")
        self.connection.execute(
            """
            INSERT INTO signal_ledger_outcomes (
                signal_id,
                symbol,
                signal_date,
                evaluation_date,
                horizon_days,
                entry_price,
                close_price,
                return_pct,
                max_runup_pct,
                max_drawdown_pct,
                hit_target,
                hit_stop,
                outcome_status,
                notes_json
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                safe_signal_id,
                outcome.symbol,
                outcome.signal_date,
                outcome.evaluation_date,
                outcome.horizon_days,
                outcome.entry_price,
                outcome.close_price,
                outcome.return_pct,
                outcome.max_runup_pct,
                outcome.max_drawdown_pct,
                _bool_to_int(outcome.hit_target),
                _bool_to_int(outcome.hit_stop),
                _outcome_status_value(outcome.outcome_status),
                _json_dumps(list(outcome.notes)),
            ),
        )
        self.connection.commit()
        return outcome

    def list_outcomes_for_signal(self, signal_id: str) -> tuple[OutcomeRecord, ...]:
        cursor = self.connection.execute(
            """
            SELECT
                symbol,
                signal_date,
                evaluation_date,
                horizon_days,
                entry_price,
                close_price,
                return_pct,
                max_runup_pct,
                max_drawdown_pct,
                hit_target,
                hit_stop,
                outcome_status,
                notes_json
            FROM signal_ledger_outcomes
            WHERE signal_id = ?
            ORDER BY outcome_row_id ASC
            """,
            (signal_id,),
        )
        return tuple(_outcome_from_row(row) for row in cursor.fetchall())


def _signal_from_row(row: sqlite3.Row | tuple[Any, ...]) -> SignalRecord:
    values = tuple(row)
    return SignalRecord(
        signal_id=str(values[0] or ""),
        symbol=str(values[1] or ""),
        signal_date=str(values[2] or ""),
        snapshot_reference=SignalSnapshotReference(
            snapshot_id=str(values[3] or ""),
            snapshot_date=str(values[4] or ""),
            timeframe=str(values[5] or ""),
            source=str(values[6] or ""),
        ),
        context_summary=_json_object(values[7]),
        strategy_summary=_json_object(values[8]),
        signal_type=_signal_type(values[9]),
        confidence=values[10],
        notes=_json_tuple(values[11]),
    )


def _outcome_from_row(row: sqlite3.Row | tuple[Any, ...]) -> OutcomeRecord:
    values = tuple(row)
    return OutcomeRecord(
        symbol=str(values[0] or ""),
        signal_date=str(values[1] or ""),
        evaluation_date=str(values[2] or ""),
        horizon_days=values[3],
        entry_price=values[4],
        close_price=values[5],
        return_pct=values[6],
        max_runup_pct=values[7],
        max_drawdown_pct=values[8],
        hit_target=_int_to_bool(values[9]),
        hit_stop=_int_to_bool(values[10]),
        outcome_status=_outcome_status(values[11]),
        notes=_json_tuple(values[12]),
    )


def _required_id(value: str, name: str) -> str:
    safe_value = str(value or "").strip()
    if not safe_value:
        raise ValueError(f"{name} is required")
    return safe_value


def _json_dumps(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def _json_loads(value: object) -> object:
    if not isinstance(value, str) or not value:
        return None
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return None


def _json_object(value: object) -> dict[str, Any]:
    loaded = _json_loads(value)
    return loaded if isinstance(loaded, dict) else {}


def _json_tuple(value: object) -> tuple[str, ...]:
    loaded = _json_loads(value)
    if isinstance(loaded, list):
        return tuple(str(item) for item in loaded if item is not None)
    return ()


def _signal_type(value: object) -> SignalType | str:
    normalized = str(value or SignalType.UNKNOWN.value)
    try:
        return SignalType(normalized)
    except ValueError:
        return normalized


def _signal_type_value(signal_type: SignalType | str) -> str:
    if isinstance(signal_type, SignalType):
        return signal_type.value
    return str(signal_type or SignalType.UNKNOWN.value)


def _outcome_status(value: object) -> OutcomeStatus | str:
    normalized = str(value or OutcomeStatus.UNKNOWN.value)
    try:
        return OutcomeStatus(normalized)
    except ValueError:
        return normalized


def _outcome_status_value(outcome_status: OutcomeStatus | str) -> str:
    if isinstance(outcome_status, OutcomeStatus):
        return outcome_status.value
    return str(outcome_status or OutcomeStatus.UNKNOWN.value)


def _bool_to_int(value: bool | None) -> int | None:
    if value is None:
        return None
    return 1 if value else 0


def _int_to_bool(value: object) -> bool | None:
    if value is None:
        return None
    return bool(value)
