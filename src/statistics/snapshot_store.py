from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import UTC, datetime
from typing import Any


SNAPSHOT_COLUMNS = (
    "snapshot_id",
    "symbol",
    "timeframe",
    "date",
    "close",
    "exos_score",
    "rating",
    "recommendation",
    "trend_score",
    "trend_state",
    "trend_slope_score",
    "squeeze_score",
    "squeeze_state",
    "market_structure_score",
    "market_structure_state",
    "snapshot_json",
    "created_at",
)


def prepare_snapshot_record(
    snapshot: dict[str, Any],
    symbol: str | None = None,
    timeframe: str | None = None,
) -> dict[str, object]:
    exos_snapshot = _extract_exos_snapshot(snapshot)
    metadata = _dict_value(exos_snapshot, "metadata")
    score = _dict_value(exos_snapshot, "score")
    trend = _dict_value(exos_snapshot, "trend")
    trend_slope = _dict_value(exos_snapshot, "trend_slope")
    squeeze = _dict_value(exos_snapshot, "squeeze")
    market_structure = _dict_value(exos_snapshot, "market_structure")

    resolved_symbol = _required_text(
        symbol or snapshot.get("symbol") or metadata.get("symbol"),
        "symbol",
    ).upper()
    resolved_timeframe = _required_text(
        timeframe or snapshot.get("timeframe") or metadata.get("timeframe"),
        "timeframe",
    )
    snapshot_date = _required_text(
        snapshot.get("latest_date")
        or snapshot.get("date")
        or metadata.get("latest_date")
        or metadata.get("date"),
        "date",
    )

    snapshot_json = json.dumps(exos_snapshot, sort_keys=True, default=str)
    snapshot_id = str(
        uuid.uuid5(
            uuid.NAMESPACE_URL,
            f"exos:snapshot:{resolved_symbol}:{resolved_timeframe}:{snapshot_date}",
        )
    )

    return {
        "snapshot_id": snapshot_id,
        "symbol": resolved_symbol,
        "timeframe": resolved_timeframe,
        "date": snapshot_date,
        "close": _optional_float(
            _first_present(snapshot.get("close"), metadata.get("close"))
        ),
        "exos_score": _optional_float(score.get("overall_score")),
        "rating": _optional_text(score.get("rating")),
        "recommendation": _optional_text(score.get("recommendation")),
        "trend_score": _optional_float(trend.get("score")),
        "trend_state": _optional_text(trend.get("state")),
        "trend_slope_score": _optional_float(trend_slope.get("score")),
        "squeeze_score": _optional_float(squeeze.get("score")),
        "squeeze_state": _optional_text(squeeze.get("state")),
        "market_structure_score": _optional_float(market_structure.get("score")),
        "market_structure_state": _optional_text(market_structure.get("state")),
        "snapshot_json": snapshot_json,
        "created_at": datetime.now(UTC).isoformat(),
    }


def insert_snapshot(
    conn: sqlite3.Connection,
    snapshot_record: dict[str, object],
) -> str | None:
    values = [snapshot_record.get(column) for column in SNAPSHOT_COLUMNS]
    conn.execute(
        """
        INSERT INTO snapshots (
            snapshot_id,
            symbol,
            timeframe,
            date,
            close,
            exos_score,
            rating,
            recommendation,
            trend_score,
            trend_state,
            trend_slope_score,
            squeeze_score,
            squeeze_state,
            market_structure_score,
            market_structure_state,
            snapshot_json,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(symbol, timeframe, date) DO UPDATE SET
            close = excluded.close,
            exos_score = excluded.exos_score,
            rating = excluded.rating,
            recommendation = excluded.recommendation,
            trend_score = excluded.trend_score,
            trend_state = excluded.trend_state,
            trend_slope_score = excluded.trend_slope_score,
            squeeze_score = excluded.squeeze_score,
            squeeze_state = excluded.squeeze_state,
            market_structure_score = excluded.market_structure_score,
            market_structure_state = excluded.market_structure_state,
            snapshot_json = excluded.snapshot_json
        """,
        values,
    )

    row = conn.execute(
        """
        SELECT snapshot_id
        FROM snapshots
        WHERE symbol = ? AND timeframe = ? AND date = ?
        LIMIT 1
        """,
        (
            snapshot_record.get("symbol"),
            snapshot_record.get("timeframe"),
            snapshot_record.get("date"),
        ),
    ).fetchone()
    return str(row[0]) if row else None


def _extract_exos_snapshot(snapshot: dict[str, Any]) -> dict[str, Any]:
    nested_snapshot = snapshot.get("exos_snapshot")
    if isinstance(nested_snapshot, dict):
        return nested_snapshot
    return snapshot


def _dict_value(mapping: dict[str, Any], key: str) -> dict[str, Any]:
    value = mapping.get(key)
    return value if isinstance(value, dict) else {}


def _required_text(value: object, field_name: str) -> str:
    if value is None:
        raise ValueError(f"snapshot {field_name} is required")

    text = str(value).strip()
    if not text:
        raise ValueError(f"snapshot {field_name} is required")
    return text


def _optional_text(value: object) -> str | None:
    if value is None:
        return None

    text = str(value).strip()
    return text or None


def _optional_float(value: object) -> float | None:
    if value is None:
        return None
    return float(value)


def _first_present(*values: object) -> object:
    for value in values:
        if value is not None:
            return value
    return None
