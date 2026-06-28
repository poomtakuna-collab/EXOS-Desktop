from __future__ import annotations

from dataclasses import dataclass

from src.data.data_provider import DataProvider, MarketDataRow, YahooFinanceDataProvider
from src.database import DatabaseManager


REQUIRED_ROW_COUNT = 300
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
    ) -> None:
        self._data_provider = data_provider or YahooFinanceDataProvider()
        self._database_manager = database_manager or DatabaseManager()

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
        if len(local_rows) >= REQUIRED_ROW_COUNT:
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