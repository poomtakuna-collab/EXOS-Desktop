from __future__ import annotations

import ast
import inspect
import sys
import unittest
from dataclasses import dataclass
from typing import Any

import src.context.relative_strength_calculator as calculator_module
from src.context import (
    RelativeStrengthContext,
    calculate_relative_strength_context,
    calculate_relative_strength_context_from_analysis,
)


def _rows(start: float, end: float) -> list[dict[str, float]]:
    return [
        {
            "open": start,
            "high": start,
            "low": start,
            "close": start,
            "volume": 1_000_000.0,
        },
        {
            "open": end,
            "high": end,
            "low": end,
            "close": end,
            "volume": 1_000_000.0,
        },
    ]


@dataclass(frozen=True)
class _RequestLike:
    ohlcv_rows: list[dict[str, float]]
    benchmark_ohlcv_rows: list[dict[str, float]]
    sector_ohlcv_rows: list[dict[str, float]]


@dataclass(frozen=True)
class _AnalysisResultLike:
    request: _RequestLike


class RelativeStrengthCalculatorTest(unittest.TestCase):
    def test_public_imports(self) -> None:
        self.assertTrue(callable(calculate_relative_strength_context))
        self.assertTrue(callable(calculate_relative_strength_context_from_analysis))

    def test_outperform_from_ohlcv_rows(self) -> None:
        context = calculate_relative_strength_context(
            symbol_rows=_rows(100.0, 112.0),
            benchmark_rows=_rows(100.0, 104.0),
            sector_rows=_rows(100.0, 106.0),
        )

        self.assertEqual(
            context,
            RelativeStrengthContext(
                stock_vs_market=8.0,
                stock_vs_sector=6.0,
                rating="outperform",
            ),
        )

    def test_neutral_from_explicit_performance_values(self) -> None:
        context = calculate_relative_strength_context(
            symbol_performance=5.0,
            benchmark_performance=4.0,
            sector_performance=6.0,
        )

        self.assertEqual(
            context,
            RelativeStrengthContext(
                stock_vs_market=1.0,
                stock_vs_sector=-1.0,
                rating="neutral",
            ),
        )

    def test_underperform_from_ohlcv_rows(self) -> None:
        context = calculate_relative_strength_context(
            symbol_rows=_rows(100.0, 94.0),
            benchmark_rows=_rows(100.0, 101.0),
            sector_rows=_rows(100.0, 100.0),
        )

        self.assertEqual(
            context,
            RelativeStrengthContext(
                stock_vs_market=-7.0,
                stock_vs_sector=-6.0,
                rating="underperform",
            ),
        )

    def test_missing_benchmark_can_compare_against_sector_only(self) -> None:
        context = calculate_relative_strength_context(
            symbol_rows=_rows(100.0, 110.0),
            sector_rows=_rows(100.0, 105.0),
        )

        self.assertEqual(
            context,
            RelativeStrengthContext(
                stock_vs_market=None,
                stock_vs_sector=5.0,
                rating="outperform",
            ),
        )

    def test_missing_data_returns_unknown_context(self) -> None:
        self.assertEqual(
            calculate_relative_strength_context(),
            RelativeStrengthContext(),
        )
        self.assertEqual(
            calculate_relative_strength_context(
                symbol_rows=_rows(100.0, 110.0),
            ),
            RelativeStrengthContext(),
        )

    def test_malformed_data_is_ignored_without_raising(self) -> None:
        context = calculate_relative_strength_context(
            symbol_rows=[
                {"close": "bad"},
                "not-a-row",
                {"close": object()},
            ],
            benchmark_rows=_rows(100.0, 105.0),
            sector_rows=_rows(100.0, 100.0),
            symbol_performance="7.5",
            benchmark_performance=False,
            sector_performance="not-a-number",
        )

        self.assertEqual(
            context,
            RelativeStrengthContext(
                stock_vs_market=2.5,
                stock_vs_sector=7.5,
                rating="outperform",
            ),
        )

    def test_invalid_close_values_return_unknown(self) -> None:
        context = calculate_relative_strength_context(
            symbol_rows=[{"close": 0.0}, {"close": 110.0}],
            benchmark_rows=_rows(100.0, 105.0),
        )

        self.assertEqual(context, RelativeStrengthContext())

    def test_calculates_from_analysis_result_like_object(self) -> None:
        analysis = _AnalysisResultLike(
            request=_RequestLike(
                ohlcv_rows=_rows(100.0, 108.0),
                benchmark_ohlcv_rows=_rows(100.0, 104.0),
                sector_ohlcv_rows=_rows(100.0, 106.0),
            )
        )

        context = calculate_relative_strength_context_from_analysis(analysis)

        self.assertEqual(
            context,
            RelativeStrengthContext(
                stock_vs_market=4.0,
                stock_vs_sector=2.0,
                rating="outperform",
            ),
        )

    def test_calculates_from_analysis_result_like_dict(self) -> None:
        context = calculate_relative_strength_context_from_analysis(
            {
                "request": {
                    "ohlcv_rows": _rows(100.0, 101.0),
                    "benchmark_ohlcv_rows": _rows(100.0, 102.0),
                    "sector_ohlcv_rows": _rows(100.0, 100.0),
                }
            }
        )

        self.assertEqual(
            context,
            RelativeStrengthContext(
                stock_vs_market=-1.0,
                stock_vs_sector=1.0,
                rating="neutral",
            ),
        )

    def test_calculator_is_deterministic_for_fixed_inputs(self) -> None:
        first = calculate_relative_strength_context(
            symbol_rows=_rows(100.0, 112.0),
            benchmark_rows=_rows(100.0, 104.0),
        )
        second = calculate_relative_strength_context(
            symbol_rows=_rows(100.0, 112.0),
            benchmark_rows=_rows(100.0, 104.0),
        )

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

        calculate_relative_strength_context(
            symbol_rows=_rows(100.0, 101.0),
            benchmark_rows=_rows(100.0, 100.0),
        )

        imported = set(sys.modules) - before
        imported_roots = {name.split(".")[0] for name in imported}
        self.assertTrue(blocked_module_roots.isdisjoint(imported_roots))


if __name__ == "__main__":
    unittest.main()
