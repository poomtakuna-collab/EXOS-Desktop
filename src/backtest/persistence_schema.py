from __future__ import annotations


CREATE_BACKTEST_RUNS_PERSISTENCE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS backtest_runs (
    run_id TEXT PRIMARY KEY,
    run_name TEXT NOT NULL,
    backtest_version TEXT NOT NULL,
    strategy_version TEXT NOT NULL,
    simulation_version TEXT NOT NULL,
    source_database_path TEXT NOT NULL,
    symbols_json TEXT NOT NULL,
    timeframe TEXT NOT NULL,
    start_date TEXT NOT NULL,
    end_date TEXT NOT NULL,
    snapshot_query_json TEXT NOT NULL,
    attempted_trades INTEGER NOT NULL,
    completed_trades INTEGER NOT NULL,
    total_trades INTEGER NOT NULL,
    winning_trades INTEGER NOT NULL,
    losing_trades INTEGER NOT NULL,
    skipped_trades INTEGER NOT NULL,
    breakeven_trades INTEGER NOT NULL,
    win_rate REAL NOT NULL,
    net_return_percent REAL NOT NULL,
    average_return REAL NOT NULL,
    max_drawdown REAL NOT NULL,
    profit_factor REAL NOT NULL,
    expectancy REAL NOT NULL,
    notes_json TEXT NOT NULL,
    created_at TEXT NOT NULL
)
"""

CREATE_BACKTEST_EVALUATIONS_PERSISTENCE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS backtest_evaluations (
    evaluation_id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL,
    sequence_number INTEGER NOT NULL,
    snapshot_id TEXT NOT NULL,
    symbol TEXT NOT NULL,
    timeframe TEXT NOT NULL,
    snapshot_date TEXT NOT NULL,
    outcome_id TEXT NOT NULL,
    evaluation_status TEXT NOT NULL,
    skip_reason TEXT NOT NULL,
    has_outcome INTEGER NOT NULL,
    has_future_rows INTEGER NOT NULL,
    future_rows_count INTEGER NOT NULL,
    strategy_score REAL NOT NULL,
    trade_grade TEXT NOT NULL,
    entry_quality TEXT NOT NULL,
    risk_rating TEXT NOT NULL,
    strategy_result_json TEXT NOT NULL,
    probability_json TEXT NOT NULL,
    prediction_json TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY(run_id) REFERENCES backtest_runs(run_id),
    UNIQUE(run_id, sequence_number)
)
"""

CREATE_BACKTEST_TRADE_RESULTS_PERSISTENCE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS backtest_trade_results (
    trade_result_id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL,
    evaluation_id TEXT NOT NULL,
    snapshot_id TEXT NOT NULL,
    entry_price REAL NOT NULL,
    exit_price REAL NOT NULL,
    stop_price REAL NOT NULL,
    target_price REAL NOT NULL,
    position_size REAL NOT NULL,
    gross_return_percent REAL NOT NULL,
    gross_pnl REAL NOT NULL,
    risk_amount REAL NOT NULL,
    reward_amount REAL NOT NULL,
    outcome_label TEXT NOT NULL,
    notes_json TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY(run_id) REFERENCES backtest_runs(run_id),
    FOREIGN KEY(evaluation_id) REFERENCES backtest_evaluations(evaluation_id),
    UNIQUE(evaluation_id)
)
"""

BACKTEST_PERSISTENCE_SCHEMA_SQL = (
    CREATE_BACKTEST_RUNS_PERSISTENCE_TABLE_SQL,
    CREATE_BACKTEST_EVALUATIONS_PERSISTENCE_TABLE_SQL,
    CREATE_BACKTEST_TRADE_RESULTS_PERSISTENCE_TABLE_SQL,
)
