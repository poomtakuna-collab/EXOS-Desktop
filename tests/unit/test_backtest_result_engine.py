from __future__ import annotations

import math
import unittest

from src.backtest import BacktestResultV1, generate_backtest_result


class BacktestResultEngineTest(unittest.TestCase):
    def test_empty_inputs_return_safe_defaults(self) -> None:
        result = generate_backtest_result([])

        _assert_valid_result(self, result)
        self.assertEqual(result.total_trades, 0)
        self.assertEqual(result.winning_trades, 0)
        self.assertEqual(result.losing_trades, 0)
        self.assertEqual(result.win_rate, 0.0)
        self.assertEqual(result.net_return_percent, 0.0)
        self.assertEqual(result.average_return, 0.0)
        self.assertEqual(result.max_drawdown, 0.0)
        self.assertEqual(result.profit_factor, 0.0)
        self.assertEqual(result.expectancy, 0.0)

    def test_mixed_returns_generate_expected_metrics(self) -> None:
        result = generate_backtest_result([5.0, -2.0, 3.0, -1.0, 0.0])

        _assert_valid_result(self, result)
        self.assertEqual(result.total_trades, 5)
        self.assertEqual(result.winning_trades, 2)
        self.assertEqual(result.losing_trades, 2)
        self.assertEqual(result.win_rate, 40.0)
        self.assertEqual(result.net_return_percent, 5.0)
        self.assertEqual(result.average_return, 1.0)
        self.assertEqual(result.max_drawdown, -2.0)
        self.assertEqual(result.profit_factor, 2.6667)
        self.assertEqual(result.expectancy, 1.0)

    def test_max_drawdown_uses_cumulative_return_curve(self) -> None:
        result = generate_backtest_result([4.0, -1.5, -3.0, 2.0, -0.5])

        _assert_valid_result(self, result)
        self.assertEqual(result.max_drawdown, -4.5)

    def test_all_wins_have_unbounded_profit_factor(self) -> None:
        result = generate_backtest_result([2.0, 4.0])

        _assert_valid_result(self, result)
        self.assertEqual(result.total_trades, 2)
        self.assertEqual(result.winning_trades, 2)
        self.assertEqual(result.losing_trades, 0)
        self.assertEqual(result.win_rate, 100.0)
        self.assertEqual(result.net_return_percent, 6.0)
        self.assertEqual(result.average_return, 3.0)
        self.assertTrue(math.isinf(result.profit_factor))
        self.assertEqual(result.expectancy, 3.0)

    def test_malformed_values_are_ignored_safely(self) -> None:
        result = generate_backtest_result([None, "bad", "2.5", -1])

        _assert_valid_result(self, result)
        self.assertEqual(result.total_trades, 2)
        self.assertEqual(result.winning_trades, 1)
        self.assertEqual(result.losing_trades, 1)
        self.assertEqual(result.net_return_percent, 1.5)

    def test_malformed_container_is_safe(self) -> None:
        result = generate_backtest_result(123)  # type: ignore[arg-type]

        _assert_valid_result(self, result)
        self.assertEqual(result.total_trades, 0)
        self.assertEqual(result.net_return_percent, 0.0)

    def test_deterministic_result(self) -> None:
        trade_returns = [1.25, -0.75, 2.5]

        first_result = generate_backtest_result(trade_returns)
        second_result = generate_backtest_result(trade_returns)

        self.assertEqual(first_result, second_result)

    def test_stable_result_shape(self) -> None:
        result = generate_backtest_result([1.0])

        self.assertEqual(
            set(result.__dict__),
            {
                "total_trades",
                "winning_trades",
                "losing_trades",
                "win_rate",
                "net_return_percent",
                "average_return",
                "max_drawdown",
                "profit_factor",
                "expectancy",
            },
        )


def _assert_valid_result(
    test_case: unittest.TestCase,
    result: BacktestResultV1,
) -> None:
    test_case.assertIsInstance(result, BacktestResultV1)
    test_case.assertGreaterEqual(result.total_trades, 0)
    test_case.assertGreaterEqual(result.winning_trades, 0)
    test_case.assertGreaterEqual(result.losing_trades, 0)
    test_case.assertGreaterEqual(result.win_rate, 0.0)
    test_case.assertLessEqual(result.win_rate, 100.0)


if __name__ == "__main__":
    unittest.main()
