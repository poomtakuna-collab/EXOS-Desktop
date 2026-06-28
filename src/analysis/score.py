from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


COMPONENT_WEIGHTS = {
    "trend": 30,
    "trend_slope": 20,
    "squeeze": 20,
    "market_structure": 30,
}


@dataclass(frozen=True)
class EXOSScore:
    overall_score: float
    rating: str
    confidence: float
    recommendation: str
    component_scores: dict[str, float]

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def analyze_score(snapshot: dict[str, object]) -> dict[str, object]:
    component_scores = {
        component: _component_score(snapshot, component)
        for component in COMPONENT_WEIGHTS
    }
    overall_score = _weighted_score(component_scores)
    confidence = _average_confidence(snapshot)

    score = EXOSScore(
        overall_score=overall_score,
        rating=_rating(overall_score),
        confidence=confidence,
        recommendation=_recommendation(overall_score, confidence),
        component_scores=component_scores,
    )
    return score.to_dict()


def _component_score(snapshot: dict[str, object], component: str) -> float:
    section = snapshot.get(component)
    if not isinstance(section, dict):
        return 0.0

    return round(_clamp(float(section.get("score", 0.0)), 0, 100), 2)


def _weighted_score(component_scores: dict[str, float]) -> float:
    weighted_total = 0.0
    for component, weight in COMPONENT_WEIGHTS.items():
        weighted_total += component_scores.get(component, 0.0) * weight
    return round(_clamp(weighted_total / sum(COMPONENT_WEIGHTS.values()), 0, 100), 2)


def _average_confidence(snapshot: dict[str, object]) -> float:
    confidence_values: list[float] = []
    for component in COMPONENT_WEIGHTS:
        section = snapshot.get(component)
        if isinstance(section, dict) and "confidence" in section:
            confidence_values.append(_normalize_confidence(section.get("confidence")))
        else:
            confidence_values.append(0.0)

    return round(sum(confidence_values) / len(confidence_values), 2)


def _normalize_confidence(value: Any) -> float:
    confidence = float(value or 0.0)
    if confidence <= 1:
        confidence *= 100
    return _clamp(confidence, 0, 100)


def _rating(score: float) -> str:
    if score >= 90:
        return "EXCELLENT"
    if score >= 80:
        return "STRONG"
    if score >= 70:
        return "GOOD"
    if score >= 60:
        return "NEUTRAL"
    if score >= 40:
        return "WEAK"
    return "POOR"


def _recommendation(score: float, confidence: float) -> str:
    if confidence < 40 or score < 50:
        return "AVOID"
    if score >= 90 and confidence >= 75:
        return "BUY"
    if score >= 70 and confidence >= 60:
        return "WATCH"
    return "HOLD"


def _clamp(value: float, minimum: float, maximum: float) -> float:
    return min(max(value, minimum), maximum)
