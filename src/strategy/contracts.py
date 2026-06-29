from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from src.strategy.types import EntryQuality, RiskRating, TradeGrade


@dataclass(frozen=True)
class StrategyInput:
    snapshot: dict[str, Any]
    probability: dict[str, Any]
    prediction: dict[str, Any]


@dataclass(frozen=True)
class StrategyResult:
    strategy_score: float
    trade_grade: TradeGrade
    entry_quality: EntryQuality
    risk_rating: RiskRating
    reward_risk_estimate: dict[str, Any]
    notes: list[str] = field(default_factory=list)
