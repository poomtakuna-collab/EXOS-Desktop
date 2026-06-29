from __future__ import annotations

import unittest

from src.backtest import (
    BacktestResult,
    ExitReason,
    SimulationResult,
    SimulationStatus,
    TradeOutcome,
    analyze_backtest_results,
)


class BacktestMetricsTest(unittest.TestCase):
    def test_empty_results_returns_safe_defaults(self) -> None:
        result = analyze_backtest_results([])

        _assert_valid_backtest_result(self, result)
        self.assertEqual(result.total_trades, 0)
        self.assertEqual(result.win_rate, 0.0)
        self.assertEqual(result.average_return, 0.0)
        self.assertTrue(any("No simulation results" in note for note in result.notes))

    def test_all_wins(self) -> None:
        result = analyze_backtest_results(
            [
                _simulation_result(TradeOutcome.WIN, 5.0, -1.0),
                _simulation_result(TradeOutcome.WIN, 3.0, -2.0),
            ]
        )

        _assert_valid_backtest_result(self, result)
        self.assertEqual(result.total_trades, 2)
        self.assertEqual(result.winning_trades, 2)
        self.assertEqual(result.losing_trades, 0)
        self.assertEqual(result.win_rate, 100.0)
        self.assertEqual(result.average_return, 4.0)

    def test_all_losses(self) -> None:
        result = analyze_backtest_results(
            [
                _simulation_result(TradeOutcome.LOSS, -4.0, -6.0),
                _simulation_result(TradeOutcome.LOSS, -2.0, -3.0),
            ]
        )

        _assert_valid_backtest_result(self, result)
        self.assertEqual(result.total_trades, 2)
        self.assertEqual(result.winning_trades, 0)
        self.assertEqual(result.losing_trades, 2)
        self.assertEqual(result.win_rate, 0.0)
        self.assertEqual(result.average_return, -3.0)

    def test_mixed_wins_and_losses(self) -> None:
        result = analyze_backtest_results(
            [
                _simulation_result(TradeOutcome.WIN, 6.0, -1.0),
                _simulation_result(TradeOutcome.LOSS, -2.0, -4.0),
                _simulation_result(TradeOutcome.WIN, 3.0, -2.0),
            ]
        )

        _assert_valid_backtest_result(self, result)
        self.assertEqual(result.total_trades, 3)
        self.assertEqual(result.winning_trades, 2)
        self.assertEqual(result.losing_trades, 1)
        self.assertEqual(result.win_rate, 66.6667)
        self.assertEqual(result.average_return, 2.3333)

    def test_breakeven_results_are_not_wins_or_losses(self) -> None:
        result = analyze_backtest_results(
            [
                _simulation_result(TradeOutcome.WIN, 4.0, -1.0),
                _simulation_result(TradeOutcome.BREAKEVEN, 0.0, -0.5),
            ]
        )

        _assert_valid_backtest_result(self, result)
        self.assertEqual(result.total_trades, 2)
        self.assertEqual(result.winning_trades, 1)
        self.assertEqual(result.losing_trades, 0)
        self.assertEqual(result.win_rate, 100.0)
        self.assertTrue(any("Breakeven simulations: 1" in note for note in result.notes))

    def test_skipped_and_insufficient_data_results_are_ignored_for_win_rate(self) -> None:
        result = analyze_backtest_results(
            [
                _simulation_result(TradeOutcome.WIN, 4.0, -1.0),
                _simulation_result(
                    TradeOutcome.OPEN,
                    None,
                    None,
                    status=SimulationStatus.INSUFFICIENT_DATA,
                    exit_reason=ExitReason.INSUFFICIENT_DATA,
                ),
                _simulation_result(
                    TradeOutcome.OPEN,
                    None,
                    None,
                    status=SimulationStatus.SKIPPED,
                    exit_reason=ExitReason.OPEN,
                ),
            ]
        )

        _assert_valid_backtest_result(self, result)
        self.assertEqual(result.total_trades, 1)
        self.assertEqual(result.win_rate, 100.0)
        self.assertTrue(
            any("Skipped / insufficient-data simulations: 2" in note for note in result.notes)
        )

    def test_max_drawdown_uses_worst_drawdown(self) -> None:
        result = analyze_backtest_results(
            [
                _simulation_result(TradeOutcome.WIN, 4.0, -3.0),
                _simulation_result(TradeOutcome.LOSS, -2.0, -7.0),
                _simulation_result(TradeOutcome.WIN, 5.0, -1.0),
            ]
        )

        _assert_valid_backtest_result(self, result)
        self.assertEqual(result.max_drawdown, -7.0)
        self.assertEqual(result.average_drawdown, -3.6667)

    def test_expectancy_is_average_completed_return(self) -> None:
        result = analyze_backtest_results(
            [
                _simulation_result(TradeOutcome.WIN, 6.0, -1.0),
                _simulation_result(TradeOutcome.LOSS, -3.0, -5.0),
                _simulation_result(TradeOutcome.BREAKEVEN, 0.0, -0.5),
            ]
        )

        _assert_valid_backtest_result(self, result)
        self.assertEqual(result.expectancy, 1.0)

    def test_malformed_simulation_data_does_not_raise(self) -> None:
        result = analyze_backtest_results(
            [
                SimulationResult(
                    status=SimulationStatus.SUCCESS,
                    trade_outcome=TradeOutcome.WIN,
                    exit_reason=ExitReason.TARGET_HIT,
                    return_percent=None,
                    max_drawdown_percent="not-a-number",  # type: ignore[arg-type]
                )
            ]
        )

        _assert_valid_backtest_result(self, result)
        self.assertEqual(result.average_return, 0.0)
        self.assertEqual(result.average_drawdown, 0.0)

    def test_stable_backtest_result_shape(self) -> None:
        result = analyze_backtest_results(
            [_simulation_result(TradeOutcome.WIN, 4.0, -1.0)]
        )

        self.assertEqual(
            set(result.__dict__),
            {
                "total_trades",
                "winning_trades",
                "losing_trades",
                "win_rate",
                "average_return",
                "average_drawdown",
                "expectancy",
                "max_drawdown",
                "notes",
            },
        )
        _assert_valid_backtest_result(self, result)


def _assert_valid_backtest_result(
    test_case: unittest.TestCase,
    result: BacktestResult,
) -> None:
    test_case.assertIsInstance(result, BacktestResult)
    test_case.assertGreaterEqual(result.total_trades, 0)
    test_case.assertGreaterEqual(result.winning_trades, 0)
    test_case.assertGreaterEqual(result.losing_trades, 0)
    test_case.assertGreaterEqual(result.win_rate, 0.0)
    test_case.assertLessEqual(result.win_rate, 100.0)
    test_case.assertIsInstance(result.notes, list)


def _simulation_result(
    trade_outcome: TradeOutcome,
    return_percent: float | None,
    max_drawdown_percent: float | None,
    status: SimulationStatus = SimulationStatus.SUCCESS,
    exit_reason: ExitReason = ExitReason.TIMEOUT,
) -> SimulationResult:
    return SimulationResult(
        status=status,
        trade_outcome=trade_outcome,
        exit_reason=exit_reason,
        return_percent=return_percent,
        max_drawdown_percent=max_drawdown_percent,
    )


if __name__ == "__main__":
    unittest.main()
