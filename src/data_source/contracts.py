from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol


MarketDataRow = dict[str, Any]


@dataclass(frozen=True)
class DataSourceConfig:
    source_name: str = "default"
    read_only: bool = True
    default_timeframe: str = "1D"
    default_horizon_days: int = 10


@dataclass(frozen=True)
class MarketDataRequest:
    symbol: str
    timeframe: str = "1D"
    start_date: str | None = None
    end_date: str | None = None
    limit: int | None = None
    config: DataSourceConfig = field(default_factory=DataSourceConfig)


@dataclass(frozen=True)
class MarketDataResult:
    request: MarketDataRequest
    rows: list[MarketDataRow] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class FutureRowsRequest:
    symbol: str
    snapshot_date: str
    timeframe: str = "1D"
    horizon_days: int = 10
    config: DataSourceConfig = field(default_factory=DataSourceConfig)


@dataclass(frozen=True)
class FutureRowsResult:
    request: FutureRowsRequest
    rows: list[MarketDataRow] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)


class MarketDataSource(Protocol):
    def load_ohlcv(self, request: MarketDataRequest) -> MarketDataResult:
        pass

    def load_future_rows(self, request: FutureRowsRequest) -> FutureRowsResult:
        pass
