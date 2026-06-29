from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from src.data import MarketDataRow


@dataclass(frozen=True)
class PipelineConfig:
    timeframe: str = "1D"
    include_probability: bool = True
    include_prediction: bool = True
    include_strategy: bool = True
    include_backtest: bool = True


@dataclass(frozen=True)
class AnalysisRequest:
    symbol: str
    config: PipelineConfig = field(default_factory=PipelineConfig)
    ohlcv_rows: list[MarketDataRow] = field(default_factory=list)
    future_rows: list[MarketDataRow] = field(default_factory=list)
    similar_patterns: list[dict[str, Any]] = field(default_factory=list)


@dataclass(frozen=True)
class AnalysisResult:
    request: AnalysisRequest
    config: PipelineConfig
    symbol: str
    timeframe: str
    snapshot: dict[str, Any]
    probability: dict[str, Any] = field(default_factory=dict)
    prediction: dict[str, Any] = field(default_factory=dict)
    strategy: dict[str, Any] | None = None
    backtest: dict[str, Any] | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)
