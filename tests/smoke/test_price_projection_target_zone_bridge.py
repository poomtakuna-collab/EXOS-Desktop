import unittest

from src.analysis import calculate_price_projection, calculate_target_zone


CURRENT_PRICE = 100.0


class PriceProjectionTargetZoneBridgeSmokeTest(unittest.TestCase):
    def test_price_projection_output_feeds_target_zone_engine(self) -> None:
        projection = calculate_price_projection(CURRENT_PRICE, _historical_matches())

        target_result = calculate_target_zone(projection)

        self.assertEqual(
            set(target_result),
            {
                "target_zone",
                "confidence",
                "evidence_count",
                "best_pattern_id",
                "best_similarity",
            },
        )
        self.assertIsInstance(target_result["target_zone"], dict)
        self.assertEqual(
            set(target_result["target_zone"]),
            {"conservative", "base", "aggressive"},
        )
        self.assertLessEqual(
            target_result["target_zone"]["conservative"],
            target_result["target_zone"]["base"],
        )
        self.assertLessEqual(
            target_result["target_zone"]["base"],
            target_result["target_zone"]["aggressive"],
        )
        self.assertEqual(target_result["confidence"], projection["confidence"])
        self.assertEqual(target_result["evidence_count"], projection["evidence_count"])
        self.assertEqual(
            target_result["best_pattern_id"],
            projection["best_pattern_id"],
        )
        self.assertEqual(
            target_result["best_similarity"],
            projection["best_similarity"],
        )

    def test_empty_projection_fields_are_handled_safely(self) -> None:
        projection = calculate_price_projection(CURRENT_PRICE, {"matches": []})

        target_result = calculate_target_zone(projection)

        self.assertIsNone(target_result["target_zone"])
        self.assertEqual(target_result["confidence"], 0.0)
        self.assertEqual(target_result["evidence_count"], 0)
        self.assertIsNone(target_result["best_pattern_id"])
        self.assertEqual(target_result["best_similarity"], 0.0)


def _historical_matches() -> list[dict[str, object]]:
    return [
        {
            "pattern_id": "strong-upside",
            "similarity_score": 90.0,
            "sample_count": 1,
            "average_5d_return": 2.0,
            "average_10d_return": 4.0,
            "average_20d_return": 6.0,
            "average_max_gain": 8.0,
            "average_drawdown": -2.0,
        },
        {
            "pattern_id": "moderate-upside",
            "similarity_score": 70.0,
            "sample_count": 1,
            "average_5d_return": 1.0,
            "average_10d_return": 3.0,
            "average_20d_return": 5.0,
            "average_max_gain": 6.0,
            "average_drawdown": -1.0,
        },
    ]


if __name__ == "__main__":
    unittest.main()
