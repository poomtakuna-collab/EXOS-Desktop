from __future__ import annotations

import unittest

from src.backtest import (
    BacktestResultV1,
    TradeOutcomeV1,
    generate_backtest_result,
    generate_trade_outcome,
)


class TradeOutcomeBacktestResultBridgeSmokeTest(unittest.TestCase):
    def test_trade_outcome_rows_feed_backtest_result_engine(self) -> None:
        outcomes = [
            generate_trade_outcome(row)
            for row in [
                _trade_row(entry_price=100.0, exit_price=110.0),
                _trade_row(entry_price=100.0, exit_price=95.0),
                _trade_row(entry_price=100.0, exit_price=100.0),
            ]
        ]
        result = generate_backtest_result(
            [outcome.gross_return_percent for outcome in outcomes]
        )

        self.assertTrue(all(isinstance(outcome, TradeOutcomeV1) for outcome in outcomes))
        self.assertIsInstance(result, BacktestResultV1)
        self.assertEqual(result.total_trades, 3)
        self.assertEqual(result.winning_trades, 1)
        self.assertEqual(result.losing_trades, 1)
        self.assertEqual(result.win_rate, 33.3333)
        self.assertEqual(result.net_return_percent, 5.0)
        self.assertEqual(result.average_return, 1.6667)


def _trade_row(entry_price: float, exit_price: float) -> dict[str, object]:
    return {
        "entry_price": entry_price,
        "exit_price": exit_price,
        "stop_price": entry_price * 0.95,
        "target_price": entry_price * 1.1,
        "position_size": 3,
    }


if __name__ == "__main__":
    unittest.main()
