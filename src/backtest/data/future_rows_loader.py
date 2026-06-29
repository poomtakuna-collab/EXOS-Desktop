from __future__ import annotations

import sqlite3
from typing import Any


class FutureRowsLoader:
    """Public interface for loading future OHLCV rows for Backtest replay."""

    def load_future_rows(
        self,
        symbol: str,
        timeframe: str,
        snapshot_date: str,
        horizon_days: int,
    ) -> list[dict[str, Any]]:
        """Load future OHLCV rows after `snapshot_date` for one replay window.

        Implementations must return deterministic rows for replay only. They must
        not fetch live data, calculate indicators, run Strategy, or mutate source
        records.
        """
        raise NotImplementedError("FutureRowsLoader.load_future_rows is not implemented yet")


class SQLiteFutureRowsLoader(FutureRowsLoader):
    """SQLite-backed reader for existing cached OHLCV rows."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        self.connection = connection

    def load_future_rows(
        self,
        symbol: str,
        timeframe: str,
        snapshot_date: str,
        horizon_days: int,
    ) -> list[dict[str, Any]]:
        if horizon_days < 0:
            raise ValueError("horizon_days must be greater than or equal to zero")
        if horizon_days == 0:
            return []
        if timeframe != "1D":
            raise ValueError("SQLiteFutureRowsLoader supports 1D timeframe only")

        self._ensure_ohlcv_daily_table()
        cursor = self.connection.execute(
            """
            SELECT symbol, date, open, high, low, close, volume, source
            FROM ohlcv_daily
            WHERE symbol = ?
              AND date > ?
            ORDER BY symbol ASC, date ASC
            LIMIT ?
            """,
            (symbol, snapshot_date, horizon_days),
        )
        return [
            {
                **_row_to_dict(cursor, row),
                "timeframe": timeframe,
            }
            for row in cursor.fetchall()
        ]

    def load_future_rows_for_snapshots(
        self,
        snapshots: list[dict[str, Any]],
        horizon_days: int,
    ) -> dict[str, list[dict[str, Any]]]:
        grouped_rows: dict[str, list[dict[str, Any]]] = {}
        for snapshot in sorted(snapshots, key=_snapshot_sort_key):
            snapshot_id = str(snapshot["snapshot_id"])
            grouped_rows[snapshot_id] = self.load_future_rows(
                symbol=str(snapshot["symbol"]),
                timeframe=str(snapshot["timeframe"]),
                snapshot_date=str(snapshot["date"]),
                horizon_days=horizon_days,
            )
        return grouped_rows

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
            raise RuntimeError("SQLite ohlcv_daily table is required for SQLiteFutureRowsLoader")


def _snapshot_sort_key(snapshot: dict[str, Any]) -> tuple[str, str, str, str]:
    return (
        str(snapshot["symbol"]),
        str(snapshot["timeframe"]),
        str(snapshot["date"]),
        str(snapshot["snapshot_id"]),
    )


def _row_to_dict(cursor: sqlite3.Cursor, row: sqlite3.Row | tuple[object, ...]) -> dict[str, Any]:
    columns = [description[0] for description in cursor.description]
    return dict(zip(columns, row, strict=True))
