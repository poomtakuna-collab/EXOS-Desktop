from __future__ import annotations

import unittest

from src.backtest import (
    BacktestInput,
    BacktestResult,
    SimulationConfig,
    run_backtest,
)
from src.strategy import EntryQuality, RiskRating, StrategyResult, TradeGrade


class BacktestPipelineTest(unittest.TestCase):
    def test_empty_input_returns_safe_result(self) -> None:
        result = run_backtest([], SimulationConfig(horizon_days=2))

        _assert_valid_backtest_result(self, result)
        self.assertEqual(result.total_trades, 0)
        self.assertEqual(result.win_rate, 0.0)

    def test_single_winning_trade(self) -> None:
        result = run_backtest(
            [
                _backtest_input(
                    future_rows=[
                        _ohlcv(high=106.0, low=99.0, close=104.0),
                        _ohlcv(high=107.0, low=101.0, close=106.0),
                    ]
                )
            ],
            SimulationConfig(horizon_days=2),
        )

        _assert_valid_backtest_result(self, result)
        self.assertEqual(result.total_trades, 1)
        self.assertEqual(result.winning_trades, 1)
        self.assertEqual(result.losing_trades, 0)
        self.assertEqual(result.win_rate, 100.0)

    def test_single_losing_trade(self) -> None:
        result = run_backtest(
            [
                _backtest_input(
                    future_rows=[
                        _ohlcv(high=102.0, low=94.0, close=96.0),
                        _ohlcv(high=100.0, low=93.0, close=95.0),
                    ]
                )
            ],
            SimulationConfig(horizon_days=2),
        )

        _assert_valid_backtest_result(self, result)
        self.assertEqual(result.total_trades, 1)
        self.assertEqual(result.winning_trades, 0)
        self.assertEqual(result.losing_trades, 1)
        self.assertEqual(result.win_rate, 0.0)

    def test_mixed_trades(self) -> None:
        result = run_backtest(
            [
                _backtest_input(
                    future_rows=[
                        _ohlcv(high=106.0, low=99.0, close=104.0),
                        _ohlcv(high=107.0, low=101.0, close=106.0),
                    ]
                ),
                _backtest_input(
                    future_rows=[
                        _ohlcv(high=102.0, low=94.0, close=96.0),
                        _ohlcv(high=100.0, low=93.0, close=95.0),
                    ]
                ),
            ],
            SimulationConfig(horizon_days=2),
        )

        _assert_valid_backtest_result(self, result)
        self.assertEqual(result.total_trades, 2)
        self.assertEqual(result.winning_trades, 1)
        self.assertEqual(result.losing_trades, 1)
        self.assertEqual(result.win_rate, 50.0)

    def test_insufficient_data_records_are_counted_in_notes(self) -> None:
        result = run_backtest(
            [
                _backtest_input(future_rows=[]),
                _backtest_input(
                    future_rows=[
                        _ohlcv(high=106.0, low=99.0, close=104.0),
                        _ohlcv(high=107.0, low=101.0, close=106.0),
                    ]
                ),
            ],
            SimulationConfig(horizon_days=2),
        )

        _assert_valid_backtest_result(self, result)
        self.assertEqual(result.total_trades, 1)
        self.assertEqual(result.win_rate, 100.0)
        self.assertTrue(
            any("Skipped / insufficient-data simulations: 1" in note for note in result.notes)
        )

    def test_deterministic_output(self) -> None:
        backtest_inputs = [
            _backtest_input(
                future_rows=[
                    _ohlcv(high=103.0, low=98.0, close=101.0),
                    _ohlcv(high=104.0, low=99.0, close=102.0),
                ]
            )
        ]
        config = SimulationConfig(horizon_days=2)

        first_result = run_backtest(backtest_inputs, config)
        second_result = run_backtest(backtest_inputs, config)

        self.assertEqual(first_result, second_result)

    def test_stable_backtest_result_shape(self) -> None:
        result = run_backtest(
            [
                _backtest_input(
                    future_rows=[
                        _ohlcv(high=106.0, low=99.0, close=104.0),
                        _ohlcv(high=107.0, low=101.0, close=106.0),
                    ]
                )
            ],
            SimulationConfig(horizon_days=2),
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


def _backtest_input(
    future_rows: list[dict[str, object]],
) -> BacktestInput:
    return BacktestInput(
        snapshot={"close": 100.0},
        probability={},
        prediction={},
        strategy_result=_strategy_result(),
        outcome={},
        future_rows=future_rows,
    )


def _strategy_result() -> StrategyResult:
    return StrategyResult(
        strategy_score=70.0,
        trade_grade=TradeGrade.GOOD,
        entry_quality=EntryQuality.GOOD,
        risk_rating=RiskRating.MEDIUM,
        reward_risk_estimate={
            "expected_reward_percent": 5.0,
            "expected_risk_percent": 5.0,
            "reward_risk_ratio": 1.0,
            "target_zone": {"low": 105.0, "high": 107.0},
            "risk_zone": {"low": 95.0, "high": 98.0},
        },
        notes=[],
    )


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
