from __future__ import annotations

from contextlib import closing
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


class BacktestPersistenceReaderTest(unittest.TestCase):
    def test_reads_backtest_run_record_by_run_id(self) -> None:
        with closing(_connection()) as connection:
            record = _run_record()
            write_backtest_run_record(connection, record)

            fetched = read_backtest_run_record(connection, "run-1")

            self.assertEqual(fetched, record)

    def test_missing_backtest_run_record_returns_none(self) -> None:
        with closing(_connection()) as connection:
            self.assertIsNone(read_backtest_run_record(connection, "missing-run"))

    def test_reads_backtest_evaluation_record_by_evaluation_id(self) -> None:
        with closing(_connection()) as connection:
            write_backtest_run_record(connection, _run_record())
            record = _evaluation_record("evaluation-1", 1)
            write_backtest_evaluation_record(connection, record)

            fetched = read_backtest_evaluation_record(connection, "evaluation-1")

            self.assertEqual(fetched, record)
            self.assertIsInstance(fetched, BacktestEvaluationRecord)
            self.assertIs(fetched.has_outcome, True)
            self.assertIs(fetched.has_future_rows, True)

    def test_missing_backtest_evaluation_record_returns_none(self) -> None:
        with closing(_connection()) as connection:
            self.assertIsNone(
                read_backtest_evaluation_record(connection, "missing-evaluation")
            )

    def test_reads_trade_result_records_by_run_id_in_deterministic_order(self) -> None:
        with closing(_connection()) as connection:
            write_backtest_run_record(connection, _run_record())
            first_evaluation = _evaluation_record("evaluation-1", 1)
            second_evaluation = _evaluation_record("evaluation-2", 2)
            first_trade = _trade_result_record("trade-b", "evaluation-1", 5.0)
            second_trade = _trade_result_record("trade-a", "evaluation-2", -2.0)
            write_backtest_evaluation_record(connection, first_evaluation)
            write_backtest_evaluation_record(connection, second_evaluation)
            write_backtest_trade_result_record(connection, first_trade)
            write_backtest_trade_result_record(connection, second_trade)

            fetched = read_backtest_trade_result_records_by_run_id(connection, "run-1")

            self.assertEqual(
                [record.trade_result_id for record in fetched],
                ["trade-a", "trade-b"],
            )
            self.assertEqual(
                fetched,
                [second_trade, first_trade],
            )

    def test_missing_trade_result_records_by_run_id_returns_empty_list(self) -> None:
        with closing(_connection()) as connection:
            self.assertEqual(
                read_backtest_trade_result_records_by_run_id(connection, "missing-run"),
                [],
            )

    def test_reader_returns_contract_types(self) -> None:
        with closing(_connection()) as connection:
            write_backtest_run_record(connection, _run_record())
            write_backtest_evaluation_record(
                connection,
                _evaluation_record("evaluation-1", 1),
            )
            write_backtest_trade_result_record(
                connection,
                _trade_result_record("trade-1", "evaluation-1", 5.0),
            )

            self.assertIsInstance(
                read_backtest_run_record(connection, "run-1"),
                BacktestRunRecord,
            )
            self.assertIsInstance(
                read_backtest_evaluation_record(connection, "evaluation-1"),
                BacktestEvaluationRecord,
            )
            self.assertTrue(
                all(
                    isinstance(record, BacktestTradeResultRecord)
                    for record in read_backtest_trade_result_records_by_run_id(
                        connection,
                        "run-1",
                    )
                )
            )


def _connection() -> sqlite3.Connection:
    connection = sqlite3.connect(":memory:")
    connection.execute("PRAGMA foreign_keys = ON")
    for statement in BACKTEST_PERSISTENCE_SCHEMA_SQL:
        connection.execute(statement)
    connection.commit()
    return connection


def _run_record() -> BacktestRunRecord:
    return BacktestRunRecord(
        run_id="run-1",
        run_name="Reader Test Run",
        source_database_path=":memory:",
        symbols_json='["AAPL"]',
        timeframe="1D",
        start_date="2026-01-01",
        end_date="2026-01-31",
        snapshot_query_json='{"symbol":"AAPL"}',
        attempted_trades=2,
        completed_trades=2,
        total_trades=2,
        winning_trades=1,
        losing_trades=1,
        win_rate=50.0,
        net_return_percent=3.0,
        average_return=1.5,
        max_drawdown=-2.0,
        profit_factor=2.5,
        expectancy=1.5,
        notes_json='["reader"]',
        created_at="2026-06-30T02:00:00Z",
    )


def _evaluation_record(
    evaluation_id: str,
    sequence_number: int,
) -> BacktestEvaluationRecord:
    return BacktestEvaluationRecord(
        evaluation_id=evaluation_id,
        run_id="run-1",
        sequence_number=sequence_number,
        snapshot_id=f"snapshot-{sequence_number}",
        symbol="AAPL",
        timeframe="1D",
        snapshot_date=f"2026-01-0{sequence_number}",
        outcome_id=f"outcome-{sequence_number}",
        evaluation_status="EVALUATED",
        has_outcome=True,
        has_future_rows=True,
        future_rows_count=10,
        strategy_score=70.0 + sequence_number,
        trade_grade="Good",
        entry_quality="Good",
        risk_rating="Medium",
        strategy_result_json='{"strategy_score":70}',
        probability_json='{"confidence":75}',
        prediction_json='{"target":105}',
        created_at=f"2026-06-30T02:0{sequence_number}:00Z",
    )


def _trade_result_record(
    trade_result_id: str,
    evaluation_id: str,
    gross_return_percent: float,
) -> BacktestTradeResultRecord:
    return BacktestTradeResultRecord(
        trade_result_id=trade_result_id,
        run_id="run-1",
        evaluation_id=evaluation_id,
        snapshot_id=f"snapshot-{evaluation_id[-1]}",
        entry_price=100.0,
        exit_price=100.0 + gross_return_percent,
        stop_price=95.0,
        target_price=105.0,
        position_size=10.0,
        gross_return_percent=gross_return_percent,
        gross_pnl=gross_return_percent * 10,
        risk_amount=50.0,
        reward_amount=50.0,
        outcome_label="Win" if gross_return_percent > 0 else "Loss",
        notes_json="[]",
        created_at=f"2026-06-30T02:1{evaluation_id[-1]}:00Z",
    )


if __name__ == "__main__":
    unittest.main()
