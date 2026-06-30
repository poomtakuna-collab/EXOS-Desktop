from __future__ import annotations

from typing import Any


EMPTY_PREDICTION_SUMMARY: dict[str, object] = {
    "confidence": 0.0,
    "evidence_count": 0,
    "best_pattern_id": None,
    "best_similarity": 0.0,
    "probability": {},
    "projection": {},
    "target_zone": None,
    "risk_zone": None,
}


def build_prediction_summary(
    probability: dict[str, Any] | None = None,
    projection: dict[str, Any] | None = None,
    target_zone: dict[str, Any] | None = None,
    risk_zone: dict[str, Any] | None = None,
) -> dict[str, object]:
    probability_section = _copy_dict(probability)
    projection_section = _copy_dict(projection)
    target_section = _copy_dict(target_zone)
    risk_section = _copy_dict(risk_zone)
    metadata_source = _metadata_source(
        probability_section,
        projection_section,
        target_section,
        risk_section,
    )

    return {
        "confidence": _bounded_float(metadata_source.get("confidence")),
        "evidence_count": _non_negative_int(metadata_source.get("evidence_count")),
        "best_pattern_id": metadata_source.get("best_pattern_id"),
        "best_similarity": _bounded_float(metadata_source.get("best_similarity")),
        "probability": probability_section,
        "projection": projection_section,
        "target_zone": target_section.get("target_zone"),
        "risk_zone": risk_section.get("risk_zone"),
    }


def _metadata_source(*sections: dict[str, Any]) -> dict[str, Any]:
    for section in sections:
        if any(
            section.get(key) is not None
            for key in (
                "confidence",
                "evidence_count",
                "best_pattern_id",
                "best_similarity",
            )
        ):
            return section
    return {}


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
