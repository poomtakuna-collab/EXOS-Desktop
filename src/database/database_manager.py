from __future__ import annotations

import sqlite3
from datetime import UTC, datetime
from pathlib import Path

from src.data.data_provider import MarketDataRow


class DatabaseManager:
    def __init__(self, database_path: Path | None = None) -> None:
        self._database_path = database_path or Path("database") / "exos.db"
        self._ensure_database()

    def get_ohlcv_daily(self, symbol: str, limit: int = 300) -> list[MarketDataRow]:
        normalized_symbol = symbol.strip().upper()
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT date, open, high, low, close, volume, source
                FROM ohlcv_daily
                WHERE symbol = ?
                ORDER BY date DESC
                LIMIT ?
                """,
                (normalized_symbol, limit),
            ).fetchall()

        return [self._row_to_market_data(row) for row in reversed(rows)]

    def upsert_ohlcv_daily(
        self, symbol: str, rows: list[MarketDataRow], source: str
    ) -> None:
        if not rows:
            return

        normalized_symbol = symbol.strip().upper()
        timestamp = datetime.now(UTC).isoformat()
        records = [
            (
                normalized_symbol,
                str(row["date"]),
                float(row["open"]),
                float(row["high"]),
                float(row["low"]),
                float(row["close"]),
                int(row["volume"]),
                source,
                timestamp,
                timestamp,
            )
            for row in rows
        ]

        with self._connect() as connection:
            connection.executemany(
                """
                INSERT INTO ohlcv_daily (
                    symbol, date, open, high, low, close, volume, source, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(symbol, date) DO UPDATE SET
                    open = excluded.open,
                    high = excluded.high,
                    low = excluded.low,
                    close = excluded.close,
                    volume = excluded.volume,
                    source = excluded.source,
                    updated_at = excluded.updated_at
                """,
                records,
            )
            connection.commit()

    def _ensure_database(self) -> None:
        self._database_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS ohlcv_daily (
                    symbol TEXT NOT NULL,
                    date TEXT NOT NULL,
                    open REAL NOT NULL,
                    high REAL NOT NULL,
                    low REAL NOT NULL,
                    close REAL NOT NULL,
                    volume INTEGER NOT NULL,
                    source TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    UNIQUE(symbol, date)
                )
                """
            )
            connection.commit()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self._database_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _row_to_market_data(self, row: sqlite3.Row) -> MarketDataRow:
        return {
            "date": row["date"],
            "open": float(row["open"]),
            "high": float(row["high"]),
            "low": float(row["low"]),
            "close": float(row["close"]),
            "volume": int(row["volume"]),
            "source": row["source"],
        }
