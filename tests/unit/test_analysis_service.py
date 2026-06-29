import ast
import inspect
import sys
import unittest
from datetime import date, timedelta

import src.application.analysis_service as analysis_service_module
from dataclasses import FrozenInstanceError, is_dataclass

from src.analysis_pipeline import AnalysisReport, AnalysisResult
from src.application import AnalysisService, AnalysisServiceResult
from src.data_source import MemoryDataSource


class AnalysisServiceTest(unittest.TestCase):
    def test_service_returns_analysis_result(self) -> None:
        service = AnalysisService(MemoryDataSource(_market_rows()))

        result = service.analyze_symbol("AAPL")

        self.assertIsInstance(result, AnalysisResult)
        self.assertEqual(result.symbol, "AAPL")
        self.assertEqual(result.timeframe, "1D")

    def test_service_populates_snapshot_probability_prediction_and_strategy(self) -> None:
        service = AnalysisService(MemoryDataSource(_market_rows()))

        result = service.analyze_symbol("AAPL")

        self.assertNotEqual(result.snapshot, {})
        self.assertNotEqual(result.probability, {})
        self.assertNotEqual(result.prediction, {})
        self.assertIsNotNone(result.strategy)
        self.assertEqual(result.snapshot["metadata"]["symbol"], "AAPL")
        self.assertEqual(result.snapshot["metadata"]["timeframe"], "1D")

    def test_service_populates_backtest_when_future_rows_are_available(self) -> None:
        service = AnalysisService(MemoryDataSource(_market_rows() + _future_rows()))

        result = service.analyze_symbol("AAPL")

        self.assertIsNotNone(result.backtest)
        self.assertIn("result", result.backtest)
        self.assertIn("report", result.backtest)
        self.assertEqual(result.backtest["result"]["attempted_trades"], 1)

    def test_service_output_is_deterministic(self) -> None:
        service = AnalysisService(MemoryDataSource(_market_rows() + _future_rows()))

        first = service.analyze_symbol("AAPL")
        second = service.analyze_symbol("AAPL")

        self.assertEqual(first, second)

    def test_service_output_has_no_recommendation(self) -> None:
        service = AnalysisService(MemoryDataSource(_market_rows() + _future_rows()))

        result = service.analyze_symbol("AAPL")

        output_values = {value.upper() for value in _flatten_values(result.__dict__)}
        self.assertNotIn("BUY", output_values)
        self.assertNotIn("SELL", output_values)
        self.assertNotIn("HOLD", output_values)

    def test_service_does_not_import_ai_network_or_broker_modules(self) -> None:
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

        tree = ast.parse(inspect.getsource(analysis_service_module))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported_roots.update(alias.name.split(".")[0] for alias in node.names)
            if isinstance(node, ast.ImportFrom) and node.module:
                imported_roots.add(node.module.split(".")[0])

        self.assertTrue(blocked_module_roots.isdisjoint(imported_roots))

    def test_running_service_does_not_load_ai_network_or_broker_modules(self) -> None:
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
        service = AnalysisService(MemoryDataSource(_market_rows() + _future_rows()))
        before = set(sys.modules)

        service.analyze_symbol("AAPL")

        imported = set(sys.modules) - before
        imported_roots = {name.split(".")[0] for name in imported}
        self.assertTrue(blocked_module_roots.isdisjoint(imported_roots))

    def test_analyze_symbol_with_report_returns_result_and_report(self) -> None:
        service = AnalysisService(MemoryDataSource(_market_rows() + _future_rows()))

        result = service.analyze_symbol_with_report("AAPL")

        self.assertTrue(is_dataclass(AnalysisServiceResult))
        self.assertIsInstance(result, AnalysisServiceResult)
        self.assertIsInstance(result.analysis_result, AnalysisResult)
        self.assertIsInstance(result.analysis_report, AnalysisReport)

        with self.assertRaises(FrozenInstanceError):
            result.analysis_result = result.analysis_result

    def test_report_matches_result_symbol_and_timeframe(self) -> None:
        service = AnalysisService(MemoryDataSource(_market_rows() + _future_rows()))

        result = service.analyze_symbol_with_report("AAPL")

        self.assertEqual(result.analysis_report.symbol, result.analysis_result.symbol)
        self.assertEqual(result.analysis_report.timeframe, result.analysis_result.timeframe)

    def test_full_pipeline_report_is_populated(self) -> None:
        service = AnalysisService(MemoryDataSource(_market_rows() + _future_rows()))

        result = service.analyze_symbol_with_report("AAPL")
        report = result.analysis_report

        self.assertEqual(report.snapshot_status, "snapshot: available")
        self.assertEqual(report.probability_status, "probability: available")
        self.assertEqual(report.prediction_status, "prediction: available")
        self.assertEqual(report.strategy_status, "strategy: available")
        self.assertTrue(report.backtest_status.startswith("backtest: available"))

    def test_analyze_symbol_with_report_output_is_deterministic(self) -> None:
        service = AnalysisService(MemoryDataSource(_market_rows() + _future_rows()))

        first = service.analyze_symbol_with_report("AAPL")
        second = service.analyze_symbol_with_report("AAPL")

        self.assertEqual(first, second)

    def test_analyze_symbol_with_report_output_has_no_recommendation(self) -> None:
        service = AnalysisService(MemoryDataSource(_market_rows() + _future_rows()))

        result = service.analyze_symbol_with_report("AAPL")

        output_values = {value.upper() for value in _flatten_values(result.__dict__)}
        self.assertNotIn("BUY", output_values)
        self.assertNotIn("SELL", output_values)
        self.assertNotIn("HOLD", output_values)

    def test_analyze_symbol_with_report_does_not_load_ai_network_or_broker_modules(self) -> None:
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
        service = AnalysisService(MemoryDataSource(_market_rows() + _future_rows()))
        before = set(sys.modules)

        service.analyze_symbol_with_report("AAPL")

        imported = set(sys.modules) - before
        imported_roots = {name.split(".")[0] for name in imported}
        self.assertTrue(blocked_module_roots.isdisjoint(imported_roots))


def _market_rows(count: int = 240) -> list[dict[str, object]]:
    start_date = date(2026, 1, 1)
    rows: list[dict[str, object]] = []
    for index in range(count):
        close = 100.0 + index * 0.25
        rows.append(
            {
                "symbol": "AAPL",
                "timeframe": "1D",
                "date": (start_date + timedelta(days=index)).isoformat(),
                "open": close - 0.25,
                "high": close + 1.0,
                "low": close - 1.0,
                "close": close,
                "volume": 1_000_000 + index,
            }
        )
    return rows


def _future_rows(count: int = 10) -> list[dict[str, object]]:
    start_date = date(2026, 8, 29)
    rows: list[dict[str, object]] = []
    for index in range(count):
        close = 160.0 + index
        rows.append(
            {
                "symbol": "AAPL",
                "timeframe": "1D",
                "date": (start_date + timedelta(days=index)).isoformat(),
                "open": close - 0.5,
                "high": close + 8.0,
                "low": close - 1.0,
                "close": close,
                "volume": 1_100_000 + index,
                "row_type": "future",
            }
        )
    return rows


def _flatten_values(value: object) -> list[str]:
    if isinstance(value, dict):
        flattened: list[str] = []
        for item in value.values():
            flattened.extend(_flatten_values(item))
        return flattened
    if isinstance(value, list):
        flattened = []
        for item in value:
            flattened.extend(_flatten_values(item))
        return flattened
    return [str(value)]


if __name__ == "__main__":
    unittest.main()
