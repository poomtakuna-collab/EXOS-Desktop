from __future__ import annotations

import sqlite3

from src.backtest.persistence_contracts import (
    BacktestEvaluationRecord,
    BacktestRunRecord,
    BacktestTradeResultRecord,
)


BACKTEST_RUN_RECORD_COLUMNS = (
    "run_id",
    "run_name",
    "backtest_version",
    "strategy_version",
    "simulation_version",
    "source_database_path",
    "symbols_json",
    "timeframe",
    "start_date",
    "end_date",
    "snapshot_query_json",
    "attempted_trades",
    "completed_trades",
    "total_trades",
    "winning_trades",
    "losing_trades",
    "skipped_trades",
    "breakeven_trades",
    "win_rate",
    "net_return_percent",
    "average_return",
    "max_drawdown",
    "profit_factor",
    "expectancy",
    "notes_json",
    "created_at",
)

BACKTEST_EVALUATION_RECORD_COLUMNS = (
    "evaluation_id",
    "run_id",
    "sequence_number",
    "snapshot_id",
    "symbol",
    "timeframe",
    "snapshot_date",
    "outcome_id",
    "evaluation_status",
    "skip_reason",
    "has_outcome",
    "has_future_rows",
    "future_rows_count",
    "strategy_score",
    "trade_grade",
    "entry_quality",
    "risk_rating",
    "strategy_result_json",
    "probability_json",
    "prediction_json",
    "created_at",
)

BACKTEST_TRADE_RESULT_RECORD_COLUMNS = (
    "trade_result_id",
    "run_id",
    "evaluation_id",
    "snapshot_id",
    "entry_price",
    "exit_price",
    "stop_price",
    "target_price",
    "position_size",
    "gross_return_percent",
    "gross_pnl",
    "risk_amount",
    "reward_amount",
    "outcome_label",
    "notes_json",
    "created_at",
)


def write_backtest_run_record(
    connection: sqlite3.Connection,
    record: BacktestRunRecord,
) -> None:
    connection.execute(
        _insert_sql("backtest_runs", BACKTEST_RUN_RECORD_COLUMNS),
        _record_values(record, BACKTEST_RUN_RECORD_COLUMNS),
    )
    connection.commit()


def write_backtest_evaluation_record(
    connection: sqlite3.Connection,
    record: BacktestEvaluationRecord,
) -> None:
    connection.execute(
        _insert_sql("backtest_evaluations", BACKTEST_EVALUATION_RECORD_COLUMNS),
        _record_values(record, BACKTEST_EVALUATION_RECORD_COLUMNS),
    )
    connection.commit()


def write_backtest_trade_result_record(
    connection: sqlite3.Connection,
    record: BacktestTradeResultRecord,
) -> None:
    connection.execute(
        _insert_sql("backtest_trade_results", BACKTEST_TRADE_RESULT_RECORD_COLUMNS),
        _record_values(record, BACKTEST_TRADE_RESULT_RECORD_COLUMNS),
    )
    connection.commit()


def _insert_sql(table_name: str, columns: tuple[str, ...]) -> str:
    column_sql = ", ".join(columns)
    placeholder_sql = ", ".join("?" for _ in columns)
    return f"INSERT INTO {table_name} ({column_sql}) VALUES ({placeholder_sql})"


def _record_values(record: object, columns: tuple[str, ...]) -> tuple[object, ...]:
    return tuple(_sqlite_value(getattr(record, column)) for column in columns)


def _sqlite_value(value: object) -> object:
    if isinstance(value, bool):
        return int(value)
    return value
