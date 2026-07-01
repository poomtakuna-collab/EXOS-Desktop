from __future__ import annotations

import ast
import inspect
import sys
import unittest
from dataclasses import dataclass
from typing import Any

import src.context.support_resistance_calculator as calculator_module
from src.context import (
    SupportResistanceContext,
    calculate_support_resistance_context,
    calculate_support_resistance_context_from_analysis,
)


def _rows(values: list[tuple[float, float, float]]) -> list[dict[str, float]]:
    return [
        {
            "open": close,
            "high": high,
            "low": low,
            "close": close,
            "volume": 1_000_000.0,
        }
        for high, low, close in values
    ]


@dataclass(frozen=True)
class _RequestLike:
    ohlcv_rows: list[dict[str, float]]


@dataclass(frozen=True)
class _AnalysisResultLike:
    request: _RequestLike
    snapshot: dict[str, Any]
    indicators: dict[str, Any] | None = None


class SupportResistanceCalculatorTest(unittest.TestCase):
    def test_public_imports(self) -> None:
        self.assertTrue(callable(calculate_support_resistance_context))
        self.assertTrue(callable(calculate_support_resistance_context_from_analysis))

    def test_missing_inputs_return_empty_context(self) -> None:
        self.assertEqual(
            calculate_support_resistance_context(),
            SupportResistanceContext(),
        )
        self.assertEqual(
            calculate_support_resistance_context(snapshot=None, price_rows=None),
            SupportResistanceContext(),
        )

    def test_bullish_inputs_find_nearest_support_and_resistance(self) -> None:
        context = calculate_support_resistance_context(
            current_price=112.0,
            snapshot={
                "market_structure": {
                    "swing_low": 98.0,
                    "swing_high": 124.0,
                    "last_pivot_low": 108.0,
                    "last_pivot_high": 118.0,
                },
                "trend": {"ema20": 109.0, "ema50": 104.0},
            },
            price_rows=_rows(
                [
                    (103.0, 97.0, 101.0),
                    (110.0, 102.0, 108.0),
                    (116.0, 106.0, 111.0),
                    (114.0, 108.0, 112.0),
                    (118.0, 109.0, 112.0),
                ]
            ),
        )

        self.assertEqual(
            context,
            SupportResistanceContext(
                nearest_support=110.0,
                nearest_resistance=114.0,
                support_distance_pct=1.7857,
                resistance_distance_pct=1.7857,
            ),
        )

    def test_bearish_inputs_find_overhead_resistance(self) -> None:
        context = calculate_support_resistance_context(
            current_price=86.0,
            snapshot={
                "market_structure": {
                    "swing_low": 74.0,
                    "swing_high": 110.0,
                    "last_pivot_low": 82.0,
                    "last_pivot_high": 92.0,
                }
            },
            indicators={"ema20": 90.0, "ema50": 96.0},
            price_rows=_rows(
                [
                    (110.0, 96.0, 102.0),
                    (104.0, 90.0, 94.0),
                    (96.0, 82.0, 88.0),
                    (92.0, 84.0, 86.0),
                ]
            ),
        )

        self.assertEqual(context.nearest_support, 84.0)
        self.assertEqual(context.nearest_resistance, 90.0)
        self.assertEqual(context.support_distance_pct, 2.3256)
        self.assertEqual(context.resistance_distance_pct, 4.6512)

    def test_neutral_range_inputs_find_range_boundaries(self) -> None:
        context = calculate_support_resistance_context(
            current_price=50.0,
            price_rows=_rows(
                [
                    (54.0, 46.0, 50.0),
                    (56.0, 48.0, 51.0),
                    (53.0, 47.0, 49.0),
                    (55.0, 45.0, 50.0),
                    (52.0, 48.0, 50.0),
                ]
            ),
        )

        self.assertEqual(context.nearest_support, 48.0)
        self.assertEqual(context.nearest_resistance, 52.0)
        self.assertEqual(context.support_distance_pct, 4.0)
        self.assertEqual(context.resistance_distance_pct, 4.0)

    def test_only_snapshot_levels_are_enough_when_price_is_explicit(self) -> None:
        context = calculate_support_resistance_context(
            current_price="100",
            snapshot={
                "market_structure": {
                    "last_pivot_low": "95.5",
                    "last_pivot_high": "106.25",
                    "swing_low": "90",
                    "swing_high": "110",
                }
            },
        )

        self.assertEqual(context.nearest_support, 95.5)
        self.assertEqual(context.nearest_resistance, 106.25)
        self.assertEqual(context.support_distance_pct, 4.5)
        self.assertEqual(context.resistance_distance_pct, 6.25)

    def test_malformed_data_is_ignored_without_raising(self) -> None:
        context = calculate_support_resistance_context(
            current_price="not-a-price",
            snapshot={
                "metadata": {"current_price": 100.0},
                "market_structure": {
                    "last_pivot_low": object(),
                    "last_pivot_high": False,
                    "swing_low": "95",
                    "swing_high": "bad",
                },
            },
            indicators={"ema20": [], "ema50": "103"},
            price_rows=[
                {"high": "bad", "low": object(), "close": 100.0},
                "not-a-row",
                {"high": 104.0, "low": 96.0, "close": 100.0},
            ],
        )

        self.assertEqual(context.nearest_support, 96.0)
        self.assertEqual(context.nearest_resistance, 103.0)
        self.assertEqual(context.support_distance_pct, 4.0)
        self.assertEqual(context.resistance_distance_pct, 3.0)

    def test_calculates_from_analysis_result_like_object(self) -> None:
        analysis = _AnalysisResultLike(
            request=_RequestLike(
                ohlcv_rows=_rows(
                    [
                        (98.0, 90.0, 95.0),
                        (103.0, 94.0, 100.0),
                        (101.0, 96.0, 99.0),
                    ]
                )
            ),
            snapshot={"metadata": {"current_price": 100.0}},
            indicators={"ema20": 99.0, "ema50": 94.0},
        )

        context = calculate_support_resistance_context_from_analysis(analysis)

        self.assertEqual(context.nearest_support, 99.0)
        self.assertEqual(context.nearest_resistance, 101.0)

    def test_calculates_from_analysis_result_like_dict(self) -> None:
        context = calculate_support_resistance_context_from_analysis(
            {
                "request": {
                    "ohlcv_rows": _rows(
                        [
                            (22.0, 18.0, 20.0),
                            (24.0, 19.0, 21.0),
                            (23.0, 20.0, 22.0),
                        ]
                    )
                },
                "snapshot": {"metadata": {"current_price": 21.0}},
                "indicators": {"ema20": 20.5},
            }
        )

        self.assertEqual(context.nearest_support, 20.5)
        self.assertEqual(context.nearest_resistance, 22.0)

    def test_calculator_is_deterministic_for_fixed_inputs(self) -> None:
        rows = _rows(
            [
                (10.0, 8.0, 9.0),
                (12.0, 9.0, 11.0),
                (11.0, 10.0, 10.5),
            ]
        )

        first = calculate_support_resistance_context(price_rows=rows)
        second = calculate_support_resistance_context(price_rows=rows)

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

        calculate_support_resistance_context(price_rows=_rows([(10.0, 8.0, 9.0)]))

        imported = set(sys.modules) - before
        imported_roots = {name.split(".")[0] for name in imported}
        self.assertTrue(blocked_module_roots.isdisjoint(imported_roots))


if __name__ == "__main__":
    unittest.main()
