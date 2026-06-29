import ast
from dataclasses import FrozenInstanceError, is_dataclass
import inspect
import sys
import unittest
from typing import get_type_hints

import src.data_source as data_source_module
import src.data_source.contracts as contracts_module
from src.data_source import (
    DataSourceConfig,
    FutureRowsRequest,
    FutureRowsResult,
    MarketDataRequest,
    MarketDataResult,
    MarketDataSource,
)


class DataSourceContractsTest(unittest.TestCase):
    def test_public_imports(self) -> None:
        self.assertIsNotNone(DataSourceConfig)
        self.assertIsNotNone(MarketDataRequest)
        self.assertIsNotNone(MarketDataResult)
        self.assertIsNotNone(FutureRowsRequest)
        self.assertIsNotNone(FutureRowsResult)
        self.assertIsNotNone(MarketDataSource)

    def test_contract_shapes_are_immutable_dataclasses(self) -> None:
        self.assertTrue(is_dataclass(DataSourceConfig))
        self.assertTrue(is_dataclass(MarketDataRequest))
        self.assertTrue(is_dataclass(MarketDataResult))
        self.assertTrue(is_dataclass(FutureRowsRequest))
        self.assertTrue(is_dataclass(FutureRowsResult))

        config = DataSourceConfig()
        market_request = MarketDataRequest(symbol="AAPL")
        market_result = MarketDataResult(request=market_request)
        future_request = FutureRowsRequest(symbol="AAPL", snapshot_date="2026-01-02")
        future_result = FutureRowsResult(request=future_request)

        with self.assertRaises(FrozenInstanceError):
            config.source_name = "other"
        with self.assertRaises(FrozenInstanceError):
            market_request.symbol = "MSFT"
        with self.assertRaises(FrozenInstanceError):
            market_result.request = MarketDataRequest(symbol="MSFT")
        with self.assertRaises(FrozenInstanceError):
            future_request.symbol = "MSFT"
        with self.assertRaises(FrozenInstanceError):
            future_result.request = FutureRowsRequest(
                symbol="MSFT", snapshot_date="2026-01-02"
            )

    def test_default_config(self) -> None:
        config = DataSourceConfig()

        self.assertEqual(config.source_name, "default")
        self.assertTrue(config.read_only)
        self.assertEqual(config.default_timeframe, "1D")
        self.assertEqual(config.default_horizon_days, 10)

    def test_request_and_result_defaults(self) -> None:
        market_request = MarketDataRequest(symbol="AAPL")
        market_result = MarketDataResult(request=market_request)
        future_request = FutureRowsRequest(symbol="AAPL", snapshot_date="2026-01-02")
        future_result = FutureRowsResult(request=future_request)

        self.assertEqual(market_request.timeframe, "1D")
        self.assertIsNone(market_request.start_date)
        self.assertIsNone(market_request.end_date)
        self.assertIsNone(market_request.limit)
        self.assertEqual(market_request.config, DataSourceConfig())
        self.assertEqual(market_result.rows, [])
        self.assertEqual(market_result.metadata, {})
        self.assertEqual(market_result.notes, [])

        self.assertEqual(future_request.timeframe, "1D")
        self.assertEqual(future_request.horizon_days, 10)
        self.assertEqual(future_request.config, DataSourceConfig())
        self.assertEqual(future_result.rows, [])
        self.assertEqual(future_result.metadata, {})
        self.assertEqual(future_result.notes, [])

    def test_protocol_interface_shape(self) -> None:
        self.assertTrue(getattr(MarketDataSource, "_is_protocol", False))

        protocol_methods = {
            name
            for name, value in MarketDataSource.__dict__.items()
            if callable(value) and not name.startswith("_")
        }
        self.assertEqual(protocol_methods, {"load_ohlcv", "load_future_rows"})

        load_ohlcv = inspect.signature(MarketDataSource.load_ohlcv)
        load_future_rows = inspect.signature(MarketDataSource.load_future_rows)
        self.assertEqual(list(load_ohlcv.parameters), ["self", "request"])
        self.assertEqual(list(load_future_rows.parameters), ["self", "request"])

        ohlcv_hints = get_type_hints(MarketDataSource.load_ohlcv)
        future_hints = get_type_hints(MarketDataSource.load_future_rows)
        self.assertIs(ohlcv_hints["request"], MarketDataRequest)
        self.assertIs(ohlcv_hints["return"], MarketDataResult)
        self.assertIs(future_hints["request"], FutureRowsRequest)
        self.assertIs(future_hints["return"], FutureRowsResult)

    def test_contracts_do_not_import_ai_network_or_broker_modules(self) -> None:
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

        for module in (contracts_module, data_source_module):
            tree = ast.parse(inspect.getsource(module))
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    imported_roots.update(alias.name.split(".")[0] for alias in node.names)
                if isinstance(node, ast.ImportFrom) and node.module:
                    imported_roots.add(node.module.split(".")[0])

        self.assertTrue(blocked_module_roots.isdisjoint(imported_roots))

    def test_importing_contracts_does_not_load_ai_network_or_broker_modules(self) -> None:
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

        import src.data_source.contracts  # noqa: F401

        imported = set(sys.modules) - before
        imported_roots = {name.split(".")[0] for name in imported}
        self.assertTrue(blocked_module_roots.isdisjoint(imported_roots))


if __name__ == "__main__":
    unittest.main()
