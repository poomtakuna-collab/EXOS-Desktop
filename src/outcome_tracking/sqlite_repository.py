from __future__ import annotations

import json
import sqlite3
from typing import Any

from src.outcome_tracking.contracts import OutcomeRecord, OutcomeStatus


CREATE_OUTCOME_RECORDS_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS outcome_records (
    outcome_row_id INTEGER PRIMARY KEY AUTOINCREMENT,
    outcome_id TEXT NOT NULL UNIQUE,
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


OUTCOME_SCHEMA_SQL = (CREATE_OUTCOME_RECORDS_TABLE_SQL,)


def initialize_outcome_schema(connection: sqlite3.Connection) -> None:
    for statement in OUTCOME_SCHEMA_SQL:
        connection.execute(statement)
    connection.commit()


class SQLiteOutcomeRepository:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self.connection = connection

    def initialize_schema(self) -> None:
        initialize_outcome_schema(self.connection)

    def save_outcome(
        self,
        signal_id: str,
        outcome: OutcomeRecord,
        *,
        outcome_id: str | None = None,
    ) -> OutcomeRecord:
        safe_signal_id = _required_id(signal_id, "signal_id")
        safe_outcome_id = _outcome_id(outcome_id, safe_signal_id, outcome)
        self.connection.execute(
            """
            INSERT INTO outcome_records (
                outcome_id,
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
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(outcome_id) DO UPDATE SET
                signal_id = excluded.signal_id,
                symbol = excluded.symbol,
                signal_date = excluded.signal_date,
                evaluation_date = excluded.evaluation_date,
                horizon_days = excluded.horizon_days,
                entry_price = excluded.entry_price,
                close_price = excluded.close_price,
                return_pct = excluded.return_pct,
                max_runup_pct = excluded.max_runup_pct,
                max_drawdown_pct = excluded.max_drawdown_pct,
                hit_target = excluded.hit_target,
                hit_stop = excluded.hit_stop,
                outcome_status = excluded.outcome_status,
                notes_json = excluded.notes_json
            """,
            (
                safe_outcome_id,
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

    def load_outcome(self, outcome_id: str) -> OutcomeRecord | None:
        row = self.connection.execute(
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
            FROM outcome_records
            WHERE outcome_id = ?
            """,
            (outcome_id,),
        ).fetchone()
        if row is None:
            return None
        return _outcome_from_row(row)

    def list_outcomes(
        self,
        *,
        symbol: str | None = None,
    ) -> tuple[OutcomeRecord, ...]:
        if symbol is None:
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
                FROM outcome_records
                ORDER BY outcome_row_id ASC
                """
            )
        else:
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
                FROM outcome_records
                WHERE symbol = ?
                ORDER BY outcome_row_id ASC
                """,
                (symbol,),
            )
        return tuple(_outcome_from_row(row) for row in cursor.fetchall())

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
            FROM outcome_records
            WHERE signal_id = ?
            ORDER BY outcome_row_id ASC
            """,
            (signal_id,),
        )
        return tuple(_outcome_from_row(row) for row in cursor.fetchall())


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


def _outcome_id(
    value: str | None,
    signal_id: str,
    outcome: OutcomeRecord,
) -> str:
    if value is not None:
        return _required_id(value, "outcome_id")
    parts = (
        signal_id,
        outcome.symbol,
        outcome.signal_date,
        outcome.evaluation_date,
        str(outcome.horizon_days or ""),
    )
    return ":".join(parts)


def _json_dumps(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def _json_loads(value: object) -> object:
    if not isinstance(value, str) or not value:
        return None
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return None


def _json_tuple(value: object) -> tuple[str, ...]:
    loaded = _json_loads(value)
    if isinstance(loaded, list):
        return tuple(str(item) for item in loaded if item is not None)
    return ()


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
