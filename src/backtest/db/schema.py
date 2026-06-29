from __future__ import annotations

import sqlite3


CREATE_BACKTEST_RUNS_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS backtest_runs (
    run_id TEXT PRIMARY KEY,
    run_name TEXT,
    backtest_version TEXT NOT NULL,
    strategy_version TEXT NOT NULL,
    simulation_version TEXT NOT NULL,
    source_database_id TEXT,
    source_database_path TEXT,
    symbols_json TEXT NOT NULL,
    timeframe TEXT,
    start_date TEXT,
    end_date TEXT,
    snapshot_query_json TEXT NOT NULL,
    attempted_trades INTEGER NOT NULL,
    completed_trades INTEGER NOT NULL,
    total_trades INTEGER NOT NULL,
    winning_trades INTEGER NOT NULL,
    losing_trades INTEGER NOT NULL,
    skipped_trades INTEGER NOT NULL,
    breakeven_trades INTEGER NOT NULL,
    win_rate REAL NOT NULL,
    average_return REAL NOT NULL,
    average_drawdown REAL NOT NULL,
    expectancy REAL NOT NULL,
    max_drawdown REAL NOT NULL,
    notes_json TEXT NOT NULL,
    created_at TEXT NOT NULL
)
"""

CREATE_BACKTEST_ASSUMPTIONS_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS backtest_assumptions (
    run_id TEXT PRIMARY KEY,
    horizon_days INTEGER NOT NULL,
    entry_price_source TEXT NOT NULL,
    conservative_same_window_rule INTEGER NOT NULL,
    target_source TEXT NOT NULL,
    stop_source TEXT NOT NULL,
    probability_source TEXT NOT NULL,
    prediction_source TEXT NOT NULL,
    strategy_source TEXT NOT NULL,
    fees_enabled INTEGER NOT NULL,
    slippage_enabled INTEGER NOT NULL,
    portfolio_enabled INTEGER NOT NULL,
    ai_enabled INTEGER NOT NULL,
    live_data_enabled INTEGER NOT NULL,
    broker_execution_enabled INTEGER NOT NULL,
    assumptions_json TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY(run_id) REFERENCES backtest_runs(run_id)
)
"""

CREATE_BACKTEST_EVALUATIONS_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS backtest_evaluations (
    evaluation_id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL,
    sequence_number INTEGER NOT NULL,
    snapshot_id TEXT NOT NULL,
    symbol TEXT NOT NULL,
    timeframe TEXT NOT NULL,
    snapshot_date TEXT NOT NULL,
    outcome_id TEXT,
    evaluation_status TEXT NOT NULL,
    skip_reason TEXT,
    has_outcome INTEGER NOT NULL,
    has_future_rows INTEGER NOT NULL,
    future_rows_count INTEGER NOT NULL,
    strategy_score REAL,
    trade_grade TEXT,
    entry_quality TEXT,
    risk_rating TEXT,
    strategy_result_json TEXT,
    probability_json TEXT,
    prediction_json TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY(run_id) REFERENCES backtest_runs(run_id),
    FOREIGN KEY(snapshot_id) REFERENCES snapshots(snapshot_id),
    FOREIGN KEY(outcome_id) REFERENCES outcomes(outcome_id),
    UNIQUE(run_id, sequence_number),
    UNIQUE(run_id, snapshot_id)
)
"""

CREATE_BACKTEST_TRADE_RESULTS_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS backtest_trade_results (
    trade_result_id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL,
    evaluation_id TEXT NOT NULL,
    snapshot_id TEXT NOT NULL,
    simulation_status TEXT NOT NULL,
    trade_outcome TEXT NOT NULL,
    exit_reason TEXT NOT NULL,
    entry_price REAL,
    exit_price REAL,
    return_percent REAL,
    max_drawdown_percent REAL,
    notes_json TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY(run_id) REFERENCES backtest_runs(run_id),
    FOREIGN KEY(evaluation_id) REFERENCES backtest_evaluations(evaluation_id),
    FOREIGN KEY(snapshot_id) REFERENCES snapshots(snapshot_id),
    UNIQUE(evaluation_id)
)
"""

REQUIRED_BACKTEST_INDEX_SQL = (
    """
    CREATE INDEX IF NOT EXISTS idx_backtest_runs_created_at
    ON backtest_runs(created_at)
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_backtest_runs_timeframe_dates
    ON backtest_runs(timeframe, start_date, end_date)
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_backtest_evaluations_run_sequence
    ON backtest_evaluations(run_id, sequence_number)
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_backtest_evaluations_run_snapshot
    ON backtest_evaluations(run_id, snapshot_id)
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_backtest_evaluations_snapshot_id
    ON backtest_evaluations(snapshot_id)
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_backtest_trade_results_run_evaluation
    ON backtest_trade_results(run_id, evaluation_id)
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_backtest_trade_results_run_status_outcome
    ON backtest_trade_results(run_id, simulation_status, trade_outcome)
    """,
)

BACKTEST_SCHEMA_SQL = (
    CREATE_BACKTEST_RUNS_TABLE_SQL,
    CREATE_BACKTEST_ASSUMPTIONS_TABLE_SQL,
    CREATE_BACKTEST_EVALUATIONS_TABLE_SQL,
    CREATE_BACKTEST_TRADE_RESULTS_TABLE_SQL,
    *REQUIRED_BACKTEST_INDEX_SQL,
)


def initialize_backtest_schema(connection: sqlite3.Connection) -> None:
    """Create Backtest-owned SQLite tables without touching source data tables."""

    connection.execute("PRAGMA foreign_keys = ON")
    for statement in BACKTEST_SCHEMA_SQL:
        connection.execute(statement)
    connection.commit()
