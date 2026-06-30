from __future__ import annotations

from typing import Any


EMPTY_TARGET_ZONE: dict[str, object] = {
    "target_zone": None,
    "confidence": 0.0,
    "evidence_count": 0,
    "best_pattern_id": None,
    "best_similarity": 0.0,
}


def calculate_target_zone(
    price_projection: dict[str, Any],
) -> dict[str, object]:
    upside_range = price_projection.get("upside_range")
    if not isinstance(upside_range, dict):
        return _empty_from_projection(price_projection)

    low = _optional_float(upside_range.get("low"))
    high = _optional_float(upside_range.get("high"))
    if low is None or high is None or low <= 0 or high <= 0:
        return _empty_from_projection(price_projection)

    conservative, aggressive = sorted((low, high))
    base = _optional_float(price_projection.get("expected_price_10d"))
    if base is None or base <= 0:
        base = (conservative + aggressive) / 2
    base = min(max(base, conservative), aggressive)

    return {
        "target_zone": {
            "conservative": round(conservative, 4),
            "base": round(base, 4),
            "aggressive": round(aggressive, 4),
        },
        "confidence": _bounded_float(price_projection.get("confidence")),
        "evidence_count": _non_negative_int(price_projection.get("evidence_count")),
        "best_pattern_id": price_projection.get("best_pattern_id"),
        "best_similarity": _bounded_float(price_projection.get("best_similarity")),
    }


def _empty_from_projection(price_projection: dict[str, Any]) -> dict[str, object]:
    return {
        **EMPTY_TARGET_ZONE,
        "confidence": _bounded_float(price_projection.get("confidence")),
        "evidence_count": _non_negative_int(price_projection.get("evidence_count")),
        "best_pattern_id": price_projection.get("best_pattern_id"),
        "best_similarity": _bounded_float(price_projection.get("best_similarity")),
    }


def _bounded_float(value: object) -> float:
    number = _optional_float(value)
    if number is None:
        return 0.0
    return round(max(0.0, min(100.0, number)), 4)


def _non_negative_int(value: object) -> int:
    number = _optional_float(value)
    if number is None or number <= 0:
        return 0
    return int(number)


def _optional_float(value: object) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
