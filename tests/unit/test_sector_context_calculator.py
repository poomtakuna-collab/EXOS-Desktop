from __future__ import annotations

import ast
import inspect
import sys
import unittest
from dataclasses import dataclass
from typing import Any

import src.context.sector_context_calculator as calculator_module
from src.context import (
    SectorContext,
    calculate_sector_context,
    calculate_sector_context_from_analysis,
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
    sector_symbol: str
    ohlcv_rows: list[dict[str, float]]
    sector_ohlcv_rows: list[dict[str, float]]
    industry_ohlcv_rows: list[dict[str, float]]


@dataclass(frozen=True)
class _AnalysisResultLike:
    request: _RequestLike


class SectorContextCalculatorTest(unittest.TestCase):
    def test_public_imports(self) -> None:
        self.assertTrue(callable(calculate_sector_context))
        self.assertTrue(callable(calculate_sector_context_from_analysis))

    def test_strong_sector_from_ohlcv_rows(self) -> None:
        context = calculate_sector_context(
            sector_symbol="XLK",
            symbol_rows=_rows(100.0, 108.0),
            sector_rows=_rows(100.0, 112.0),
            industry_rows=_rows(100.0, 105.0),
        )

        self.assertEqual(
            context,
            SectorContext(
                sector_symbol="XLK",
                trend="up",
                relative_to_market="strong",
            ),
        )

    def test_weak_sector_from_ohlcv_rows(self) -> None:
        context = calculate_sector_context(
            sector_symbol="XLY",
            symbol_rows=_rows(100.0, 97.0),
            sector_rows=_rows(100.0, 94.0),
            industry_rows=_rows(100.0, 100.0),
        )

        self.assertEqual(
            context,
            SectorContext(
                sector_symbol="XLY",
                trend="down",
                relative_to_market="weak",
            ),
        )

    def test_neutral_sector_from_explicit_performance_values(self) -> None:
        context = calculate_sector_context(
            sector_symbol="XLV",
            symbol_performance=2.0,
            sector_performance=1.5,
            industry_performance=0.5,
        )

        self.assertEqual(
            context,
            SectorContext(
                sector_symbol="XLV",
                trend="sideways",
                relative_to_market="neutral",
            ),
        )

    def test_missing_industry_benchmark_compares_sector_to_symbol(self) -> None:
        context = calculate_sector_context(
            sector_symbol="XLC",
            symbol_rows=_rows(100.0, 103.0),
            sector_rows=_rows(100.0, 108.0),
        )

        self.assertEqual(
            context,
            SectorContext(
                sector_symbol="XLC",
                trend="up",
                relative_to_market="strong",
            ),
        )

    def test_missing_all_comparison_benchmarks_returns_unknown_strength(self) -> None:
        context = calculate_sector_context(
            sector_symbol="XLI",
            sector_rows=_rows(100.0, 104.0),
        )

        self.assertEqual(
            context,
            SectorContext(
                sector_symbol="XLI",
                trend="up",
                relative_to_market="unknown",
            ),
        )

    def test_missing_sector_data_returns_unknown_context(self) -> None:
        self.assertEqual(calculate_sector_context(), SectorContext())
        self.assertEqual(
            calculate_sector_context(symbol_rows=_rows(100.0, 110.0)),
            SectorContext(),
        )

    def test_malformed_inputs_are_ignored_without_raising(self) -> None:
        context = calculate_sector_context(
            sector_symbol="  XLF  ",
            symbol_rows=[
                {"close": "bad"},
                "not-a-row",
                {"close": object()},
            ],
            sector_rows=[
                {"close": 100.0},
                {"close": "bad"},
            ],
            industry_rows=_rows(100.0, 104.0),
            symbol_performance="5.0",
            sector_performance="9.0",
            industry_performance=False,
        )

        self.assertEqual(
            context,
            SectorContext(
                sector_symbol="  XLF  ",
                trend="up",
                relative_to_market="strong",
            ),
        )

    def test_invalid_sector_close_values_return_unknown_trend(self) -> None:
        context = calculate_sector_context(
            sector_rows=[{"close": 0.0}, {"close": 110.0}],
            industry_rows=_rows(100.0, 104.0),
        )

        self.assertEqual(context, SectorContext())

    def test_calculates_from_analysis_result_like_object(self) -> None:
        analysis = _AnalysisResultLike(
            request=_RequestLike(
                sector_symbol="XLK",
                ohlcv_rows=_rows(100.0, 105.0),
                sector_ohlcv_rows=_rows(100.0, 108.0),
                industry_ohlcv_rows=_rows(100.0, 104.0),
            )
        )

        context = calculate_sector_context_from_analysis(analysis)

        self.assertEqual(
            context,
            SectorContext(
                sector_symbol="XLK",
                trend="up",
                relative_to_market="strong",
            ),
        )

    def test_calculates_from_analysis_result_like_dict(self) -> None:
        context = calculate_sector_context_from_analysis(
            {
                "request": {
                    "sector_symbol": "XLV",
                    "ohlcv_rows": _rows(100.0, 102.0),
                    "sector_ohlcv_rows": _rows(100.0, 101.0),
                    "industry_ohlcv_rows": _rows(100.0, 100.5),
                }
            }
        )

        self.assertEqual(
            context,
            SectorContext(
                sector_symbol="XLV",
                trend="sideways",
                relative_to_market="neutral",
            ),
        )

    def test_calculator_is_deterministic_for_fixed_inputs(self) -> None:
        first = calculate_sector_context(
            sector_rows=_rows(100.0, 108.0),
            industry_rows=_rows(100.0, 104.0),
        )
        second = calculate_sector_context(
            sector_rows=_rows(100.0, 108.0),
            industry_rows=_rows(100.0, 104.0),
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

        calculate_sector_context(
            sector_rows=_rows(100.0, 101.0),
            industry_rows=_rows(100.0, 100.0),
        )

        imported = set(sys.modules) - before
        imported_roots = {name.split(".")[0] for name in imported}
        self.assertTrue(blocked_module_roots.isdisjoint(imported_roots))


if __name__ == "__main__":
    unittest.main()
