from __future__ import annotations

from typing import Any


EMPTY_STRATEGY_REPORT: dict[str, object] = {
    "confidence": 0.0,
    "evidence_count": 0,
    "best_pattern_id": None,
    "best_similarity": 0.0,
    "prediction_summary": {},
    "strategy_summary": {},
    "trade_plan": {},
    "position_sizing": {},
}


def build_strategy_report(
    prediction_summary: dict[str, Any] | None = None,
    strategy_summary: dict[str, Any] | None = None,
    trade_plan: dict[str, Any] | None = None,
    position_sizing: dict[str, Any] | None = None,
) -> dict[str, object]:
    prediction_section = _copy_dict(prediction_summary)

    return {
        "confidence": _bounded_float(prediction_section.get("confidence")),
        "evidence_count": _non_negative_int(prediction_section.get("evidence_count")),
        "best_pattern_id": prediction_section.get("best_pattern_id"),
        "best_similarity": _bounded_float(prediction_section.get("best_similarity")),
        "prediction_summary": prediction_section,
        "strategy_summary": _copy_dict(strategy_summary),
        "trade_plan": _copy_dict(trade_plan),
        "position_sizing": _copy_dict(position_sizing),
    }


def _copy_dict(value: dict[str, Any] | None) -> dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}


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
