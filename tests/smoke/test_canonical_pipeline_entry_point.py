import unittest

from src.analysis_pipeline import (
    AnalysisRequest,
    CanonicalAnalysisResultV1,
    analyze_symbol,
    analyze_symbol_with_canonical_brain,
)


class CanonicalPipelineEntryPointSmokeTest(unittest.TestCase):
    def test_opt_in_entry_point_does_not_change_legacy_analyze_symbol(self) -> None:
        legacy_request = AnalysisRequest(
            symbol="AAPL",
            ohlcv_rows=_ohlcv_rows(),
            similar_patterns=_legacy_similar_patterns(),
        )
        canonical_request = AnalysisRequest(
            symbol="AAPL",
            ohlcv_rows=_ohlcv_rows(),
            similar_patterns=_canonical_pattern_library(),
        )

        legacy_before = analyze_symbol(legacy_request)
        canonical_result = analyze_symbol_with_canonical_brain(canonical_request)
        legacy_after = analyze_symbol(legacy_request)

        self.assertEqual(legacy_before, legacy_after)
        self.assertIsInstance(canonical_result, CanonicalAnalysisResultV1)
        self.assertEqual(
            canonical_result.metadata["entry_point"],
            "analyze_symbol_with_canonical_brain",
        )
        self.assertEqual(
            canonical_result.metadata["analysis_result_mapping"],
            "separate_result_type",
        )
        self.assertEqual(
            canonical_result.canonical_brain.metadata["adapter"],
            "canonical_brain_adapter_v1",
        )
        self.assertNotEqual(canonical_result.canonical_brain.prediction_summary, {})


def _ohlcv_rows(count: int = 240) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for index in range(count):
        close = 100.0 + index * 0.25
        rows.append(
            {
                "date": f"2026-04-{index % 28 + 1:02d}",
                "open": close - 0.25,
                "high": close + 1.0,
                "low": close - 1.0,
                "close": close,
                "volume": 1_000_000 + index,
            }
        )
    return rows


def _legacy_similar_patterns() -> list[dict[str, object]]:
    return [
        {
            "pattern_id": 101,
            "similarity_score": 92.0,
            "confidence": 80.0,
            "sample_count": 30,
            "average_5d_return": 2.0,
            "average_10d_return": 4.0,
            "average_20d_return": 6.0,
            "hit_5pct_rate": 55.0,
            "hit_10pct_rate": 25.0,
            "average_max_gain": 8.0,
            "average_drawdown": -3.0,
        }
    ]


def _canonical_pattern_library() -> list[dict[str, object]]:
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
