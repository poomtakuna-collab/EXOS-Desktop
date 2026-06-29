from __future__ import annotations

import unittest

from src.strategy import (
    EntryQuality,
    RiskRating,
    StrategyInput,
    StrategyResult,
    TradeGrade,
    analyze_strategy,
)


class StrategyEngineTest(unittest.TestCase):
    def test_valid_strategy_input_returns_strategy_result(self) -> None:
        result = analyze_strategy(_strategy_input())

        _assert_valid_strategy_result(self, result)

    def test_strategy_score_stays_inside_expected_bounds(self) -> None:
        result = analyze_strategy(_strategy_input())

        self.assertGreaterEqual(result.strategy_score, 0)
        self.assertLessEqual(result.strategy_score, 100)

    def test_default_inputs_do_not_raise_exceptions(self) -> None:
        result = analyze_strategy(
            StrategyInput(
                snapshot={},
                probability={},
                prediction={},
            )
        )

        _assert_valid_strategy_result(self, result)

    def test_empty_probability_input_returns_valid_result(self) -> None:
        strategy_input = _strategy_input(probability={})

        result = analyze_strategy(strategy_input)

        _assert_valid_strategy_result(self, result)

    def test_empty_prediction_input_returns_valid_result(self) -> None:
        strategy_input = _strategy_input(prediction={})

        result = analyze_strategy(strategy_input)

        _assert_valid_strategy_result(self, result)

    def test_missing_optional_fields_returns_valid_result(self) -> None:
        strategy_input = _strategy_input(
            probability={
                "confidence": 50.0,
            },
            prediction={
                "expected_return": 1.5,
            },
        )

        result = analyze_strategy(strategy_input)

        _assert_valid_strategy_result(self, result)

    def test_low_confidence_scenario_has_low_quality_labels(self) -> None:
        result = analyze_strategy(_low_confidence_input())

        _assert_valid_strategy_result(self, result)
        self.assertIn(result.trade_grade, {TradeGrade.WEAK, TradeGrade.AVOID})
        self.assertEqual(result.entry_quality, EntryQuality.POOR)

    def test_high_confidence_scenario_has_high_quality_labels(self) -> None:
        result = analyze_strategy(_high_confidence_input())

        _assert_valid_strategy_result(self, result)
        self.assertIn(result.trade_grade, {TradeGrade.EXCELLENT, TradeGrade.GOOD})
        self.assertIn(result.entry_quality, {EntryQuality.IDEAL, EntryQuality.GOOD})

    def test_zero_evidence_remains_valid(self) -> None:
        strategy_input = _strategy_input(
            probability={
                **_strategy_input().probability,
                "evidence_count": 0,
            }
        )

        result = analyze_strategy(strategy_input)

        _assert_valid_strategy_result(self, result)
        self.assertTrue(any("Evidence score: 0.0" in note for note in result.notes))

    def test_high_evidence_is_capped_inside_score_bounds(self) -> None:
        strategy_input = _strategy_input(
            probability={
                **_strategy_input().probability,
                "evidence_count": 10_000,
            }
        )

        result = analyze_strategy(strategy_input)

        _assert_valid_strategy_result(self, result)

    def test_score_can_clamp_to_zero_boundary(self) -> None:
        result = analyze_strategy(_zero_boundary_input())

        _assert_valid_strategy_result(self, result)
        self.assertEqual(result.strategy_score, 0)
        self.assertEqual(result.trade_grade, TradeGrade.AVOID)

    def test_score_can_reach_upper_boundary(self) -> None:
        result = analyze_strategy(_upper_boundary_input())

        _assert_valid_strategy_result(self, result)
        self.assertEqual(result.strategy_score, 100)
        self.assertEqual(result.trade_grade, TradeGrade.EXCELLENT)

    def test_reward_risk_ratio_is_none_when_expected_risk_is_zero(self) -> None:
        strategy_input = _strategy_input(
            probability={
                **_strategy_input().probability,
                "expected_drawdown_10d": 0,
            }
        )

        result = analyze_strategy(strategy_input)

        _assert_valid_strategy_result(self, result)
        self.assertIsNone(result.reward_risk_estimate["reward_risk_ratio"])

    def test_reward_risk_ratio_handles_negative_expected_reward(self) -> None:
        strategy_input = _strategy_input(
            probability={
                **_strategy_input().probability,
                "expected_drawdown_10d": -5,
            },
            prediction={
                **_strategy_input().prediction,
                "expected_return": -2,
            },
        )

        result = analyze_strategy(strategy_input)

        _assert_valid_strategy_result(self, result)
        self.assertLess(result.reward_risk_estimate["reward_risk_ratio"], 0)

    def test_invalid_numeric_values_do_not_raise_exceptions(self) -> None:
        result = analyze_strategy(
            StrategyInput(
                snapshot={},
                probability={
                    "confidence": "not-a-number",
                    "evidence_count": object(),
                    "expected_drawdown_10d": None,
                },
                prediction={
                    "expected_return": "not-a-number",
                    "confidence": [],
                    "target_zone_low": {},
                },
            )
        )

        _assert_valid_strategy_result(self, result)


