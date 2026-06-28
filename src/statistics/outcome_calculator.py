from __future__ import annotations

import sqlite3
import uuid
from datetime import UTC, datetime
from typing import Any

from src.data import MarketDataRow


OUTCOME_COLUMNS = (
    "outcome_id",
    "snapshot_id",
    "forward_5d_return",
    "forward_10d_return",
    "forward_20d_return",
    "max_gain_10d",
    "max_drawdown_10d",
    "hit_5pct_10d",
    "hit_10pct_10d",
    "label_10d",
    "calculated_at",
)


def calculate_outcome_for_snapshot(
    snapshot_record: dict[str, Any],
    future_rows: list[MarketDataRow],
) -> dict[str, object]:
    if len(future_rows) < 20:
        raise ValueError("at least 20 future rows are required")

    snapshot_id = _required_text(snapshot_record.get("snapshot_id"), "snapshot_id")
    snapshot_close = _required_float(snapshot_record.get("close"), "close")
    first_10_rows = future_rows[:10]

    forward_5d_return = _return_percent(
        snapshot_close,
        _row_float(future_rows[4], "close"),
    )
    forward_10d_return = _return_percent(
        snapshot_close,
        _row_float(future_rows[9], "close"),
    )
    forward_20d_return = _return_percent(
        snapshot_close,
        _row_float(future_rows[19], "close"),
    )
    max_gain_10d = _return_percent(
        snapshot_close,
        max(_row_float(row, "high") for row in first_10_rows),
    )
    max_drawdown_10d = _return_percent(
        snapshot_close,
        min(_row_float(row, "low") for row in first_10_rows),
    )

    return {
        "outcome_id": _outcome_id(snapshot_id),
        "snapshot_id": snapshot_id,
        "forward_5d_return": forward_5d_return,
        "forward_10d_return": forward_10d_return,
        "forward_20d_return": forward_20d_return,
        "max_gain_10d": max_gain_10d,
        "max_drawdown_10d": max_drawdown_10d,
        "hit_5pct_10d": int(max_gain_10d >= 5),
        "hit_10pct_10d": int(max_gain_10d >= 10),
        "label_10d": label_10d(forward_10d_return),
        "calculated_at": datetime.now(UTC).isoformat(),
    }


def label_10d(forward_10d_return: float) -> str:
    if forward_10d_return >= 10:
        return "Strong Bull"
    if forward_10d_return <= -10:
        return "Crash"
    if forward_10d_return >= 5:
        return "Bull"
    if forward_10d_return <= -5:
        return "Bear"
    return "Sideway"


def insert_or_update_outcome(
    conn: sqlite3.Connection,
    outcome_record: dict[str, object],
) -> str | None:
    values = [outcome_record.get(column) for column in OUTCOME_COLUMNS]
    conn.execute(
        """
        INSERT INTO outcomes (
            outcome_id,
            snapshot_id,
            forward_5d_return,
            forward_10d_return,
            forward_20d_return,
            max_gain_10d,
            max_drawdown_10d,
            hit_5pct_10d,
            hit_10pct_10d,
            label_10d,
            calculated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(outcome_id) DO UPDATE SET
            snapshot_id = excluded.snapshot_id,
            forward_5d_return = excluded.forward_5d_return,
            forward_10d_return = excluded.forward_10d_return,
            forward_20d_return = excluded.forward_20d_return,
            max_gain_10d = excluded.max_gain_10d,
            max_drawdown_10d = excluded.max_drawdown_10d,
            hit_5pct_10d = excluded.hit_5pct_10d,
            hit_10pct_10d = excluded.hit_10pct_10d,
            label_10d = excluded.label_10d,
            calculated_at = excluded.calculated_at
        """,
        values,
    )

    row = conn.execute(
        """
        SELECT outcome_id
        FROM outcomes
        WHERE snapshot_id = ?
        LIMIT 1
        """,
        (outcome_record.get("snapshot_id"),),
    ).fetchone()
    return str(row[0]) if row else None


def calculate_outcomes_for_series(
    conn: sqlite3.Connection,
    rows: list[MarketDataRow],
    symbol: str,
    timeframe: str,
) -> dict[str, object]:
    row_index_by_date = {_row_text(row, "date"): index for index, row in enumerate(rows)}
    normalized_symbol = symbol.strip().upper()

    calculated_count = 0
    skipped_count = 0
    first_date: str | None = None
    last_date: str | None = None

    cursor = conn.execute(
        """
        SELECT snapshot_id, symbol, timeframe, date, close
        FROM snapshots
        WHERE symbol = ? AND timeframe = ?
        ORDER BY date
        """,
        (normalized_symbol, timeframe),
    )

    for snapshot_row in cursor:
        snapshot_record = _snapshot_row_to_record(snapshot_row)
        snapshot_date = _required_text(snapshot_record.get("date"), "date")
        row_index = row_index_by_date.get(snapshot_date)
        if row_index is None:
            skipped_count += 1
            continue

        future_rows = rows[row_index + 1 : row_index + 21]
        if len(future_rows) < 20:
            skipped_count += 1
            continue

        outcome_record = calculate_outcome_for_snapshot(snapshot_record, future_rows)
        insert_or_update_outcome(conn, outcome_record)
        calculated_count += 1
        first_date = first_date or snapshot_date
        last_date = snapshot_date

    return {
        "calculated_count": calculated_count,
        "skipped_count": skipped_count,
        "first_date": first_date,
        "last_date": last_date,
    }


def _snapshot_row_to_record(row: sqlite3.Row | tuple[object, ...]) -> dict[str, object]:
    if isinstance(row, sqlite3.Row):
        return {
            "snapshot_id": row["snapshot_id"],
            "symbol": row["symbol"],
            "timeframe": row["timeframe"],
            "date": row["date"],
            "close": row["close"],
        }

    return {
        "snapshot_id": row[0],
        "symbol": row[1],
        "timeframe": row[2],
        "date": row[3],
        "close": row[4],
    }


def _outcome_id(snapshot_id: str) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f"exos:outcome:{snapshot_id}"))


def _return_percent(start_price: float, end_price: float) -> float:
    if start_price == 0:
        raise ValueError("snapshot close must not be zero")
    return round(((end_price - start_price) / start_price) * 100, 4)


def _required_text(value: object, field_name: str) -> str:
    if value is None:
        raise ValueError(f"snapshot {field_name} is required")

    text = str(value).strip()
    if not text:
        raise ValueError(f"snapshot {field_name} is required")
    return text


def _required_float(value: object, field_name: str) -> float:
    if value is None:
        raise ValueError(f"snapshot {field_name} is required")
    return float(value)


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
