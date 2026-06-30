from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from src.analysis_pipeline.canonical_brain_adapter import (
    CanonicalBrainAdapterResult,
    build_canonical_brain_analysis,
)
from src.analysis_pipeline.contracts import AnalysisRequest, PipelineConfig


MAPPING_DECISION = (
    "Canonical Brain output is returned as a separate immutable result because "
    "Prediction Summary is nested and does not map cleanly to the existing "
    "AnalysisResult.prediction shape."
)


@dataclass(frozen=True)
class CanonicalAnalysisResultV1:
    request: AnalysisRequest | None
    config: PipelineConfig
    symbol: str
    timeframe: str
    canonical_brain: CanonicalBrainAdapterResult
    metadata: dict[str, Any] = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)


def analyze_symbol_with_canonical_brain(
    request: AnalysisRequest | None,
) -> CanonicalAnalysisResultV1:
    canonical_brain = build_canonical_brain_analysis(request)
    config = request.config if isinstance(request, AnalysisRequest) else PipelineConfig()
    symbol = request.symbol if isinstance(request, AnalysisRequest) else ""
    timeframe = config.timeframe

    return CanonicalAnalysisResultV1(
        request=request if isinstance(request, AnalysisRequest) else None,
        config=config,
        symbol=symbol,
        timeframe=timeframe,
        canonical_brain=canonical_brain,
        metadata={
            "entry_point": "analyze_symbol_with_canonical_brain",
            "result_type": "CanonicalAnalysisResultV1",
            "uses_adapter": "canonical_brain_adapter_v1",
            "analysis_result_mapping": "separate_result_type",
            "mapping_reason": MAPPING_DECISION,
            "symbol": symbol,
            "timeframe": timeframe,
            "rows": canonical_brain.metadata.get("rows", 0),
            "pattern_count": canonical_brain.metadata.get("pattern_count", 0),
            "match_count": canonical_brain.metadata.get("match_count", 0),
        },
        notes=[
            MAPPING_DECISION,
            *canonical_brain.notes,
        ],
    )
