from __future__ import annotations

from contextlib import closing
import sqlite3
import unittest

from src.backtest import (
    BACKTEST_PERSISTENCE_SCHEMA_SQL,
    BacktestPersistenceSummaryV1,
    BacktestRunRecord,
    BacktestTradeResultRecord,
    build_backtest_evaluation_record,
    build_backtest_run_record,
    build_backtest_trade_result_record,
    build_validation_report,
    persist_backtest_run_v1,
    read_backtest_evaluation_record,
    read_backtest_run_record,
    read_backtest_trade_result_records_by_run_id,
    run_backtest_v1,
)


class BacktestPersistenceOrchestratorTest(unittest.TestCase):
    def test_builds_run_record_from_backtest_run_and_validation_report(self) -> None:
        backtest_run = _backtest_run()
        validation_report = build_validation_report(backtest_run)

        record = build_backtest_run_record(
            backtest_run=backtest_run,
            validation_report=validation_report,
            run_id="run-1",
            run_name="Orchestrator Unit Run",
            source_database_path=":memory:",
            symbols_json='["AAPL"]',
            timeframe="1D",
            start_date="2026-01-01",
            end_date="2026-01-31",
            snapshot_query_json='{"symbol":"AAPL"}',
            created_at="2026-06-30T04:00:00Z",
        )

        self.assertIsInstance(record, BacktestRunRecord)
        self.assertEqual(record.run_id, "run-1")
        self.assertEqual(record.attempted_trades, 2)
        self.assertEqual(record.completed_trades, 2)
        self.assertEqual(record.total_trades, backtest_run.result.total_trades)
        self.assertEqual(record.winning_trades, 2)
        self.assertEqual(record.net_return_percent, 6.0)
        self.assertIn("Validation report generated", record.notes_json)

    def test_builds_evaluation_record_with_deterministic_ids(self) -> None:
        trade = _backtest_run().trades[0]

        record = build_backtest_evaluation_record(
            trade,
            run_id="run-1",
            sequence_number=1,
            created_at="2026-06-30T04:00:00Z",
        )

        self.assertEqual(record.evaluation_id, "run-1:evaluation:0001")
        self.assertEqual(record.snapshot_id, "run-1:snapshot:0001")
        self.assertEqual(record.evaluation_status, "EVALUATED")
        self.assertEqual(record.skip_reason, "")
        self.assertFalse(record.has_future_rows)

    def test_builds_trade_result_record_from_trade_outcome(self) -> None:
        trade = _backtest_run().trades[0]

        record = build_backtest_trade_result_record(
            trade,
            run_id="run-1",
            sequence_number=1,
            created_at="2026-06-30T04:00:00Z",
        )

        self.assertIsInstance(record, BacktestTradeResultRecord)
        self.assertEqual(record.trade_result_id, "run-1:trade:0001")
        self.assertEqual(record.evaluation_id, "run-1:evaluation:0001")
        self.assertEqual(record.entry_price, trade.entry_price)
        self.assertEqual(record.gross_return_percent, trade.gross_return_percent)
        self.assertEqual(record.outcome_label, trade.outcome_label)

    def test_persists_run_evaluations_and_trade_results(self) -> None:
        with closing(_connection()) as connection:
            backtest_run = _backtest_run()
            validation_report = build_validation_report(backtest_run)

            summary = persist_backtest_run_v1(
                connection,
                backtest_run,
                validation_report,
                run_id="run-1",
                created_at="2026-06-30T04:00:00Z",
            )

            self.assertIsInstance(summary, BacktestPersistenceSummaryV1)
            self.assertEqual(summary.run_id, "run-1")
            self.assertEqual(summary.run_records_written, 1)
            self.assertEqual(summary.evaluation_records_written, 2)
            self.assertEqual(summary.trade_result_records_written, 2)
            self.assertIsNotNone(read_backtest_run_record(connection, "run-1"))
            self.assertIsNotNone(
                read_backtest_evaluation_record(
                    connection,
                    "run-1:evaluation:0001",
                )
            )
            self.assertEqual(
                len(read_backtest_trade_result_records_by_run_id(connection, "run-1")),
                2,
            )

    def test_empty_run_persists_only_run_record(self) -> None:
        with closing(_connection()) as connection:
            backtest_run = run_backtest_v1([])
            validation_report = build_validation_report(backtest_run)

            summary = persist_backtest_run_v1(
                connection,
                backtest_run,
                validation_report,
                run_id="empty-run",
            )

            self.assertEqual(summary.run_records_written, 1)
            self.assertEqual(summary.evaluation_records_written, 0)
            self.assertEqual(summary.trade_result_records_written, 0)
            self.assertEqual(
                read_backtest_trade_result_records_by_run_id(connection, "empty-run"),
                [],
            )

    def test_persistence_summary_shape_is_stable(self) -> None:
        with closing(_connection()) as connection:
            summary = persist_backtest_run_v1(
                connection,
                run_backtest_v1([]),
                build_validation_report(run_backtest_v1([])),
                run_id="shape-run",
            )

            self.assertEqual(
                set(summary.__dict__),
                {
                    "run_id",
                    "run_records_written",
                    "evaluation_records_written",
                    "trade_result_records_written",
                    "notes",
                },
            )

    def test_persistence_summary_is_deterministic(self) -> None:
        with closing(_connection()) as connection:
            summary = persist_backtest_run_v1(
                connection,
                run_backtest_v1([]),
                build_validation_report(run_backtest_v1([])),
                run_id="deterministic-run",
            )

            self.assertEqual(
                summary,
                BacktestPersistenceSummaryV1(
                    run_id="deterministic-run",
                    run_records_written=1,
                    evaluation_records_written=0,
                    trade_result_records_written=0,
                    notes=[
                        "BacktestRunV1 persisted with ValidationReportV1 context."
                    ],
                ),
            )


def _connection() -> sqlite3.Connection:
    connection = sqlite3.connect(":memory:")
    connection.execute("PRAGMA foreign_keys = ON")
    for statement in BACKTEST_PERSISTENCE_SCHEMA_SQL:
        connection.execute(statement)
    connection.commit()
    return connection


def _backtest_run():
    return run_backtest_v1(
        [
            {
                "trade_setup": _trade_setup(),
                "future_rows": [_ohlcv(high=106.0, low=99.0, close=105.0)],
            },
            {
                "trade_setup": _trade_setup(),
                "future_rows": [_ohlcv(high=104.0, low=96.0, close=101.0)],
            },
        ]
    )


def _trade_setup() -> dict[str, object]:
    return {
        "entry_price": 100.0,
        "stop_price": 95.0,
        "target_price": 105.0,
        "position_size": 10.0,
    }


def _ohlcv(high: float, low: float, close: float) -> dict[str, object]:
    return {
        "open": 100.0,
        "high": high,
        "low": low,
        "close": close,
        "volume": 1_000_000,
    }


if __name__ == "__main__":
    unittest.main()
