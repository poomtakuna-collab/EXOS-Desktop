import ast
import inspect
import sys
import unittest

import src.data_source.memory_source as memory_source_module
from src.data_source import (
    FutureRowsRequest,
    FutureRowsResult,
    MarketDataRequest,
    MarketDataResult,
    MemoryDataSource,
)


def _rows() -> list[dict[str, object]]:
    return [
        {
            "symbol": "MSFT",
            "timeframe": "1D",
            "date": "2026-01-02",
            "open": 201.0,
            "high": 203.0,
            "low": 200.0,
            "close": 202.0,
            "volume": 2000,
        },
        {
            "symbol": "AAPL",
            "timeframe": "1W",
            "date": "2026-01-01",
            "open": 90.0,
            "high": 95.0,
            "low": 88.0,
            "close": 94.0,
            "volume": 7000,
        },
        {
            "symbol": "AAPL",
            "timeframe": "1D",
            "date": "2026-01-03",
            "open": 103.0,
            "high": 105.0,
            "low": 102.0,
            "close": 104.0,
            "volume": 3000,
        },
        {
            "symbol": "AAPL",
            "timeframe": "1D",
            "date": "2026-01-01",
            "open": 100.0,
            "high": 102.0,
            "low": 99.0,
            "close": 101.0,
            "volume": 1000,
        },
        {
            "symbol": "AAPL",
            "timeframe": "1D",
            "date": "2026-01-02",
            "open": 101.0,
            "high": 104.0,
            "low": 100.0,
            "close": 103.0,
            "volume": 2500,
        },
        {
            "symbol": "AAPL",
            "timeframe": "1D",
            "date": "2026-01-04",
            "open": 104.0,
            "high": 106.0,
            "low": 103.0,
            "close": 105.0,
            "volume": 3200,
        },
    ]


class MemoryDataSourceTest(unittest.TestCase):
    def test_loads_matching_ohlcv_rows(self) -> None:
        source = MemoryDataSource(_rows())
        request = MarketDataRequest(symbol="AAPL")

        result = source.load_ohlcv(request)

        self.assertIsInstance(result, MarketDataResult)
        self.assertEqual(result.request, request)
        self.assertEqual(
            [row["date"] for row in result.rows],
            ["2026-01-01", "2026-01-02", "2026-01-03", "2026-01-04"],
        )
        self.assertTrue(all(row["symbol"] == "AAPL" for row in result.rows))
        self.assertTrue(all(row["timeframe"] == "1D" for row in result.rows))

    def test_ohlcv_load_excludes_rows_marked_as_future(self) -> None:
        rows = _rows() + [
            {
                "symbol": "AAPL",
                "timeframe": "1D",
                "date": "2026-01-05",
                "open": 105.0,
                "high": 106.0,
                "low": 104.0,
                "close": 105.5,
                "volume": 3300,
                "row_type": "future",
            }
        ]
        source = MemoryDataSource(rows)

        result = source.load_ohlcv(MarketDataRequest(symbol="AAPL"))

        self.assertEqual(
            [row["date"] for row in result.rows],
            ["2026-01-01", "2026-01-02", "2026-01-03", "2026-01-04"],
        )

    def test_future_rows_return_rows_after_snapshot_date_only(self) -> None:
        source = MemoryDataSource(_rows())
        request = FutureRowsRequest(
            symbol="AAPL",
            snapshot_date="2026-01-02",
            horizon_days=2,
        )

        result = source.load_future_rows(request)

        self.assertIsInstance(result, FutureRowsResult)
        self.assertEqual(result.request, request)
        self.assertEqual([row["date"] for row in result.rows], ["2026-01-03", "2026-01-04"])

    def test_filters_by_timeframe_start_end_and_limit(self) -> None:
        source = MemoryDataSource(_rows())
        request = MarketDataRequest(
            symbol="AAPL",
            timeframe="1D",
            start_date="2026-01-02",
            end_date="2026-01-04",
            limit=2,
        )

        result = source.load_ohlcv(request)

        self.assertEqual([row["date"] for row in result.rows], ["2026-01-02", "2026-01-03"])

    def test_ordering_is_deterministic(self) -> None:
        source = MemoryDataSource(reversed(_rows()))
        request = MarketDataRequest(symbol="AAPL", timeframe="1D")

        first = source.load_ohlcv(request)
        second = source.load_ohlcv(request)

        self.assertEqual(first.rows, second.rows)
        self.assertEqual(
            [row["date"] for row in first.rows],
            ["2026-01-01", "2026-01-02", "2026-01-03", "2026-01-04"],
        )

    def test_empty_result_is_deterministic(self) -> None:
        source = MemoryDataSource(_rows())
        request = MarketDataRequest(symbol="NVDA", timeframe="1D")

        first = source.load_ohlcv(request)
        second = source.load_ohlcv(request)

        self.assertEqual(first.rows, [])
        self.assertEqual(second.rows, [])
        self.assertEqual(first, second)

    def test_source_is_read_only(self) -> None:
        stored_rows = _rows()
        source = MemoryDataSource(stored_rows)
        stored_rows[3]["close"] = 999.0

        first = source.load_ohlcv(MarketDataRequest(symbol="AAPL"))
        first.rows[0]["close"] = 888.0
        second = source.load_ohlcv(MarketDataRequest(symbol="AAPL"))

        self.assertEqual(second.rows[0]["close"], 101.0)
        self.assertFalse(hasattr(source, "save"))
        self.assertFalse(hasattr(source, "write"))
        self.assertFalse(hasattr(source, "insert"))

    def test_memory_source_does_not_import_ai_network_or_broker_modules(self) -> None:
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

        tree = ast.parse(inspect.getsource(memory_source_module))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported_roots.update(alias.name.split(".")[0] for alias in node.names)
            if isinstance(node, ast.ImportFrom) and node.module:
                imported_roots.add(node.module.split(".")[0])

        self.assertTrue(blocked_module_roots.isdisjoint(imported_roots))

    def test_importing_memory_source_does_not_load_ai_network_or_broker_modules(self) -> None:
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

        import src.data_source.memory_source  # noqa: F401

        imported = set(sys.modules) - before
        imported_roots = {name.split(".")[0] for name in imported}
        self.assertTrue(blocked_module_roots.isdisjoint(imported_roots))


if __name__ == "__main__":
    unittest.main()
