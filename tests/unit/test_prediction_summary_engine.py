import unittest

from src.analysis import build_prediction_summary


class PredictionSummaryEngineTest(unittest.TestCase):
    def test_empty_inputs_return_safe_summary(self) -> None:
        result = build_prediction_summary()

        self.assertEqual(
            result,
            {
                "confidence": 0.0,
                "evidence_count": 0,
                "best_pattern_id": None,
                "best_similarity": 0.0,
                "probability": {},
                "projection": {},
                "target_zone": None,
                "risk_zone": None,
            },
        )

    def test_builds_prediction_summary_sections(self) -> None:
        probability = _probability()
        projection = _projection()
        target_zone = _target_zone()
        risk_zone = _risk_zone()

        result = build_prediction_summary(
            probability=probability,
            projection=projection,
            target_zone=target_zone,
            risk_zone=risk_zone,
        )

        self.assertEqual(result["probability"], probability)
        self.assertEqual(result["projection"], projection)
        self.assertEqual(result["target_zone"], target_zone["target_zone"])
        self.assertEqual(result["risk_zone"], risk_zone["risk_zone"])

    def test_preserves_key_metadata_from_probability(self) -> None:
        result = build_prediction_summary(
            probability=_probability(),
            projection={**_projection(), "confidence": 20.0},
            target_zone=_target_zone(),
            risk_zone=_risk_zone(),
        )

        self.assertEqual(result["confidence"], 74.0)
        self.assertEqual(result["evidence_count"], 12)
        self.assertEqual(result["best_pattern_id"], "pattern-1")
        self.assertEqual(result["best_similarity"], 91.0)

    def test_uses_later_metadata_when_probability_is_missing(self) -> None:
        result = build_prediction_summary(
            projection=_projection(),
            target_zone=_target_zone(),
            risk_zone=_risk_zone(),
        )

        self.assertEqual(result["confidence"], 68.0)
        self.assertEqual(result["evidence_count"], 8)
        self.assertEqual(result["best_pattern_id"], "pattern-2")
        self.assertEqual(result["best_similarity"], 88.0)

    def test_clamps_metadata_bounds(self) -> None:
        result = build_prediction_summary(
            probability={
                "confidence": 125.0,
                "evidence_count": -5,
                "best_pattern_id": "pattern-1",
                "best_similarity": -20.0,
            }
        )

        self.assertEqual(result["confidence"], 100.0)
        self.assertEqual(result["evidence_count"], 0)
        self.assertEqual(result["best_similarity"], 0.0)

    def test_output_has_no_trade_decision(self) -> None:
        result = build_prediction_summary(
            probability=_probability(),
            projection=_projection(),
            target_zone=_target_zone(),
            risk_zone=_risk_zone(),
        )

        values = {str(value).upper() for value in result.values()}
        self.assertNotIn("BUY", values)
        self.assertNotIn("SELL", values)
        self.assertNotIn("HOLD", values)


def _probability() -> dict[str, object]:
    return {
        "probability_positive": 65.0,
        "probability_negative": 20.0,
        "probability_neutral": 15.0,
        "confidence": 74.0,
        "evidence_count": 12,
        "best_pattern_id": "pattern-1",
        "best_similarity": 91.0,
    }


def _projection() -> dict[str, object]:
    return {
        "current_price": 100.0,
        "expected_price_10d": 104.0,
        "upside_range": {"low": 102.0, "high": 108.0},
        "downside_range": {"low": 94.0, "high": 99.0},
        "confidence": 68.0,
        "evidence_count": 8,
        "best_pattern_id": "pattern-2",
        "best_similarity": 88.0,
    }


def _target_zone() -> dict[str, object]:
    return {
        "target_zone": {
            "conservative": 102.0,
            "base": 104.0,
            "aggressive": 108.0,
        },
        "confidence": 68.0,
        "evidence_count": 8,
        "best_pattern_id": "pattern-2",
        "best_similarity": 88.0,
    }


def _risk_zone() -> dict[str, object]:
    return {
        "risk_zone": {
            "conservative": 99.0,
            "base": 98.0,
            "aggressive": 94.0,
        },
        "confidence": 68.0,
        "evidence_count": 8,
        "best_pattern_id": "pattern-2",
        "best_similarity": 88.0,
    }


if __name__ == "__main__":
    unittest.main()
