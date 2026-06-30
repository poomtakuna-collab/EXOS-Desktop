from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class BacktestRunRecord:
    run_id: str = ""
    run_name: str = ""
    backtest_version: str = "v1"
    strategy_version: str = "v1"
    simulation_version: str = "v1"
    source_database_path: str = ""
    symbols_json: str = "[]"
    timeframe: str = ""
    start_date: str = ""
    end_date: str = ""
    snapshot_query_json: str = "{}"
    attempted_trades: int = 0
    completed_trades: int = 0
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    skipped_trades: int = 0
    breakeven_trades: int = 0
    win_rate: float = 0.0
    net_return_percent: float = 0.0
    average_return: float = 0.0
    max_drawdown: float = 0.0
    profit_factor: float = 0.0
    expectancy: float = 0.0
    notes_json: str = "[]"
    created_at: str = ""


@dataclass(frozen=True)
class BacktestEvaluationRecord:
    evaluation_id: str = ""
    run_id: str = ""
    sequence_number: int = 0
    snapshot_id: str = ""
    symbol: str = ""
    timeframe: str = ""
    snapshot_date: str = ""
    outcome_id: str = ""
    evaluation_status: str = ""
    skip_reason: str = ""
    has_outcome: bool = False
    has_future_rows: bool = False
    future_rows_count: int = 0
    strategy_score: float = 0.0
    trade_grade: str = ""
    entry_quality: str = ""
    risk_rating: str = ""
    strategy_result_json: str = "{}"
    probability_json: str = "{}"
    prediction_json: str = "{}"
    created_at: str = ""


@dataclass(frozen=True)
class BacktestTradeResultRecord:
    trade_result_id: str = ""
    run_id: str = ""
    evaluation_id: str = ""
    snapshot_id: str = ""
    entry_price: float = 0.0
    exit_price: float = 0.0
    stop_price: float = 0.0
    target_price: float = 0.0
    position_size: float = 0.0
    gross_return_percent: float = 0.0
    gross_pnl: float = 0.0
    risk_amount: float = 0.0
    reward_amount: float = 0.0
    outcome_label: str = ""
    notes_json: str = "[]"
    created_at: str = ""
