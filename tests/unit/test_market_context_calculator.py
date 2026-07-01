from __future__ import annotations

import ast
import inspect
import sys
import unittest
from dataclasses import dataclass
from typing import Any

import src.context.market_context_calculator as calculator_module
from src.context import (
    MarketContext,
    calculate_market_context,
    calculate_market_context_from_analysis,
)


def _snapshot(
    *,
    trend: dict[str, Any] | None = None,
    trend_slope: dict[str, Any] | None = None,
    squeeze: dict[str, Any] | None = None,
    market_structure: dict[str, Any] | None = None,
    score: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "trend": trend or {},
        "trend_slope": trend_slope or {},
        "squeeze": squeeze or {},
        "market_structure": market_structure or {},
        "score": score or {},
    }


@dataclass(frozen=True)
class _AnalysisResultLike:
    snapshot: dict[str, Any]
    probability: dict[str, Any]
    prediction: dict[str, Any] | None = None
    strategy: dict[str, Any] | None = None


class MarketContextCalculatorTest(unittest.TestCase):
    def test_public_imports(self) -> None:
        self.assertTrue(callable(calculate_market_context))
        self.assertTrue(callable(calculate_market_context_from_analysis))

    def test_missing_inputs_return_unknown_context(self) -> None:
        self.assertEqual(calculate_market_context(), MarketContext())
        self.assertEqual(calculate_market_context(snapshot=None), MarketContext())

    def test_bullish_snapshot_returns_risk_on_context(self) -> None:
        context = calculate_market_context(
            snapshot=_snapshot(
                trend={"state": "bullish", "score": 70.0},
                trend_slope={"direction": "up", "score": 62.0},
                squeeze={"state": "NONE", "compression_ratio": 1.2},
                score={"overall_score": 72.5, "confidence": 75.0},
            )
        )

        self.assertEqual(
            context,
            MarketContext(
                trend="up",
                momentum="positive",
                volatility="normal",
                risk_state="risk_on",
            ),
        )

    def test_bearish_market_structure_returns_risk_off_context(self) -> None:
        context = calculate_market_context(
            snapshot=_snapshot(
                trend={"state": "mixed", "score": 50.0},
                trend_slope={"direction": "down", "score": 38.0},
                squeeze={"state": "RELEASING", "compression_ratio": 1.7},
                market_structure={"state": "BREAKOUT_DOWN", "score": 20.0},
                score={"overall_score": 35.0, "confidence": 80.0},
            )
        )

        self.assertEqual(context.trend, "down")
        self.assertEqual(context.momentum, "negative")
        self.assertEqual(context.volatility, "elevated")
        self.assertEqual(context.risk_state, "risk_off")

    def test_score_thresholds_handle_partial_snapshot(self) -> None:
        context = calculate_market_context(
            snapshot={
                "trend": {"score": 66.0},
                "trend_slope": {"score": 50.0},
                "squeeze": {"compression_ratio": 0.8},
                "score": {"overall_score": 65.0, "confidence": 45.0},
            }
        )

        self.assertEqual(context.trend, "up")
        self.assertEqual(context.momentum, "neutral")
        self.assertEqual(context.volatility, "compressed")
        self.assertEqual(context.risk_state, "risk_on")

    def test_malformed_values_are_ignored_without_raising(self) -> None:
        context = calculate_market_context(
            snapshot={
                "trend": {"state": None, "score": "not-a-number"},
                "trend_slope": {"direction": "flat", "score": object()},
                "squeeze": {"state": "weird", "compression_ratio": "nope"},
                "score": {"overall_score": object(), "confidence": False},
            },
            probability={"confidence": "unknown"},
            prediction={"ignored": object()},
            strategy={"ignored": object()},
        )

        self.assertEqual(context.trend, "unknown")
        self.assertEqual(context.momentum, "unknown")
        self.assertEqual(context.volatility, "unknown")
        self.assertEqual(context.risk_state, "unknown")

    def test_calculates_from_analysis_result_like_object(self) -> None:
        analysis = _AnalysisResultLike(
            snapshot=_snapshot(
                trend={"state": "bearish", "score": 30.0},
                trend_slope={"direction": "down", "score": 40.0},
                squeeze={"state": "EXPANDED", "compression_ratio": 1.8},
                score={"overall_score": 30.0, "confidence": 70.0},
            ),
            probability={},
        )

        context = calculate_market_context_from_analysis(analysis)

        self.assertEqual(
            context,
            MarketContext(
                trend="down",
                momentum="negative",
                volatility="elevated",
                risk_state="risk_off",
            ),
        )

    def test_calculates_from_analysis_result_like_dict(self) -> None:
        context = calculate_market_context_from_analysis(
            {
                "snapshot": _snapshot(
                    trend={"state": "mixed", "score": 50.0},
                    trend_slope={"direction": "flat", "score": 50.0},
                    squeeze={"state": "NONE", "compression_ratio": 1.1},
                    score={"overall_score": 50.0, "confidence": 90.0},
                ),
                "probability": {},
                "prediction": {},
                "strategy": None,
            }
        )

        self.assertEqual(
            context,
            MarketContext(
                trend="sideways",
                momentum="neutral",
                volatility="normal",
                risk_state="neutral",
            ),
        )

    def test_calculator_is_deterministic_for_fixed_inputs(self) -> None:
        snapshot = _snapshot(
            trend={"state": "bullish", "score": 70.0},
            trend_slope={"direction": "up", "score": 60.0},
            squeeze={"state": "BUILDING", "compression_ratio": 0.9},
            score={"overall_score": 80.0, "confidence": 80.0},
        )

        first = calculate_market_context(snapshot=snapshot)
        second = calculate_market_context(snapshot=snapshot)

        self.assertEqual(first, second)

    def test_calculator_does_not_import_ai_network_or_broker_modules(self) -> None:
        blocked_module_roots = {
            "openai",
            "anthropic",
            "yfinance",
            "requests",
            "httpx",
            "urllib3",
            "alpaca",
            "ib_insync",
        }
        imported_roots: set[str] = set()

        tree = ast.parse(inspect.getsource(calculator_module))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported_roots.update(alias.name.split(".")[0] for alias in node.names)
            if isinstance(node, ast.ImportFrom) and node.module:
                imported_roots.add(node.module.split(".")[0])

        self.assertTrue(blocked_module_roots.isdisjoint(imported_roots))

    def test_running_calculator_does_not_load_ai_network_or_broker_modules(self) -> None:
        blocked_module_roots = {
            "openai",
            "anthropic",
            "yfinance",
            "requests",
            "httpx",
            "urllib3",
            "alpaca",
            "ib_insync",
        }
        before = set(sys.modules)

        calculate_market_context(snapshot=_snapshot())

        imported = set(sys.modules) - before
        imported_roots = {name.split(".")[0] for name in imported}
        self.assertTrue(blocked_module_roots.isdisjoint(imported_roots))


if __name__ == "__main__":
    unittest.main()
