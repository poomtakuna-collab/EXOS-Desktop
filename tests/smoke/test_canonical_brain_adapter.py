import unittest

from src.analysis_pipeline import AnalysisRequest, build_canonical_brain_analysis


class CanonicalBrainAdapterSmokeTest(unittest.TestCase):
    def test_adapter_builds_deterministic_canonical_output(self) -> None:
        request = AnalysisRequest(
            symbol="AAPL",
            ohlcv_rows=_ohlcv_rows(),
            similar_patterns=_pattern_library(),
        )

        first = build_canonical_brain_analysis(request)
        second = build_canonical_brain_analysis(request)

        self.assertEqual(first, second)
        self.assertNotEqual(first.snapshot, {})
        self.assertNotEqual(first.resolver_output, {"matches": []})
        self.assertNotEqual(first.probability, {})
        self.assertNotEqual(first.projection, {})
        self.assertIn("target_zone", first.target_zone)
        self.assertIn("risk_zone", first.risk_zone)
        self.assertNotEqual(first.prediction_summary, {})
        self.assertEqual(first.metadata["adapter"], "canonical_brain_adapter_v1")

        output_values = {
            value.upper()
            for value in _flatten_values(
                {
                    "result": first.__dict__,
                }
            )
        }
        self.assertNotIn("BUY", output_values)
        self.assertNotIn("SELL", output_values)
        self.assertNotIn("HOLD", output_values)


def _ohlcv_rows(count: int = 240) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for index in range(count):
        close = 100.0 + index * 0.5
        rows.append(
            {
                "date": f"2026-02-{index % 28 + 1:02d}",
                "open": close - 0.25,
                "high": close + 1.0,
                "low": close - 1.0,
                "close": close,
                "volume": 1_000_000 + index,
            }
        )
    return rows


def _pattern_library() -> list[dict[str, object]]:
    return [
        {
            "pattern_id": "positive-pattern",
            "trend": "bullish",
            "trend_slope": 95.0,
            "squeeze": "NONE",
            "market_structure": "BULLISH",
            "dominant_label": "Bull",
            "sample_count": 8,
            "average_5d_return": 2.0,
            "average_10d_return": 4.0,
            "average_20d_return": 6.0,
            "average_max_gain": 7.0,
            "average_drawdown": -2.0,
        },
        {
            "pattern_id": "neutral-pattern",
            "trend": "mixed",
            "trend_slope": 50.0,
            "squeeze": "NONE",
            "market_structure": "RANGE",
            "dominant_label": "Sideways",
            "sample_count": 3,
            "average_5d_return": 0.2,
            "average_10d_return": 0.5,
            "average_20d_return": 0.8,
            "average_max_gain": 2.0,
            "average_drawdown": -1.0,
        },
    ]


def _flatten_values(value: object) -> list[str]:
    if isinstance(value, dict):
        flattened: list[str] = []
        for item in value.values():
            flattened.extend(_flatten_values(item))
        return flattened
    if isinstance(value, list):
        flattened = []
        for item in value:
            flattened.extend(_flatten_values(item))
        return flattened
    return [str(value)]


if __name__ == "__main__":
    unittest.main()
