from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from src.context.types import MarketContext


def calculate_market_context(
    *,
    snapshot: Mapping[str, Any] | None = None,
    probability: Mapping[str, Any] | None = None,
    prediction: Mapping[str, Any] | None = None,
    strategy: Mapping[str, Any] | None = None,
) -> MarketContext:
    """Calculate deterministic market context from available analysis outputs."""
    del prediction
    del strategy

    snapshot_data = snapshot if isinstance(snapshot, Mapping) else {}
    probability_data = probability if isinstance(probability, Mapping) else {}

    return MarketContext(
        trend=_trend(snapshot_data),
        momentum=_momentum(snapshot_data, probability_data),
        volatility=_volatility(snapshot_data),
        risk_state=_risk_state(snapshot_data),
    )


def calculate_market_context_from_analysis(analysis_result: Any) -> MarketContext:
    """Calculate market context from an AnalysisResult-like object or dict."""
    if isinstance(analysis_result, Mapping):
        return calculate_market_context(
            snapshot=_mapping_or_none(analysis_result.get("snapshot")),
            probability=_mapping_or_none(analysis_result.get("probability")),
            prediction=_mapping_or_none(analysis_result.get("prediction")),
            strategy=_mapping_or_none(analysis_result.get("strategy")),
        )

    return calculate_market_context(
        snapshot=_mapping_or_none(getattr(analysis_result, "snapshot", None)),
        probability=_mapping_or_none(getattr(analysis_result, "probability", None)),
        prediction=_mapping_or_none(getattr(analysis_result, "prediction", None)),
        strategy=_mapping_or_none(getattr(analysis_result, "strategy", None)),
    )


def _trend(snapshot: Mapping[str, Any]) -> str:
    trend_section = _section(snapshot, "trend")
    structure_section = _section(snapshot, "market_structure")

    trend_state = _normalized_string(trend_section.get("state"))
    structure_state = _normalized_string(structure_section.get("state"))
    trend_score = _score(trend_section)
    structure_score = _score(structure_section)

    if trend_state == "bullish" or structure_state in {"hh_hl", "breakout_up", "choch_up"}:
        return "up"
    if trend_state == "bearish" or structure_state in {"lh_ll", "breakout_down", "choch_down"}:
        return "down"
    if trend_score is not None:
        if trend_score >= 65:
            return "up"
        if trend_score <= 35:
            return "down"
        return "sideways"
    if structure_score is not None:
        if structure_score >= 65:
            return "up"
        if structure_score <= 35:
            return "down"
        return "sideways"
    if trend_state in {"mixed", "flat", "range"} or structure_state == "range":
        return "sideways"
    return "unknown"


def _momentum(
    snapshot: Mapping[str, Any],
    probability: Mapping[str, Any],
) -> str:
    slope_section = _section(snapshot, "trend_slope")
    direction = _normalized_string(slope_section.get("direction"))
    slope_score = _score(slope_section)
    probability_confidence = _number(probability.get("confidence"))

    if direction == "up":
        return "positive"
    if direction == "down":
        return "negative"
    if slope_score is not None:
        if slope_score >= 55:
            return "positive"
        if slope_score <= 45:
            return "negative"
        return "neutral"
    if probability_confidence is not None and probability_confidence <= 0:
        return "unknown"
    return "unknown"


def _volatility(snapshot: Mapping[str, Any]) -> str:
    squeeze_section = _section(snapshot, "squeeze")
    squeeze_state = _normalized_string(squeeze_section.get("state"))
    compression_ratio = _number(squeeze_section.get("compression_ratio"))

    if squeeze_state in {"releasing", "expanded"}:
        return "elevated"
    if squeeze_state in {"squeeze", "building"}:
        return "compressed"
    if compression_ratio is not None:
        if compression_ratio >= 1.5:
            return "elevated"
        if compression_ratio <= 1.0:
            return "compressed"
        return "normal"
    if squeeze_state in {"none", "unknown"}:
        return "normal"
    return "unknown"


def _risk_state(snapshot: Mapping[str, Any]) -> str:
    trend_value = _trend(snapshot)
    volatility_value = _volatility(snapshot)
    score_section = _section(snapshot, "score")
    overall_score = _number(score_section.get("overall_score"))
    confidence = _number(score_section.get("confidence"))

    if trend_value == "down" or volatility_value == "elevated":
        return "risk_off"
    if (
        trend_value == "up"
        and volatility_value in {"normal", "compressed"}
        and overall_score is not None
        and confidence is not None
        and overall_score >= 60
        and confidence >= 40
    ):
        return "risk_on"
    if trend_value == "unknown" and overall_score is None:
        return "unknown"
    return "neutral"


def _section(snapshot: Mapping[str, Any], name: str) -> Mapping[str, Any]:
    value = snapshot.get(name)
    return value if isinstance(value, Mapping) else {}


def _score(section: Mapping[str, Any]) -> float | None:
    return _number(section.get("score"))


def _number(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _normalized_string(value: Any) -> str:
    return str(value or "").strip().lower()


def _mapping_or_none(value: Any) -> Mapping[str, Any] | None:
    return value if isinstance(value, Mapping) else None
