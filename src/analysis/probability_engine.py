from __future__ import annotations

from typing import Any


EMPTY_PROBABILITY_SUMMARY: dict[str, object] = {
    "probability_positive": 0.0,
    "probability_negative": 0.0,
    "probability_neutral": 0.0,
    "expected_return_5d": 0.0,
    "expected_return_10d": 0.0,
    "expected_return_20d": 0.0,
    "expected_max_gain_10d": 0.0,
    "expected_drawdown_10d": 0.0,
    "confidence": 0.0,
    "evidence_count": 0,
    "best_pattern_id": None,
    "best_similarity": 0.0,
}

POSITIVE_OUTCOMES = frozenset(
    {
        "bull",
        "gain",
        "positive",
        "profit",
        "strong bull",
        "up",
        "win",
        "winner",
    }
)
NEGATIVE_OUTCOMES = frozenset(
    {
        "bear",
        "crash",
        "down",
        "loss",
        "loser",
        "negative",
    }
)
NEUTRAL_OUTCOMES = frozenset(
    {
        "breakeven",
        "break even",
        "flat",
        "neutral",
        "sideway",
        "sideways",
    }
)


def calculate_probability_summary(
    resolver_output: dict[str, Any],
) -> dict[str, object]:
    matches = resolver_output.get("matches")
    if not isinstance(matches, list) or not matches:
        return dict(EMPTY_PROBABILITY_SUMMARY)

    weighted_matches = [
        (match, outcome, _match_weight(match))
        for match in matches
        if isinstance(match, dict)
        for outcome in [_outcome_bucket(match.get("outcome"))]
        if outcome is not None and _match_weight(match) > 0
    ]
    if not weighted_matches:
        return dict(EMPTY_PROBABILITY_SUMMARY)

    total_weight = sum(weight for _, _, weight in weighted_matches)
    evidence_count = sum(_sample_count(match) for match, _, _ in weighted_matches)
    best_match = max(
        (match for match, _, _ in weighted_matches),
        key=lambda match: (
            _similarity(match),
            str(match.get("pattern_id") or ""),
        ),
    )
    average_similarity = _weighted_similarity(weighted_matches, total_weight)
    evidence_factor = min(evidence_count / 100.0, 1.0)

    return {
        "probability_positive": _bucket_probability(
            weighted_matches,
            "positive",
            total_weight,
        ),
        "probability_negative": _bucket_probability(
            weighted_matches,
            "negative",
            total_weight,
        ),
        "probability_neutral": _bucket_probability(
            weighted_matches,
            "neutral",
            total_weight,
        ),
        "expected_return_5d": _weighted_pattern_average(
            weighted_matches,
            "average_5d_return",
            total_weight,
        ),
        "expected_return_10d": _weighted_pattern_average(
            weighted_matches,
            "average_10d_return",
            total_weight,
        ),
        "expected_return_20d": _weighted_pattern_average(
            weighted_matches,
            "average_20d_return",
            total_weight,
        ),
        "expected_max_gain_10d": _weighted_pattern_average(
            weighted_matches,
            "average_max_gain",
            total_weight,
        ),
        "expected_drawdown_10d": _weighted_pattern_average(
            weighted_matches,
            "average_drawdown",
            total_weight,
        ),
        "confidence": round(average_similarity * evidence_factor, 4),
        "evidence_count": evidence_count,
        "best_pattern_id": best_match.get("pattern_id"),
        "best_similarity": _similarity(best_match),
    }


def _bucket_probability(
    weighted_matches: list[tuple[dict[str, Any], str, float]],
    bucket: str,
    total_weight: float,
) -> float:
    if total_weight <= 0:
        return 0.0
    bucket_weight = sum(
        weight
        for _, outcome, weight in weighted_matches
        if outcome == bucket
    )
    return round(bucket_weight / total_weight * 100.0, 4)


def _weighted_pattern_average(
    weighted_matches: list[tuple[dict[str, Any], str, float]],
    key: str,
    total_weight: float,
) -> float:
    if total_weight <= 0:
        return 0.0

    total = 0.0
    for match, _, weight in weighted_matches:
        pattern = match.get("pattern")
        if not isinstance(pattern, dict):
            pattern = {}
        total += (_optional_float(pattern.get(key)) or 0.0) * weight
    return round(total / total_weight, 4)


def _weighted_similarity(
    weighted_matches: list[tuple[dict[str, Any], str, float]],
    total_weight: float,
) -> float:
    if total_weight <= 0:
        return 0.0
    total = sum(_similarity(match) * weight for match, _, weight in weighted_matches)
    return round(total / total_weight, 4)


def _match_weight(match: dict[str, Any]) -> float:
    return _similarity(match) * _sample_count(match)


def _similarity(match: dict[str, Any]) -> float:
    similarity = _optional_float(match.get("similarity")) or 0.0
    return max(0.0, min(100.0, similarity))


def _sample_count(match: dict[str, Any]) -> int:
    pattern = match.get("pattern")
    if not isinstance(pattern, dict):
        return 1

    value = _optional_float(pattern.get("sample_count"))
    if value is None or value <= 0:
        return 1
    return int(value)


def _outcome_bucket(outcome: object) -> str | None:
    if outcome is None:
        return None

    normalized = str(outcome).strip().lower()
    if normalized in POSITIVE_OUTCOMES:
        return "positive"
    if normalized in NEGATIVE_OUTCOMES:
        return "negative"
    if normalized in NEUTRAL_OUTCOMES:
        return "neutral"
    return None


def _optional_float(value: object) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
