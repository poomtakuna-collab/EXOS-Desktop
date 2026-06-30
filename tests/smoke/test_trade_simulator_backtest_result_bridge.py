from __future__ import annotations

import unittest

from src.backtest import (
    BacktestResultV1,
    TradeOutcomeV1,
    generate_backtest_result,
    simulate_trade,
)


class TradeSimulatorBacktestResultBridgeSmokeTest(unittest.TestCase):
    def test_simulated_trades_feed_backtest_result_engine(self) -> None:
        outcomes = [
            simulate_trade(_trade_setup(), [_ohlcv(high=106.0, low=99.0, close=105.0)]),
            simulate_trade(_trade_setup(), [_ohlcv(high=102.0, low=94.0, close=95.0)]),
            simulate_trade(_trade_setup(), [_ohlcv(high=104.0, low=96.0, close=101.0)]),
        ]
        result = generate_backtest_result(
            [outcome.gross_return_percent for outcome in outcomes]
        )

        self.assertTrue(all(isinstance(outcome, TradeOutcomeV1) for outcome in outcomes))
        self.assertIsInstance(result, BacktestResultV1)
        self.assertEqual(result.total_trades, 3)
        self.assertEqual(result.winning_trades, 2)
        self.assertEqual(result.losing_trades, 1)
        self.assertEqual(result.net_return_percent, 1.0)


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
