import unittest

from src.analysis import calculate_target_zone


class TargetZoneEngineTest(unittest.TestCase):
    def test_empty_projection_returns_safe_target_zone(self) -> None:
        result = calculate_target_zone({})

        self.assertIsNone(result["target_zone"])
        self.assertEqual(result["confidence"], 0.0)
        self.assertEqual(result["evidence_count"], 0)

    def test_derives_target_zone_from_upside_range(self) -> None:
        result = calculate_target_zone(
            {
                "expected_price_10d": 104.0,
                "upside_range": {"low": 102.0, "high": 108.0},
                "confidence": 72.5,
                "evidence_count": 12,
                "best_pattern_id": "pattern-1",
                "best_similarity": 91.0,
            }
        )

        self.assertEqual(
            result["target_zone"],
            {
                "conservative": 102.0,
                "base": 104.0,
                "aggressive": 108.0,
            },
        )
        self.assertEqual(result["confidence"], 72.5)
        self.assertEqual(result["evidence_count"], 12)
        self.assertEqual(result["best_pattern_id"], "pattern-1")
        self.assertEqual(result["best_similarity"], 91.0)

    def test_base_is_clamped_to_upside_range(self) -> None:
        low_result = calculate_target_zone(
            {
                "expected_price_10d": 99.0,
                "upside_range": {"low": 102.0, "high": 108.0},
            }
        )
        high_result = calculate_target_zone(
            {
                "expected_price_10d": 120.0,
                "upside_range": {"low": 102.0, "high": 108.0},
            }
        )

        self.assertEqual(low_result["target_zone"]["base"], 102.0)
        self.assertEqual(high_result["target_zone"]["base"], 108.0)

    def test_reversed_upside_range_is_normalized(self) -> None:
        result = calculate_target_zone(
            {
                "expected_price_10d": 105.0,
                "upside_range": {"low": 110.0, "high": 102.0},
            }
        )

        self.assertEqual(result["target_zone"]["conservative"], 102.0)
        self.assertEqual(result["target_zone"]["aggressive"], 110.0)

    def test_missing_upside_fields_do_not_crash(self) -> None:
        result = calculate_target_zone(
            {
                "expected_price_10d": 105.0,
                "upside_range": {"low": 102.0},
                "confidence": 55.0,
                "evidence_count": 3,
            }
        )

        self.assertIsNone(result["target_zone"])
        self.assertEqual(result["confidence"], 55.0)
        self.assertEqual(result["evidence_count"], 3)

    def test_output_has_no_trade_decision(self) -> None:
        result = calculate_target_zone(
            {
                "expected_price_10d": 104.0,
                "upside_range": {"low": 102.0, "high": 108.0},
            }
        )

        values = {str(value).upper() for value in result.values()}
        self.assertNotIn("BUY", values)
        self.assertNotIn("SELL", values)
        self.assertNotIn("HOLD", values)


if __name__ == "__main__":
    unittest.main()
