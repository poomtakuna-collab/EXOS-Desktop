from __future__ import annotations

import unittest
from dataclasses import FrozenInstanceError

from src.backtest import (
    BacktestEvaluationRecord,
    BacktestRunRecord,
    BacktestTradeResultRecord,
)


class BacktestPersistenceContractsTest(unittest.TestCase):
    def test_run_record_defaults_are_deterministic(self) -> None:
        record = BacktestRunRecord()

        self.assertEqual(record.run_id, "")
        self.assertEqual(record.backtest_version, "v1")
        self.assertEqual(record.strategy_version, "v1")
        self.assertEqual(record.simulation_version, "v1")
        self.assertEqual(record.symbols_json, "[]")
        self.assertEqual(record.snapshot_query_json, "{}")
        self.assertEqual(record.total_trades, 0)
        self.assertEqual(record.net_return_percent, 0.0)
        self.assertEqual(record.profit_factor, 0.0)
        self.assertEqual(record.notes_json, "[]")
        self.assertEqual(record.created_at, "")

    def test_evaluation_record_defaults_are_deterministic(self) -> None:
        record = BacktestEvaluationRecord()

        self.assertEqual(record.evaluation_id, "")
        self.assertEqual(record.run_id, "")
        self.assertEqual(record.sequence_number, 0)
        self.assertEqual(record.snapshot_id, "")
        self.assertEqual(record.evaluation_status, "")
        self.assertFalse(record.has_outcome)
        self.assertFalse(record.has_future_rows)
        self.assertEqual(record.future_rows_count, 0)
        self.assertEqual(record.strategy_result_json, "{}")
        self.assertEqual(record.probability_json, "{}")
        self.assertEqual(record.prediction_json, "{}")
        self.assertEqual(record.created_at, "")

    def test_trade_result_record_defaults_are_deterministic(self) -> None:
        record = BacktestTradeResultRecord()

        self.assertEqual(record.trade_result_id, "")
        self.assertEqual(record.run_id, "")
        self.assertEqual(record.evaluation_id, "")
        self.assertEqual(record.snapshot_id, "")
        self.assertEqual(record.entry_price, 0.0)
        self.assertEqual(record.exit_price, 0.0)
        self.assertEqual(record.stop_price, 0.0)
        self.assertEqual(record.target_price, 0.0)
        self.assertEqual(record.position_size, 0.0)
        self.assertEqual(record.gross_return_percent, 0.0)
        self.assertEqual(record.gross_pnl, 0.0)
        self.assertEqual(record.risk_amount, 0.0)
        self.assertEqual(record.reward_amount, 0.0)
        self.assertEqual(record.outcome_label, "")
        self.assertEqual(record.notes_json, "[]")
        self.assertEqual(record.created_at, "")

    def test_record_shapes_are_stable(self) -> None:
        self.assertEqual(
            set(BacktestRunRecord().__dict__),
            {
                "run_id",
                "run_name",
                "backtest_version",
                "strategy_version",
                "simulation_version",
                "source_database_path",
                "symbols_json",
                "timeframe",
                "start_date",
                "end_date",
                "snapshot_query_json",
                "attempted_trades",
                "completed_trades",
                "total_trades",
                "winning_trades",
                "losing_trades",
                "skipped_trades",
                "breakeven_trades",
                "win_rate",
                "net_return_percent",
                "average_return",
                "max_drawdown",
                "profit_factor",
                "expectancy",
                "notes_json",
                "created_at",
            },
        )
        self.assertEqual(
            set(BacktestEvaluationRecord().__dict__),
            {
                "evaluation_id",
                "run_id",
                "sequence_number",
                "snapshot_id",
                "symbol",
                "timeframe",
                "snapshot_date",
                "outcome_id",
                "evaluation_status",
                "skip_reason",
                "has_outcome",
                "has_future_rows",
                "future_rows_count",
                "strategy_score",
                "trade_grade",
                "entry_quality",
                "risk_rating",
                "strategy_result_json",
                "probability_json",
                "prediction_json",
                "created_at",
            },
        )
        self.assertEqual(
            set(BacktestTradeResultRecord().__dict__),
            {
                "trade_result_id",
                "run_id",
                "evaluation_id",
                "snapshot_id",
                "entry_price",
                "exit_price",
                "stop_price",
                "target_price",
                "position_size",
                "gross_return_percent",
                "gross_pnl",
                "risk_amount",
                "reward_amount",
                "outcome_label",
                "notes_json",
                "created_at",
            },
        )

    def test_records_are_frozen(self) -> None:
        with self.assertRaises(FrozenInstanceError):
            BacktestRunRecord().run_id = "changed"  # type: ignore[misc]

        with self.assertRaises(FrozenInstanceError):
            BacktestEvaluationRecord().run_id = "changed"  # type: ignore[misc]

        with self.assertRaises(FrozenInstanceError):
            BacktestTradeResultRecord().run_id = "changed"  # type: ignore[misc]

    def test_records_accept_explicit_values_without_side_effects(self) -> None:
        run_record = BacktestRunRecord(
            run_id="run-1",
            total_trades=2,
            winning_trades=1,
            losing_trades=1,
            net_return_percent=1.5,
        )
        evaluation_record = BacktestEvaluationRecord(
            evaluation_id="eval-1",
            run_id="run-1",
            sequence_number=1,
            snapshot_id="snapshot-1",
            has_future_rows=True,
            future_rows_count=10,
        )
        trade_record = BacktestTradeResultRecord(
            trade_result_id="trade-1",
            run_id="run-1",
            evaluation_id="eval-1",
            snapshot_id="snapshot-1",
            gross_return_percent=5.0,
            outcome_label="Win",
        )

        self.assertEqual(run_record.run_id, "run-1")
        self.assertEqual(run_record.net_return_percent, 1.5)
        self.assertEqual(evaluation_record.sequence_number, 1)
        self.assertTrue(evaluation_record.has_future_rows)
        self.assertEqual(trade_record.gross_return_percent, 5.0)
        self.assertEqual(trade_record.outcome_label, "Win")


if __name__ == "__main__":
    unittest.main()
