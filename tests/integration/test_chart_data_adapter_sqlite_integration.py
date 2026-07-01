from __future__ import annotations

import sqlite3
import tempfile
import unittest
from pathlib import Path

from src.data import HistoricalDataResult
from src.gui.chart_data_adapter import ChartDataAdapter


class ChartDataAdapterSQLiteIntegrationTest(unittest.TestCase):
    def test_sqlite_data_source_load_preserves_order_and_values(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "exos.db"
            _create_database(db_path, _mixed_rows())
            legacy = _LegacyLoader(
                cached=HistoricalDataResult(rows=[_chart_row("legacy", 1.0)], source="legacy"),
                historical=HistoricalDataResult(rows=[], source="legacy-live"),
            )
            adapter = ChartDataAdapter(
                legacy_data_loader=legacy,
                database_path=db_path,
                required_row_count=4,
            )

            result = adapter.get_cached_historical_data("aapl")

            self.assertEqual(result.source, "sqlite")
            self.assertEqual(
                [row["date"] for row in result.rows],
                ["2026-01-01", "2026-01-02", "2026-01-03", "2026-01-04"],
            )
            self.assertEqual([row["close"] for row in result.rows], [101.0, 102.0, 103.0, 104.0])
            self.assertEqual(result.rows[0]["open"], 100.5)
            self.assertEqual(result.rows[-1]["volume"], 4000)
            self.assertTrue(all("symbol" not in row for row in result.rows))
            self.assertEqual(legacy.cached_calls, 0)

    def test_historical_load_uses_sqlite_only_when_required_count_is_available(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "exos.db"
            _create_database(db_path, _mixed_rows())
            legacy = _LegacyLoader(
                cached=HistoricalDataResult(rows=[], source="legacy"),
                historical=HistoricalDataResult(rows=[_chart_row("legacy-live", 91.0)], source="legacy-live"),
            )
            adapter = ChartDataAdapter(
                legacy_data_loader=legacy,
                database_path=db_path,
                required_row_count=4,
            )

            result = adapter.get_historical_data("AAPL")

            self.assertEqual(result.source, "sqlite")
            self.assertEqual(len(result.rows), 4)
            self.assertEqual(legacy.historical_calls, 0)

    def test_historical_load_falls_back_when_sqlite_rows_are_insufficient(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "exos.db"
            _create_database(db_path, _mixed_rows())
            legacy = _LegacyLoader(
                cached=HistoricalDataResult(rows=[], source="legacy"),
                historical=HistoricalDataResult(rows=[_chart_row("legacy-live", 91.0)], source="legacy-live"),
            )
            adapter = ChartDataAdapter(
                legacy_data_loader=legacy,
                database_path=db_path,
                required_row_count=5,
            )

            result = adapter.get_historical_data("AAPL")

            self.assertEqual(result.source, "legacy-live")
            self.assertEqual(result.rows[0]["date"], "legacy-live")
            self.assertEqual(legacy.historical_calls, 1)

    def test_cached_load_falls_back_only_when_sqlite_unavailable_or_empty(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "exos.db"
            _create_database(db_path, _mixed_rows())
            legacy = _LegacyLoader(
                cached=HistoricalDataResult(rows=[_chart_row("legacy-cache", 88.0)], source="legacy-cache"),
                historical=HistoricalDataResult(rows=[], source="legacy-live"),
            )
            adapter = ChartDataAdapter(
                legacy_data_loader=legacy,
                database_path=db_path,
                required_row_count=4,
            )

            sqlite_result = adapter.get_cached_historical_data("AAPL")
            empty_symbol_result = adapter.get_cached_historical_data("NVDA")

            self.assertEqual(sqlite_result.source, "sqlite")
            self.assertEqual(empty_symbol_result.source, "legacy-cache")
            self.assertEqual(legacy.cached_calls, 1)

    def test_missing_sqlite_table_falls_back_to_legacy(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "exos.db"
            connection = sqlite3.connect(db_path)
            try:
                connection.execute("CREATE TABLE unrelated (id INTEGER PRIMARY KEY)")
                connection.commit()
            finally:
                connection.close()
            legacy = _LegacyLoader(
                cached=HistoricalDataResult(rows=[_chart_row("legacy-cache", 88.0)], source="legacy-cache"),
                historical=HistoricalDataResult(rows=[_chart_row("legacy-live", 89.0)], source="legacy-live"),
            )
            adapter = ChartDataAdapter(
                legacy_data_loader=legacy,
                database_path=db_path,
                required_row_count=1,
            )

            result = adapter.get_cached_historical_data("AAPL")

            self.assertEqual(result.source, "legacy-cache")
            self.assertEqual(legacy.cached_calls, 1)

    def test_sqlite_chart_loading_does_not_write_to_database(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "exos.db"
            _create_database(db_path, _mixed_rows())
            before = _database_snapshot(db_path)
            legacy = _LegacyLoader(
                cached=HistoricalDataResult(rows=[_chart_row("legacy-cache", 88.0)], source="legacy-cache"),
                historical=HistoricalDataResult(rows=[_chart_row("legacy-live", 89.0)], source="legacy-live"),
            )
            adapter = ChartDataAdapter(
                legacy_data_loader=legacy,
                database_path=db_path,
                required_row_count=4,
            )

            adapter.get_cached_historical_data("AAPL")
            adapter.get_historical_data("AAPL")

            self.assertEqual(_database_snapshot(db_path), before)
            self.assertEqual(legacy.cached_calls, 0)
            self.assertEqual(legacy.historical_calls, 0)


class _LegacyLoader:
    def __init__(
        self,
        *,
        cached: HistoricalDataResult,
        historical: HistoricalDataResult,
    ) -> None:
        self.cached = cached
        self.historical = historical
        self.cached_calls = 0
        self.historical_calls = 0

    def get_cached_historical_data(self, symbol: str) -> HistoricalDataResult:
        del symbol
        self.cached_calls += 1
        return self.cached

    def get_historical_data(self, symbol: str) -> HistoricalDataResult:
        del symbol
        self.historical_calls += 1
        return self.historical


def _create_database(
    db_path: Path,
    rows: list[dict[str, object]],
) -> None:
    connection = sqlite3.connect(db_path)
    try:
        connection.execute(
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
        connection.executemany(
            """
            INSERT INTO ohlcv_daily (
                symbol, date, open, high, low, close, volume, source, row_type
            )
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
        connection.commit()
    finally:
        connection.close()


def _mixed_rows() -> list[dict[str, object]]:
    return [
        _db_row("MSFT", "2026-01-02", 202.0),
        _db_row("AAPL", "2026-01-03", 103.0),
        _db_row("AAPL", "2026-01-01", 101.0),
        {**_db_row("AAPL", "2026-01-05", 105.0), "row_type": "future"},
        _db_row("AAPL", "2026-01-02", 102.0),
        _db_row("AAPL", "2026-01-04", 104.0),
    ]


def _db_row(
    symbol: str,
    row_date: str,
    close: float,
) -> dict[str, object]:
    return {
        "symbol": symbol,
        "date": row_date,
        "open": close - 0.5,
        "high": close + 1.0,
        "low": close - 1.0,
        "close": close,
        "volume": int(close - 100.0) * 1000,
        "source": "fixture",
        "row_type": None,
    }


def _chart_row(row_date: str, close: float) -> dict[str, object]:
    return {
        "date": row_date,
        "open": close - 0.5,
        "high": close + 1.0,
        "low": close - 1.0,
        "close": close,
        "volume": 1000,
        "source": "legacy",
    }


def _database_snapshot(db_path: Path) -> list[tuple[object, ...]]:
    connection = sqlite3.connect(db_path)
    try:
        return connection.execute(
            """
            SELECT symbol, date, open, high, low, close, volume, source, row_type
            FROM ohlcv_daily
            ORDER BY symbol, date, row_type
            """
        ).fetchall()
    finally:
        connection.close()


if __name__ == "__main__":
    unittest.main()
