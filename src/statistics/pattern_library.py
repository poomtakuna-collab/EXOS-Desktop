from __future__ import annotations

import sqlite3
import uuid
from datetime import UTC, datetime

from src.statistics.pattern_discovery import discover_patterns


PATTERN_COLUMNS = (
    "pattern_id",
    "trend_state",
    "squeeze_state",
    "market_structure_state",
    "rating",
    "recommendation",
    "sample_count",
    "average_5d_return",
    "average_10d_return",
    "average_20d_return",
    "hit_5pct_rate",
    "hit_10pct_rate",
    "average_max_gain",
    "average_drawdown",
    "dominant_label",
    "confidence",
    "created_at",
    "updated_at",
)


def rebuild_pattern_library(
    conn: sqlite3.Connection,
    min_samples: int = 30,
) -> dict[str, int]:
    patterns = discover_patterns(conn, min_samples=min_samples)
    timestamp = datetime.now(UTC).isoformat()
    records = [_pattern_to_record(pattern, timestamp) for pattern in patterns]

    conn.execute("DELETE FROM patterns")
    if records:
        conn.executemany(
            """
            INSERT INTO patterns (
                pattern_id,
                trend_state,
                squeeze_state,
                market_structure_state,
                rating,
                recommendation,
                sample_count,
                average_5d_return,
                average_10d_return,
                average_20d_return,
                hit_5pct_rate,
                hit_10pct_rate,
                average_max_gain,
                average_drawdown,
                dominant_label,
                confidence,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [_record_values(record) for record in records],
        )

    return {
        "total_patterns": len(patterns),
        "inserted_patterns": len(records),
    }


def load_pattern_library(conn: sqlite3.Connection) -> list[dict[str, object]]:
    cursor = conn.execute(
        """
        SELECT
            pattern_id,
            trend_state,
            squeeze_state,
            market_structure_state,
            rating,
            recommendation,
            sample_count,
            average_5d_return,
            average_10d_return,
            average_20d_return,
            hit_5pct_rate,
            hit_10pct_rate,
            average_max_gain,
            average_drawdown,
            dominant_label,
            confidence,
            created_at,
            updated_at
        FROM patterns
        ORDER BY confidence DESC, average_10d_return DESC, sample_count DESC
        """
    )
    return [_pattern_row_to_dict(row) for row in cursor.fetchall()]


def get_pattern(
    conn: sqlite3.Connection,
    pattern_id: str,
) -> dict[str, object] | None:
    row = conn.execute(
        """
        SELECT
            pattern_id,
            trend_state,
            squeeze_state,
            market_structure_state,
            rating,
            recommendation,
            sample_count,
            average_5d_return,
            average_10d_return,
            average_20d_return,
            hit_5pct_rate,
            hit_10pct_rate,
            average_max_gain,
            average_drawdown,
            dominant_label,
            confidence,
            created_at,
            updated_at
        FROM patterns
        WHERE pattern_id = ?
        LIMIT 1
        """,
        (pattern_id,),
    ).fetchone()
    return _pattern_row_to_dict(row) if row else None


def _pattern_to_record(
    pattern: dict[str, object],
    timestamp: str,
) -> dict[str, object]:
    return {
        "pattern_id": _pattern_id(pattern),
        "trend_state": pattern.get("trend_state"),
        "squeeze_state": pattern.get("squeeze_state"),
        "market_structure_state": pattern.get("market_structure_state"),
        "rating": pattern.get("rating"),
        "recommendation": pattern.get("recommendation"),
        "sample_count": int(pattern.get("sample_count") or 0),
        "average_5d_return": pattern.get("average_5d_return"),
        "average_10d_return": pattern.get("average_10d_return"),
        "average_20d_return": pattern.get("average_20d_return"),
        "hit_5pct_rate": pattern.get("hit_5pct_rate"),
        "hit_10pct_rate": pattern.get("hit_10pct_rate"),
        "average_max_gain": pattern.get("average_max_gain"),
        "average_drawdown": pattern.get("average_drawdown"),
        "dominant_label": pattern.get("dominant_label"),
        "confidence": pattern.get("confidence"),
        "created_at": timestamp,
        "updated_at": timestamp,
    }


def _pattern_id(pattern: dict[str, object]) -> str:
    parts = [
        pattern.get("trend_state"),
        pattern.get("squeeze_state"),
        pattern.get("market_structure_state"),
        pattern.get("rating"),
        pattern.get("recommendation"),
    ]
    key = "|".join("" if part is None else str(part) for part in parts)
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f"exos:pattern:{key}"))


def _record_values(record: dict[str, object]) -> tuple[object, ...]:
    return tuple(record.get(column) for column in PATTERN_COLUMNS)


def _pattern_row_to_dict(row: sqlite3.Row | tuple[object, ...]) -> dict[str, object]:
    values = tuple(row)
    return {
        "pattern_id": values[0],
        "trend_state": values[1],
        "squeeze_state": values[2],
        "market_structure_state": values[3],
        "rating": values[4],
        "recommendation": values[5],
        "sample_count": int(values[6]),
        "average_5d_return": _optional_float(values[7]),
        "average_10d_return": _optional_float(values[8]),
        "average_20d_return": _optional_float(values[9]),
        "hit_5pct_rate": _optional_float(values[10]),
        "hit_10pct_rate": _optional_float(values[11]),
        "average_max_gain": _optional_float(values[12]),
        "average_drawdown": _optional_float(values[13]),
        "dominant_label": values[14],
        "confidence": _optional_float(values[15]),
        "created_at": values[16],
        "updated_at": values[17],
    }


def _optional_float(value: object) -> float | None:
    if value is None:
        return None
    return float(value)