def _assert_valid_strategy_result(
    test_case: unittest.TestCase,
    result: StrategyResult,
) -> None:
    test_case.assertIsInstance(result, StrategyResult)
    test_case.assertGreaterEqual(result.strategy_score, 0)
    test_case.assertLessEqual(result.strategy_score, 100)
    test_case.assertIsInstance(result.trade_grade, TradeGrade)
    test_case.assertIn(result.trade_grade, set(TradeGrade))
    test_case.assertIsInstance(result.entry_quality, EntryQuality)
    test_case.assertIn(result.entry_quality, set(EntryQuality))
    test_case.assertIsInstance(result.risk_rating, RiskRating)
    test_case.assertIn(result.risk_rating, set(RiskRating))
    test_case.assertIsInstance(result.reward_risk_estimate, dict)
    test_case.assertIsInstance(result.notes, list)
    test_case.assertGreater(len(result.notes), 0)


def _strategy_input(
    snapshot: dict[str, object] | None = None,
    probability: dict[str, object] | None = None,
    prediction: dict[str, object] | None = None,
) -> StrategyInput:
    return StrategyInput(
        snapshot=snapshot if snapshot is not None else {
            "snapshot_id": "snapshot-1",
            "symbol": "AAPL",
            "timeframe": "1D",
            "date": "2026-01-01",
            "close": 100.0,
        },
        probability=probability if probability is not None else {
            "expected_return_5d": 2.0,
            "expected_return_10d": 4.0,
            "expected_return_20d": 6.0,
            "probability_up_5pct_10d": 55.0,
            "probability_up_10pct_10d": 25.0,
            "probability_down_5pct_10d": 20.0,
            "expected_max_gain_10d": 7.0,
            "expected_drawdown_10d": -3.0,
            "confidence": 70.0,
            "evidence_count": 80,
            "best_pattern_id": "pattern-1",
            "best_similarity": 82.0,
        },
        prediction=prediction if prediction is not None else {
            "expected_price_5d": 102.0,
            "expected_price_10d": 104.0,
            "expected_price_20d": 106.0,
            "target_zone_low": 103.0,
            "target_zone_high": 107.0,
            "risk_zone_low": 96.0,
            "risk_zone_high": 98.0,
            "expected_return": 4.0,
            "confidence": 68.0,
            "time_horizon": "10D",
            "best_pattern_id": "pattern-1",
            "best_similarity": 82.0,
        },
    )


def _low_confidence_input() -> StrategyInput:
    return _strategy_input(
        probability={
            "expected_return_10d": -5.0,
            "probability_down_5pct_10d": 85.0,
            "expected_drawdown_10d": -18.0,
            "confidence": 5.0,
            "evidence_count": 0,
        },
        prediction={
            "expected_return": -5.0,
            "confidence": 5.0,
            "expected_price_10d": 95.0,
            "target_zone_low": 94.0,
            "target_zone_high": 96.0,
            "risk_zone_low": 80.0,
            "risk_zone_high": 85.0,
        },
    )


def _high_confidence_input() -> StrategyInput:
    return _strategy_input(
        probability={
            "expected_return_10d": 8.0,
            "probability_down_5pct_10d": 3.0,
            "expected_drawdown_10d": -1.0,
            "confidence": 95.0,
            "evidence_count": 150,
        },
        prediction={
            "expected_return": 8.0,
            "confidence": 96.0,
            "expected_price_10d": 108.0,
            "target_zone_low": 106.0,
            "target_zone_high": 112.0,
            "risk_zone_low": 99.0,
            "risk_zone_high": 100.0,
        },
    )


def _zero_boundary_input() -> StrategyInput:
    return _strategy_input(
        probability={
            "expected_return_10d": -10.0,
            "probability_down_5pct_10d": 100.0,
            "expected_drawdown_10d": -20.0,
            "confidence": 0.0,
            "evidence_count": 0,
        },
        prediction={
            "expected_return": -10.0,
            "confidence": 0.0,
        },
    )


def _upper_boundary_input() -> StrategyInput:
    return _strategy_input(
        probability={
            "expected_return_10d": 12.0,
            "probability_down_5pct_10d": 0.0,
            "expected_drawdown_10d": -0.00001,
            "confidence": 100.0,
            "evidence_count": 100,
        },
        prediction={
            "expected_return": 12.0,
            "confidence": 100.0,
        },
    )


if __name__ == "__main__":
    unittest.main()
