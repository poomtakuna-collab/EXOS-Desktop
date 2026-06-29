from __future__ import annotations

from typing import Any

from src.strategy.contracts import StrategyInput, StrategyResult
from src.strategy.types import EntryQuality, RiskRating, TradeGrade


MAX_SCORE = 100.0
MIN_SCORE = 0.0
EVIDENCE_COUNT_FOR_FULL_SCORE = 100.0


def analyze_strategy(strategy_input: StrategyInput) -> StrategyResult:
    probability = strategy_input.probability
    prediction = strategy_input.prediction

    expected_reward = _expected_reward_percent(probability, prediction)
    expected_risk = _expected_risk_percent(probability, prediction)
    reward_risk_ratio = _reward_risk_ratio(expected_reward, expected_risk)

    confidence_score = _confidence_score(probability, prediction)
    evidence_score = _evidence_score(probability)
    return_score = _return_score(expected_reward)
    reward_risk_score = _reward_risk_score(reward_risk_ratio)
    risk_penalty = _risk_penalty(probability, expected_risk)

    strategy_score = _clamp(
        confidence_score * 0.30
        + evidence_score * 0.25
        + return_score * 0.25
        + reward_risk_score * 0.20
        - risk_penalty,
        MIN_SCORE,
        MAX_SCORE,
    )
    strategy_score = round(strategy_score, 4)

    risk_rating = _risk_rating(probability, expected_risk)
    trade_grade = _trade_grade(strategy_score)
    entry_quality = _entry_quality(strategy_score, risk_rating)

    return StrategyResult(
        strategy_score=strategy_score,
        trade_grade=trade_grade,
        entry_quality=entry_quality,
        risk_rating=risk_rating,
        reward_risk_estimate={
            "expected_reward_percent": round(expected_reward, 4),
            "expected_risk_percent": round(expected_risk, 4),
            "reward_risk_ratio": reward_risk_ratio,
            "target_zone": {
                "low": _optional_float(prediction.get("target_zone_low")),
                "high": _optional_float(prediction.get("target_zone_high")),
            },
            "risk_zone": {
                "low": _optional_float(prediction.get("risk_zone_low")),
                "high": _optional_float(prediction.get("risk_zone_high")),
            },
        },
        notes=_strategy_notes(
            confidence_score=confidence_score,
            evidence_score=evidence_score,
            expected_reward=expected_reward,
            expected_risk=expected_risk,
            reward_risk_ratio=reward_risk_ratio,
            risk_rating=risk_rating,
        ),
    )


def _expected_reward_percent(
    probability: dict[str, Any],
    prediction: dict[str, Any],
) -> float:
    prediction_return = _optional_float(prediction.get("expected_return"))
    if prediction_return is not None:
        return prediction_return

    return _optional_float(probability.get("expected_return_10d")) or 0.0


def _expected_risk_percent(
    probability: dict[str, Any],
    prediction: dict[str, Any],
) -> float:
    drawdown = _optional_float(probability.get("expected_drawdown_10d"))
    if drawdown is not None:
        return abs(drawdown)

    risk_zone_low = _optional_float(prediction.get("risk_zone_low"))
    risk_zone_high = _optional_float(prediction.get("risk_zone_high"))
    current_price = _current_price(prediction)
    if current_price and risk_zone_low is not None and risk_zone_high is not None:
        risk_price = min(risk_zone_low, risk_zone_high)
        return abs((risk_price - current_price) / current_price * 100)

    return 0.0


def _current_price(prediction: dict[str, Any]) -> float | None:
    for key in ("expected_price_10d", "target_zone_low", "target_zone_high"):
        value = _optional_float(prediction.get(key))
        if value is not None and value > 0:
            return value
    return None


def _reward_risk_ratio(expected_reward: float, expected_risk: float) -> float | None:
    if expected_risk <= 0:
        return None
    return round(expected_reward / expected_risk, 4)


