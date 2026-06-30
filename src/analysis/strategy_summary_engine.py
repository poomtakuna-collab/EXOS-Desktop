from __future__ import annotations

from typing import Any


EMPTY_STRATEGY_SUMMARY: dict[str, object] = {
    "market_bias": "unknown",
    "risk_level": "unknown",
    "reward_risk_ratio": None,
    "notes": ["Prediction summary data unavailable"],
}


def build_strategy_summary(
    prediction_summary: dict[str, Any] | None,
) -> dict[str, object]:
    if not isinstance(prediction_summary, dict) or not prediction_summary:
        return dict(EMPTY_STRATEGY_SUMMARY)

    market_bias = _market_bias(prediction_summary)
    risk_level = _risk_level(prediction_summary)
    reward_risk_ratio = _reward_risk_ratio(prediction_summary)

    return {
        "market_bias": market_bias,
        "risk_level": risk_level,
        "reward_risk_ratio": reward_risk_ratio,
        "notes": _notes(market_bias, risk_level, reward_risk_ratio),
    }


def _market_bias(prediction_summary: dict[str, Any]) -> str:
    probability = _dict_value(prediction_summary.get("probability"))
    positive = _optional_float(probability.get("probability_positive"))
    negative = _optional_float(probability.get("probability_negative"))
    neutral = _optional_float(probability.get("probability_neutral"))

    if positive is not None or negative is not None or neutral is not None:
        positive_value = positive or 0.0
        negative_value = negative or 0.0
        neutral_value = neutral or 0.0
        if positive_value > negative_value and positive_value >= neutral_value:
            return "positive"
        if negative_value > positive_value and negative_value >= neutral_value:
            return "negative"
        return "neutral"

    projection = _dict_value(prediction_summary.get("projection"))
    expected_return = _optional_float(projection.get("expected_return_10d"))
    if expected_return is None:
        return "unknown"
    if expected_return > 0:
        return "positive"
    if expected_return < 0:
        return "negative"
    return "neutral"


def _risk_level(prediction_summary: dict[str, Any]) -> str:
    risk_percent = _risk_percent_from_zone(prediction_summary)
    if risk_percent is not None:
        if risk_percent >= 8.0:
            return "high"
        if risk_percent >= 3.0:
            return "medium"
        return "low"

    probability = _dict_value(prediction_summary.get("probability"))
    negative_probability = _optional_float(probability.get("probability_negative"))
    if negative_probability is None:
        return "unknown"
    if negative_probability >= 60.0:
        return "high"
    if negative_probability >= 30.0:
        return "medium"
    return "low"


def _reward_risk_ratio(prediction_summary: dict[str, Any]) -> float | None:
    current_price = _current_price(prediction_summary)
    target_zone = _dict_value(prediction_summary.get("target_zone"))
    risk_zone = _dict_value(prediction_summary.get("risk_zone"))
    target_price = _optional_float(target_zone.get("aggressive"))
    risk_price = _optional_float(risk_zone.get("aggressive"))

    if (
        current_price is None
        or current_price <= 0
        or target_price is None
        or risk_price is None
    ):
        return None

    reward_percent = max((target_price - current_price) / current_price * 100.0, 0.0)
    risk_percent = max((current_price - risk_price) / current_price * 100.0, 0.0)
    if risk_percent <= 0:
        return None
    return round(reward_percent / risk_percent, 4)


def _risk_percent_from_zone(prediction_summary: dict[str, Any]) -> float | None:
    current_price = _current_price(prediction_summary)
    risk_zone = _dict_value(prediction_summary.get("risk_zone"))
    aggressive_risk = _optional_float(risk_zone.get("aggressive"))
    if current_price is None or current_price <= 0 or aggressive_risk is None:
        return None
    return max((current_price - aggressive_risk) / current_price * 100.0, 0.0)


def _current_price(prediction_summary: dict[str, Any]) -> float | None:
    projection = _dict_value(prediction_summary.get("projection"))
    current_price = _optional_float(projection.get("current_price"))
    if current_price is not None:
        return current_price
    return _optional_float(projection.get("expected_price_10d"))


def _notes(
    market_bias: str,
    risk_level: str,
    reward_risk_ratio: float | None,
) -> list[str]:
    notes = [
        f"Market bias: {market_bias}",
        f"Risk level: {risk_level}",
    ]
    if reward_risk_ratio is None:
        notes.append("Reward/risk ratio unavailable")
    else:
        notes.append(f"Reward/risk ratio: {reward_risk_ratio}")
    return notes


def _dict_value(value: object) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _optional_float(value: object) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
