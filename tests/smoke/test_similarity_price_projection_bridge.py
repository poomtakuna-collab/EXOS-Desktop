import unittest

from src.analysis import calculate_price_projection, resolve_similar_patterns


CURRENT_PRICE = 125.0


class SimilarityPriceProjectionBridgeSmokeTest(unittest.TestCase):
    def test_similarity_resolver_output_feeds_price_projection_engine(self) -> None:
        resolver_output = resolve_similar_patterns(
            _snapshot(),
            _pattern_library(),
            top_k=3,
        )

        projection = calculate_price_projection(CURRENT_PRICE, resolver_output)

        self.assertIn("matches", resolver_output)
        self.assertEqual(len(resolver_output["matches"]), 3)
        self.assertEqual(
            set(projection),
            {
                "current_price",
                "expected_price_5d",
                "expected_price_10d",
                "expected_price_20d",
                "expected_return_5d",
                "expected_return_10d",
                "expected_return_20d",
                "upside_range",
                "downside_range",
                "confidence",
                "evidence_count",
                "best_pattern_id",
                "best_similarity",
            },
        )
        self.assertEqual(projection["current_price"], CURRENT_PRICE)
        self.assertEqual(projection["evidence_count"], len(resolver_output["matches"]))

        for key in (
            "expected_price_5d",
            "expected_price_10d",
            "expected_price_20d",
        ):
            self.assertGreater(projection[key], 0.0)

        for key in (
            "expected_return_5d",
            "expected_return_10d",
            "expected_return_20d",
        ):
            self.assertIsInstance(projection[key], float)

        self.assertIsInstance(projection["upside_range"], dict)
        self.assertGreaterEqual(
            projection["upside_range"]["high"],
            projection["upside_range"]["low"],
        )
        self.assertIsInstance(projection["downside_range"], dict)
        self.assertGreaterEqual(
            projection["downside_range"]["high"],
            projection["downside_range"]["low"],
        )
        self.assertGreaterEqual(projection["confidence"], 0.0)
        self.assertLessEqual(projection["confidence"], 100.0)
        self.assertGreaterEqual(projection["best_similarity"], 0.0)
        self.assertLessEqual(projection["best_similarity"], 100.0)

    def test_missing_projection_fields_are_handled_safely(self) -> None:
        resolver_output = resolve_similar_patterns(
            _snapshot(),
            _pattern_library_without_outcomes(),
            top_k=2,
        )

        projection = calculate_price_projection(CURRENT_PRICE, resolver_output)

        self.assertEqual(projection["current_price"], CURRENT_PRICE)
        self.assertEqual(projection["expected_price_5d"], CURRENT_PRICE)
        self.assertEqual(projection["expected_price_10d"], CURRENT_PRICE)
        self.assertEqual(projection["expected_price_20d"], CURRENT_PRICE)
        self.assertEqual(projection["evidence_count"], 0)
        self.assertIsNone(projection["upside_range"])
        self.assertIsNone(projection["downside_range"])


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


def _pattern_library_without_outcomes() -> list[dict[str, object]]:
    return [
        {
            "pattern_id": "partial-one",
            "trend": "up",
            "trend_slope": 70.0,
            "adx": 31.0,
            "rsi": 58.0,
            "atr": 2.1,
            "squeeze": "released",
            "market_structure": "higher_high",
        },
        {
            "pattern_id": "partial-two",
            "trend": "up",
            "trend_slope": 68.0,
            "adx": 30.0,
            "rsi": 57.0,
            "atr": 2.2,
            "squeeze": "released",
            "market_structure": "higher_high",
        },
    ]


if __name__ == "__main__":
    unittest.main()
