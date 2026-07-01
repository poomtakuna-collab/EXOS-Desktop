from __future__ import annotations

import ast
import inspect
import sys
import unittest
from dataclasses import dataclass
from typing import Any

import src.context.volume_context_calculator as calculator_module
from src.context import (
    VolumeContext,
    calculate_volume_context,
    calculate_volume_context_from_analysis,
)


def _rows(volumes: list[float]) -> list[dict[str, float]]:
    return [
        {
            "open": 100.0,
            "high": 101.0,
            "low": 99.0,
            "close": 100.0,
            "volume": volume,
        }
        for volume in volumes
    ]


@dataclass(frozen=True)
class _RequestLike:
    ohlcv_rows: list[dict[str, float]]


@dataclass(frozen=True)
class _AnalysisResultLike:
    request: _RequestLike
    snapshot: dict[str, Any]
    indicators: dict[str, Any] | None = None


class VolumeContextCalculatorTest(unittest.TestCase):
    def test_public_imports(self) -> None:
        self.assertTrue(callable(calculate_volume_context))
        self.assertTrue(callable(calculate_volume_context_from_analysis))

    def test_missing_inputs_return_unknown_context(self) -> None:
        self.assertEqual(calculate_volume_context(), VolumeContext())
        self.assertEqual(
            calculate_volume_context(snapshot=None, indicators=None, price_rows=None),
            VolumeContext(),
        )

    def test_low_volume_regime_from_ohlcv_rows(self) -> None:
        context = calculate_volume_context(price_rows=_rows([100.0, 110.0, 90.0, 60.0]))

        self.assertEqual(
            context,
            VolumeContext(relative_volume=0.6, volume_state="low"),
        )

    def test_normal_volume_regime_from_explicit_volumes(self) -> None:
        context = calculate_volume_context(
            current_volume=120_000,
            average_volume=100_000,
        )

        self.assertEqual(
            context,
            VolumeContext(relative_volume=1.2, volume_state="normal"),
        )

    def test_high_volume_regime_from_snapshot_volume_section(self) -> None:
        context = calculate_volume_context(
            snapshot={
                "volume": {
                    "current_volume": "180000",
                    "average_volume": "100000",
                }
            }
        )

        self.assertEqual(
            context,
            VolumeContext(relative_volume=1.8, volume_state="high"),
        )

    def test_spike_volume_regime_from_indicator_relative_volume(self) -> None:
        context = calculate_volume_context(indicators={"relative_volume": 2.75})

        self.assertEqual(
            context,
            VolumeContext(relative_volume=2.75, volume_state="spike"),
        )

    def test_relative_volume_from_snapshot_takes_precedence(self) -> None:
        context = calculate_volume_context(
            snapshot={"volume": {"relative_volume": 1.49}},
            current_volume=300_000,
            average_volume=100_000,
        )

        self.assertEqual(
            context,
            VolumeContext(relative_volume=1.49, volume_state="normal"),
        )

    def test_not_enough_volume_history_returns_unknown(self) -> None:
        context = calculate_volume_context(price_rows=_rows([100.0, 120.0]))

        self.assertEqual(context, VolumeContext())

    def test_malformed_data_is_ignored_without_raising(self) -> None:
        context = calculate_volume_context(
            snapshot={
                "volume": {
                    "relative_volume": "bad",
                    "current_volume": object(),
                    "average_volume": False,
                }
            },
            indicators={"volume": {"volume_sma20": "100000"}},
            price_rows=[
                {"volume": object()},
                "not-a-row",
                {"volume": 100_000},
                {"volume": "150000"},
            ],
            current_volume="200000",
            average_volume="not-a-number",
        )

        self.assertEqual(
            context,
            VolumeContext(relative_volume=2.0, volume_state="high"),
        )

    def test_non_positive_values_are_ignored(self) -> None:
        context = calculate_volume_context(
            current_volume=0,
            average_volume=-1,
            relative_volume=False,
            price_rows=_rows([100.0, 100.0, 100.0, 250.0]),
        )

        self.assertEqual(
            context,
            VolumeContext(relative_volume=2.5, volume_state="spike"),
        )

    def test_calculates_from_analysis_result_like_object(self) -> None:
        analysis = _AnalysisResultLike(
            request=_RequestLike(ohlcv_rows=_rows([100.0, 110.0, 90.0, 150.0])),
            snapshot={},
            indicators=None,
        )

        context = calculate_volume_context_from_analysis(analysis)

        self.assertEqual(
            context,
            VolumeContext(relative_volume=1.5, volume_state="high"),
        )

    def test_calculates_from_analysis_result_like_dict(self) -> None:
        context = calculate_volume_context_from_analysis(
            {
                "request": {"ohlcv_rows": _rows([100.0, 100.0, 100.0, 65.0])},
                "snapshot": {},
                "indicators": {},
            }
        )

        self.assertEqual(
            context,
            VolumeContext(relative_volume=0.65, volume_state="low"),
        )

    def test_calculator_is_deterministic_for_fixed_inputs(self) -> None:
        rows = _rows([100.0, 110.0, 90.0, 125.0])

        first = calculate_volume_context(price_rows=rows)
        second = calculate_volume_context(price_rows=rows)

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

        calculate_volume_context(price_rows=_rows([100.0, 100.0, 100.0, 100.0]))

        imported = set(sys.modules) - before
        imported_roots = {name.split(".")[0] for name in imported}
        self.assertTrue(blocked_module_roots.isdisjoint(imported_roots))


if __name__ == "__main__":
    unittest.main()
