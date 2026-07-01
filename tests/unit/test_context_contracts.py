from __future__ import annotations

import ast
import inspect
import json
import sys
import unittest
from dataclasses import FrozenInstanceError, is_dataclass

import src.context as context_module
import src.context.types as types_module
from src.context import (
    ContextRequest,
    ContextResult,
    MarketContext,
    RelativeStrengthContext,
    SectorContext,
    SupportResistanceContext,
    VolumeContext,
)


class ContextContractsTest(unittest.TestCase):
    def test_public_imports(self) -> None:
        self.assertIsNotNone(ContextRequest)
        self.assertIsNotNone(MarketContext)
        self.assertIsNotNone(SectorContext)
        self.assertIsNotNone(RelativeStrengthContext)
        self.assertIsNotNone(VolumeContext)
        self.assertIsNotNone(SupportResistanceContext)
        self.assertIsNotNone(ContextResult)

    def test_contract_shapes_are_immutable_dataclasses(self) -> None:
        contracts = (
            ContextRequest,
            MarketContext,
            SectorContext,
            RelativeStrengthContext,
            VolumeContext,
            SupportResistanceContext,
            ContextResult,
        )
        for contract in contracts:
            self.assertTrue(is_dataclass(contract))

        request = ContextRequest(symbol="AAPL")
        market = MarketContext()
        sector = SectorContext()
        relative_strength = RelativeStrengthContext()
        volume = VolumeContext()
        support_resistance = SupportResistanceContext()
        result = ContextResult(request=request)

        with self.assertRaises(FrozenInstanceError):
            request.symbol = "MSFT"
        with self.assertRaises(FrozenInstanceError):
            market.trend = "up"
        with self.assertRaises(FrozenInstanceError):
            sector.trend = "up"
        with self.assertRaises(FrozenInstanceError):
            relative_strength.rating = "strong"
        with self.assertRaises(FrozenInstanceError):
            volume.volume_state = "elevated"
        with self.assertRaises(FrozenInstanceError):
            support_resistance.nearest_support = 100.0
        with self.assertRaises(FrozenInstanceError):
            result.request = ContextRequest(symbol="MSFT")

    def test_default_values_are_stable(self) -> None:
        request = ContextRequest()
        result = ContextResult()

        self.assertEqual(request.symbol, "")
        self.assertEqual(request.market_symbol, "QQQ")
        self.assertIsNone(request.sector_symbol)
        self.assertIsNone(request.industry_symbol)
        self.assertEqual(request.lookback_days, 252)
        self.assertEqual(result.market, MarketContext())
        self.assertEqual(result.sector, SectorContext())
        self.assertEqual(result.relative_strength, RelativeStrengthContext())
        self.assertEqual(result.volume, VolumeContext())
        self.assertEqual(result.support_resistance, SupportResistanceContext())
        self.assertEqual(result.warnings, ())

    def test_to_dict_returns_plain_serializable_dicts(self) -> None:
        result = ContextResult(
            request=ContextRequest(
                symbol="AAPL",
                sector_symbol="XLK",
                industry_symbol="TECH",
            ),
            market=MarketContext(
                trend="up",
                momentum="positive",
                volatility="normal",
                risk_state="neutral",
            ),
            sector=SectorContext(sector_symbol="XLK", relative_to_market="strong"),
            relative_strength=RelativeStrengthContext(
                stock_vs_market=1.25,
                stock_vs_sector=1.1,
                rating="strong",
            ),
            volume=VolumeContext(relative_volume=1.5, volume_state="elevated"),
            support_resistance=SupportResistanceContext(
                nearest_support=100.0,
                nearest_resistance=120.0,
                support_distance_pct=3.5,
                resistance_distance_pct=8.0,
            ),
            warnings=("context data not calculated yet",),
        )

        output = result.to_dict()

        self.assertIsInstance(output, dict)
        self.assertEqual(output["request"]["symbol"], "AAPL")
        self.assertEqual(output["market"]["trend"], "up")
        self.assertEqual(output["sector"]["sector_symbol"], "XLK")
        self.assertEqual(output["relative_strength"]["stock_vs_market"], 1.25)
        self.assertEqual(output["volume"]["relative_volume"], 1.5)
        self.assertEqual(output["support_resistance"]["nearest_support"], 100.0)
        self.assertEqual(output["warnings"], ["context data not calculated yet"])
        json.dumps(output, sort_keys=True)

    def test_individual_to_dict_methods_are_serializable(self) -> None:
        values = [
            ContextRequest(symbol="AAPL"),
            MarketContext(),
            SectorContext(),
            RelativeStrengthContext(stock_vs_market=1.0),
            VolumeContext(relative_volume=1.0),
            SupportResistanceContext(nearest_support=100.0),
        ]

        for value in values:
            output = value.to_dict()
            self.assertIsInstance(output, dict)
            json.dumps(output, sort_keys=True)

    def test_context_does_not_import_ai_network_or_broker_modules(self) -> None:
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

        for module in (context_module, types_module):
            tree = ast.parse(inspect.getsource(module))
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    imported_roots.update(alias.name.split(".")[0] for alias in node.names)
                if isinstance(node, ast.ImportFrom) and node.module:
                    imported_roots.add(node.module.split(".")[0])

        self.assertTrue(blocked_module_roots.isdisjoint(imported_roots))

    def test_importing_context_does_not_load_ai_network_or_broker_modules(self) -> None:
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

        import src.context  # noqa: F401

        imported = set(sys.modules) - before
        imported_roots = {name.split(".")[0] for name in imported}
        self.assertTrue(blocked_module_roots.isdisjoint(imported_roots))


if __name__ == "__main__":
    unittest.main()
