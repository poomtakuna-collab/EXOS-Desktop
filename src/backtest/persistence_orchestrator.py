from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass

from src.backtest.backtest_runner import BacktestRunV1
from src.backtest.persistence_contracts import (
    BacktestEvaluationRecord,
    BacktestRunRecord,
    BacktestTradeResultRecord,
)
from src.backtest.persistence_writer import (
    write_backtest_evaluation_record,
    write_backtest_run_record,
    write_backtest_trade_result_record,
)
from src.backtest.trade_outcome import TradeOutcomeV1
from src.backtest.validation_report import ValidationReportV1


@dataclass(frozen=True)
class BacktestPersistenceSummaryV1:
    run_id: str
    run_records_written: int
    evaluation_records_written: int
    trade_result_records_written: int
    notes: list[str]


def persist_backtest_run_v1(
    connection: sqlite3.Connection,
    backtest_run: BacktestRunV1,
    validation_report: ValidationReportV1,
    *,
    run_id: str = "backtest-run-v1",
    run_name: str = "",
    source_database_path: str = "",
    symbols_json: str = "[]",
    timeframe: str = "",
    start_date: str = "",
    end_date: str = "",
    snapshot_query_json: str = "{}",
    created_at: str = "",
) -> BacktestPersistenceSummaryV1:
    run_record = build_backtest_run_record(
        backtest_run=backtest_run,
        validation_report=validation_report,
        run_id=run_id,
        run_name=run_name,
        source_database_path=source_database_path,
        symbols_json=symbols_json,
        timeframe=timeframe,
        start_date=start_date,
        end_date=end_date,
        snapshot_query_json=snapshot_query_json,
        created_at=created_at,
    )
    evaluation_records = [
        build_backtest_evaluation_record(
            trade=trade,
            run_id=run_id,
            sequence_number=index,
            created_at=created_at,
        )
        for index, trade in enumerate(backtest_run.trades, start=1)
    ]
    trade_result_records = [
        build_backtest_trade_result_record(
            trade=trade,
            run_id=run_id,
            sequence_number=index,
            created_at=created_at,
        )
        for index, trade in enumerate(backtest_run.trades, start=1)
    ]

    write_backtest_run_record(connection, run_record)
    for record in evaluation_records:
        write_backtest_evaluation_record(connection, record)
    for record in trade_result_records:
        write_backtest_trade_result_record(connection, record)

    return BacktestPersistenceSummaryV1(
        run_id=run_id,
        run_records_written=1,
        evaluation_records_written=len(evaluation_records),
        trade_result_records_written=len(trade_result_records),
        notes=["BacktestRunV1 persisted with ValidationReportV1 context."],
    )


def build_backtest_run_record(
    backtest_run: BacktestRunV1,
    validation_report: ValidationReportV1,
    *,
    run_id: str,
    run_name: str = "",
    source_database_path: str = "",
    symbols_json: str = "[]",
    timeframe: str = "",
    start_date: str = "",
    end_date: str = "",
    snapshot_query_json: str = "{}",
    created_at: str = "",
) -> BacktestRunRecord:
    result = backtest_run.result
    return BacktestRunRecord(
        run_id=run_id,
        run_name=run_name,
        source_database_path=source_database_path,
        symbols_json=symbols_json,
        timeframe=timeframe,
        start_date=start_date,
        end_date=end_date,
        snapshot_query_json=snapshot_query_json,
        attempted_trades=len(backtest_run.trades),
        completed_trades=_valid_trade_count(backtest_run.trades),
        total_trades=result.total_trades,
        winning_trades=result.winning_trades,
        losing_trades=result.losing_trades,
        skipped_trades=0,
        breakeven_trades=_label_count(backtest_run.trades, "Breakeven"),
        win_rate=result.win_rate,
        net_return_percent=result.net_return_percent,
        average_return=result.average_return,
        max_drawdown=result.max_drawdown,
        profit_factor=result.profit_factor,
        expectancy=result.expectancy,
        notes_json=_notes_json(validation_report.notes),
        created_at=created_at,
    )


def build_backtest_evaluation_record(
    trade: TradeOutcomeV1,
    *,
    run_id: str,
    sequence_number: int,
    created_at: str = "",
) -> BacktestEvaluationRecord:
    return BacktestEvaluationRecord(
        evaluation_id=_evaluation_id(run_id, sequence_number),
        run_id=run_id,
        sequence_number=sequence_number,
        snapshot_id=_snapshot_id(run_id, sequence_number),
        evaluation_status=(
            "INVALID" if trade.outcome_label == "Invalid" else "EVALUATED"
        ),
        skip_reason=(
            "Invalid trade outcome" if trade.outcome_label == "Invalid" else ""
        ),
        has_future_rows=False,
        future_rows_count=0,
        created_at=created_at,
    )


def build_backtest_trade_result_record(
    trade: TradeOutcomeV1,
    *,
    run_id: str,
    sequence_number: int,
    created_at: str = "",
) -> BacktestTradeResultRecord:
    return BacktestTradeResultRecord(
        trade_result_id=_trade_result_id(run_id, sequence_number),
        run_id=run_id,
        evaluation_id=_evaluation_id(run_id, sequence_number),
        snapshot_id=_snapshot_id(run_id, sequence_number),
        entry_price=trade.entry_price,
        exit_price=trade.exit_price,
        stop_price=trade.stop_price,
        target_price=trade.target_price,
        position_size=trade.position_size,
        gross_return_percent=trade.gross_return_percent,
        gross_pnl=trade.gross_pnl,
        risk_amount=trade.risk_amount,
        reward_amount=trade.reward_amount,
        outcome_label=trade.outcome_label,
        created_at=created_at,
    )


def _valid_trade_count(trades: list[TradeOutcomeV1]) -> int:
    return len([trade for trade in trades if trade.outcome_label != "Invalid"])


def _label_count(trades: list[TradeOutcomeV1], label: str) -> int:
    return len([trade for trade in trades if trade.outcome_label == label])


def _notes_json(notes: list[str]) -> str:
    return json.dumps(list(notes), sort_keys=True)


def _evaluation_id(run_id: str, sequence_number: int) -> str:
    return f"{run_id}:evaluation:{sequence_number:04d}"


def _trade_result_id(run_id: str, sequence_number: int) -> str:
    return f"{run_id}:trade:{sequence_number:04d}"


def _snapshot_id(run_id: str, sequence_number: int) -> str:
    return f"{run_id}:snapshot:{sequence_number:04d}"
