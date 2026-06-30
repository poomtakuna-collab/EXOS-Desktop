import unittest

from src.analysis import (
    build_prediction_summary,
    build_strategy_summary,
    build_trade_plan,
    calculate_price_projection,
    calculate_probability_summary,
    calculate_risk_zone,
    calculate_target_zone,
    resolve_similar_patterns,
)


CURRENT_PRICE = 125.0


class StrategySummaryTradePlanBridgeSmokeTest(unittest.TestCase):
    def test_strategy_summary_feeds_trade_plan(self) -> None:
        resolver_output = resolve_similar_patterns(
            _snapshot(),
            _pattern_library(),
            top_k=3,
        )
        probability = calculate_probability_summary(resolver_output)
        projection = calculate_price_projection(CURRENT_PRICE, resolver_output)
        target_zone = calculate_target_zone(projection)
        risk_zone = calculate_risk_zone(projection)
        prediction_summary = build_prediction_summary(
            probability=probability,
            projection=projection,
            target_zone=target_zone,
            risk_zone=risk_zone,
        )
        strategy_summary = build_strategy_summary(prediction_summary)

        first_plan = build_trade_plan(prediction_summary, strategy_summary)
        second_plan = build_trade_plan(prediction_summary, strategy_summary)

        self.assertEqual(first_plan, second_plan)
        self.assertEqual(
            set(first_plan),
            {
                "entry_zone",
                "stop_zone",
                "target_zone",
                "risk_reward",
                "invalidation_notes",
            },
        )
        self.assertIsInstance(first_plan["invalidation_notes"], list)
        if first_plan["entry_zone"] is not None:
            self.assertLessEqual(
                first_plan["entry_zone"]["low"],
                first_plan["entry_zone"]["high"],
            )
        if first_plan["risk_reward"] is not None:
            self.assertEqual(
                first_plan["risk_reward"]["market_bias"],
                strategy_summary["market_bias"],
            )
            self.assertEqual(
                first_plan["risk_reward"]["risk_level"],
                strategy_summary["risk_level"],
            )


def _snapshot() -> dict[str, object]:
    return {
        "trend": {"state": "up"},
        "trend_slope": {"score": 70.0},
        "adx": 31.0,
        "rsi": 58.0,
        "atr": 2.1,
        "squeeze": {"state": "released"},
        "market_structure": {"state": "higher_high"},
    }


def _pattern_library() -> list[dict[str, object]]:
    return [
        {
            "pattern_id": "positive-pattern",
            "trend": "up",
            "trend_slope": 69.0,
            "adx": 30.0,
            "rsi": 59.0,
            "atr": 2.0,
            "squeeze": "released",
            "market_structure": "higher_high",
            "dominant_label": "Bull",
            "average_5d_return": 2.0,
            "average_10d_return": 4.0,
            "average_20d_return": 6.0,
            "average_max_gain": 5.0,
            "average_drawdown": -1.5,
        },
        {
            "pattern_id": "neutral-pattern",
            "trend": "up",
            "trend_slope": 60.0,
            "adx": 25.0,
            "rsi": 52.0,
            "atr": 2.5,
            "squeeze": "released",
            "market_structure": "higher_high",
            "dominant_label": "Sideway",
            "average_5d_return": 0.5,
            "average_10d_return": 0.8,
            "average_20d_return": 1.0,
            "average_max_gain": 2.0,
            "average_drawdown": -2.0,
        },
        {
            "pattern_id": "negative-pattern",
            "trend": "down",
            "trend_slope": 25.0,
            "adx": 18.0,
            "rsi": 35.0,
            "atr": 4.0,
            "squeeze": "compression",
            "market_structure": "lower_low",
            "dominant_label": "Bear",
            "average_5d_return": -1.5,
            "average_10d_return": -3.0,
            "average_20d_return": -5.0,
            "average_max_gain": 1.0,
            "average_drawdown": -6.0,
        },
    ]


if __name__ == "__main__":
    unittest.main()
