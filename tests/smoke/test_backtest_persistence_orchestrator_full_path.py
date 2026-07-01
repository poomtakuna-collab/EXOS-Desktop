from __future__ import annotations

from contextlib import closing
import sqlite3
import unittest

from src.backtest import (
    BACKTEST_PERSISTENCE_SCHEMA_SQL,
    build_validation_report,
    persist_backtest_run_v1,
    read_backtest_run_record,
    read_backtest_trade_result_records_by_run_id,
    run_backtest_v1,
)


class BacktestPersistenceOrchestratorFullPathSmokeTest(unittest.TestCase):
    def test_runner_to_validation_to_persistence_to_reader(self) -> None:
        with closing(sqlite3.connect(":memory:")) as connection:
            connection.execute("PRAGMA foreign_keys = ON")
            for statement in BACKTEST_PERSISTENCE_SCHEMA_SQL:
                connection.execute(statement)
            connection.commit()

            backtest_run = run_backtest_v1(
                [
                    {
                        "trade_setup": _trade_setup(),
                        "future_rows": [_ohlcv(high=106.0, low=99.0, close=105.0)],
                    },
                    {
                        "trade_setup": _trade_setup(),
                        "future_rows": [_ohlcv(high=102.0, low=94.0, close=95.0)],
                    },
                ]
            )
            validation_report = build_validation_report(backtest_run)
            summary = persist_backtest_run_v1(
                connection,
                backtest_run,
                validation_report,
                run_id="smoke-run",
                run_name="Smoke Persistence Run",
                created_at="2026-06-30T05:00:00Z",
            )
            run_record = read_backtest_run_record(connection, "smoke-run")
            trade_records = read_backtest_trade_result_records_by_run_id(
                connection,
                "smoke-run",
            )

            self.assertEqual(summary.run_records_written, 1)
            self.assertEqual(summary.evaluation_records_written, 2)
            self.assertEqual(summary.trade_result_records_written, 2)
            self.assertIsNotNone(run_record)
            self.assertEqual(run_record.total_trades, 2)
            self.assertEqual(run_record.winning_trades, 1)
            self.assertEqual(run_record.losing_trades, 1)
            self.assertEqual(
                [record.outcome_label for record in trade_records],
                ["Win", "Loss"],
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
