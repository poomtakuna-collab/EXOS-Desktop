import ast
import inspect
import sqlite3
import sys
import unittest

import src.data_source.sqlite_source as sqlite_source_module
from src.data_source import (
    FutureRowsRequest,
    FutureRowsResult,
    MarketDataRequest,
    MarketDataResult,
    SQLiteDataSource,
)


class SQLiteDataSourceTest(unittest.TestCase):
    def test_loads_ohlcv_rows_in_deterministic_order(self) -> None:
        conn = _connection()
        _create_ohlcv_daily(conn)
        _insert_rows(conn, _rows())
        source = SQLiteDataSource(conn)

        result = source.load_ohlcv(MarketDataRequest(symbol="AAPL"))

        self.assertIsInstance(result, MarketDataResult)
        self.assertEqual(
            [row["date"] for row in result.rows],
            ["2026-01-01", "2026-01-02", "2026-01-03", "2026-01-04"],
        )
        self.assertTrue(all(row["symbol"] == "AAPL" for row in result.rows))
        self.assertTrue(all(row["timeframe"] == "1D" for row in result.rows))

    def test_limited_load_returns_latest_rows_in_ascending_order(self) -> None:
        conn = _connection()
        _create_ohlcv_daily(conn)
        _insert_rows(conn, _rows())
        source = SQLiteDataSource(conn)

        result = source.load_ohlcv(MarketDataRequest(symbol="AAPL", limit=2))

        self.assertEqual([row["date"] for row in result.rows], ["2026-01-03", "2026-01-04"])
        self.assertEqual([row["close"] for row in result.rows], [103.0, 104.0])

    def test_filters_by_symbol_start_end_and_limit(self) -> None:
        conn = _connection()
        _create_ohlcv_daily(conn)
        _insert_rows(conn, _rows())
        source = SQLiteDataSource(conn)

        result = source.load_ohlcv(
            MarketDataRequest(
                symbol="AAPL",
                start_date="2026-01-02",
                end_date="2026-01-04",
                limit=2,
            )
        )

        self.assertEqual([row["date"] for row in result.rows], ["2026-01-03", "2026-01-04"])

    def test_unlimited_date_range_load_remains_deterministic(self) -> None:
        conn = _connection()
        _create_ohlcv_daily(conn)
        _insert_rows(conn, _rows())
        source = SQLiteDataSource(conn)

        result = source.load_ohlcv(
            MarketDataRequest(
                symbol="AAPL",
                start_date="2026-01-02",
                end_date="2026-01-04",
            )
        )

        self.assertEqual(
            [row["date"] for row in result.rows],
            ["2026-01-02", "2026-01-03", "2026-01-04"],
        )

    def test_future_rows_use_existing_backtest_loader_behavior(self) -> None:
        conn = _connection()
        _create_ohlcv_daily(conn, include_role=False)
        _insert_rows(conn, _rows(include_role=False), include_role=False)
        source = SQLiteDataSource(conn)

        result = source.load_future_rows(
            FutureRowsRequest(
                symbol="AAPL",
                snapshot_date="2026-01-02",
                horizon_days=2,
            )
        )

        self.assertIsInstance(result, FutureRowsResult)
        self.assertEqual([row["date"] for row in result.rows], ["2026-01-03", "2026-01-04"])

    def test_future_rows_can_use_marked_future_fixtures(self) -> None:
        conn = _connection()
        _create_ohlcv_daily(conn)
        _insert_rows(conn, _rows() + _future_rows())
        source = SQLiteDataSource(conn)

        market_result = source.load_ohlcv(MarketDataRequest(symbol="AAPL"))
        future_result = source.load_future_rows(
            FutureRowsRequest(
                symbol="AAPL",
                snapshot_date=market_result.rows[-1]["date"],
                horizon_days=2,
            )
        )

        self.assertEqual(market_result.rows[-1]["date"], "2026-01-04")
        self.assertEqual([row["date"] for row in future_result.rows], ["2026-01-05", "2026-01-06"])

    def test_empty_result_is_deterministic(self) -> None:
        conn = _connection()
        _create_ohlcv_daily(conn)
        _insert_rows(conn, _rows())
        source = SQLiteDataSource(conn)
        request = MarketDataRequest(symbol="NVDA")

        first = source.load_ohlcv(request)
        second = source.load_ohlcv(request)

        self.assertEqual(first.rows, [])
        self.assertEqual(second.rows, [])
        self.assertEqual(first, second)

    def test_missing_table_failure_is_clear(self) -> None:
        source = SQLiteDataSource(_connection())

        with self.assertRaisesRegex(RuntimeError, "ohlcv_daily"):
            source.load_ohlcv(MarketDataRequest(symbol="AAPL"))
        with self.assertRaisesRegex(RuntimeError, "ohlcv_daily"):
            source.load_future_rows(
                FutureRowsRequest(symbol="AAPL", snapshot_date="2026-01-01")
            )

    def test_source_is_read_only(self) -> None:
        conn = _connection()
        _create_ohlcv_daily(conn)
        _insert_rows(conn, _rows())
        before = _table_rows(conn)
        source = SQLiteDataSource(conn)

        result = source.load_ohlcv(MarketDataRequest(symbol="AAPL"))
        result.rows[0]["close"] = 999.0
        source.load_future_rows(
            FutureRowsRequest(symbol="AAPL", snapshot_date="2026-01-02")
        )

        self.assertEqual(_table_rows(conn), before)
        self.assertFalse(hasattr(source, "save"))
        self.assertFalse(hasattr(source, "write"))
        self.assertFalse(hasattr(source, "insert"))

    def test_sqlite_source_does_not_import_ai_network_or_broker_modules(self) -> None:
        blocked_module_roots = _blocked_module_roots()
        imported_roots: set[str] = set()

        tree = ast.parse(inspect.getsource(sqlite_source_module))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported_roots.update(alias.name.split(".")[0] for alias in node.names)
            if isinstance(node, ast.ImportFrom) and node.module:
                imported_roots.add(node.module.split(".")[0])

        self.assertTrue(blocked_module_roots.isdisjoint(imported_roots))

    def test_running_sqlite_source_does_not_load_ai_network_or_broker_modules(self) -> None:
        conn = _connection()
        _create_ohlcv_daily(conn)
        _insert_rows(conn, _rows())
        source = SQLiteDataSource(conn)
        before = set(sys.modules)

        source.load_ohlcv(MarketDataRequest(symbol="AAPL"))
        source.load_future_rows(
            FutureRowsRequest(symbol="AAPL", snapshot_date="2026-01-02")
        )

        imported = set(sys.modules) - before
        imported_roots = {name.split(".")[0] for name in imported}
        self.assertTrue(_blocked_module_roots().isdisjoint(imported_roots))


