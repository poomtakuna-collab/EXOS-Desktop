from __future__ import annotations

import unittest

from src.backtest import BacktestResultV1, generate_backtest_result


class BacktestResultGenerationSmokeTest(unittest.TestCase):
    def test_result_generation_smoke(self) -> None:
        first_result = generate_backtest_result([2.0, -1.0, 0.5])
        second_result = generate_backtest_result([2.0, -1.0, 0.5])

        self.assertIsInstance(first_result, BacktestResultV1)
        self.assertEqual(first_result, second_result)
        self.assertEqual(first_result.total_trades, 3)
        self.assertEqual(first_result.winning_trades, 2)
        self.assertEqual(first_result.losing_trades, 1)
        self.assertEqual(first_result.net_return_percent, 1.5)


if __name__ == "__main__":
    unittest.main()
