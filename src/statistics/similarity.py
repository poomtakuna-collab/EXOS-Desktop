from __future__ import annotations

import sqlite3
from typing import Any

from src.statistics.pattern_library import load_pattern_library


EXACT_MATCH_FIELDS = (
    ("trend_state", ("trend", "state")),
    ("squeeze_state", ("squeeze", "state")),
    ("market_structure_state", ("market_structure", "state")),
    ("rating", ("score", "rating")),
    ("recommendation", ("score", "recommendation")),
)

NUMERIC_FIELDS = (
    ("overall_score", ("score", "overall_score")),
    ("trend_score", ("trend", "score")),
    ("trend_slope_score", ("trend_slope", "score")),
    ("squeeze_score", ("squeeze", "score")),
    ("market_structure_score", ("market_structure", "score")),
)


def calculate_similarity(
    snapshot: dict[str, Any],
    pattern: dict[str, Any],
) -> dict[str, object]:
    field_scores: list[float] = []
    matched_fields = 0

    for pattern_key, snapshot_path in EXACT_MATCH_FIELDS:
        snapshot_value = _nested_value(snapshot, snapshot_path)
        pattern_value = pattern.get(pattern_key)
        if snapshot_value is None or pattern_value is None:
            continue

        total_score = 100.0 if str(snapshot_value) == str(pattern_value) else 0.0
        field_scores.append(total_score)
        if total_score == 100.0:
            matched_fields += 1

    for pattern_key, snapshot_path in NUMERIC_FIELDS:
        snapshot_value = _optional_float(_nested_value(snapshot, snapshot_path))
        pattern_value = _optional_float(pattern.get(pattern_key))
        if snapshot_value is None or pattern_value is None:
            continue

        total_score = _numeric_similarity(snapshot_value, pattern_value)
        field_scores.append(total_score)
        if total_score >= 90.0:
            matched_fields += 1

    total_fields = len(field_scores)
    similarity_score = (
        round(sum(field_scores) / total_fields, 2) if total_fields else 0.0
    )

    return {
        "similarity_score": similarity_score,
        "matched_fields": matched_fields,
        "total_fields": total_fields,
    }


def find_similar_patterns(
    conn: sqlite3.Connection,
    snapshot: dict[str, Any],
    top_n: int = 10,
) -> list[dict[str, object]]:
    if top_n <= 0:
        return []

    results: list[dict[str, object]] = []
    for pattern in load_pattern_library(conn):
        similarity = calculate_similarity(snapshot, pattern)
        results.append(
            {
                "pattern_id": pattern.get("pattern_id"),
                "similarity_score": similarity["similarity_score"],
                "confidence": pattern.get("confidence"),
                "sample_count": pattern.get("sample_count"),
                "average_10d_return": pattern.get("average_10d_return"),
                "average_20d_return": pattern.get("average_20d_return"),
                "dominant_label": pattern.get("dominant_label"),
            }
        )

    return sorted(
        results,
        key=lambda result: (
            float(result.get("similarity_score") or 0.0),
            float(result.get("confidence") or 0.0),
            int(result.get("sample_count") or 0),
        ),
        reverse=True,
    )[:top_n]


def find_best_match(
    conn: sqlite3.Connection,
    snapshot: dict[str, Any],
) -> dict[str, object] | None:
    matches = find_similar_patterns(conn, snapshot, top_n=1)
    return matches[0] if matches else None


def _nested_value(snapshot: dict[str, Any], path: tuple[str, str]) -> object:
    section = snapshot.get(path[0])
    if not isinstance(section, dict):
        return None
    return section.get(path[1])


def _optional_float(value: object) -> float | None:
    if value is None:
        return None
    return float(value)


def _numeric_similarity(left: float, right: float) -> float:
    return round(max(0.0, 100.0 - abs(left - right)), 2)
