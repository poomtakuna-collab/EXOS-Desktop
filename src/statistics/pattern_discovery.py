from __future__ import annotations

import re
import sqlite3


FACTOR_COLUMNS = (
    "trend_state",
    "squeeze_state",
    "market_structure_state",
    "rating",
    "recommendation",
)


def discover_patterns(
    conn: sqlite3.Connection,
    min_samples: int = 30,
) -> list[dict[str, object]]:
    if min_samples <= 0:
        raise ValueError("min_samples must be greater than 0")

    cursor = conn.execute(_PATTERN_QUERY, (min_samples,))
    return [_pattern_row_to_dict(row) for row in cursor.fetchall()]


def discover_best_patterns(
    conn: sqlite3.Connection,
    min_samples: int = 50,
    minimum_average_10d_return: float = 5.0,
    minimum_hit_5pct_rate: float = 60.0,
) -> list[dict[str, object]]:
    patterns = discover_patterns(conn, min_samples=min_samples)
    best_patterns = [
        pattern
        for pattern in patterns
        if float(pattern.get("average_10d_return") or 0.0)
        > minimum_average_10d_return
        and float(pattern.get("hit_5pct_rate") or 0.0) > minimum_hit_5pct_rate
    ]
    return sorted(
        best_patterns,
        key=lambda pattern: (
            float(pattern.get("confidence") or 0.0),
            float(pattern.get("average_10d_return") or 0.0),
            int(pattern.get("sample_count") or 0),
        ),
        reverse=True,
    )


def discover_strong_bull_patterns(
    conn: sqlite3.Connection,
    min_samples: int = 30,
) -> list[dict[str, object]]:
    patterns = discover_patterns(conn, min_samples=min_samples)
    strong_patterns = [
        pattern
        for pattern in patterns
        if pattern.get("dominant_label") == "Strong Bull"
        or float(pattern.get("average_10d_return") or 0.0) >= 10
    ]
    return sorted(
        strong_patterns,
        key=lambda pattern: (
            float(pattern.get("average_10d_return") or 0.0),
            float(pattern.get("confidence") or 0.0),
        ),
        reverse=True,
    )


def summarize_pattern_statistics(
    conn: sqlite3.Connection,
    min_samples: int = 1,
) -> dict[str, object]:
    if min_samples <= 0:
        raise ValueError("min_samples must be greater than 0")

    row = conn.execute(_PATTERN_SUMMARY_QUERY, (min_samples,)).fetchone()
    if row is None or row[0] is None:
        return {
            "total_patterns": 0,
            "largest_pattern": 0,
            "average_pattern_size": 0.0,
            "best_pattern_return": None,
            "best_hit_rate": None,
        }

    return {
        "total_patterns": int(row[0]),
        "largest_pattern": int(row[1] or 0),
        "average_pattern_size": _optional_float(row[2]) or 0.0,
        "best_pattern_return": _optional_float(row[3]),
        "best_hit_rate": _optional_float(row[4]),
    }


def summarize_factor_distribution(
    conn: sqlite3.Connection,
    outcome_filter: str | dict[str, object] | None = None,
) -> dict[str, list[dict[str, object]]]:
    where_clause, params = _outcome_filter_clause(outcome_filter)
    summary: dict[str, list[dict[str, object]]] = {}

    for factor in FACTOR_COLUMNS:
        cursor = conn.execute(
            f"""
            SELECT
                s.{factor} AS value,
                COUNT(*) AS count
            FROM snapshots s
            INNER JOIN outcomes o ON o.snapshot_id = s.snapshot_id
            {where_clause}
            GROUP BY s.{factor}
            ORDER BY count DESC, value ASC
            """,
            params,
        )
        summary[factor] = [
            {
                "value": row[0],
                "count": int(row[1]),
            }
            for row in cursor.fetchall()
        ]

    return summary


def _pattern_row_to_dict(row: sqlite3.Row | tuple[object, ...]) -> dict[str, object]:
    values = tuple(row)
    sample_count = int(values[5])
    return {
        "trend_state": values[0],
        "squeeze_state": values[1],
        "market_structure_state": values[2],
        "rating": values[3],
        "recommendation": values[4],
        "sample_count": sample_count,
        "average_5d_return": _optional_float(values[6]),
        "average_10d_return": _optional_float(values[7]),
        "average_20d_return": _optional_float(values[8]),
        "hit_5pct_rate": _optional_float(values[9]),
        "hit_10pct_rate": _optional_float(values[10]),
        "average_max_gain": _optional_float(values[11]),
        "average_drawdown": _optional_float(values[12]),
        "dominant_label": values[13],
        "confidence": _confidence_from_sample_count(sample_count),
    }


def _confidence_from_sample_count(sample_count: int) -> float:
    return round(min(sample_count, 100), 2)


def _optional_float(value: object) -> float | None:
    if value is None:
        return None
    return float(value)


