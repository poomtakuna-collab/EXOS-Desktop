from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from src.analysis import (
    build_exos_snapshot,
    build_prediction_summary,
    calculate_price_projection,
    calculate_probability_summary,
    calculate_risk_zone,
    calculate_target_zone,
    resolve_similar_patterns,
)
from src.analysis_pipeline.contracts import AnalysisRequest


CANONICAL_BRAIN_CHAIN = (
    "similar_pattern_resolver",
    "probability_engine",
    "price_projection",
    "target_zone",
    "risk_zone",
    "prediction_summary",
)


@dataclass(frozen=True)
class CanonicalBrainAdapterResult:
    snapshot: dict[str, Any]
    resolver_output: dict[str, Any]
    probability: dict[str, Any]
    projection: dict[str, Any]
    target_zone: dict[str, Any]
    risk_zone: dict[str, Any]
    prediction_summary: dict[str, Any]
    metadata: dict[str, Any] = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)


def build_canonical_brain_analysis(
    request: AnalysisRequest | None,
) -> CanonicalBrainAdapterResult:
    safe_request = request if isinstance(request, AnalysisRequest) else None
    notes: list[str] = []

    snapshot = _build_snapshot(safe_request, notes)
    pattern_library = _pattern_library(safe_request)
    resolver_output = resolve_similar_patterns(snapshot, pattern_library)

    probability = (
        calculate_probability_summary(resolver_output)
        if _include_probability(safe_request)
        else {}
    )
    current_price = _latest_close(safe_request, notes)
    projection = (
        calculate_price_projection(current_price, resolver_output)
        if _include_prediction(safe_request)
        else {}
    )
    target_zone = calculate_target_zone(projection) if projection else {}
    risk_zone = calculate_risk_zone(projection) if projection else {}
    prediction_summary = (
        build_prediction_summary(
            probability=probability,
            projection=projection,
            target_zone=target_zone,
            risk_zone=risk_zone,
        )
        if _include_prediction(safe_request)
        else {}
    )

    return CanonicalBrainAdapterResult(
        snapshot=snapshot,
        resolver_output=resolver_output,
        probability=probability,
        projection=projection,
        target_zone=target_zone,
        risk_zone=risk_zone,
        prediction_summary=prediction_summary,
        metadata=_metadata(
            request=safe_request,
            pattern_library=pattern_library,
            resolver_output=resolver_output,
            current_price=current_price,
        ),
        notes=notes,
    )


def _build_snapshot(
    request: AnalysisRequest | None,
    notes: list[str],
) -> dict[str, Any]:
    if request is None:
        notes.append("No AnalysisRequest supplied; canonical adapter returned safe defaults.")
        return {}
    if not request.ohlcv_rows:
        notes.append("No OHLCV rows supplied; snapshot is unavailable.")
        return {}

    try:
        return build_exos_snapshot(
            request.ohlcv_rows,
            symbol=request.symbol,
            timeframe=request.config.timeframe,
        )
    except (KeyError, TypeError, ValueError):
        notes.append("Malformed OHLCV rows supplied; snapshot is unavailable.")
        return {}


def _pattern_library(request: AnalysisRequest | None) -> list[dict[str, Any]]:
    if request is None:
        return []

    patterns: list[dict[str, Any]] = []
    for item in request.similar_patterns:
        if not isinstance(item, dict):
            continue
        nested_pattern = item.get("pattern")
        if isinstance(nested_pattern, dict):
            pattern = dict(nested_pattern)
            if "pattern_id" not in pattern:
                pattern["pattern_id"] = item.get("pattern_id")
            if "outcome" not in pattern and item.get("outcome") is not None:
                pattern["outcome"] = item.get("outcome")
            patterns.append(pattern)
            continue
        patterns.append(dict(item))
    return patterns


def _latest_close(
    request: AnalysisRequest | None,
    notes: list[str],
) -> float:
    if request is None or not request.ohlcv_rows:
        return 0.0

    try:
        return max(float(request.ohlcv_rows[-1]["close"]), 0.0)
    except (KeyError, TypeError, ValueError):
        notes.append("Latest close is unavailable; projection uses 0.0.")
        return 0.0


def _include_probability(request: AnalysisRequest | None) -> bool:
    return bool(request is None or request.config.include_probability)


def _include_prediction(request: AnalysisRequest | None) -> bool:
    return bool(request is None or request.config.include_prediction)


def _metadata(
    request: AnalysisRequest | None,
    pattern_library: list[dict[str, Any]],
    resolver_output: dict[str, Any],
    current_price: float,
) -> dict[str, Any]:
    matches = resolver_output.get("matches")
    match_count = len(matches) if isinstance(matches, list) else 0
    rows = len(request.ohlcv_rows) if request is not None else 0
    symbol = request.symbol if request is not None else ""
    timeframe = request.config.timeframe if request is not None else ""
    return {
        "adapter": "canonical_brain_adapter_v1",
        "canonical_path": "src.analysis",
        "chain": list(CANONICAL_BRAIN_CHAIN),
        "symbol": symbol,
        "timeframe": timeframe,
        "rows": rows,
        "pattern_count": len(pattern_library),
        "match_count": match_count,
        "current_price": round(current_price, 4),
    }
