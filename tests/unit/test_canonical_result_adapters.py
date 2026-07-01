from __future__ import annotations

import ast
import inspect
import json
import sys
import unittest
from types import SimpleNamespace

import src.canonical_result.adapters as adapters_module
from src.canonical_result import (
    ADAPTER_VERSION_V1,
    CanonicalBrainResultV1,
    CanonicalDiagnosticsV1,
    CanonicalIdentityV1,
    CanonicalPredictionResultV1,
    CanonicalResultV1,
    build_canonical_brain_result_v1,
    build_canonical_diagnostics_v1,
    build_canonical_identity_v1,
    build_canonical_prediction_result_v1,
    build_canonical_result_v1,
)


class CanonicalResultAdaptersTest(unittest.TestCase):
    def test_public_adapter_imports(self) -> None:
        self.assertEqual(ADAPTER_VERSION_V1, "canonical_result_adapter_v1")
        self.assertIsNotNone(build_canonical_result_v1)
        self.assertIsNotNone(build_canonical_identity_v1)
        self.assertIsNotNone(build_canonical_brain_result_v1)
        self.assertIsNotNone(build_canonical_prediction_result_v1)
        self.assertIsNotNone(build_canonical_diagnostics_v1)

    def test_maps_canonical_pipeline_object_shape(self) -> None:
        source = SimpleNamespace(
            symbol="AAPL",
            timeframe="1D",
            canonical_brain=SimpleNamespace(
                snapshot={
                    "symbol": "AAPL",
                    "timeframe": "1D",
                    "snapshot_id": "snapshot-1",
                    "snapshot_date": "2026-07-01",
                },
                resolver_output={"matches": [{"pattern_id": "p1"}]},
                probability={
                    "probability_positive": 64.0,
                    "probability_negative": 24.0,
                    "probability_neutral": 12.0,
                    "expected_return_10d": 4.5,
                    "confidence": 70.0,
                    "evidence_count": 20,
                },
                projection={
                    "expected_price_5d": 104.0,
                    "expected_price_10d": 108.0,
                    "expected_price_20d": 114.0,
                    "expected_return_5d": 2.0,
                    "expected_return_10d": 4.5,
                    "expected_return_20d": 8.0,
                    "best_pattern_id": "p1",
                    "best_similarity": 91.0,
                },
                target_zone={
                    "target_zone": {
                        "conservative": 106.0,
                        "base": 108.0,
                        "aggressive": 112.0,
                    }
                },
                risk_zone={
                    "risk_zone": {
                        "conservative": 98.0,
                        "base": 96.0,
                        "aggressive": 94.0,
                    }
                },
                prediction_summary={
                    "confidence": 72.0,
                    "evidence_count": 20,
                    "best_pattern_id": "p1",
                    "best_similarity": 91.0,
                },
                metadata={
                    "canonical_path": "src.analysis",
                    "symbol": "AAPL",
                    "timeframe": "1D",
                    "pattern_count": 5,
                },
                notes=["canonical brain adapter note"],
            ),
            data_source_metadata={"market_data": {"source": "memory"}},
            metadata={
                "entry_point": "analyze_symbol_v2",
                "result_type": "CanonicalAnalysisResultV2",
                "rows": 300,
                "future_rows": 10,
                "similar_patterns": 5,
            },
            notes=["pipeline note"],
        )

        result = build_canonical_result_v1(source)

        self.assertIsInstance(result, CanonicalResultV1)
        self.assertEqual(result.identity.symbol, "AAPL")
        self.assertEqual(result.identity.timeframe, "1D")
        self.assertEqual(result.identity.snapshot_id, "snapshot-1")
        self.assertEqual(result.identity.source, "src.analysis")
        self.assertEqual(result.identity.pipeline_name, "analyze_symbol_v2")
        self.assertEqual(result.brain.snapshot["snapshot_id"], "snapshot-1")
        self.assertEqual(result.brain.resolver_output["matches"][0]["pattern_id"], "p1")
        self.assertIsNotNone(result.prediction)
        self.assertEqual(result.prediction.confidence, 72.0)
        self.assertEqual(result.prediction.probability_positive, 64.0)
        self.assertEqual(result.prediction.expected_price_10d, 108.0)
        self.assertEqual(result.prediction.target_base, 108.0)
        self.assertEqual(result.prediction.risk_aggressive, 94.0)
        self.assertEqual(result.diagnostics.source_pipeline, "analyze_symbol_v2")
        self.assertEqual(result.diagnostics.available_sections, ("brain", "prediction"))
        self.assertEqual(result.diagnostics.row_count, 300)
        self.assertEqual(result.diagnostics.future_row_count, 10)
        self.assertEqual(result.diagnostics.similar_pattern_count, 5)
        self.assertEqual(result.diagnostics.notes, ("pipeline note",))
        self.assertEqual(result.diagnostics.adapter_version, ADAPTER_VERSION_V1)
        json.dumps(result.to_dict(), sort_keys=True)

    def test_maps_legacy_analysis_result_dictionary_shape(self) -> None:
        source = {
            "symbol": "MSFT",
            "timeframe": "1D",
            "snapshot": {
                "symbol": "MSFT",
                "date": "2026-07-01",
                "snapshot_id": "snapshot-legacy",
                "timeframe": "1D",
            },
            "probability": {
                "probability_positive": "55.5",
                "expected_return_5d": "1.2",
                "expected_return_10d": "2.4",
                "confidence": "60.0",
                "evidence_count": "12",
            },
            "prediction": {
                "expected_price_10d": "250.5",
                "expected_return": "2.4",
                "best_pattern_id": 123,
                "best_similarity": "88.8",
            },
            "metadata": {
                "entry_point": "analyze_symbol",
                "rows": "120",
                "future_rows": "0",
                "similar_patterns": "3",
            },
            "notes": ["legacy analysis result"],
        }

        result = build_canonical_result_v1(source)

        self.assertEqual(result.identity.symbol, "MSFT")
        self.assertEqual(result.identity.snapshot_date, "2026-07-01")
        self.assertEqual(result.brain.projection["expected_price_10d"], "250.5")
        self.assertEqual(result.brain.prediction_summary["best_pattern_id"], 123)
        self.assertIsNotNone(result.prediction)
        self.assertEqual(result.prediction.evidence_count, 12)
        self.assertEqual(result.prediction.expected_return_10d, 2.4)
        self.assertEqual(result.prediction.expected_price_10d, 250.5)
        self.assertEqual(result.prediction.best_pattern_id, "123")
        self.assertEqual(result.prediction.best_similarity, 88.8)
        self.assertEqual(result.diagnostics.source_pipeline, "analyze_symbol")
        self.assertEqual(result.diagnostics.legacy_payload_keys[0], "symbol")
        json.dumps(result.to_dict(), sort_keys=True)

    def test_missing_and_malformed_sections_are_safe(self) -> None:
        source = {
            "symbol": "BAD",
            "canonical_brain": {
                "snapshot": "not-a-dict",
                "probability": ["not-a-dict"],
                "prediction_summary": None,
            },
            "metadata": {
                "entry_point": "malformed_fixture",
                "rows": "not-a-number",
            },
        }

        result = build_canonical_result_v1(source)

        self.assertEqual(result.identity.symbol, "BAD")
        self.assertEqual(result.brain, CanonicalBrainResultV1())
        self.assertIsNone(result.prediction)
        self.assertEqual(result.diagnostics.available_sections, ())
        self.assertEqual(result.diagnostics.skipped_sections, ("prediction",))
        self.assertEqual(result.diagnostics.row_count, 0)
        self.assertIn("Malformed snapshot section skipped.", result.diagnostics.warnings)
        self.assertIn("Malformed probability section skipped.", result.diagnostics.warnings)
        json.dumps(result.to_dict(), sort_keys=True)

    def test_individual_builder_helpers_return_expected_contracts(self) -> None:
        source = {
            "symbol": "AAPL",
            "timeframe": "1D",
            "snapshot": {"symbol": "AAPL"},
            "probability": {"confidence": 50.0, "evidence_count": 10},
        }

        identity = build_canonical_identity_v1(source)
        brain = build_canonical_brain_result_v1(source)
        prediction = build_canonical_prediction_result_v1(source, brain=brain)
        diagnostics = build_canonical_diagnostics_v1(
            source,
            brain=brain,
            prediction=prediction,
        )

        self.assertIsInstance(identity, CanonicalIdentityV1)
        self.assertIsInstance(brain, CanonicalBrainResultV1)
        self.assertIsInstance(prediction, CanonicalPredictionResultV1)
        self.assertIsInstance(diagnostics, CanonicalDiagnosticsV1)

    def test_adapter_module_does_not_import_runtime_layers_or_infrastructure(self) -> None:
        blocked_module_roots = {
            "openai",
            "anthropic",
            "yfinance",
            "requests",
            "httpx",
            "urllib3",
            "alpaca",
            "ib_insync",
            "sqlite3",
            "src.analysis",
            "src.analysis_pipeline",
            "src.strategy",
            "src.backtest",
            "src.context",
            "src.signal_ledger",
            "src.outcome_tracking",
            "src.database",
            "src.data_source",
        }
        imported_roots: set[str] = set()

        tree = ast.parse(inspect.getsource(adapters_module))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported_roots.update(alias.name for alias in node.names)
            if isinstance(node, ast.ImportFrom) and node.module:
                imported_roots.add(node.module)

        self.assertTrue(blocked_module_roots.isdisjoint(imported_roots))

    def test_importing_adapters_does_not_load_ai_network_broker_or_database_modules(self) -> None:
        blocked_module_roots = {
            "openai",
            "anthropic",
            "yfinance",
            "requests",
            "httpx",
            "urllib3",
            "alpaca",
            "ib_insync",
            "sqlite3",
        }
        before = set(sys.modules)

        import src.canonical_result.adapters  # noqa: F401

        imported = set(sys.modules) - before
        imported_roots = {name.split(".")[0] for name in imported}
        self.assertTrue(blocked_module_roots.isdisjoint(imported_roots))


if __name__ == "__main__":
    unittest.main()
