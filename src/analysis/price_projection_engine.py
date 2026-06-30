from __future__ import annotations

from typing import Any


EMPTY_PRICE_PROJECTION: dict[str, object] = {
    "current_price": 0.0,
    "expected_price_5d": 0.0,
    "expected_price_10d": 0.0,
    "expected_price_20d": 0.0,
    "expected_return_5d": 0.0,
    "expected_return_10d": 0.0,
    "expected_return_20d": 0.0,
    "upside_range": None,
    "downside_range": None,
    "confidence": 0.0,
    "evidence_count": 0,
    "best_pattern_id": None,
    "best_similarity": 0.0,
}


def calculate_price_projection(
    current_price: float,
    matched_patterns: dict[str, Any] | list[dict[str, Any]],
) -> dict[str, object]:
    price = max(float(current_price), 0.0)
    matches = _coerce_matches(matched_patterns)
    weighted_matches = [
        (match, _match_weight(match))
        for match in matches
        if isinstance(match, dict)
        and _match_weight(match) > 0
        and _has_projection_data(match)
    ]
    if price <= 0 or not weighted_matches:
        return {
            **EMPTY_PRICE_PROJECTION,
            "current_price": round(price, 4),
            "expected_price_5d": round(price, 4),
            "expected_price_10d": round(price, 4),
            "expected_price_20d": round(price, 4),
        }

    total_weight = sum(weight for _, weight in weighted_matches)
    evidence_count = sum(_sample_count(match) for match, _ in weighted_matches)
    expected_return_5d = _weighted_average(
        weighted_matches,
        "average_5d_return",
        total_weight,
    )
    expected_return_10d = _weighted_average(
        weighted_matches,
        "average_10d_return",
        total_weight,
    )
    expected_return_20d = _weighted_average(
        weighted_matches,
        "average_20d_return",
        total_weight,
    )
    expected_max_gain = _weighted_average(
        weighted_matches,
        "average_max_gain",
        total_weight,
    )
    expected_drawdown = _weighted_average(
        weighted_matches,
        "average_drawdown",
        total_weight,
    )
    best_match = max(
        (match for match, _ in weighted_matches),
        key=lambda match: (
            _similarity(match),
            str(match.get("pattern_id") or ""),
        ),
    )

    return {
        "current_price": round(price, 4),
        "expected_price_5d": _project_price(price, expected_return_5d),
        "expected_price_10d": _project_price(price, expected_return_10d),
        "expected_price_20d": _project_price(price, expected_return_20d),
        "expected_return_5d": expected_return_5d,
        "expected_return_10d": expected_return_10d,
        "expected_return_20d": expected_return_20d,
        "upside_range": _upside_range(price, expected_return_10d, expected_max_gain),
        "downside_range": _downside_range(price, expected_return_10d, expected_drawdown),
        "confidence": _confidence(weighted_matches, total_weight, evidence_count),
        "evidence_count": evidence_count,
        "best_pattern_id": best_match.get("pattern_id"),
        "best_similarity": _similarity(best_match),
    }


def _coerce_matches(
    matched_patterns: dict[str, Any] | list[dict[str, Any]],
) -> list[dict[str, Any]]:
    if isinstance(matched_patterns, list):
        return matched_patterns
    matches = matched_patterns.get("matches") if isinstance(matched_patterns, dict) else None
    return matches if isinstance(matches, list) else []


def _has_projection_data(match: dict[str, Any]) -> bool:
    return any(
        _projection_value(match, key) is not None
        for key in (
            "average_5d_return",
            "average_10d_return",
            "average_20d_return",
            "average_max_gain",
            "average_drawdown",
        )
    )


def _weighted_average(
    weighted_matches: list[tuple[dict[str, Any], float]],
    key: str,
    total_weight: float,
) -> float:
    if total_weight <= 0:
        return 0.0

    total = 0.0
    for match, weight in weighted_matches:
        total += (_projection_value(match, key) or 0.0) * weight
    return round(total / total_weight, 4)


def _projection_value(match: dict[str, Any], key: str) -> float | None:
    pattern = match.get("pattern")
    if isinstance(pattern, dict):
        value = _optional_float(pattern.get(key))
        if value is not None:
            return value
    return _optional_float(match.get(key))


def _upside_range(
    current_price: float,
    expected_return_10d: float,
    expected_max_gain: float,
) -> dict[str, float] | None:
    high_return = max(expected_return_10d, expected_max_gain)
    if high_return <= 0:
        return None
    low_return = max(0.0, min(expected_return_10d, high_return))
    return {
        "low": _project_price(current_price, low_return),
        "high": _project_price(current_price, high_return),
    }


def _downside_range(
    current_price: float,
    expected_return_10d: float,
    expected_drawdown: float,
) -> dict[str, float] | None:
    low_return = min(expected_return_10d, expected_drawdown)
    if low_return >= 0:
        return None
    high_return = min(0.0, max(expected_return_10d, low_return))
    prices = sorted(
        (
            _project_price(current_price, low_return),
            _project_price(current_price, high_return),
        )
    )
    return {
        "low": prices[0],
        "high": prices[1],
    }


def _confidence(
    weighted_matches: list[tuple[dict[str, Any], float]],
    total_weight: float,
    evidence_count: int,
) -> float:
    if total_weight <= 0:
        return 0.0
    weighted_similarity = sum(
        _similarity(match) * weight
        for match, weight in weighted_matches
    ) / total_weight
    evidence_factor = min(evidence_count / 100.0, 1.0)
    return round(weighted_similarity * evidence_factor, 4)


def _match_weight(match: dict[str, Any]) -> float:
    return _similarity(match) * _sample_count(match)


def _similarity(match: dict[str, Any]) -> float:
    similarity = _optional_float(match.get("similarity"))
    if similarity is None:
        similarity = _optional_float(match.get("similarity_score"))
    return max(0.0, min(100.0, similarity or 0.0))


def _sample_count(match: dict[str, Any]) -> int:
    pattern = match.get("pattern")
    if isinstance(pattern, dict):
        value = _optional_float(pattern.get("sample_count"))
        if value is not None and value > 0:
            return int(value)

    value = _optional_float(match.get("sample_count"))
    if value is None or value <= 0:
        return 1
    return int(value)


def _project_price(current_price: float, return_percent: float) -> float:
    return round(current_price * (1 + return_percent / 100.0), 4)


def _optional_float(value: object) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
