import unittest

from src.analysis import (
    build_prediction_summary,
    build_strategy_report,
    build_strategy_summary,
    build_trade_plan,
    calculate_position_sizing,
    calculate_price_projection,
    calculate_probability_summary,
    calculate_risk_zone,
    calculate_target_zone,
    resolve_similar_patterns,
)


CURRENT_PRICE = 125.0


class FullStrategyReportChainSmokeTest(unittest.TestCase):
    def test_full_strategy_chain_builds_strategy_report(self) -> None:
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
        trade_plan = build_trade_plan(prediction_summary, strategy_summary)
        position_sizing = calculate_position_sizing(
            trade_plan,
            account_size=25_000.0,
            account_risk_percent=1.5,
        )

        first_report = build_strategy_report(
            prediction_summary=prediction_summary,
            strategy_summary=strategy_summary,
            trade_plan=trade_plan,
            position_sizing=position_sizing,
        )
        second_report = build_strategy_report(
            prediction_summary=prediction_summary,
            strategy_summary=strategy_summary,
            trade_plan=trade_plan,
            position_sizing=position_sizing,
        )

        self.assertEqual(first_report, second_report)
        self.assertEqual(
            set(first_report),
            {
                "confidence",
                "evidence_count",
                "best_pattern_id",
                "best_similarity",
                "prediction_summary",
                "strategy_summary",
                "trade_plan",
                "position_sizing",
            },
        )
        self.assertEqual(first_report["prediction_summary"], prediction_summary)
        self.assertEqual(first_report["strategy_summary"], strategy_summary)
        self.assertEqual(first_report["trade_plan"], trade_plan)
        self.assertEqual(first_report["position_sizing"], position_sizing)
        self.assertEqual(first_report["confidence"], prediction_summary["confidence"])
        self.assertEqual(
            first_report["evidence_count"],
            prediction_summary["evidence_count"],
        )
        self.assertEqual(
            first_report["best_pattern_id"],
            prediction_summary["best_pattern_id"],
        )
        self.assertEqual(
            first_report["best_similarity"],
            prediction_summary["best_similarity"],
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
