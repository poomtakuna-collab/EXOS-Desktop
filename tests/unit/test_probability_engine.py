import unittest

from src.analysis import calculate_probability_summary


def _match(
    pattern_id: str,
    similarity: float,
    outcome: str,
    sample_count: int = 1,
    average_10d_return: float = 0.0,
) -> dict[str, object]:
    return {
        "pattern_id": pattern_id,
        "similarity": similarity,
        "outcome": outcome,
        "pattern": {
            "pattern_id": pattern_id,
            "sample_count": sample_count,
            "average_5d_return": average_10d_return / 2,
            "average_10d_return": average_10d_return,
            "average_20d_return": average_10d_return * 2,
            "average_max_gain": max(average_10d_return, 0.0),
            "average_drawdown": min(average_10d_return, 0.0),
        },
    }


class ProbabilityEngineTest(unittest.TestCase):
    def test_empty_matches_returns_safe_summary(self) -> None:
        result = calculate_probability_summary({"matches": []})

        self.assertEqual(result["probability_positive"], 0.0)
        self.assertEqual(result["probability_negative"], 0.0)
        self.assertEqual(result["probability_neutral"], 0.0)
        self.assertEqual(result["evidence_count"], 0)
        self.assertIsNone(result["best_pattern_id"])

    def test_calculates_weighted_probabilities_from_resolver_output(self) -> None:
        result = calculate_probability_summary(
            {
                "matches": [
                    _match("positive", 90.0, "win", sample_count=2),
                    _match("negative", 60.0, "loss", sample_count=1),
                    _match("neutral", 30.0, "sideway", sample_count=1),
                ]
            }
        )

        self.assertEqual(result["probability_positive"], 66.6667)
        self.assertEqual(result["probability_negative"], 22.2222)
        self.assertEqual(result["probability_neutral"], 11.1111)
        self.assertEqual(result["evidence_count"], 4)
        self.assertEqual(result["best_pattern_id"], "positive")
        self.assertEqual(result["best_similarity"], 90.0)

    def test_calculates_weighted_return_summary(self) -> None:
        result = calculate_probability_summary(
            {
                "matches": [
                    _match("strong", 100.0, "Strong Bull", average_10d_return=8.0),
                    _match("weak", 50.0, "Bear", average_10d_return=-4.0),
                ]
            }
        )

        self.assertEqual(result["expected_return_5d"], 2.0)
        self.assertEqual(result["expected_return_10d"], 4.0)
        self.assertEqual(result["expected_return_20d"], 8.0)
        self.assertEqual(result["expected_max_gain_10d"], 5.3333)
        self.assertEqual(result["expected_drawdown_10d"], -1.3333)

    def test_ignores_matches_without_recognized_outcomes(self) -> None:
        result = calculate_probability_summary(
            {
                "matches": [
                    _match("known", 75.0, "Bull", average_10d_return=6.0),
                    _match("unknown", 100.0, "mystery", average_10d_return=-10.0),
                ]
            }
        )

        self.assertEqual(result["probability_positive"], 100.0)
        self.assertEqual(result["probability_negative"], 0.0)
        self.assertEqual(result["expected_return_10d"], 6.0)
        self.assertEqual(result["evidence_count"], 1)

    def test_missing_fields_do_not_crash(self) -> None:
        result = calculate_probability_summary(
            {
                "matches": [
                    {
                        "pattern_id": "partial",
                        "similarity": 80.0,
                        "outcome": "win",
                        "pattern": {},
                    }
                ]
            }
        )

        self.assertEqual(result["probability_positive"], 100.0)
        self.assertEqual(result["evidence_count"], 1)
        self.assertGreaterEqual(result["confidence"], 0.0)

    def test_output_has_no_trade_decision(self) -> None:
        result = calculate_probability_summary(
            {"matches": [_match("positive", 90.0, "win")]}
        )

        values = {str(value).upper() for value in result.values()}
        self.assertNotIn("BUY", values)
        self.assertNotIn("SELL", values)
        self.assertNotIn("HOLD", values)


if __name__ == "__main__":
    unittest.main()
