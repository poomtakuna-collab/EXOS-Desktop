import unittest

from src.analysis import calculate_price_projection


def _resolver_match(
    pattern_id: str,
    similarity: float = 90.0,
    sample_count: int = 1,
    average_10d_return: float = 4.0,
) -> dict[str, object]:
    return {
        "pattern_id": pattern_id,
        "similarity": similarity,
        "outcome": "Bull",
        "pattern": {
            "pattern_id": pattern_id,
            "sample_count": sample_count,
            "average_5d_return": average_10d_return / 2,
            "average_10d_return": average_10d_return,
            "average_20d_return": average_10d_return * 2,
            "average_max_gain": max(average_10d_return + 2, 0.0),
            "average_drawdown": min(average_10d_return - 6, 0.0),
        },
    }


class PriceProjectionEngineTest(unittest.TestCase):
    def test_empty_matches_return_safe_projection(self) -> None:
        result = calculate_price_projection(100.0, {"matches": []})

        self.assertEqual(result["current_price"], 100.0)
        self.assertEqual(result["expected_price_10d"], 100.0)
        self.assertIsNone(result["upside_range"])
        self.assertIsNone(result["downside_range"])
        self.assertEqual(result["evidence_count"], 0)

    def test_calculates_projection_from_resolver_matches(self) -> None:
        result = calculate_price_projection(
            100.0,
            {
                "matches": [
                    _resolver_match("strong", similarity=100.0, average_10d_return=8.0),
                    _resolver_match("weak", similarity=50.0, average_10d_return=-4.0),
                ]
            },
        )

        self.assertEqual(result["expected_return_5d"], 2.0)
        self.assertEqual(result["expected_return_10d"], 4.0)
        self.assertEqual(result["expected_return_20d"], 8.0)
        self.assertEqual(result["expected_price_10d"], 104.0)
        self.assertEqual(result["upside_range"], {"low": 104.0, "high": 106.6667})
        self.assertEqual(result["downside_range"], {"low": 96.6667, "high": 100.0})
        self.assertEqual(result["best_pattern_id"], "strong")

    def test_accepts_probability_compatible_match_rows(self) -> None:
        result = calculate_price_projection(
            50.0,
            [
                {
                    "pattern_id": "legacy",
                    "similarity_score": 80.0,
                    "sample_count": 2,
                    "average_5d_return": 1.0,
                    "average_10d_return": 3.0,
                    "average_20d_return": 5.0,
                    "average_max_gain": 7.0,
                    "average_drawdown": -2.0,
                }
            ],
        )

        self.assertEqual(result["expected_price_5d"], 50.5)
        self.assertEqual(result["expected_price_10d"], 51.5)
        self.assertEqual(result["expected_price_20d"], 52.5)
        self.assertEqual(result["upside_range"], {"low": 51.5, "high": 53.5})
        self.assertEqual(result["downside_range"], {"low": 49.0, "high": 50.0})
        self.assertEqual(result["evidence_count"], 2)

    def test_missing_outcome_fields_do_not_crash(self) -> None:
        result = calculate_price_projection(
            100.0,
            {
                "matches": [
                    {
                        "pattern_id": "partial",
                        "similarity": 75.0,
                        "pattern": {},
                    }
                ]
            },
        )

        self.assertEqual(result["expected_price_10d"], 100.0)
        self.assertEqual(result["evidence_count"], 0)

    def test_projection_is_deterministic(self) -> None:
        matches = {"matches": [_resolver_match("one"), _resolver_match("two", 70.0)]}

        first = calculate_price_projection(123.45, matches)
        second = calculate_price_projection(123.45, matches)

        self.assertEqual(first, second)

    def test_output_has_no_trade_decision(self) -> None:
        result = calculate_price_projection(
            100.0,
            {"matches": [_resolver_match("positive")]},
        )

        values = {str(value).upper() for value in result.values()}
        self.assertNotIn("BUY", values)
        self.assertNotIn("SELL", values)
        self.assertNotIn("HOLD", values)


if __name__ == "__main__":
    unittest.main()
