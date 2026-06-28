from __future__ import annotations

import sqlite3
from typing import Any

from src.analysis import build_exos_snapshot
from src.data import MarketDataRow
from src.statistics.snapshot_store import insert_snapshot, prepare_snapshot_record


def collect_snapshot(
    conn: sqlite3.Connection,
    rows: list[MarketDataRow],
    symbol: str,
    timeframe: str,
) -> str | None:
    if not rows:
        return None

    snapshot = build_exos_snapshot(rows, symbol=symbol, timeframe=timeframe)
    snapshot = _with_latest_market_metadata(snapshot, rows[-1])
    snapshot_record = prepare_snapshot_record(
        snapshot,
        symbol=symbol,
        timeframe=timeframe,
    )
    return insert_snapshot(conn, snapshot_record)


def collect_snapshots_for_series(
    conn: sqlite3.Connection,
    rows: list[MarketDataRow],
    symbol: str,
    timeframe: str,
    window_size: int = 300,
) -> dict[str, object]:
    if window_size <= 0:
        raise ValueError("window_size must be greater than 0")

    inserted_count = 0
    skipped_count = 0
    first_date: str | None = None
    last_date: str | None = None

    for index in range(len(rows)):
        if index + 1 < window_size:
            skipped_count += 1
            continue

        window_rows = rows[index + 1 - window_size : index + 1]
        snapshot_id = collect_snapshot(conn, window_rows, symbol, timeframe)
        if snapshot_id is None:
            skipped_count += 1
            continue

        snapshot_date = _row_text(window_rows[-1], "date")
        first_date = first_date or snapshot_date
        last_date = snapshot_date
        inserted_count += 1

    return {
        "inserted_count": inserted_count,
        "skipped_count": skipped_count,
        "first_date": first_date,
        "last_date": last_date,
    }


def _with_latest_market_metadata(
    snapshot: dict[str, Any],
    latest_row: MarketDataRow,
) -> dict[str, Any]:
    enriched_snapshot = dict(snapshot)
    metadata = dict(enriched_snapshot.get("metadata") or {})
    metadata["date"] = _row_text(latest_row, "date")
    metadata["close"] = _row_float(latest_row, "close")
    enriched_snapshot["metadata"] = metadata
    return enriched_snapshot


def _row_text(row: MarketDataRow, key: str) -> str:
    value = row.get(key)
    if value is None:
        raise ValueError(f"market row {key} is required")

    text = str(value).strip()
    if not text:
        raise ValueError(f"market row {key} is required")
    return text


def _row_float(row: MarketDataRow, key: str) -> float:
    value = row.get(key)
    if value is None:
        raise ValueError(f"market row {key} is required")
    return float(value)
