import unittest

from src.analysis import calculate_risk_zone


class RiskZoneEngineTest(unittest.TestCase):
    def test_empty_projection_returns_safe_risk_zone(self) -> None:
        result = calculate_risk_zone({})

        self.assertIsNone(result["risk_zone"])
        self.assertEqual(result["confidence"], 0.0)
        self.assertEqual(result["evidence_count"], 0)

    def test_derives_risk_zone_from_downside_range(self) -> None:
        result = calculate_risk_zone(
            {
                "expected_price_10d": 96.0,
                "downside_range": {"low": 90.0, "high": 98.0},
                "confidence": 72.5,
                "evidence_count": 12,
                "best_pattern_id": "pattern-1",
                "best_similarity": 91.0,
            }
        )

        self.assertEqual(
            result["risk_zone"],
            {
                "conservative": 98.0,
                "base": 96.0,
                "aggressive": 90.0,
            },
        )
        self.assertEqual(result["confidence"], 72.5)
        self.assertEqual(result["evidence_count"], 12)
        self.assertEqual(result["best_pattern_id"], "pattern-1")
        self.assertEqual(result["best_similarity"], 91.0)

    def test_base_is_clamped_to_downside_range(self) -> None:
        low_result = calculate_risk_zone(
            {
                "expected_price_10d": 80.0,
                "downside_range": {"low": 90.0, "high": 98.0},
            }
        )
        high_result = calculate_risk_zone(
            {
                "expected_price_10d": 105.0,
                "downside_range": {"low": 90.0, "high": 98.0},
            }
        )

        self.assertEqual(low_result["risk_zone"]["base"], 90.0)
        self.assertEqual(high_result["risk_zone"]["base"], 98.0)

    def test_reversed_downside_range_is_normalized(self) -> None:
        result = calculate_risk_zone(
            {
                "expected_price_10d": 95.0,
                "downside_range": {"low": 98.0, "high": 90.0},
            }
        )

        self.assertEqual(result["risk_zone"]["conservative"], 98.0)
        self.assertEqual(result["risk_zone"]["aggressive"], 90.0)

    def test_missing_downside_fields_do_not_crash(self) -> None:
        result = calculate_risk_zone(
            {
                "expected_price_10d": 95.0,
                "downside_range": {"low": 90.0},
                "confidence": 55.0,
                "evidence_count": 3,
            }
        )

        self.assertIsNone(result["risk_zone"])
        self.assertEqual(result["confidence"], 55.0)
        self.assertEqual(result["evidence_count"], 3)

    def test_output_has_no_trade_decision(self) -> None:
        result = calculate_risk_zone(
            {
                "expected_price_10d": 96.0,
                "downside_range": {"low": 90.0, "high": 98.0},
            }
        )

        values = {str(value).upper() for value in result.values()}
        self.assertNotIn("BUY", values)
        self.assertNotIn("SELL", values)
        self.assertNotIn("HOLD", values)


if __name__ == "__main__":
    unittest.main()
