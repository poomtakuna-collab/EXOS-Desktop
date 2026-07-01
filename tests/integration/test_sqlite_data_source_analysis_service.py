import sqlite3
from contextlib import closing
import sys
import unittest
from datetime import date, timedelta

from src.application import AnalysisService, AnalysisServiceResult
from src.data_source import SQLiteDataSource


class SQLiteDataSourceAnalysisServiceIntegrationTest(unittest.TestCase):
    def test_sqlite_data_source_to_analysis_service_to_report(self) -> None:
        with closing(sqlite3.connect(":memory:")) as conn:
            _create_ohlcv_daily(conn)
            _insert_rows(conn, _market_rows() + _future_rows())
            service = AnalysisService(SQLiteDataSource(conn))

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

    def test_sqlite_integration_does_not_import_ai_network_or_broker_modules(self) -> None:
        with closing(sqlite3.connect(":memory:")) as conn:
            _create_ohlcv_daily(conn)
            _insert_rows(conn, _market_rows() + _future_rows())
            service = AnalysisService(SQLiteDataSource(conn))
            before = set(sys.modules)

            service.analyze_symbol_with_report("AAPL")

        imported = set(sys.modules) - before
        imported_roots = {name.split(".")[0] for name in imported}
        self.assertTrue(_blocked_module_roots().isdisjoint(imported_roots))


def _create_ohlcv_daily(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE ohlcv_daily (
            symbol TEXT NOT NULL,
            date TEXT NOT NULL,
            open REAL NOT NULL,
            high REAL NOT NULL,
            low REAL NOT NULL,
            close REAL NOT NULL,
            volume INTEGER NOT NULL,
            source TEXT NOT NULL,
            row_type TEXT
        )
        """
    )


def _insert_rows(conn: sqlite3.Connection, rows: list[dict[str, object]]) -> None:
    conn.executemany(
        """
        INSERT INTO ohlcv_daily
            (symbol, date, open, high, low, close, volume, source, row_type)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            (
                row["symbol"],
                row["date"],
                row["open"],
                row["high"],
                row["low"],
                row["close"],
                row["volume"],
                row["source"],
                row.get("row_type"),
            )
            for row in rows
        ],
    )


def _market_rows(count: int = 240) -> list[dict[str, object]]:
    start_date = date(2026, 1, 1)
    rows: list[dict[str, object]] = []
    for index in range(count):
        close = 100.0 + index * 0.25
        rows.append(_row((start_date + timedelta(days=index)).isoformat(), close))
    return rows


def _future_rows(count: int = 10) -> list[dict[str, object]]:
    start_date = date(2026, 8, 29)
    rows: list[dict[str, object]] = []
    for index in range(count):
        close = 160.0 + index
        rows.append(
            {
                **_row((start_date + timedelta(days=index)).isoformat(), close),
                "row_type": "future",
            }
        )
    return rows


def _row(row_date: str, close: float) -> dict[str, object]:
    return {
        "symbol": "AAPL",
        "date": row_date,
        "open": close - 0.5,
        "high": close + 8.0,
        "low": close - 1.0,
        "close": close,
        "volume": 1_000_000,
        "source": "fixture",
        "row_type": None,
    }


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


def _blocked_module_roots() -> set[str]:
    return {
        "openai",
        "anthropic",
        "yfinance",
        "requests",
        "httpx",
        "urllib3",
        "alpaca",
        "ib_insync",
    }


if __name__ == "__main__":
    unittest.main()
