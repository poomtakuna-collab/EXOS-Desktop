from __future__ import annotations

import unittest

from src.backtest import BacktestRunV1, BacktestResultV1, TradeOutcomeV1, run_backtest_v1


class BacktestRunnerFullPathSmokeTest(unittest.TestCase):
    def test_full_runner_path_generates_trades_and_result(self) -> None:
        run = run_backtest_v1(
            [
                {
                    "trade_setup": _trade_setup(),
                    "future_rows": [_ohlcv(high=106.0, low=99.0, close=105.0)],
                },
                {
                    "trade_setup": _trade_setup(),
                    "future_rows": [_ohlcv(high=103.0, low=96.0, close=101.0)],
                },
            ]
        )

        self.assertIsInstance(run, BacktestRunV1)
        self.assertTrue(all(isinstance(trade, TradeOutcomeV1) for trade in run.trades))
        self.assertIsInstance(run.result, BacktestResultV1)
        self.assertEqual(len(run.trades), 2)
        self.assertEqual(run.result.total_trades, 2)
        self.assertEqual(run.result.winning_trades, 2)
        self.assertEqual(run.result.net_return_percent, 6.0)


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
