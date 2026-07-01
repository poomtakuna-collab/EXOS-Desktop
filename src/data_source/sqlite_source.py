from __future__ import annotations

import sqlite3
from typing import Any

from src.backtest.data import SQLiteFutureRowsLoader
from src.data_source.contracts import (
    FutureRowsRequest,
    FutureRowsResult,
    MarketDataRequest,
    MarketDataResult,
    MarketDataRow,
)


class SQLiteDataSource:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self.connection = connection
        self._future_rows_loader = SQLiteFutureRowsLoader(connection)

    def load_ohlcv(self, request: MarketDataRequest) -> MarketDataResult:
        if request.timeframe != "1D":
            raise ValueError("SQLiteDataSource supports 1D timeframe only")
        if request.limit is not None and request.limit < 0:
            raise ValueError("MarketDataRequest.limit must be greater than or equal to zero")
        if request.limit == 0:
            return self._market_result(request, [])

        self._ensure_ohlcv_daily_table()
        role_filter = self._non_future_role_filter()
        where_clauses = ["symbol = ?"]
        parameters: list[object] = [request.symbol]

        if request.start_date is not None:
            where_clauses.append("date >= ?")
            parameters.append(request.start_date)
        if request.end_date is not None:
            where_clauses.append("date <= ?")
            parameters.append(request.end_date)
        if role_filter is not None:
            where_clauses.append(role_filter)

        if request.limit is not None:
            sql = """
            SELECT symbol, date, open, high, low, close, volume, source
            FROM (
                SELECT symbol, date, open, high, low, close, volume, source
                FROM ohlcv_daily
                WHERE """ + "\n                  AND ".join(where_clauses) + """
                ORDER BY symbol DESC, date DESC
                LIMIT ?
            ) latest_ohlcv
            ORDER BY symbol ASC, date ASC
            """
            parameters.append(request.limit)
        else:
            sql = """
            SELECT symbol, date, open, high, low, close, volume, source
            FROM ohlcv_daily
            WHERE """ + "\n              AND ".join(where_clauses)
            sql += "\n            ORDER BY symbol ASC, date ASC"

        cursor = self.connection.execute(sql, tuple(parameters))
        rows = [_with_timeframe(_row_to_dict(cursor, row), request.timeframe) for row in cursor.fetchall()]
        return self._market_result(request, rows)

    def load_future_rows(self, request: FutureRowsRequest) -> FutureRowsResult:
        if self._has_future_role_column():
            rows = self._load_marked_future_rows(request)
        else:
            rows = self._future_rows_loader.load_future_rows(
                symbol=request.symbol,
                timeframe=request.timeframe,
                snapshot_date=request.snapshot_date,
                horizon_days=request.horizon_days,
            )
        return FutureRowsResult(
            request=request,
            rows=[dict(row) for row in rows],
            metadata={"source": "sqlite", "row_count": len(rows), "read_only": True},
        )

    def _load_marked_future_rows(
        self,
        request: FutureRowsRequest,
    ) -> list[MarketDataRow]:
        if request.timeframe != "1D":
            raise ValueError("SQLiteDataSource supports 1D timeframe only")
        if request.horizon_days < 0:
            raise ValueError("horizon_days must be greater than or equal to zero")
        if request.horizon_days == 0:
            return []

        self._ensure_ohlcv_daily_table()
        role_column = self._future_role_column()
        if role_column is None:
            return []

        cursor = self.connection.execute(
            f"""
            SELECT symbol, date, open, high, low, close, volume, source
            FROM ohlcv_daily
            WHERE symbol = ?
              AND date > ?
              AND {role_column} = 'future'
            ORDER BY symbol ASC, date ASC
            LIMIT ?
            """,
            (request.symbol, request.snapshot_date, request.horizon_days),
        )
        return [
            _with_timeframe(_row_to_dict(cursor, row), request.timeframe)
            for row in cursor.fetchall()
        ]

    def _market_result(
        self,
        request: MarketDataRequest,
        rows: list[MarketDataRow],
    ) -> MarketDataResult:
        return MarketDataResult(
            request=request,
            rows=[dict(row) for row in rows],
            metadata={"source": "sqlite", "row_count": len(rows), "read_only": True},
        )

    def _ensure_ohlcv_daily_table(self) -> None:
        row = self.connection.execute(
            """
            SELECT 1
            FROM sqlite_master
            WHERE type = 'table'
              AND name = 'ohlcv_daily'
            """
        ).fetchone()
        if row is None:
            raise RuntimeError("SQLite ohlcv_daily table is required for SQLiteDataSource")

    def _non_future_role_filter(self) -> str | None:
        role_column = self._future_role_column()
        if role_column is None:
            return None
        return f"({role_column} IS NULL OR {role_column} != 'future')"

    def _has_future_role_column(self) -> bool:
        return self._future_role_column() is not None

    def _future_role_column(self) -> str | None:
        columns = self._ohlcv_daily_columns()
        for column in ("row_type", "source_role", "data_role"):
            if column in columns:
                return column
        return None

    def _ohlcv_daily_columns(self) -> set[str]:
        self._ensure_ohlcv_daily_table()
        cursor = self.connection.execute("PRAGMA table_info(ohlcv_daily)")
        return {str(row[1]) for row in cursor.fetchall()}


def _row_to_dict(cursor: sqlite3.Cursor, row: sqlite3.Row | tuple[object, ...]) -> dict[str, Any]:
    columns = [description[0] for description in cursor.description]
    return dict(zip(columns, row, strict=True))


def _with_timeframe(row: dict[str, Any], timeframe: str) -> MarketDataRow:
    return {**row, "timeframe": timeframe}
