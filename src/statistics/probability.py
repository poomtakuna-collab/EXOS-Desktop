from __future__ import annotations

import sqlite3

from src.statistics.similarity import find_similar_patterns


EMPTY_PROBABILITY = {
    "expected_return_5d": 0.0,
    "expected_return_10d": 0.0,
    "expected_return_20d": 0.0,
    "probability_up_5pct_10d": 0.0,
    "probability_up_10pct_10d": 0.0,
    "probability_down_5pct_10d": 0.0,
    "expected_max_gain_10d": 0.0,
    "expected_drawdown_10d": 0.0,
    "confidence": 0.0,
    "evidence_count": 0,
    "best_pattern_id": None,
    "best_similarity": 0.0,
}


def calculate_probability_from_matches(
    matches: list[dict[str, object]],
) -> dict[str, object]:
    if not matches:
        return dict(EMPTY_PROBABILITY)

    weighted_matches = [
        (match, _match_weight(match))
        for match in matches
        if _match_weight(match) > 0
    ]
    if not weighted_matches:
        return dict(EMPTY_PROBABILITY)

    total_weight = sum(weight for _, weight in weighted_matches)
    evidence_count = sum(int(match.get("sample_count") or 0) for match, _ in weighted_matches)
    best_match = max(
        matches,
        key=lambda match: (
            _optional_float(match.get("similarity_score")) or 0.0,
            _optional_float(match.get("confidence")) or 0.0,
        ),
    )

    average_similarity = _weighted_average(
        weighted_matches,
        "similarity_score",
        total_weight,
    )
    average_pattern_confidence = _weighted_average(
        weighted_matches,
        "confidence",
        total_weight,
    )
    evidence_confidence = min(evidence_count / 100, 1.0) * 100

    confidence = round(
        average_similarity * 0.45
        + average_pattern_confidence * 0.35
        + evidence_confidence * 0.20,
        4,
    )

    return {
        "expected_return_5d": _weighted_average(
            weighted_matches,
            "average_5d_return",
            total_weight,
        ),
        "expected_return_10d": _weighted_average(
            weighted_matches,
            "average_10d_return",
            total_weight,
        ),
        "expected_return_20d": _weighted_average(
            weighted_matches,
            "average_20d_return",
            total_weight,
        ),
        "probability_up_5pct_10d": _weighted_average(
            weighted_matches,
            "hit_5pct_rate",
            total_weight,
        ),
        "probability_up_10pct_10d": _weighted_average(
            weighted_matches,
            "hit_10pct_rate",
            total_weight,
        ),
        "probability_down_5pct_10d": _weighted_down_probability(
            weighted_matches,
            total_weight,
        ),
        "expected_max_gain_10d": _weighted_average(
            weighted_matches,
            "average_max_gain",
            total_weight,
        ),
        "expected_drawdown_10d": _weighted_average(
            weighted_matches,
            "average_drawdown",
            total_weight,
        ),
        "confidence": confidence,
        "evidence_count": evidence_count,
        "best_pattern_id": best_match.get("pattern_id"),
        "best_similarity": _optional_float(best_match.get("similarity_score")) or 0.0,
    }


def predict_probability_for_snapshot(
    conn: sqlite3.Connection,
    snapshot: dict[str, object],
    top_n: int = 10,
) -> dict[str, object]:
    matches = find_similar_patterns(conn, snapshot, top_n=top_n)
    return {
        "matches": matches,
        "probability": calculate_probability_from_matches(matches),
    }


def _match_weight(match: dict[str, object]) -> float:
    similarity_score = _optional_float(match.get("similarity_score")) or 0.0
    pattern_confidence = _optional_float(match.get("confidence")) or 0.0
    return max(similarity_score, 0.0) * max(pattern_confidence, 0.0)


def _weighted_average(
    weighted_matches: list[tuple[dict[str, object], float]],
    key: str,
    total_weight: float,
) -> float:
    if total_weight <= 0:
        return 0.0

    total = 0.0
    for match, weight in weighted_matches:
        total += (_optional_float(match.get(key)) or 0.0) * weight
    return round(total / total_weight, 4)


def _weighted_down_probability(
    weighted_matches: list[tuple[dict[str, object], float]],
    total_weight: float,
) -> float:
    if total_weight <= 0:
        return 0.0

    total = 0.0
    for match, weight in weighted_matches:
        drawdown = _optional_float(match.get("average_drawdown")) or 0.0
        down_probability = min(max(abs(drawdown) / 5 * 100, 0.0), 100.0)
        total += down_probability * weight
    return round(total / total_weight, 4)


def _optional_float(value: object) -> float | None:
    if value is None:
        return None
    return float(value)
