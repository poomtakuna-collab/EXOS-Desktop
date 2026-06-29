from __future__ import annotations

from dataclasses import dataclass
import sqlite3
from typing import Any


@dataclass(frozen=True)
class SnapshotQuery:
    symbol: str | None = None
    symbols: tuple[str, ...] = ()
    timeframe: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    limit: int | None = None
    minimum_exos_score: float | None = None
    trend_state: str | None = None
    squeeze_state: str | None = None
    market_structure_state: str | None = None


class SnapshotLoader:
    """Public interface for loading stored snapshot records for Backtest."""

    def load_snapshot(self, snapshot_id: str) -> dict[str, Any] | None:
        """Load one stored snapshot by its stable `snapshot_id`.

        Implementations must return the stored snapshot record without recalculating
        indicators, mutating source data, or opening live market-data paths.
        """
        raise NotImplementedError("SnapshotLoader.load_snapshot is not implemented yet")

    def load_snapshots(self, query: SnapshotQuery) -> list[dict[str, Any]]:
        """Load stored snapshots matching `query` in deterministic order.

        Implementations must preserve `snapshot_id` and return records ordered by
        the Backtest Data Layer contract without executing strategy logic.
        """
        raise NotImplementedError("SnapshotLoader.load_snapshots is not implemented yet")


class SQLiteSnapshotLoader(SnapshotLoader):
    """SQLite-backed reader for existing Backtest snapshot records."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        self.connection = connection

    def load_snapshot(self, snapshot_id: str) -> dict[str, Any] | None:
        self._ensure_snapshots_table()
        cursor = self.connection.execute(
            """
            SELECT *
            FROM snapshots
            WHERE snapshot_id = ?
            """,
            (snapshot_id,),
        )
        row = cursor.fetchone()
        if row is None:
            return None
        return _row_to_dict(cursor, row)

    def load_snapshots(self, query: SnapshotQuery) -> list[dict[str, Any]]:
        self._ensure_snapshots_table()
        if query.limit is not None and query.limit < 0:
            raise ValueError("SnapshotQuery.limit must be greater than or equal to zero")
        if query.limit == 0:
            return []

        where_clauses: list[str] = []
        parameters: list[object] = []

        symbols = _query_symbols(query)
        if symbols:
            placeholders = ", ".join("?" for _ in symbols)
            where_clauses.append(f"symbol IN ({placeholders})")
            parameters.extend(symbols)
        if query.timeframe is not None:
            where_clauses.append("timeframe = ?")
            parameters.append(query.timeframe)
        if query.start_date is not None:
            where_clauses.append("date >= ?")
            parameters.append(query.start_date)
        if query.end_date is not None:
            where_clauses.append("date <= ?")
            parameters.append(query.end_date)
        if query.minimum_exos_score is not None:
            where_clauses.append("exos_score >= ?")
            parameters.append(query.minimum_exos_score)
        if query.trend_state is not None:
            where_clauses.append("trend_state = ?")
            parameters.append(query.trend_state)
        if query.squeeze_state is not None:
            where_clauses.append("squeeze_state = ?")
            parameters.append(query.squeeze_state)
        if query.market_structure_state is not None:
            where_clauses.append("market_structure_state = ?")
            parameters.append(query.market_structure_state)

        sql = """
            SELECT *
            FROM snapshots
        """
        if where_clauses:
            sql += "\nWHERE " + "\n  AND ".join(where_clauses)
        sql += "\nORDER BY symbol ASC, timeframe ASC, date ASC, snapshot_id ASC"
        if query.limit is not None:
            sql += "\nLIMIT ?"
            parameters.append(query.limit)

        cursor = self.connection.execute(sql, tuple(parameters))
        return [_row_to_dict(cursor, row) for row in cursor.fetchall()]

    def _ensure_snapshots_table(self) -> None:
        row = self.connection.execute(
            """
            SELECT 1
            FROM sqlite_master
            WHERE type = 'table'
              AND name = 'snapshots'
            """
        ).fetchone()
        if row is None:
            raise RuntimeError("SQLite snapshots table is required for SQLiteSnapshotLoader")


def _query_symbols(query: SnapshotQuery) -> tuple[str, ...]:
    symbols = tuple(symbol for symbol in query.symbols if symbol)
    if query.symbol is None:
        return symbols
    if query.symbol in symbols:
        return symbols
    return (query.symbol, *symbols)


def _row_to_dict(cursor: sqlite3.Cursor, row: sqlite3.Row | tuple[object, ...]) -> dict[str, Any]:
    columns = [description[0] for description in cursor.description]
    return dict(zip(columns, row, strict=True))
