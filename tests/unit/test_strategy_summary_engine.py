import unittest

from src.analysis import build_strategy_summary


class StrategySummaryEngineTest(unittest.TestCase):
    def test_empty_prediction_summary_returns_safe_summary(self) -> None:
        result = build_strategy_summary({})

        self.assertEqual(
            result,
            {
                "market_bias": "unknown",
                "risk_level": "unknown",
                "reward_risk_ratio": None,
                "notes": ["Prediction summary data unavailable"],
            },
        )

    def test_builds_positive_low_risk_summary(self) -> None:
        result = build_strategy_summary(_prediction_summary())

        self.assertEqual(result["market_bias"], "positive")
        self.assertEqual(result["risk_level"], "low")
        self.assertEqual(result["reward_risk_ratio"], 4.0)
        self.assertEqual(
            result["notes"],
            [
                "Market bias: positive",
                "Risk level: low",
                "Reward/risk ratio: 4.0",
            ],
        )

    def test_builds_negative_high_risk_summary(self) -> None:
        result = build_strategy_summary(
            {
                **_prediction_summary(),
                "probability": {
                    "probability_positive": 10.0,
                    "probability_negative": 70.0,
                    "probability_neutral": 20.0,
                },
                "risk_zone": {
                    "conservative": 96.0,
                    "base": 92.0,
                    "aggressive": 88.0,
                },
            }
        )

        self.assertEqual(result["market_bias"], "negative")
        self.assertEqual(result["risk_level"], "high")

    def test_uses_projection_return_when_probability_is_missing(self) -> None:
        result = build_strategy_summary(
            {
                **_prediction_summary(),
                "probability": {},
                "projection": {
                    "current_price": 100.0,
                    "expected_return_10d": -2.0,
                },
            }
        )

        self.assertEqual(result["market_bias"], "negative")

    def test_missing_zones_make_reward_risk_unavailable(self) -> None:
        result = build_strategy_summary(
            {
                "probability": {
                    "probability_positive": 45.0,
                    "probability_negative": 20.0,
                    "probability_neutral": 35.0,
                },
                "projection": {"current_price": 100.0},
            }
        )

        self.assertIsNone(result["reward_risk_ratio"])
        self.assertIn("Reward/risk ratio unavailable", result["notes"])

    def test_output_has_no_trade_decision(self) -> None:
        result = build_strategy_summary(_prediction_summary())

        flattened = [str(value).upper() for value in _flatten_values(result)]
        self.assertNotIn("BUY", flattened)
        self.assertNotIn("SELL", flattened)
        self.assertNotIn("HOLD", flattened)


def _prediction_summary() -> dict[str, object]:
    return {
        "probability": {
            "probability_positive": 65.0,
            "probability_negative": 20.0,
            "probability_neutral": 15.0,
        },
        "projection": {
            "current_price": 100.0,
            "expected_return_10d": 4.0,
        },
        "target_zone": {
            "conservative": 102.0,
            "base": 104.0,
            "aggressive": 108.0,
        },
        "risk_zone": {
            "conservative": 99.0,
            "base": 98.0,
            "aggressive": 98.0,
        },
    }


def _flatten_values(value: object) -> list[object]:
    if isinstance(value, dict):
        flattened: list[object] = []
        for item in value.values():
            flattened.extend(_flatten_values(item))
        return flattened
    if isinstance(value, list):
        flattened = []
        for item in value:
            flattened.extend(_flatten_values(item))
        return flattened
    return [value]


if __name__ == "__main__":
    unittest.main()
