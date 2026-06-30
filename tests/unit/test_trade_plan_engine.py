import unittest

from src.analysis import build_trade_plan


class TradePlanEngineTest(unittest.TestCase):
    def test_empty_inputs_return_safe_trade_plan(self) -> None:
        result = build_trade_plan({}, {})

        self.assertEqual(
            result,
            {
                "entry_zone": None,
                "stop_zone": None,
                "target_zone": None,
                "risk_reward": None,
                "invalidation_notes": ["Prediction summary data unavailable"],
            },
        )

    def test_builds_trade_plan_from_prediction_and_strategy_summaries(self) -> None:
        result = build_trade_plan(_prediction_summary(), _strategy_summary())

        self.assertEqual(result["entry_zone"], {"low": 100.0, "high": 104.0})
        self.assertEqual(
            result["stop_zone"],
            {"conservative": 99.0, "base": 98.0, "aggressive": 96.0},
        )
        self.assertEqual(
            result["target_zone"],
            {"conservative": 102.0, "base": 104.0, "aggressive": 108.0},
        )
        self.assertEqual(
            result["risk_reward"],
            {
                "reward_risk_ratio": 2.0,
                "market_bias": "positive",
                "risk_level": "medium",
            },
        )
        self.assertEqual(
            result["invalidation_notes"],
            ["Trade plan derived from prediction and strategy summaries"],
        )

    def test_missing_zones_are_handled_safely(self) -> None:
        result = build_trade_plan(
            {"projection": {"current_price": 100.0}},
            {"market_bias": "neutral", "risk_level": "unknown"},
        )

        self.assertEqual(result["entry_zone"], {"low": 100.0, "high": 100.0})
        self.assertIsNone(result["stop_zone"])
        self.assertIsNone(result["target_zone"])
        self.assertIsNone(result["risk_reward"]["reward_risk_ratio"])
        self.assertIn("Stop zone unavailable", result["invalidation_notes"])
        self.assertIn("Target zone unavailable", result["invalidation_notes"])

    def test_strategy_notes_are_preserved_as_invalidation_context(self) -> None:
        result = build_trade_plan(
            _prediction_summary(),
            {
                **_strategy_summary(),
                "notes": ["Risk level: medium"],
            },
        )

        self.assertIn("Risk level: medium", result["invalidation_notes"])

    def test_output_has_no_trade_decision(self) -> None:
        result = build_trade_plan(_prediction_summary(), _strategy_summary())

        flattened = [str(value).upper() for value in _flatten_values(result)]
        self.assertNotIn("BUY", flattened)
        self.assertNotIn("SELL", flattened)
        self.assertNotIn("HOLD", flattened)


def _prediction_summary() -> dict[str, object]:
    return {
        "projection": {
            "current_price": 100.0,
            "expected_price_10d": 104.0,
        },
        "target_zone": {
            "conservative": 102.0,
            "base": 104.0,
            "aggressive": 108.0,
        },
        "risk_zone": {
            "conservative": 99.0,
            "base": 98.0,
            "aggressive": 96.0,
        },
    }


def _strategy_summary() -> dict[str, object]:
    return {
        "market_bias": "positive",
        "risk_level": "medium",
        "reward_risk_ratio": 2.0,
        "notes": [],
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
