from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from typing import Callable

from src.data.data_provider import DataProvider, MarketDataRow, YahooFinanceDataProvider
from src.database import DatabaseManager


REQUIRED_ROW_COUNT = 2500
CACHE_FRESHNESS_MAX_AGE_DAYS = 3
SQLITE_CACHE_SOURCE = "SQLite Cache"


class DataLoadError(Exception):
    pass


@dataclass(frozen=True)
class HistoricalDataResult:
    rows: list[MarketDataRow]
    source: str


class DataManager:
    def __init__(
        self,
        data_provider: DataProvider | None = None,
        database_manager: DatabaseManager | None = None,
        today: Callable[[], date] | None = None,
    ) -> None:
        self._data_provider = data_provider or YahooFinanceDataProvider()
        self._database_manager = database_manager or DatabaseManager()
        self._today = today or date.today

    def get_cached_historical_data(self, symbol: str) -> HistoricalDataResult:
        normalized_symbol = symbol.strip().upper()
        if not normalized_symbol:
            return HistoricalDataResult(rows=[], source=SQLITE_CACHE_SOURCE)

        local_rows = self._database_manager.get_ohlcv_daily(
            normalized_symbol, limit=REQUIRED_ROW_COUNT
        )
        return HistoricalDataResult(rows=local_rows, source=SQLITE_CACHE_SOURCE)

    def get_historical_data(self, symbol: str) -> HistoricalDataResult:
        normalized_symbol = symbol.strip().upper()
        if not normalized_symbol:
            return HistoricalDataResult(rows=[], source="")

        local_rows = self._database_manager.get_ohlcv_daily(
            normalized_symbol, limit=REQUIRED_ROW_COUNT
        )
        if len(local_rows) >= REQUIRED_ROW_COUNT and self.is_cache_fresh(normalized_symbol):
            return HistoricalDataResult(rows=local_rows, source=SQLITE_CACHE_SOURCE)

        try:
            provider_rows = self._data_provider.get_historical_data(normalized_symbol)
        except Exception as error:
            raise DataLoadError(
                f"Unable to load market data for {normalized_symbol}: {error}"
            ) from error

        provider_source = self._data_provider.source_name
        self._database_manager.upsert_ohlcv_daily(
            normalized_symbol, provider_rows, provider_source
        )
        return HistoricalDataResult(rows=provider_rows, source=provider_source)

    def is_cache_fresh(self, symbol: str) -> bool:
        normalized_symbol = symbol.strip().upper()
        if not normalized_symbol:
            return False
        latest_date = self._database_manager.get_latest_ohlcv_daily_date(normalized_symbol)
        return is_ohlcv_cache_fresh(latest_date, as_of_date=self._today())


def is_historical_data_fresh(
    result: HistoricalDataResult,
    *,
    as_of_date: date | None = None,
    max_age_days: int = CACHE_FRESHNESS_MAX_AGE_DAYS,
) -> bool:
    return is_ohlcv_cache_fresh(
        _latest_row_date(result.rows),
        as_of_date=as_of_date,
        max_age_days=max_age_days,
    )


def is_ohlcv_cache_fresh(
    latest_date: str | date | None,
    *,
    as_of_date: date | None = None,
    max_age_days: int = CACHE_FRESHNESS_MAX_AGE_DAYS,
) -> bool:
    parsed_latest_date = _parse_date(latest_date)
    if parsed_latest_date is None:
        return False
    today = as_of_date or date.today()
    if parsed_latest_date > today:
        return True
    return today - parsed_latest_date <= timedelta(days=max_age_days)


def _latest_row_date(rows: list[MarketDataRow]) -> str | date | None:
    if not rows:
        return None
    return rows[-1].get("date")


def _parse_date(value: str | date | None) -> date | None:
    if isinstance(value, date):
        return value
    if not value:
        return None
    try:
        return date.fromisoformat(str(value))
    except ValueError:
        return None
