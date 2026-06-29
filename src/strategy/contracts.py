from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, TypedDict

from src.strategy.types import EntryQuality, RiskRating, TradeGrade


class PriceZone(TypedDict):
    low: float | None
    high: float | None


class RewardRiskEstimate(TypedDict):
    expected_reward_percent: float
    expected_risk_percent: float
    reward_risk_ratio: float | None
    target_zone: PriceZone
    risk_zone: PriceZone


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
    reward_risk_estimate: RewardRiskEstimate
    notes: list[str] = field(default_factory=list)
