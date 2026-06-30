from __future__ import annotations

import sqlite3
import unittest

from src.backtest import (
    BACKTEST_PERSISTENCE_SCHEMA_SQL,
    BacktestEvaluationRecord,
    BacktestRunRecord,
    BacktestTradeResultRecord,
    read_backtest_evaluation_record,
    read_backtest_run_record,
    read_backtest_trade_result_records_by_run_id,
    write_backtest_evaluation_record,
    write_backtest_run_record,
    write_backtest_trade_result_record,
)


class BacktestPersistenceReaderWriterSmokeTest(unittest.TestCase):
    def test_writes_records_and_reads_them_back(self) -> None:
        with sqlite3.connect(":memory:") as connection:
            connection.execute("PRAGMA foreign_keys = ON")
            for statement in BACKTEST_PERSISTENCE_SCHEMA_SQL:
                connection.execute(statement)
            connection.commit()

            run_record = _run_record()
            evaluation_record = _evaluation_record()
            trade_record = _trade_result_record()

            write_backtest_run_record(connection, run_record)
            write_backtest_evaluation_record(connection, evaluation_record)
            write_backtest_trade_result_record(connection, trade_record)

            self.assertEqual(
                read_backtest_run_record(connection, run_record.run_id),
                run_record,
            )
            self.assertEqual(
                read_backtest_evaluation_record(
                    connection,
                    evaluation_record.evaluation_id,
                ),
                evaluation_record,
            )
            self.assertEqual(
                read_backtest_trade_result_records_by_run_id(
                    connection,
                    run_record.run_id,
                ),
                [trade_record],
            )


def _run_record() -> BacktestRunRecord:
    return BacktestRunRecord(
        run_id="run-smoke-reader-1",
        run_name="Reader Smoke Run",
        source_database_path=":memory:",
        symbols_json='["MSFT"]',
        timeframe="1D",
        snapshot_query_json='{"symbol":"MSFT"}',
        attempted_trades=1,
        completed_trades=1,
        total_trades=1,
        winning_trades=1,
        win_rate=100.0,
        net_return_percent=4.0,
        average_return=4.0,
        profit_factor=float("inf"),
        expectancy=4.0,
        created_at="2026-06-30T03:00:00Z",
    )


def _evaluation_record() -> BacktestEvaluationRecord:
    return BacktestEvaluationRecord(
        evaluation_id="evaluation-smoke-reader-1",
        run_id="run-smoke-reader-1",
        sequence_number=1,
        snapshot_id="snapshot-smoke-reader-1",
        symbol="MSFT",
        timeframe="1D",
        snapshot_date="2026-01-04",
        evaluation_status="EVALUATED",
        has_future_rows=True,
        future_rows_count=5,
        created_at="2026-06-30T03:01:00Z",
    )


def _trade_result_record() -> BacktestTradeResultRecord:
    return BacktestTradeResultRecord(
        trade_result_id="trade-smoke-reader-1",
        run_id="run-smoke-reader-1",
        evaluation_id="evaluation-smoke-reader-1",
        snapshot_id="snapshot-smoke-reader-1",
        entry_price=100.0,
        exit_price=104.0,
        stop_price=95.0,
        target_price=104.0,
        position_size=4.0,
        gross_return_percent=4.0,
        gross_pnl=16.0,
        risk_amount=20.0,
        reward_amount=16.0,
        outcome_label="Win",
        created_at="2026-06-30T03:02:00Z",
    )


if __name__ == "__main__":
    unittest.main()
