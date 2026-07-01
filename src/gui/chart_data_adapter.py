from __future__ import annotations

import sqlite3
from datetime import date
from pathlib import Path
from typing import Callable, Protocol

from src.data import (
    REQUIRED_ROW_COUNT,
    DataManager,
    HistoricalDataResult,
    MarketDataRow,
    is_historical_data_fresh,
)
from src.data_source import MarketDataRequest, MarketDataSource, SQLiteDataSource
from src.data_source.analysis_cutoff import (
    determine_analysis_cutoff_date,
    rows_through_analysis_cutoff,
)


DEFAULT_CHART_DATABASE_PATH = Path("database") / "exos.db"
DEFAULT_CHART_TIMEFRAME = "1D"


class LegacyChartDataLoader(Protocol):
    def get_cached_historical_data(self, symbol: str) -> HistoricalDataResult:
        """Load currently cached historical chart data."""

    def get_historical_data(self, symbol: str) -> HistoricalDataResult:
        """Load historical chart data through the legacy path."""


class ChartDataAdapter:
    def __init__(
        self,
        *,
        legacy_data_loader: LegacyChartDataLoader | None = None,
        data_source: MarketDataSource | None = None,
        database_path: Path | str | None = None,
        required_row_count: int = REQUIRED_ROW_COUNT,
        today: Callable[[], date] | None = None,
    ) -> None:
        self._legacy_data_loader = legacy_data_loader or DataManager()
        self._data_source = data_source
        self._database_path = Path(database_path or DEFAULT_CHART_DATABASE_PATH)
        self._required_row_count = required_row_count
        self._today = today or date.today

    def get_cached_historical_data(self, symbol: str) -> HistoricalDataResult:
        data_source_result = self._load_from_data_source(symbol)
        if data_source_result is not None and data_source_result.rows:
            return self._apply_analysis_cutoff(data_source_result)
        return self._apply_analysis_cutoff(
            self._legacy_data_loader.get_cached_historical_data(symbol)
        )

    def get_historical_data(self, symbol: str) -> HistoricalDataResult:
        data_source_result = self._load_from_data_source(symbol)
        cutoff_result = (
            self._apply_analysis_cutoff(data_source_result)
            if data_source_result is not None
            else None
        )
        if (
            cutoff_result is not None
            and len(cutoff_result.rows) >= self._required_row_count
            and is_historical_data_fresh(cutoff_result, as_of_date=self._today())
        ):
            return cutoff_result
        return self._apply_analysis_cutoff(
            self._legacy_data_loader.get_historical_data(symbol)
        )

    def _apply_analysis_cutoff(
        self,
        result: HistoricalDataResult,
    ) -> HistoricalDataResult:
        cutoff = determine_analysis_cutoff_date(
            result.rows,
            as_of_date=self._today(),
        )
        rows = rows_through_analysis_cutoff(result.rows, cutoff.analysis_cutoff_date)
        if len(rows) > self._required_row_count:
            rows = rows[-self._required_row_count :]
        return HistoricalDataResult(rows=rows, source=result.source)

    def _load_from_data_source(self, symbol: str) -> HistoricalDataResult | None:
        normalized_symbol = str(symbol or "").strip().upper()
        if not normalized_symbol:
            return None

        if self._data_source is not None:
            return _load_ohlcv(
                self._data_source,
                symbol=normalized_symbol,
                limit=self._required_row_count + 1,
            )

        if not self._database_path.exists():
            return None

        uri = self._database_path.resolve().as_uri() + "?mode=ro"
        connection = sqlite3.connect(uri, uri=True)
        try:
            data_source = SQLiteDataSource(connection)
            return _load_ohlcv(
                data_source,
                symbol=normalized_symbol,
                limit=self._required_row_count + 1,
            )
        except (RuntimeError, sqlite3.Error, ValueError):
            return None
        finally:
            connection.close()


def _load_ohlcv(
    data_source: MarketDataSource,
    *,
    symbol: str,
    limit: int,
) -> HistoricalDataResult | None:
    try:
        result = data_source.load_ohlcv(
            MarketDataRequest(
                symbol=symbol,
                timeframe=DEFAULT_CHART_TIMEFRAME,
                limit=limit,
            )
        )
    except (RuntimeError, ValueError, sqlite3.Error):
        return None

    return HistoricalDataResult(
        rows=[_chart_row(row) for row in result.rows],
        source=str(result.metadata.get("source") or "Data Source v1"),
    )


def _chart_row(row: MarketDataRow) -> MarketDataRow:
    return {
        "date": row.get("date", ""),
        "open": row.get("open", 0.0),
        "high": row.get("high", 0.0),
        "low": row.get("low", 0.0),
        "close": row.get("close", 0.0),
        "volume": row.get("volume", 0),
        "source": row.get("source", ""),
    }
