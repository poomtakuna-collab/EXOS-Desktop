from dataclasses import FrozenInstanceError, is_dataclass
import unittest

from src.analysis_pipeline import (
    AnalysisRequest,
    CanonicalAnalysisResultV1,
    analyze_symbol_with_canonical_brain,
)


class CanonicalPipelineTest(unittest.TestCase):
    def test_public_entry_point_returns_separate_immutable_result(self) -> None:
        request = AnalysisRequest(
            symbol="AAPL",
            ohlcv_rows=_ohlcv_rows(),
            similar_patterns=_pattern_library(),
        )

        result = analyze_symbol_with_canonical_brain(request)

        self.assertTrue(is_dataclass(CanonicalAnalysisResultV1))
        self.assertIsInstance(result, CanonicalAnalysisResultV1)
        self.assertEqual(result.request, request)
        self.assertEqual(result.config, request.config)
        self.assertEqual(result.symbol, "AAPL")
        self.assertEqual(result.timeframe, "1D")
        self.assertEqual(
            result.metadata["analysis_result_mapping"],
            "separate_result_type",
        )
        self.assertIn("Prediction Summary is nested", result.metadata["mapping_reason"])

        with self.assertRaises(FrozenInstanceError):
            result.symbol = "MSFT"

    def test_entry_point_uses_canonical_adapter_output(self) -> None:
        request = AnalysisRequest(
            symbol="AAPL",
            ohlcv_rows=_ohlcv_rows(),
            similar_patterns=_pattern_library(),
        )

        result = analyze_symbol_with_canonical_brain(request)

        self.assertEqual(
            result.canonical_brain.metadata["adapter"],
            "canonical_brain_adapter_v1",
        )
        self.assertEqual(result.canonical_brain.metadata["canonical_path"], "src.analysis")
        self.assertNotEqual(result.canonical_brain.snapshot, {})
        self.assertNotEqual(result.canonical_brain.resolver_output, {"matches": []})
        self.assertNotEqual(result.canonical_brain.probability, {})
        self.assertNotEqual(result.canonical_brain.prediction_summary, {})

    def test_empty_request_returns_safe_defaults(self) -> None:
        result = analyze_symbol_with_canonical_brain(AnalysisRequest(symbol="AAPL"))

        self.assertEqual(result.symbol, "AAPL")
        self.assertEqual(result.metadata["rows"], 0)
        self.assertEqual(result.metadata["pattern_count"], 0)
        self.assertEqual(result.metadata["match_count"], 0)
        self.assertEqual(result.canonical_brain.snapshot, {})
        self.assertEqual(result.canonical_brain.resolver_output, {"matches": []})
        self.assertIn("No OHLCV rows supplied", " ".join(result.notes))

    def test_none_request_returns_safe_defaults(self) -> None:
        result = analyze_symbol_with_canonical_brain(None)

        self.assertIsNone(result.request)
        self.assertEqual(result.symbol, "")
        self.assertEqual(result.timeframe, "1D")
        self.assertEqual(result.metadata["rows"], 0)
        self.assertEqual(result.canonical_brain.snapshot, {})
        self.assertIn("No AnalysisRequest supplied", " ".join(result.notes))

    def test_output_is_deterministic_for_fixed_inputs(self) -> None:
        request = AnalysisRequest(
            symbol="AAPL",
            ohlcv_rows=_ohlcv_rows(),
            similar_patterns=_pattern_library(),
        )

        first = analyze_symbol_with_canonical_brain(request)
        second = analyze_symbol_with_canonical_brain(request)

        self.assertEqual(first, second)
        self.assertEqual(first.metadata, second.metadata)
        self.assertEqual(first.notes, second.notes)


def _ohlcv_rows(count: int = 240) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for index in range(count):
        close = 100.0 + index * 0.5
        rows.append(
            {
                "date": f"2026-03-{index % 28 + 1:02d}",
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
            "sample_count": 5,
            "average_5d_return": 2.0,
            "average_10d_return": 4.0,
            "average_20d_return": 6.0,
            "average_max_gain": 7.0,
            "average_drawdown": -2.0,
        }
    ]


if __name__ == "__main__":
    unittest.main()
