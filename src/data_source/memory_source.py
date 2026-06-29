from __future__ import annotations

from typing import Iterable

from src.data_source.contracts import (
    FutureRowsRequest,
    FutureRowsResult,
    MarketDataRequest,
    MarketDataResult,
    MarketDataRow,
)


class MemoryDataSource:
    def __init__(self, rows: Iterable[MarketDataRow]) -> None:
        self._rows = tuple(dict(row) for row in rows)

    def load_ohlcv(self, request: MarketDataRequest) -> MarketDataResult:
        rows = [
            row
            for row in self._ordered_rows()
            if self._matches_symbol(row, request.symbol)
            and self._matches_timeframe(row, request.timeframe)
            and self._date_between(row, request.start_date, request.end_date)
            and not self._is_future_row(row)
        ]

        if request.limit is not None:
            rows = rows[: request.limit]

        return MarketDataResult(
            request=request,
            rows=self._copy_rows(rows),
            metadata={"source": "memory", "row_count": len(rows), "read_only": True},
        )

    def load_future_rows(self, request: FutureRowsRequest) -> FutureRowsResult:
        ordered_rows = [
            row
            for row in self._ordered_rows()
            if self._matches_symbol(row, request.symbol)
            and self._matches_timeframe(row, request.timeframe)
            and str(row.get("date", "")) > request.snapshot_date
        ]
        marked_future_rows = [row for row in ordered_rows if self._is_future_row(row)]
        rows = marked_future_rows or ordered_rows

        rows = rows[: request.horizon_days]

        return FutureRowsResult(
            request=request,
            rows=self._copy_rows(rows),
            metadata={"source": "memory", "row_count": len(rows), "read_only": True},
        )

    def _ordered_rows(self) -> list[MarketDataRow]:
        return sorted(
            self._rows,
            key=lambda row: (
                str(row.get("symbol", "")),
                str(row.get("timeframe", "")),
                str(row.get("date", "")),
            ),
        )

    def _matches_symbol(self, row: MarketDataRow, symbol: str) -> bool:
        return str(row.get("symbol", "")) == symbol

    def _matches_timeframe(self, row: MarketDataRow, timeframe: str) -> bool:
        return str(row.get("timeframe", "")) == timeframe

    def _date_between(
        self,
        row: MarketDataRow,
        start_date: str | None,
        end_date: str | None,
    ) -> bool:
        date = str(row.get("date", ""))
        if start_date is not None and date < start_date:
            return False
        if end_date is not None and date > end_date:
            return False
        return True

    def _is_future_row(self, row: MarketDataRow) -> bool:
        return str(
            row.get("row_type")
            or row.get("source_role")
            or row.get("data_role")
            or ""
        ) == "future"

    def _copy_rows(self, rows: Iterable[MarketDataRow]) -> list[MarketDataRow]:
        return [dict(row) for row in rows]
