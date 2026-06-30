from __future__ import annotations

import sqlite3
import unittest

from src.backtest import (
    BACKTEST_EVALUATION_RECORD_COLUMNS,
    BACKTEST_PERSISTENCE_SCHEMA_SQL,
    BACKTEST_RUN_RECORD_COLUMNS,
    BACKTEST_TRADE_RESULT_RECORD_COLUMNS,
    BacktestEvaluationRecord,
    BacktestRunRecord,
    BacktestTradeResultRecord,
    write_backtest_evaluation_record,
    write_backtest_run_record,
    write_backtest_trade_result_record,
)


class BacktestPersistenceWriterTest(unittest.TestCase):
    def test_writer_column_lists_match_contract_shapes(self) -> None:
        self.assertEqual(
            set(BACKTEST_RUN_RECORD_COLUMNS),
            set(BacktestRunRecord().__dict__),
        )
        self.assertEqual(
            set(BACKTEST_EVALUATION_RECORD_COLUMNS),
            set(BacktestEvaluationRecord().__dict__),
        )
        self.assertEqual(
            set(BACKTEST_TRADE_RESULT_RECORD_COLUMNS),
            set(BacktestTradeResultRecord().__dict__),
        )

    def test_writes_backtest_run_record(self) -> None:
        with _connection() as connection:
            record = _run_record()

            write_backtest_run_record(connection, record)

            row = _row_by_id(connection, "backtest_runs", "run_id", record.run_id)
            self.assertEqual(row["run_id"], "run-1")
            self.assertEqual(row["total_trades"], 1)
            self.assertEqual(row["net_return_percent"], 5.0)
            self.assertEqual(row["profit_factor"], 2.5)

    def test_writes_backtest_evaluation_record(self) -> None:
        with _connection() as connection:
            write_backtest_run_record(connection, _run_record())
            record = _evaluation_record()

            write_backtest_evaluation_record(connection, record)

            row = _row_by_id(
                connection,
                "backtest_evaluations",
                "evaluation_id",
                record.evaluation_id,
            )
            self.assertEqual(row["evaluation_id"], "evaluation-1")
            self.assertEqual(row["sequence_number"], 1)
            self.assertEqual(row["has_outcome"], 1)
            self.assertEqual(row["has_future_rows"], 1)

    def test_writes_backtest_trade_result_record(self) -> None:
        with _connection() as connection:
            write_backtest_run_record(connection, _run_record())
            write_backtest_evaluation_record(connection, _evaluation_record())
            record = _trade_result_record()

            write_backtest_trade_result_record(connection, record)

            row = _row_by_id(
                connection,
                "backtest_trade_results",
                "trade_result_id",
                record.trade_result_id,
            )
            self.assertEqual(row["trade_result_id"], "trade-1")
            self.assertEqual(row["gross_return_percent"], 5.0)
            self.assertEqual(row["gross_pnl"], 50.0)
            self.assertEqual(row["outcome_label"], "Win")

    def test_duplicate_primary_key_raises_sqlite_integrity_error(self) -> None:
        with _connection() as connection:
            record = _run_record()
            write_backtest_run_record(connection, record)

            with self.assertRaises(sqlite3.IntegrityError):
                write_backtest_run_record(connection, record)

    def test_trade_result_requires_existing_evaluation_when_foreign_keys_are_on(self) -> None:
        with _connection() as connection:
            write_backtest_run_record(connection, _run_record())

            with self.assertRaises(sqlite3.IntegrityError):
                write_backtest_trade_result_record(
                    connection,
                    _trade_result_record(),
                )


def _connection() -> sqlite3.Connection:
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    for statement in BACKTEST_PERSISTENCE_SCHEMA_SQL:
        connection.execute(statement)
    connection.commit()
    return connection


def _row_by_id(
    connection: sqlite3.Connection,
    table_name: str,
    key_name: str,
    key_value: str,
) -> sqlite3.Row:
    return connection.execute(
        f"SELECT * FROM {table_name} WHERE {key_name} = ?",
        (key_value,),
    ).fetchone()


def _run_record() -> BacktestRunRecord:
    return BacktestRunRecord(
        run_id="run-1",
        run_name="Unit Test Run",
        source_database_path=":memory:",
        symbols_json='["AAPL"]',
        timeframe="1D",
        start_date="2026-01-01",
        end_date="2026-01-31",
        snapshot_query_json='{"symbol":"AAPL"}',
        attempted_trades=1,
        completed_trades=1,
        total_trades=1,
        winning_trades=1,
        win_rate=100.0,
        net_return_percent=5.0,
        average_return=5.0,
        profit_factor=2.5,
        expectancy=5.0,
        notes_json='["ok"]',
        created_at="2026-06-30T00:00:00Z",
    )


def _evaluation_record() -> BacktestEvaluationRecord:
    return BacktestEvaluationRecord(
        evaluation_id="evaluation-1",
        run_id="run-1",
        sequence_number=1,
        snapshot_id="snapshot-1",
        symbol="AAPL",
        timeframe="1D",
        snapshot_date="2026-01-02",
        outcome_id="outcome-1",
        evaluation_status="EVALUATED",
        has_outcome=True,
        has_future_rows=True,
        future_rows_count=10,
        strategy_score=72.5,
        trade_grade="Good",
        entry_quality="Good",
        risk_rating="Medium",
        strategy_result_json='{"strategy_score":72.5}',
        probability_json='{"confidence":80}',
        prediction_json='{"target":105}',
        created_at="2026-06-30T00:01:00Z",
    )


def _trade_result_record() -> BacktestTradeResultRecord:
    return BacktestTradeResultRecord(
        trade_result_id="trade-1",
        run_id="run-1",
        evaluation_id="evaluation-1",
        snapshot_id="snapshot-1",
        entry_price=100.0,
        exit_price=105.0,
        stop_price=95.0,
        target_price=105.0,
        position_size=10.0,
        gross_return_percent=5.0,
        gross_pnl=50.0,
        risk_amount=50.0,
        reward_amount=50.0,
        outcome_label="Win",
        notes_json='["target hit"]',
        created_at="2026-06-30T00:02:00Z",
    )


if __name__ == "__main__":
    unittest.main()
