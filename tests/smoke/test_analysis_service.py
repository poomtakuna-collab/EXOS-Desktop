from __future__ import annotations

import sys
import unittest
from datetime import date, timedelta

from src.application import AnalysisService, AnalysisServiceResult
from src.data_source import MemoryDataSource


class AnalysisServiceSmokeTest(unittest.TestCase):
    def test_full_deterministic_application_service_flow(self) -> None:
        service = AnalysisService(
            MemoryDataSource(_fake_ohlcv_rows() + _fake_similar_patterns() + _fake_future_rows())
        )

        first = service.analyze_symbol_with_report("AAPL")
        second = service.analyze_symbol_with_report("AAPL")

        self.assertIsInstance(first, AnalysisServiceResult)
        self.assertNotEqual(first.analysis_result.snapshot, {})
        self.assertNotEqual(first.analysis_result.probability, {})
        self.assertNotEqual(first.analysis_result.prediction, {})
        self.assertIsNotNone(first.analysis_result.strategy)
        self.assertIsNotNone(first.analysis_result.backtest)
        self.assertEqual(first.analysis_report.symbol, "AAPL")
        self.assertEqual(first.analysis_report.timeframe, "1D")
        self.assertEqual(first.analysis_report.snapshot_status, "snapshot: available")
        self.assertEqual(first.analysis_report.probability_status, "probability: available")
        self.assertEqual(first.analysis_report.prediction_status, "prediction: available")
        self.assertEqual(first.analysis_report.strategy_status, "strategy: available")
        self.assertTrue(first.analysis_report.backtest_status.startswith("backtest: available"))
        self.assertEqual(first, second)

        output_values = {value.upper() for value in _flatten_values(first.__dict__)}
        self.assertNotIn("BUY", output_values)
        self.assertNotIn("SELL", output_values)
        self.assertNotIn("HOLD", output_values)

    def test_full_application_service_flow_does_not_import_ai_network_or_broker_modules(self) -> None:
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
        service = AnalysisService(
            MemoryDataSource(_fake_ohlcv_rows() + _fake_similar_patterns() + _fake_future_rows())
        )
        before = set(sys.modules)

        service.analyze_symbol_with_report("AAPL")

        imported = set(sys.modules) - before
        imported_roots = {name.split(".")[0] for name in imported}
        self.assertTrue(blocked_module_roots.isdisjoint(imported_roots))


def _fake_ohlcv_rows(count: int = 240) -> list[dict[str, object]]:
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


def _fake_similar_patterns() -> list[dict[str, object]]:
    return [
        {
            "row_type": "similar_pattern",
            "pattern_id": 101,
            "similarity_score": 92.0,
            "confidence": 80.0,
            "sample_count": 30,
            "average_5d_return": 2.0,
            "average_10d_return": 4.0,
            "average_20d_return": 6.0,
            "hit_5pct_rate": 55.0,
            "hit_10pct_rate": 25.0,
            "average_max_gain": 8.0,
            "average_drawdown": -3.0,
        },
        {
            "row_type": "similar_pattern",
            "pattern_id": 202,
            "similarity_score": 84.0,
            "confidence": 70.0,
            "sample_count": 20,
            "average_5d_return": 1.0,
            "average_10d_return": 2.0,
            "average_20d_return": 3.0,
            "hit_5pct_rate": 45.0,
            "hit_10pct_rate": 15.0,
            "average_max_gain": 5.0,
            "average_drawdown": -2.0,
        },
    ]


def _fake_future_rows(count: int = 10) -> list[dict[str, object]]:
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