def _outcome_filter_clause(
    outcome_filter: str | dict[str, object] | None,
) -> tuple[str, tuple[object, ...]]:
    if outcome_filter is None:
        return "", ()

    if isinstance(outcome_filter, dict):
        return _dict_filter_clause(outcome_filter)

    match = re.fullmatch(r"\s*label_10d\s*=\s*['\"]([^'\"]+)['\"]\s*", outcome_filter)
    if not match:
        raise ValueError("only label_10d='value' outcome filters are supported")

    return "WHERE o.label_10d = ?", (match.group(1),)


def _dict_filter_clause(outcome_filter: dict[str, object]) -> tuple[str, tuple[object, ...]]:
    if not outcome_filter:
        return "", ()

    if set(outcome_filter) != {"label_10d"}:
        raise ValueError("only label_10d outcome filters are supported")

    return "WHERE o.label_10d = ?", (outcome_filter["label_10d"],)


_PATTERN_QUERY = """
WITH joined AS (
    SELECT
        s.trend_state,
        s.squeeze_state,
        s.market_structure_state,
        s.rating,
        s.recommendation,
        o.forward_5d_return,
        o.forward_10d_return,
        o.forward_20d_return,
        o.max_gain_10d,
        o.max_drawdown_10d,
        o.hit_5pct_10d,
        o.hit_10pct_10d,
        o.label_10d
    FROM snapshots s
    INNER JOIN outcomes o ON o.snapshot_id = s.snapshot_id
),
grouped AS (
    SELECT
        trend_state,
        squeeze_state,
        market_structure_state,
        rating,
        recommendation,
        COUNT(*) AS sample_count,
        ROUND(AVG(forward_5d_return), 4) AS average_5d_return,
        ROUND(AVG(forward_10d_return), 4) AS average_10d_return,
        ROUND(AVG(forward_20d_return), 4) AS average_20d_return,
        ROUND(AVG(hit_5pct_10d) * 100, 4) AS hit_5pct_rate,
        ROUND(AVG(hit_10pct_10d) * 100, 4) AS hit_10pct_rate,
        ROUND(AVG(max_gain_10d), 4) AS average_max_gain,
        ROUND(AVG(max_drawdown_10d), 4) AS average_drawdown
    FROM joined
    GROUP BY
        trend_state,
        squeeze_state,
        market_structure_state,
        rating,
        recommendation
    HAVING COUNT(*) >= ?
),
label_counts AS (
    SELECT
        trend_state,
        squeeze_state,
        market_structure_state,
        rating,
        recommendation,
        label_10d,
        COUNT(*) AS label_count,
        ROW_NUMBER() OVER (
            PARTITION BY
                trend_state,
                squeeze_state,
                market_structure_state,
                rating,
                recommendation
            ORDER BY COUNT(*) DESC, label_10d ASC
        ) AS label_rank
    FROM joined
    GROUP BY
        trend_state,
        squeeze_state,
        market_structure_state,
        rating,
        recommendation,
        label_10d
),
dominant AS (
    SELECT
        trend_state,
        squeeze_state,
        market_structure_state,
        rating,
        recommendation,
        label_10d AS dominant_label
    FROM label_counts
    WHERE label_rank = 1
)
SELECT
    g.trend_state,
    g.squeeze_state,
    g.market_structure_state,
    g.rating,
    g.recommendation,
    g.sample_count,
    g.average_5d_return,
    g.average_10d_return,
    g.average_20d_return,
    g.hit_5pct_rate,
    g.hit_10pct_rate,
    g.average_max_gain,
    g.average_drawdown,
    d.dominant_label
FROM grouped g
INNER JOIN dominant d
    ON g.trend_state IS d.trend_state
    AND g.squeeze_state IS d.squeeze_state
    AND g.market_structure_state IS d.market_structure_state
    AND g.rating IS d.rating
    AND g.recommendation IS d.recommendation
ORDER BY g.average_10d_return DESC, g.sample_count DESC
"""

_PATTERN_SUMMARY_QUERY = """
WITH grouped AS (
    SELECT
        COUNT(*) AS sample_count,
        AVG(o.forward_10d_return) AS average_10d_return,
        AVG(o.hit_5pct_10d) * 100 AS hit_5pct_rate
    FROM snapshots s
    INNER JOIN outcomes o ON o.snapshot_id = s.snapshot_id
    GROUP BY
        s.trend_state,
        s.squeeze_state,
        s.market_structure_state,
        s.rating,
        s.recommendation
    HAVING COUNT(*) >= ?
)
SELECT
    COUNT(*) AS total_patterns,
    MAX(sample_count) AS largest_pattern,
    ROUND(AVG(sample_count), 4) AS average_pattern_size,
    ROUND(MAX(average_10d_return), 4) AS best_pattern_return,
    ROUND(MAX(hit_5pct_rate), 4) AS best_hit_rate
FROM grouped
"""
