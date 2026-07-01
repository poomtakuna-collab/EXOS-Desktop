from __future__ import annotations

import sqlite3
import tempfile
import unittest
from pathlib import Path

from src.data import HistoricalDataResult
from src.data_source import MemoryDataSource
from src.gui.chart_data_adapter import ChartDataAdapter


class ChartDataAdapterTest(unittest.TestCase):
    def test_cached_load_uses_data_source_when_rows_exist(self) -> None:
        legacy = _LegacyLoader(
            cached=HistoricalDataResult(rows=[_row("legacy", 90.0)], source="legacy"),
            historical=HistoricalDataResult(rows=[_row("legacy-live", 91.0)], source="legacy-live"),
        )
        adapter = ChartDataAdapter(
            legacy_data_loader=legacy,
            data_source=MemoryDataSource([_row("2026-07-01", 100.0, symbol="AAPL")]),
            required_row_count=1,
        )

        result = adapter.get_cached_historical_data("aapl")

        self.assertEqual(result.source, "memory")
        self.assertEqual(result.rows[0]["date"], "2026-07-01")
        self.assertEqual(legacy.cached_calls, 0)

    def test_cached_load_falls_back_to_legacy_when_data_source_has_no_rows(self) -> None:
        legacy = _LegacyLoader(
            cached=HistoricalDataResult(rows=[_row("legacy", 90.0)], source="legacy"),
            historical=HistoricalDataResult(rows=[], source="legacy-live"),
        )
        adapter = ChartDataAdapter(
            legacy_data_loader=legacy,
            data_source=MemoryDataSource([_row("2026-07-01", 100.0, symbol="MSFT")]),
            required_row_count=1,
        )

        result = adapter.get_cached_historical_data("AAPL")

        self.assertEqual(result.source, "legacy")
        self.assertEqual(result.rows[0]["date"], "legacy")
        self.assertEqual(legacy.cached_calls, 1)

    def test_historical_load_uses_data_source_when_required_rows_are_available(self) -> None:
        legacy = _LegacyLoader(
            cached=HistoricalDataResult(rows=[], source="legacy"),
            historical=HistoricalDataResult(rows=[_row("legacy-live", 91.0)], source="legacy-live"),
        )
        adapter = ChartDataAdapter(
            legacy_data_loader=legacy,
            data_source=MemoryDataSource(
                [
                    _row("2026-07-01", 100.0, symbol="AAPL"),
                    _row("2026-07-02", 101.0, symbol="AAPL"),
                ]
            ),
            required_row_count=2,
        )

        result = adapter.get_historical_data("AAPL")

        self.assertEqual(result.source, "memory")
        self.assertEqual(len(result.rows), 2)
        self.assertEqual(legacy.historical_calls, 0)

    def test_historical_load_falls_back_when_data_source_rows_are_insufficient(self) -> None:
        legacy = _LegacyLoader(
            cached=HistoricalDataResult(rows=[], source="legacy"),
            historical=HistoricalDataResult(rows=[_row("legacy-live", 91.0)], source="legacy-live"),
        )
        adapter = ChartDataAdapter(
            legacy_data_loader=legacy,
            data_source=MemoryDataSource([_row("2026-07-01", 100.0, symbol="AAPL")]),
            required_row_count=2,
        )

        result = adapter.get_historical_data("AAPL")

        self.assertEqual(result.source, "legacy-live")
        self.assertEqual(legacy.historical_calls, 1)

    def test_data_source_errors_fall_back_to_legacy(self) -> None:
        legacy = _LegacyLoader(
            cached=HistoricalDataResult(rows=[_row("legacy", 90.0)], source="legacy"),
            historical=HistoricalDataResult(rows=[], source="legacy-live"),
        )
        adapter = ChartDataAdapter(
            legacy_data_loader=legacy,
            data_source=_FailingDataSource(),
            required_row_count=1,
        )

        result = adapter.get_cached_historical_data("AAPL")

        self.assertEqual(result.source, "legacy")
        self.assertEqual(legacy.cached_calls, 1)

    def test_default_sqlite_data_source_reads_existing_database_read_only(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "exos.db"
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
                        source TEXT NOT NULL
                    )
                    """
                )
                connection.execute(
                    """
                    INSERT INTO ohlcv_daily (
                        symbol, date, open, high, low, close, volume, source
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    ("AAPL", "2026-07-01", 99.0, 101.0, 98.0, 100.0, 1000, "fixture"),
                )
                connection.commit()
            finally:
                connection.close()

            legacy = _LegacyLoader(
                cached=HistoricalDataResult(rows=[_row("legacy", 90.0)], source="legacy"),
                historical=HistoricalDataResult(rows=[], source="legacy-live"),
            )
            adapter = ChartDataAdapter(
                legacy_data_loader=legacy,
                database_path=db_path,
                required_row_count=1,
            )

            result = adapter.get_cached_historical_data("AAPL")

            self.assertEqual(result.source, "sqlite")
            self.assertEqual(result.rows[0]["date"], "2026-07-01")
            self.assertEqual(result.rows[0]["source"], "fixture")
            self.assertEqual(legacy.cached_calls, 0)


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


class _FailingDataSource:
    def load_ohlcv(self, request: object) -> object:
        del request
        raise RuntimeError("fixture failure")

    def load_future_rows(self, request: object) -> object:
        del request
        raise RuntimeError("fixture failure")


def _row(
    date: str,
    close: float,
    *,
    symbol: str = "AAPL",
) -> dict[str, object]:
    return {
        "symbol": symbol,
        "timeframe": "1D",
        "date": date,
        "open": close - 1.0,
        "high": close + 1.0,
        "low": close - 2.0,
        "close": close,
        "volume": 1000,
        "source": "fixture",
    }


if __name__ == "__main__":
    unittest.main()
