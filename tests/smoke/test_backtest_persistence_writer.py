from __future__ import annotations

import sqlite3
import unittest

from src.backtest import (
    BACKTEST_PERSISTENCE_SCHEMA_SQL,
    BacktestEvaluationRecord,
    BacktestRunRecord,
    BacktestTradeResultRecord,
    write_backtest_evaluation_record,
    write_backtest_run_record,
    write_backtest_trade_result_record,
)


class BacktestPersistenceWriterSmokeTest(unittest.TestCase):
    def test_creates_schema_and_persists_run_evaluation_and_trade_result(self) -> None:
        with sqlite3.connect(":memory:") as connection:
            connection.execute("PRAGMA foreign_keys = ON")
            for statement in BACKTEST_PERSISTENCE_SCHEMA_SQL:
                connection.execute(statement)
            connection.commit()

            write_backtest_run_record(connection, _run_record())
            write_backtest_evaluation_record(connection, _evaluation_record())
            write_backtest_trade_result_record(connection, _trade_result_record())

            self.assertEqual(_count(connection, "backtest_runs"), 1)
            self.assertEqual(_count(connection, "backtest_evaluations"), 1)
            self.assertEqual(_count(connection, "backtest_trade_results"), 1)


def _count(connection: sqlite3.Connection, table_name: str) -> int:
    row = connection.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()
    return int(row[0])


def _run_record() -> BacktestRunRecord:
    return BacktestRunRecord(
        run_id="run-smoke-1",
        run_name="Smoke Run",
        source_database_path=":memory:",
        symbols_json='["MSFT"]',
        timeframe="1D",
        snapshot_query_json='{"symbol":"MSFT"}',
        attempted_trades=1,
        completed_trades=1,
        total_trades=1,
        winning_trades=1,
        win_rate=100.0,
        net_return_percent=3.0,
        average_return=3.0,
        profit_factor=float("inf"),
        expectancy=3.0,
        created_at="2026-06-30T01:00:00Z",
    )


def _evaluation_record() -> BacktestEvaluationRecord:
    return BacktestEvaluationRecord(
        evaluation_id="evaluation-smoke-1",
        run_id="run-smoke-1",
        sequence_number=1,
        snapshot_id="snapshot-smoke-1",
        symbol="MSFT",
        timeframe="1D",
        snapshot_date="2026-01-03",
        evaluation_status="EVALUATED",
        has_future_rows=True,
        future_rows_count=5,
        strategy_result_json="{}",
        probability_json="{}",
        prediction_json="{}",
        created_at="2026-06-30T01:01:00Z",
    )


def _trade_result_record() -> BacktestTradeResultRecord:
    return BacktestTradeResultRecord(
        trade_result_id="trade-smoke-1",
        run_id="run-smoke-1",
        evaluation_id="evaluation-smoke-1",
        snapshot_id="snapshot-smoke-1",
        entry_price=100.0,
        exit_price=103.0,
        stop_price=95.0,
        target_price=103.0,
        position_size=4.0,
        gross_return_percent=3.0,
        gross_pnl=12.0,
        risk_amount=20.0,
        reward_amount=12.0,
        outcome_label="Win",
        notes_json="[]",
        created_at="2026-06-30T01:02:00Z",
    )


if __name__ == "__main__":
    unittest.main()
