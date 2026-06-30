from src.backtest.contracts import (
    BacktestInput,
    BacktestReport,
    BacktestResult,
    SimulationConfig,
    SimulationResult,
    SimulationRule,
)
from src.backtest.backtest_runner import BacktestRunV1, run_backtest_v1
from src.backtest.db_runner import SQLiteBacktestRun, run_sqlite_backtest_read_only
from src.backtest.engine import replay_trade
from src.backtest.metrics import analyze_backtest_results
from src.backtest.persistence_contracts import (
    BacktestEvaluationRecord,
    BacktestRunRecord,
    BacktestTradeResultRecord,
)
from src.backtest.persistence_schema import (
    BACKTEST_PERSISTENCE_SCHEMA_SQL,
    CREATE_BACKTEST_EVALUATIONS_PERSISTENCE_TABLE_SQL,
    CREATE_BACKTEST_RUNS_PERSISTENCE_TABLE_SQL,
    CREATE_BACKTEST_TRADE_RESULTS_PERSISTENCE_TABLE_SQL,
)
from src.backtest.persistence_reader import (
    read_backtest_evaluation_record,
    read_backtest_run_record,
    read_backtest_trade_result_records_by_run_id,
)
from src.backtest.persistence_orchestrator import (
    BacktestPersistenceSummaryV1,
    build_backtest_evaluation_record,
    build_backtest_run_record,
    build_backtest_trade_result_record,
    persist_backtest_run_v1,
)
from src.backtest.persistence_writer import (
    BACKTEST_EVALUATION_RECORD_COLUMNS,
    BACKTEST_RUN_RECORD_COLUMNS,
    BACKTEST_TRADE_RESULT_RECORD_COLUMNS,
    write_backtest_evaluation_record,
    write_backtest_run_record,
    write_backtest_trade_result_record,
)
from src.backtest.pipeline import run_backtest
from src.backtest.report import build_backtest_report
from src.backtest.result_engine import BacktestResultV1, generate_backtest_result
from src.backtest.trade_simulator import simulate_trade
from src.backtest.trade_outcome import TradeOutcomeV1, generate_trade_outcome
from src.backtest.types import ExitReason, SimulationStatus, TradeOutcome
from src.backtest.validation_report import (
    ValidationReportV1,
    build_validation_report,
)

__all__ = [
    "BacktestInput",
    "BacktestReport",
    "BacktestEvaluationRecord",
    "BacktestPersistenceSummaryV1",
    "BacktestResultV1",
    "BacktestRunRecord",
    "BacktestRunV1",
    "BacktestResult",
    "BacktestTradeResultRecord",
    "BACKTEST_EVALUATION_RECORD_COLUMNS",
    "BACKTEST_PERSISTENCE_SCHEMA_SQL",
    "BACKTEST_RUN_RECORD_COLUMNS",
    "BACKTEST_TRADE_RESULT_RECORD_COLUMNS",
    "CREATE_BACKTEST_EVALUATIONS_PERSISTENCE_TABLE_SQL",
    "CREATE_BACKTEST_RUNS_PERSISTENCE_TABLE_SQL",
    "CREATE_BACKTEST_TRADE_RESULTS_PERSISTENCE_TABLE_SQL",
    "ExitReason",
    "SimulationConfig",
    "SimulationResult",
    "SimulationRule",
    "SimulationStatus",
    "SQLiteBacktestRun",
    "TradeOutcome",
    "TradeOutcomeV1",
    "ValidationReportV1",
    "analyze_backtest_results",
    "build_backtest_report",
    "build_backtest_evaluation_record",
    "build_backtest_run_record",
    "build_backtest_trade_result_record",
    "build_validation_report",
    "generate_backtest_result",
    "generate_trade_outcome",
    "replay_trade",
    "read_backtest_evaluation_record",
    "read_backtest_run_record",
    "read_backtest_trade_result_records_by_run_id",
    "persist_backtest_run_v1",
    "run_backtest",
    "run_backtest_v1",
    "run_sqlite_backtest_read_only",
    "simulate_trade",
    "write_backtest_evaluation_record",
    "write_backtest_run_record",
    "write_backtest_trade_result_record",
]
