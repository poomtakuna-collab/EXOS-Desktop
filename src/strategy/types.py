from __future__ import annotations

from enum import StrEnum


class TradeGrade(StrEnum):
    EXCELLENT = "Excellent"
    GOOD = "Good"
    NEUTRAL = "Neutral"
    WEAK = "Weak"
    AVOID = "Avoid"


class RiskRating(StrEnum):
    VERY_LOW = "Very Low"
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    VERY_HIGH = "Very High"


class EntryQuality(StrEnum):
    IDEAL = "Ideal"
    GOOD = "Good"
    ACCEPTABLE = "Acceptable"
    POOR = "Poor"
