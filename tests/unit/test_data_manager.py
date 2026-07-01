from __future__ import annotations

from datetime import date
import unittest

import src.data.data_manager as data_manager_module
from src.data import DataLoadError, DataManager


class DataManagerTest(unittest.TestCase):
    def setUp(self) -> None:
        self._original_required_count = data_manager_module.REQUIRED_ROW_COUNT
        data_manager_module.REQUIRED_ROW_COUNT = 3

    def tearDown(self) -> None:
        data_manager_module.REQUIRED_ROW_COUNT = self._original_required_count

    def test_full_row_count_but_stale_latest_date_triggers_refresh(self) -> None:
        database = _Database(
            rows=[
                _row("2026-06-24", 100.0),
                _row("2026-06-25", 101.0),
                _row("2026-06-26", 102.0),
            ],
            latest_date="2026-06-26",
        )
        provider = _Provider(
            rows=[
                _row("2026-06-27", 103.0),
                _row("2026-06-30", 104.0),
                _row("2026-07-01", 105.0),
            ]
        )
        manager = DataManager(
            data_provider=provider,
            database_manager=database,
            today=lambda: date(2026, 7, 1),
        )

        result = manager.get_historical_data("aapl")

        self.assertEqual(result.source, "provider")
        self.assertEqual([row["date"] for row in result.rows], ["2026-06-27", "2026-06-30", "2026-07-01"])
        self.assertEqual(provider.calls, ["AAPL"])
        self.assertEqual(database.upserts, [("AAPL", provider.rows, "provider")])

    def test_full_row_count_and_fresh_latest_date_uses_cache(self) -> None:
        cached_rows = [
            _row("2026-06-29", 100.0),
            _row("2026-06-30", 101.0),
            _row("2026-07-01", 102.0),
        ]
        database = _Database(rows=cached_rows, latest_date="2026-07-01")
        provider = _Provider(rows=[_row("2026-07-02", 103.0)])
        manager = DataManager(
            data_provider=provider,
            database_manager=database,
            today=lambda: date(2026, 7, 1),
        )

        result = manager.get_historical_data("AAPL")

        self.assertEqual(result.source, "SQLite Cache")
        self.assertEqual(result.rows, cached_rows)
        self.assertEqual(provider.calls, [])
        self.assertEqual(database.upserts, [])

    def test_insufficient_row_count_still_fetches(self) -> None:
        database = _Database(
            rows=[
                _row("2026-06-30", 101.0),
                _row("2026-07-01", 102.0),
            ],
            latest_date="2026-07-01",
        )
        provider = _Provider(rows=[_row("2026-07-01", 102.0)])
        manager = DataManager(
            data_provider=provider,
            database_manager=database,
            today=lambda: date(2026, 7, 1),
        )

        result = manager.get_historical_data("AAPL")

        self.assertEqual(result.source, "provider")
        self.assertEqual(provider.calls, ["AAPL"])
        self.assertEqual(database.upserts, [("AAPL", provider.rows, "provider")])

    def test_provider_fetch_failure_is_wrapped_as_data_load_error(self) -> None:
        database = _Database(
            rows=[
                _row("2026-06-24", 100.0),
                _row("2026-06-25", 101.0),
                _row("2026-06-26", 102.0),
            ],
            latest_date="2026-06-26",
        )
        provider = _Provider(rows=[], error=RuntimeError("network unavailable"))
        manager = DataManager(
            data_provider=provider,
            database_manager=database,
            today=lambda: date(2026, 7, 1),
        )

        with self.assertRaisesRegex(DataLoadError, "Unable to load market data for AAPL"):
            manager.get_historical_data("AAPL")

        self.assertEqual(provider.calls, ["AAPL"])
        self.assertEqual(database.upserts, [])


class _Database:
    def __init__(self, *, rows: list[dict[str, object]], latest_date: str | None) -> None:
        self.rows = rows
        self.latest_date = latest_date
        self.upserts: list[tuple[str, list[dict[str, object]], str]] = []

    def get_ohlcv_daily(self, symbol: str, limit: int) -> list[dict[str, object]]:
        del symbol
        return self.rows[-limit:]

    def get_latest_ohlcv_daily_date(self, symbol: str) -> str | None:
        del symbol
        return self.latest_date

    def upsert_ohlcv_daily(
        self,
        symbol: str,
        rows: list[dict[str, object]],
        source: str,
    ) -> None:
        self.upserts.append((symbol, rows, source))


class _Provider:
    source_name = "provider"

    def __init__(
        self,
        *,
        rows: list[dict[str, object]],
        error: Exception | None = None,
    ) -> None:
        self.rows = rows
        self.error = error
        self.calls: list[str] = []

    def get_historical_data(self, symbol: str) -> list[dict[str, object]]:
        self.calls.append(symbol)
        if self.error is not None:
            raise self.error
        return self.rows


def _row(row_date: str, close: float) -> dict[str, object]:
    return {
        "date": row_date,
        "open": close - 1.0,
        "high": close + 1.0,
        "low": close - 2.0,
        "close": close,
        "volume": 1000,
    }


if __name__ == "__main__":
    unittest.main()