def _confidence_score(
    probability: dict[str, Any],
    prediction: dict[str, Any],
) -> float:
    probability_confidence = _optional_float(probability.get("confidence"))
    prediction_confidence = _optional_float(prediction.get("confidence"))
    confidence_values = [
        value
        for value in (probability_confidence, prediction_confidence)
        if value is not None
    ]
    if not confidence_values:
        return 0.0
    return _clamp(sum(confidence_values) / len(confidence_values), MIN_SCORE, MAX_SCORE)


def _evidence_score(probability: dict[str, Any]) -> float:
    evidence_count = _optional_float(probability.get("evidence_count")) or 0.0
    return _clamp(
        evidence_count / EVIDENCE_COUNT_FOR_FULL_SCORE * MAX_SCORE,
        MIN_SCORE,
        MAX_SCORE,
    )


def _return_score(expected_reward: float) -> float:
    return _clamp(50.0 + expected_reward * 5.0, MIN_SCORE, MAX_SCORE)


def _reward_risk_score(reward_risk_ratio: float | None) -> float:
    if reward_risk_ratio is None:
        return 50.0
    return _clamp(reward_risk_ratio / 3.0 * MAX_SCORE, MIN_SCORE, MAX_SCORE)


def _risk_penalty(probability: dict[str, Any], expected_risk: float) -> float:
    downside_probability = _optional_float(
        probability.get("probability_down_5pct_10d")
    ) or 0.0
    downside_penalty = _clamp(downside_probability / 100.0 * 20.0, 0.0, 20.0)
    drawdown_penalty = _clamp(expected_risk / 20.0 * 10.0, 0.0, 10.0)
    return downside_penalty + drawdown_penalty


def _trade_grade(strategy_score: float) -> TradeGrade:
    if strategy_score >= 80:
        return TradeGrade.EXCELLENT
    if strategy_score >= 65:
        return TradeGrade.GOOD
    if strategy_score >= 45:
        return TradeGrade.NEUTRAL
    if strategy_score >= 25:
        return TradeGrade.WEAK
    return TradeGrade.AVOID


def _entry_quality(
    strategy_score: float,
    risk_rating: RiskRating,
) -> EntryQuality:
    if strategy_score >= 80 and risk_rating in {RiskRating.VERY_LOW, RiskRating.LOW}:
        return EntryQuality.IDEAL
    if strategy_score >= 65 and risk_rating != RiskRating.VERY_HIGH:
        return EntryQuality.GOOD
    if strategy_score >= 45 and risk_rating in {
        RiskRating.VERY_LOW,
        RiskRating.LOW,
        RiskRating.MEDIUM,
    }:
        return EntryQuality.ACCEPTABLE
    return EntryQuality.POOR


def _risk_rating(probability: dict[str, Any], expected_risk: float) -> RiskRating:
    downside_probability = _optional_float(
        probability.get("probability_down_5pct_10d")
    ) or 0.0
    risk_score = _clamp(downside_probability * 0.6 + expected_risk * 2.0, 0.0, 100.0)

    if risk_score >= 80:
        return RiskRating.VERY_HIGH
    if risk_score >= 60:
        return RiskRating.HIGH
    if risk_score >= 35:
        return RiskRating.MEDIUM
    if risk_score >= 15:
        return RiskRating.LOW
    return RiskRating.VERY_LOW


def _strategy_notes(
    confidence_score: float,
    evidence_score: float,
    expected_reward: float,
    expected_risk: float,
    reward_risk_ratio: float | None,
    risk_rating: RiskRating,
) -> list[str]:
    notes = [
        f"Confidence score: {round(confidence_score, 2)}",
        f"Evidence score: {round(evidence_score, 2)}",
        f"Expected reward: {round(expected_reward, 2)}%",
        f"Expected risk: {round(expected_risk, 2)}%",
        f"Risk rating: {risk_rating.value}",
    ]
    if reward_risk_ratio is None:
        notes.append("Reward/risk ratio unavailable because expected risk is zero")
    else:
        notes.append(f"Reward/risk ratio: {reward_risk_ratio}")
    return notes


def _optional_float(value: object) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(maximum, value))
