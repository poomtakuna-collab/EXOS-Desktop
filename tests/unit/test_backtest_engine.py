from __future__ import annotations

import unittest

from src.backtest import (
    BacktestInput,
    ExitReason,
    SimulationConfig,
    SimulationResult,
    SimulationStatus,
    TradeOutcome,
    replay_trade,
)
from src.strategy import EntryQuality, RiskRating, StrategyResult, TradeGrade


class BacktestEngineTest(unittest.TestCase):
    def test_target_hit_returns_win(self) -> None:
        result = replay_trade(
            _backtest_input(
                future_rows=[
                    _ohlcv(high=106.0, low=99.0, close=104.0),
                    _ohlcv(high=107.0, low=101.0, close=106.0),
                ]
            ),
            SimulationConfig(horizon_days=2),
        )

        _assert_valid_simulation_result(self, result)
        self.assertEqual(result.status, SimulationStatus.SUCCESS)
        self.assertEqual(result.trade_outcome, TradeOutcome.WIN)
        self.assertEqual(result.exit_reason, ExitReason.TARGET_HIT)
        self.assertEqual(result.exit_price, 105.0)

    def test_stop_hit_returns_loss(self) -> None:
        result = replay_trade(
            _backtest_input(
                future_rows=[
                    _ohlcv(high=102.0, low=94.0, close=96.0),
                    _ohlcv(high=100.0, low=93.0, close=95.0),
                ]
            ),
            SimulationConfig(horizon_days=2),
        )

        _assert_valid_simulation_result(self, result)
        self.assertEqual(result.status, SimulationStatus.SUCCESS)
        self.assertEqual(result.trade_outcome, TradeOutcome.LOSS)
        self.assertEqual(result.exit_reason, ExitReason.STOP_HIT)
        self.assertEqual(result.exit_price, 95.0)

    def test_target_and_stop_same_candle_uses_conservative_stop(self) -> None:
        result = replay_trade(
            _backtest_input(
                future_rows=[
                    _ohlcv(high=106.0, low=94.0, close=101.0),
                    _ohlcv(high=107.0, low=100.0, close=106.0),
                ]
            ),
            SimulationConfig(horizon_days=2),
        )

        _assert_valid_simulation_result(self, result)
        self.assertEqual(result.trade_outcome, TradeOutcome.LOSS)
        self.assertEqual(result.exit_reason, ExitReason.STOP_HIT)
        self.assertEqual(result.exit_price, 95.0)

    def test_timeout_uses_final_available_close(self) -> None:
        result = replay_trade(
            _backtest_input(
                future_rows=[
                    _ohlcv(high=103.0, low=98.0, close=101.0),
                    _ohlcv(high=104.0, low=99.0, close=102.0),
                ]
            ),
            SimulationConfig(horizon_days=2),
        )

        _assert_valid_simulation_result(self, result)
        self.assertEqual(result.status, SimulationStatus.SUCCESS)
        self.assertEqual(result.trade_outcome, TradeOutcome.WIN)
        self.assertEqual(result.exit_reason, ExitReason.TIMEOUT)
        self.assertEqual(result.exit_price, 102.0)
        self.assertEqual(result.return_percent, 2.0)

    def test_missing_future_data_returns_insufficient_data(self) -> None:
        result = replay_trade(
            _backtest_input(future_rows=[]),
            SimulationConfig(horizon_days=2),
        )

        _assert_valid_simulation_result(self, result)
        self.assertEqual(result.status, SimulationStatus.INSUFFICIENT_DATA)
        self.assertEqual(result.trade_outcome, TradeOutcome.OPEN)
        self.assertEqual(result.exit_reason, ExitReason.INSUFFICIENT_DATA)

    def test_invalid_inputs_return_insufficient_data(self) -> None:
        result = replay_trade(
            _backtest_input(
                snapshot={"close": "not-a-number"},
                future_rows=[
                    _ohlcv(high=106.0, low=99.0, close=104.0),
                    _ohlcv(high=107.0, low=101.0, close=106.0),
                ],
            ),
            SimulationConfig(horizon_days=2),
        )

        _assert_valid_simulation_result(self, result)
        self.assertEqual(result.status, SimulationStatus.INSUFFICIENT_DATA)
        self.assertEqual(result.exit_reason, ExitReason.INSUFFICIENT_DATA)

    def test_strategy_result_entry_price_takes_precedence(self) -> None:
        result = replay_trade(
            _backtest_input(
                strategy_result=_strategy_result(
                    reward_risk_estimate={
                        "entry_price": 101.0,
                        "expected_reward_percent": 5.0,
                        "expected_risk_percent": 5.0,
                        "reward_risk_ratio": 1.0,
                        "target_zone": {"low": 106.0, "high": 108.0},
                        "risk_zone": {"low": 96.0, "high": 98.0},
                    }
                ),
                future_rows=[
                    _ohlcv(high=106.0, low=100.0, close=105.0),
                    _ohlcv(high=107.0, low=101.0, close=106.0),
                ],
            ),
            SimulationConfig(horizon_days=2),
        )

        _assert_valid_simulation_result(self, result)
        self.assertEqual(result.entry_price, 101.0)
        self.assertEqual(result.exit_price, 106.0)

    def test_deterministic_replay_returns_same_result(self) -> None:
        backtest_input = _backtest_input(
            future_rows=[
                _ohlcv(high=103.0, low=98.0, close=101.0),
                _ohlcv(high=104.0, low=99.0, close=102.0),
            ]
        )
        config = SimulationConfig(horizon_days=2)

        first_result = replay_trade(backtest_input, config)
        second_result = replay_trade(backtest_input, config)

        self.assertEqual(first_result, second_result)

    def test_stable_simulation_result_shape(self) -> None:
        result = replay_trade(
            _backtest_input(
                future_rows=[
                    _ohlcv(high=103.0, low=98.0, close=101.0),
                    _ohlcv(high=104.0, low=99.0, close=102.0),
                ]
            ),
            SimulationConfig(horizon_days=2),
        )

        self.assertEqual(
            set(result.__dict__),
            {
                "status",
                "trade_outcome",
                "exit_reason",
                "entry_price",
                "exit_price",
                "return_percent",
                "max_drawdown_percent",
                "notes",
            },
        )
        _assert_valid_simulation_result(self, result)


def _assert_valid_simulation_result(
    test_case: unittest.TestCase,
    result: SimulationResult,
) -> None:
    test_case.assertIsInstance(result, SimulationResult)
    test_case.assertIn(result.status, set(SimulationStatus))
    test_case.assertIn(result.trade_outcome, set(TradeOutcome))
    test_case.assertIn(result.exit_reason, set(ExitReason))
    test_case.assertIsInstance(result.notes, list)


def _backtest_input(
    snapshot: dict[str, object] | None = None,
    strategy_result: StrategyResult | None = None,
    future_rows: list[dict[str, object]] | None = None,
) -> BacktestInput:
    return BacktestInput(
        snapshot=snapshot if snapshot is not None else {"close": 100.0},
        probability={},
        prediction={},
        strategy_result=strategy_result or _strategy_result(),
        outcome={},
        future_rows=future_rows or [],
    )


def _strategy_result(
    reward_risk_estimate: dict[str, object] | None = None,
) -> StrategyResult:
    return StrategyResult(
        strategy_score=70.0,
        trade_grade=TradeGrade.GOOD,
        entry_quality=EntryQuality.GOOD,
        risk_rating=RiskRating.MEDIUM,
        reward_risk_estimate=reward_risk_estimate
        if reward_risk_estimate is not None
        else {
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
