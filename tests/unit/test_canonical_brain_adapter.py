import unittest

from src.analysis_pipeline import (
    CANONICAL_BRAIN_CHAIN,
    AnalysisRequest,
    CanonicalBrainAdapterResult,
    PipelineConfig,
    build_canonical_brain_analysis,
)


class CanonicalBrainAdapterTest(unittest.TestCase):
    def test_empty_inputs_return_safe_defaults(self) -> None:
        result = build_canonical_brain_analysis(AnalysisRequest(symbol="AAPL"))

        self.assertIsInstance(result, CanonicalBrainAdapterResult)
        self.assertEqual(result.snapshot, {})
        self.assertEqual(result.resolver_output, {"matches": []})
        self.assertEqual(result.probability["evidence_count"], 0)
        self.assertEqual(result.projection["current_price"], 0.0)
        self.assertEqual(result.prediction_summary["evidence_count"], 0)
        self.assertEqual(result.metadata["adapter"], "canonical_brain_adapter_v1")
        self.assertEqual(result.metadata["canonical_path"], "src.analysis")
        self.assertEqual(result.metadata["rows"], 0)
        self.assertEqual(result.metadata["pattern_count"], 0)
        self.assertEqual(result.metadata["match_count"], 0)
        self.assertIn("No OHLCV rows supplied", result.notes[0])

    def test_malformed_inputs_return_safe_defaults(self) -> None:
        result = build_canonical_brain_analysis(
            AnalysisRequest(
                symbol="AAPL",
                ohlcv_rows=[{"date": "2026-01-01"}],
                similar_patterns=[None, "bad-pattern"],  # type: ignore[list-item]
            )
        )

        self.assertEqual(result.snapshot, {})
        self.assertEqual(result.resolver_output, {"matches": []})
        self.assertEqual(result.metadata["pattern_count"], 0)
        self.assertEqual(result.metadata["current_price"], 0.0)
        self.assertTrue(
            any(note.startswith("Malformed OHLCV rows supplied") for note in result.notes)
        )
        self.assertTrue(
            any(note.startswith("Latest close is unavailable") for note in result.notes)
        )

    def test_deterministic_output_for_fixed_inputs(self) -> None:
        request = AnalysisRequest(
            symbol="AAPL",
            ohlcv_rows=_ohlcv_rows(),
            similar_patterns=_pattern_library(),
        )

        first = build_canonical_brain_analysis(request)
        second = build_canonical_brain_analysis(request)

        self.assertEqual(first, second)
        self.assertGreater(first.probability["evidence_count"], 0)
        self.assertEqual(first.probability["best_pattern_id"], "positive-pattern")
        self.assertEqual(
            first.prediction_summary["probability"],
            first.probability,
        )
        self.assertEqual(
            first.prediction_summary["projection"],
            first.projection,
        )

    def test_metadata_shape_identifies_canonical_chain(self) -> None:
        request = AnalysisRequest(
            symbol="MSFT",
            config=PipelineConfig(timeframe="1D"),
            ohlcv_rows=_ohlcv_rows(),
            similar_patterns=_pattern_library(),
        )

        result = build_canonical_brain_analysis(request)

        self.assertEqual(
            set(result.metadata),
            {
                "adapter",
                "canonical_path",
                "chain",
                "symbol",
                "timeframe",
                "rows",
                "pattern_count",
                "match_count",
                "current_price",
            },
        )
        self.assertEqual(result.metadata["chain"], list(CANONICAL_BRAIN_CHAIN))
        self.assertEqual(result.metadata["symbol"], "MSFT")
        self.assertEqual(result.metadata["timeframe"], "1D")
        self.assertEqual(result.metadata["rows"], len(_ohlcv_rows()))
        self.assertEqual(result.metadata["pattern_count"], len(_pattern_library()))
        self.assertEqual(result.metadata["match_count"], len(_pattern_library()))
        self.assertGreater(result.metadata["current_price"], 0.0)

    def test_config_can_skip_probability_and_prediction_sections(self) -> None:
        request = AnalysisRequest(
            symbol="AAPL",
            config=PipelineConfig(include_probability=False, include_prediction=False),
            ohlcv_rows=_ohlcv_rows(),
            similar_patterns=_pattern_library(),
        )

        result = build_canonical_brain_analysis(request)

        self.assertNotEqual(result.snapshot, {})
        self.assertNotEqual(result.resolver_output, {"matches": []})
        self.assertEqual(result.probability, {})
        self.assertEqual(result.projection, {})
        self.assertEqual(result.target_zone, {})
        self.assertEqual(result.risk_zone, {})
        self.assertEqual(result.prediction_summary, {})


def _ohlcv_rows(count: int = 240) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for index in range(count):
        close = 100.0 + index * 0.5
        rows.append(
            {
                "date": f"2026-01-{index % 28 + 1:02d}",
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
        },
        {
            "pattern_id": "negative-pattern",
            "trend": "bearish",
            "trend_slope": 10.0,
            "squeeze": "COMPRESSION",
            "market_structure": "BEARISH",
            "dominant_label": "Bear",
            "sample_count": 2,
            "average_5d_return": -1.0,
            "average_10d_return": -3.0,
            "average_20d_return": -5.0,
            "average_max_gain": 1.0,
            "average_drawdown": -6.0,
        },
    ]


if __name__ == "__main__":
    unittest.main()
