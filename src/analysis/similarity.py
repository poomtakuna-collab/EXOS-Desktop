from __future__ import annotations

from typing import Any


SIMILARITY_WEIGHTS: dict[str, float] = {
    "trend": 25.0,
    "trend_slope": 20.0,
    "adx": 15.0,
    "rsi": 10.0,
    "atr": 10.0,
    "squeeze": 10.0,
    "market_structure": 10.0,
}

NUMERIC_FIELDS = frozenset({"trend_slope", "adx", "rsi", "atr"})
CATEGORICAL_FIELDS = frozenset({"trend", "squeeze", "market_structure"})

FIELD_ALIASES: dict[str, tuple[tuple[str, ...], ...]] = {
    "trend": (
        ("trend",),
        ("trend_state",),
        ("trend", "state"),
    ),
    "trend_slope": (
        ("trend_slope",),
        ("trend_slope_score",),
        ("trend_slope", "score"),
        ("trend_slope", "value"),
        ("trend_slope", "trend_slope"),
    ),
    "adx": (
        ("adx",),
        ("adx_score",),
        ("indicators", "adx"),
        ("indicator", "adx"),
        ("trend", "adx"),
    ),
    "rsi": (
        ("rsi",),
        ("rsi_score",),
        ("indicators", "rsi"),
        ("indicator", "rsi"),
        ("momentum", "rsi"),
    ),
    "atr": (
        ("atr",),
        ("atr_score",),
        ("indicators", "atr"),
        ("indicator", "atr"),
        ("volatility", "atr"),
    ),
    "squeeze": (
        ("squeeze",),
        ("squeeze_state",),
        ("squeeze", "state"),
    ),
    "market_structure": (
        ("market_structure",),
        ("market_structure_state",),
        ("market_structure", "state"),
    ),
}


def calculate_weighted_similarity(
    snapshot: dict[str, Any],
    pattern: dict[str, Any],
    weights: dict[str, float] | None = None,
) -> float:
    active_weights = weights or SIMILARITY_WEIGHTS
    weighted_score = 0.0
    total_weight = sum(active_weights.values())
    if total_weight <= 0:
        return 0.0

    for field, weight in active_weights.items():
        left = resolve_similarity_value(snapshot, field)
        right = resolve_similarity_value(pattern, field)
        field_score = calculate_field_similarity(field, left, right)
        weighted_score += field_score * weight

    return round(max(0.0, min(100.0, weighted_score / total_weight)), 2)


def calculate_field_similarity(field: str, left: object, right: object) -> float:
    if left is None or right is None:
        return 0.0

    if field in NUMERIC_FIELDS:
        left_number = _optional_float(left)
        right_number = _optional_float(right)
        if left_number is None or right_number is None:
            return 0.0
        return _numeric_similarity(left_number, right_number)

    if field in CATEGORICAL_FIELDS:
        return _categorical_similarity(left, right)

    return 0.0


def resolve_similarity_value(source: dict[str, Any], field: str) -> object:
    for path in FIELD_ALIASES.get(field, ((field,),)):
        value = _nested_value(source, path)
        if isinstance(value, dict):
            value = _nested_value(value, ("state",))
        if value is not None:
            return value
    return None


def _categorical_similarity(left: object, right: object) -> float:
    left_text = str(left).strip().lower()
    right_text = str(right).strip().lower()
    if not left_text or not right_text:
        return 0.0
    return 100.0 if left_text == right_text else 0.0


def _numeric_similarity(left: float, right: float) -> float:
    difference = abs(left - right)
    scale = _numeric_scale(left, right)
    if scale <= 0:
        return 100.0 if difference == 0 else 0.0
    return round(max(0.0, 100.0 - difference / scale * 100.0), 2)


def _numeric_scale(left: float, right: float) -> float:
    if 0.0 <= left <= 100.0 and 0.0 <= right <= 100.0:
        return 100.0
    return max(abs(left), abs(right), 1.0)


def _nested_value(source: dict[str, Any], path: tuple[str, ...]) -> object:
    current: object = source
    for key in path:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current


def _optional_float(value: object) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
