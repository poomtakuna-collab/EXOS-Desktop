from __future__ import annotations

import ast
import inspect
import json
import sys
import unittest
from dataclasses import FrozenInstanceError, is_dataclass

import src.canonical_result as canonical_result_module
import src.canonical_result.types as types_module
from src.canonical_result import (
    CANONICAL_RESULT_SCHEMA_VERSION_V1,
    CanonicalBacktestResultV1,
    CanonicalBrainResultV1,
    CanonicalContextResultV1,
    CanonicalDiagnosticsV1,
    CanonicalIdentityV1,
    CanonicalPredictionResultV1,
    CanonicalResultV1,
    CanonicalSignalSummaryV1,
    CanonicalStrategyResultV1,
)


class CanonicalResultContractsTest(unittest.TestCase):
    def test_public_imports(self) -> None:
        self.assertEqual(CANONICAL_RESULT_SCHEMA_VERSION_V1, "canonical_result_v1")
        self.assertIsNotNone(CanonicalIdentityV1)
        self.assertIsNotNone(CanonicalBrainResultV1)
        self.assertIsNotNone(CanonicalPredictionResultV1)
        self.assertIsNotNone(CanonicalContextResultV1)
        self.assertIsNotNone(CanonicalStrategyResultV1)
        self.assertIsNotNone(CanonicalBacktestResultV1)
        self.assertIsNotNone(CanonicalSignalSummaryV1)
        self.assertIsNotNone(CanonicalDiagnosticsV1)
        self.assertIsNotNone(CanonicalResultV1)

    def test_contract_shapes_are_immutable_dataclasses(self) -> None:
        contracts = (
            CanonicalIdentityV1,
            CanonicalBrainResultV1,
            CanonicalPredictionResultV1,
            CanonicalContextResultV1,
            CanonicalStrategyResultV1,
            CanonicalBacktestResultV1,
            CanonicalSignalSummaryV1,
            CanonicalDiagnosticsV1,
            CanonicalResultV1,
        )
        for contract in contracts:
            self.assertTrue(is_dataclass(contract))

        result = CanonicalResultV1(identity=CanonicalIdentityV1(symbol="AAPL"))
        brain = CanonicalBrainResultV1(snapshot={"symbol": "AAPL"})
        prediction = CanonicalPredictionResultV1(confidence=75.0)

        with self.assertRaises(FrozenInstanceError):
            result.identity = CanonicalIdentityV1(symbol="MSFT")
        with self.assertRaises(FrozenInstanceError):
            brain.probability = {"probability_positive": 60.0}
        with self.assertRaises(FrozenInstanceError):
            prediction.confidence = 80.0

    def test_minimal_construction_uses_stable_defaults(self) -> None:
        result = CanonicalResultV1()

        self.assertEqual(result.schema_version, CANONICAL_RESULT_SCHEMA_VERSION_V1)
        self.assertEqual(result.identity, CanonicalIdentityV1())
        self.assertEqual(result.brain, CanonicalBrainResultV1())
        self.assertEqual(result.diagnostics, CanonicalDiagnosticsV1())
        self.assertIsNone(result.prediction)
        self.assertIsNone(result.context)
        self.assertIsNone(result.strategy)
        self.assertIsNone(result.backtest)
        self.assertIsNone(result.signal_summary)

        output = result.to_dict()
        self.assertEqual(output["schema_version"], "canonical_result_v1")
        self.assertEqual(output["identity"]["symbol"], "")
        self.assertEqual(output["brain"]["snapshot"], {})
        self.assertEqual(output["diagnostics"]["available_sections"], [])
        self.assertIsNone(output["prediction"])
        json.dumps(output, sort_keys=True)

    def test_optional_sections_can_be_constructed_independently(self) -> None:
        result = CanonicalResultV1(
            identity=CanonicalIdentityV1(
                symbol="AAPL",
                timeframe="1D",
                snapshot_id="snapshot-1",
                snapshot_date="2026-07-01",
            ),
            brain=CanonicalBrainResultV1(
                snapshot={"symbol": "AAPL", "close": 100.0},
                probability={"probability_positive": 62.5},
                prediction_summary={"confidence": 70.0},
            ),
            prediction=CanonicalPredictionResultV1(
                confidence=70.0,
                evidence_count=24,
                probability_positive=62.5,
            ),
            diagnostics=CanonicalDiagnosticsV1(
                source_pipeline="analysis_pipeline_v2",
                available_sections=("brain", "prediction"),
                skipped_sections=("strategy", "backtest"),
            ),
        )

        output = result.to_dict()

        self.assertEqual(output["identity"]["symbol"], "AAPL")
        self.assertEqual(output["brain"]["snapshot"]["close"], 100.0)
        self.assertEqual(output["prediction"]["confidence"], 70.0)
        self.assertEqual(output["diagnostics"]["available_sections"], ["brain", "prediction"])
        self.assertEqual(output["diagnostics"]["skipped_sections"], ["strategy", "backtest"])
        self.assertIsNone(output["strategy"])
        self.assertIsNone(output["backtest"])
        json.dumps(output, sort_keys=True)

    def test_full_serialization_returns_json_safe_plain_dict(self) -> None:
        result = CanonicalResultV1(
            identity=CanonicalIdentityV1(
                symbol="AAPL",
                timeframe="1D",
                snapshot_id="snapshot-1",
                snapshot_date="2026-07-01",
                analysis_date="2026-07-01",
                source="analysis_pipeline",
                pipeline_name="analysis_pipeline_v2",
                pipeline_version="v2",
                run_id="run-1",
            ),
            brain=CanonicalBrainResultV1(
                snapshot={"symbol": "AAPL", "nested": {"trend": "up"}},
                resolver_output={"matches": [{"pattern_id": "p1", "similarity": 91.5}]},
                probability={"probability_positive": 66.0},
                projection={"expected_price_10d": 112.5},
                target_zone={"target_zone": {"base": 115.0}},
                risk_zone={"risk_zone": {"base": 95.0}},
                prediction_summary={"confidence": 72.0},
                metadata={"adapter": "canonical_brain_adapter_v1"},
                notes=("brain mapped without changing raw sections",),
            ),
            prediction=CanonicalPredictionResultV1(
                confidence=72.0,
                evidence_count=42,
                probability_positive=66.0,
                probability_negative=22.0,
                probability_neutral=12.0,
                expected_return_5d=2.5,
                expected_return_10d=5.0,
                expected_return_20d=8.0,
                expected_price_5d=105.0,
                expected_price_10d=110.0,
                expected_price_20d=118.0,
                target_conservative=108.0,
                target_base=112.0,
                target_aggressive=116.0,
                risk_conservative=98.0,
                risk_base=95.0,
                risk_aggressive=92.0,
                best_pattern_id="p1",
                best_similarity=91.5,
                notes=("prediction normalized for reports",),
            ),
            context=CanonicalContextResultV1(
                market={"trend": "up", "risk_state": "neutral"},
                sector={"sector_symbol": "XLK", "relative_to_market": "strong"},
                relative_strength={"rating": "outperform"},
                volume={"volume_state": "high"},
                support_resistance={"nearest_support": 100.0},
                warnings=("sector benchmark unavailable",),
            ),
            strategy=CanonicalStrategyResultV1(
                strategy_score=74.5,
                trade_grade="B",
                entry_quality="good",
                risk_rating="moderate",
                expected_reward_percent=8.0,
                expected_risk_percent=3.0,
                reward_risk_ratio=2.67,
                target_zone_low=108.0,
                target_zone_high=116.0,
                risk_zone_low=92.0,
                risk_zone_high=98.0,
                notes=("strategy normalized for UI",),
            ),
            backtest=CanonicalBacktestResultV1(
                attempted_trades=10,
                completed_trades=8,
                total_trades=8,
                winning_trades=5,
                losing_trades=3,
                skipped_trades=2,
                breakeven_trades=0,
                win_rate=62.5,
                average_return=3.2,
                expectancy=1.4,
                max_drawdown=-4.5,
                net_return_percent=25.6,
                profit_factor=1.8,
                summary="Validated 8 trades.",
                validation_summary="Validation report generated.",
                notes=("backtest optional",),
            ),
            signal_summary=CanonicalSignalSummaryV1(
                symbol="AAPL",
                signal_date="2026-07-01",
                timeframe="1D",
                signal_type="setup",
                confidence=72.0,
                snapshot_id="snapshot-1",
                snapshot_date="2026-07-01",
                context_summary={"market": {"trend": "up"}},
                strategy_summary={"strategy_score": 74.5},
                prediction_summary={"confidence": 72.0},
                notes=("signal-ready extract",),
            ),
            diagnostics=CanonicalDiagnosticsV1(
                source_pipeline="analysis_pipeline_v2",
                available_sections=("brain", "prediction", "context", "strategy", "backtest"),
                skipped_sections=(),
                data_source_metadata={"source": "memory", "row_count": 300},
                row_count=300,
                future_row_count=10,
                similar_pattern_count=12,
                warnings=("read model only",),
                notes=("no pipeline wiring",),
                legacy_payload_keys=("snapshot", "probability", "prediction_summary"),
                adapter_version="v1",
            ),
        )

        output = result.to_dict()

        self.assertEqual(output["schema_version"], "canonical_result_v1")
        self.assertEqual(output["identity"]["run_id"], "run-1")
        self.assertEqual(output["brain"]["resolver_output"]["matches"][0]["pattern_id"], "p1")
        self.assertEqual(output["brain"]["notes"], ["brain mapped without changing raw sections"])
        self.assertEqual(output["context"]["warnings"], ["sector benchmark unavailable"])
        self.assertEqual(output["strategy"]["reward_risk_ratio"], 2.67)
        self.assertEqual(output["backtest"]["attempted_trades"], 10)
        self.assertEqual(output["signal_summary"]["signal_type"], "setup")
        self.assertEqual(output["diagnostics"]["legacy_payload_keys"], ["snapshot", "probability", "prediction_summary"])
        json.dumps(output, sort_keys=True)

    def test_individual_to_dict_methods_are_serializable(self) -> None:
        values = [
            CanonicalIdentityV1(symbol="AAPL"),
            CanonicalBrainResultV1(snapshot={"symbol": "AAPL"}),
            CanonicalPredictionResultV1(confidence=50.0),
            CanonicalContextResultV1(market={"trend": "up"}),
            CanonicalStrategyResultV1(strategy_score=70.0),
            CanonicalBacktestResultV1(total_trades=3),
            CanonicalSignalSummaryV1(symbol="AAPL"),
            CanonicalDiagnosticsV1(available_sections=("brain",)),
        ]

        for value in values:
            output = value.to_dict()
            self.assertIsInstance(output, dict)
            json.dumps(output, sort_keys=True)

    def test_canonical_result_does_not_import_ai_network_broker_database_or_pipeline_modules(self) -> None:
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
            "src.strategy",
            "src.backtest",
            "src.context",
            "src.signal_ledger",
            "src.outcome_tracking",
        }
        imported_roots: set[str] = set()

        for module in (canonical_result_module, types_module):
            tree = ast.parse(inspect.getsource(module))
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    imported_roots.update(alias.name for alias in node.names)
                if isinstance(node, ast.ImportFrom) and node.module:
                    imported_roots.add(node.module)

        self.assertTrue(blocked_module_roots.isdisjoint(imported_roots))

    def test_importing_canonical_result_does_not_load_ai_network_broker_or_database_modules(self) -> None:
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

        import src.canonical_result  # noqa: F401

        imported = set(sys.modules) - before
        imported_roots = {name.split(".")[0] for name in imported}
        self.assertTrue(blocked_module_roots.isdisjoint(imported_roots))


if __name__ == "__main__":
    unittest.main()
