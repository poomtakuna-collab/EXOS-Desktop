from __future__ import annotations

import sqlite3

from src.backtest.persistence_contracts import (
    BacktestEvaluationRecord,
    BacktestRunRecord,
    BacktestTradeResultRecord,
)
from src.backtest.persistence_writer import (
    BACKTEST_EVALUATION_RECORD_COLUMNS,
    BACKTEST_RUN_RECORD_COLUMNS,
    BACKTEST_TRADE_RESULT_RECORD_COLUMNS,
)


def read_backtest_run_record(
    connection: sqlite3.Connection,
    run_id: str,
) -> BacktestRunRecord | None:
    row = connection.execute(
        _select_by_key_sql("backtest_runs", BACKTEST_RUN_RECORD_COLUMNS, "run_id"),
        (run_id,),
    ).fetchone()
    if row is None:
        return None
    return BacktestRunRecord(**_row_dict(row, BACKTEST_RUN_RECORD_COLUMNS))


def read_backtest_evaluation_record(
    connection: sqlite3.Connection,
    evaluation_id: str,
) -> BacktestEvaluationRecord | None:
    row = connection.execute(
        _select_by_key_sql(
            "backtest_evaluations",
            BACKTEST_EVALUATION_RECORD_COLUMNS,
            "evaluation_id",
        ),
        (evaluation_id,),
    ).fetchone()
    if row is None:
        return None

    values = _row_dict(row, BACKTEST_EVALUATION_RECORD_COLUMNS)
    values["has_outcome"] = bool(values["has_outcome"])
    values["has_future_rows"] = bool(values["has_future_rows"])
    return BacktestEvaluationRecord(**values)


def read_backtest_trade_result_records_by_run_id(
    connection: sqlite3.Connection,
    run_id: str,
) -> list[BacktestTradeResultRecord]:
    rows = connection.execute(
        _select_by_key_sql(
            "backtest_trade_results",
            BACKTEST_TRADE_RESULT_RECORD_COLUMNS,
            "run_id",
        )
        + " ORDER BY trade_result_id ASC",
        (run_id,),
    ).fetchall()
    return [
        BacktestTradeResultRecord(**_row_dict(row, BACKTEST_TRADE_RESULT_RECORD_COLUMNS))
        for row in rows
    ]


def _select_by_key_sql(
    table_name: str,
    columns: tuple[str, ...],
    key_column: str,
) -> str:
    column_sql = ", ".join(columns)
    return f"SELECT {column_sql} FROM {table_name} WHERE {key_column} = ?"


def _row_dict(row: sqlite3.Row | tuple[object, ...], columns: tuple[str, ...]) -> dict[str, object]:
    return {column: row[index] for index, column in enumerate(columns)}