def _connection() -> sqlite3.Connection:
    return sqlite3.connect(":memory:")


def _create_ohlcv_daily(conn: sqlite3.Connection, include_role: bool = True) -> None:
    role_column = ", row_type TEXT" if include_role else ""
    conn.execute(
        f"""
        CREATE TABLE ohlcv_daily (
            symbol TEXT NOT NULL,
            date TEXT NOT NULL,
            open REAL NOT NULL,
            high REAL NOT NULL,
            low REAL NOT NULL,
            close REAL NOT NULL,
            volume INTEGER NOT NULL,
            source TEXT NOT NULL
            {role_column}
        )
        """
    )


def _insert_rows(
    conn: sqlite3.Connection,
    rows: list[dict[str, object]],
    include_role: bool = True,
) -> None:
    if include_role:
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
        return

    conn.executemany(
        """
        INSERT INTO ohlcv_daily
            (symbol, date, open, high, low, close, volume, source)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
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
            )
            for row in rows
        ],
    )


def _rows(include_role: bool = True) -> list[dict[str, object]]:
    rows = [
        _row("MSFT", "2026-01-02", 201.0),
        _row("AAPL", "2026-01-03", 103.0),
        _row("AAPL", "2026-01-01", 101.0),
        _row("AAPL", "2026-01-02", 102.0),
        _row("AAPL", "2026-01-04", 104.0),
    ]
    if not include_role:
        for row in rows:
            row.pop("row_type", None)
    return rows


def _future_rows() -> list[dict[str, object]]:
    return [
        {**_row("AAPL", "2026-01-05", 105.0), "row_type": "future"},
        {**_row("AAPL", "2026-01-06", 106.0), "row_type": "future"},
        {**_row("AAPL", "2026-01-07", 107.0), "row_type": "future"},
    ]


def _row(symbol: str, row_date: str, close: float) -> dict[str, object]:
    return {
        "symbol": symbol,
        "date": row_date,
        "open": close - 0.5,
        "high": close + 1.0,
        "low": close - 1.0,
        "close": close,
        "volume": 1000,
        "source": "fixture",
        "row_type": None,
    }


def _table_rows(conn: sqlite3.Connection) -> list[tuple[object, ...]]:
    return conn.execute(
        """
        SELECT symbol, date, open, high, low, close, volume, source, row_type
        FROM ohlcv_daily
        ORDER BY symbol, date
        """
    ).fetchall()


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
