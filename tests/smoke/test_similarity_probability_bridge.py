import unittest

from src.analysis import calculate_probability_summary, resolve_similar_patterns


class SimilarityProbabilityBridgeSmokeTest(unittest.TestCase):
    def test_similarity_resolver_output_feeds_probability_engine(self) -> None:
        resolver_output = resolve_similar_patterns(
            _snapshot(),
            _pattern_library(),
            top_k=3,
        )

        first_summary = calculate_probability_summary(resolver_output)
        second_summary = calculate_probability_summary(resolver_output)

        self.assertIn("matches", resolver_output)
        self.assertEqual(len(resolver_output["matches"]), 3)
        self.assertEqual(first_summary, second_summary)
        self.assertEqual(
            set(first_summary),
            {
                "probability_positive",
                "probability_negative",
                "probability_neutral",
                "expected_return_5d",
                "expected_return_10d",
                "expected_return_20d",
                "expected_max_gain_10d",
                "expected_drawdown_10d",
                "confidence",
                "evidence_count",
                "best_pattern_id",
                "best_similarity",
            },
        )
        self.assertEqual(first_summary["evidence_count"], len(resolver_output["matches"]))

        for key in (
            "probability_positive",
            "probability_negative",
            "probability_neutral",
            "confidence",
            "best_similarity",
        ):
            self.assertGreaterEqual(first_summary[key], 0.0)
            self.assertLessEqual(first_summary[key], 100.0)

        probability_total = (
            first_summary["probability_positive"]
            + first_summary["probability_negative"]
            + first_summary["probability_neutral"]
        )
        self.assertAlmostEqual(probability_total, 100.0, places=3)


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
