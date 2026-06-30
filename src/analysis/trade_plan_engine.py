from __future__ import annotations

from typing import Any


EMPTY_TRADE_PLAN: dict[str, object] = {
    "entry_zone": None,
    "stop_zone": None,
    "target_zone": None,
    "risk_reward": None,
    "invalidation_notes": ["Prediction summary data unavailable"],
}


def build_trade_plan(
    prediction_summary: dict[str, Any] | None,
    strategy_summary: dict[str, Any] | None,
) -> dict[str, object]:
    prediction = _dict_value(prediction_summary)
    strategy = _dict_value(strategy_summary)
    if not prediction and not strategy:
        return dict(EMPTY_TRADE_PLAN)

    entry_zone = _entry_zone(prediction)
    stop_zone = _zone_or_none(prediction.get("risk_zone"))
    target_zone = _zone_or_none(prediction.get("target_zone"))
    risk_reward = _risk_reward(strategy)

    return {
        "entry_zone": entry_zone,
        "stop_zone": stop_zone,
        "target_zone": target_zone,
        "risk_reward": risk_reward,
        "invalidation_notes": _invalidation_notes(
            entry_zone,
            stop_zone,
            target_zone,
            risk_reward,
            strategy,
        ),
    }


def _entry_zone(prediction_summary: dict[str, Any]) -> dict[str, float] | None:
    projection = _dict_value(prediction_summary.get("projection"))
    current_price = _optional_float(projection.get("current_price"))
    expected_price = _optional_float(projection.get("expected_price_10d"))
    if current_price is None or current_price <= 0:
        return None
    if expected_price is None or expected_price <= 0:
        expected_price = current_price

    low, high = sorted((current_price, expected_price))
    return {
        "low": round(low, 4),
        "high": round(high, 4),
    }


def _zone_or_none(value: object) -> dict[str, float] | None:
    zone = _dict_value(value)
    if not zone:
        return None

    result: dict[str, float] = {}
    for key in ("conservative", "base", "aggressive"):
        number = _optional_float(zone.get(key))
        if number is None or number <= 0:
            return None
        result[key] = round(number, 4)
    return result


def _risk_reward(strategy_summary: dict[str, Any]) -> dict[str, object] | None:
    ratio = _optional_float(strategy_summary.get("reward_risk_ratio"))
    market_bias = strategy_summary.get("market_bias")
    risk_level = strategy_summary.get("risk_level")
    if ratio is None and market_bias is None and risk_level is None:
        return None
    return {
        "reward_risk_ratio": round(ratio, 4) if ratio is not None else None,
        "market_bias": market_bias if market_bias is not None else "unknown",
        "risk_level": risk_level if risk_level is not None else "unknown",
    }


def _invalidation_notes(
    entry_zone: dict[str, float] | None,
    stop_zone: dict[str, float] | None,
    target_zone: dict[str, float] | None,
    risk_reward: dict[str, object] | None,
    strategy_summary: dict[str, Any],
) -> list[str]:
    notes: list[str] = []
    if entry_zone is None:
        notes.append("Entry zone unavailable")
    if stop_zone is None:
        notes.append("Stop zone unavailable")
    if target_zone is None:
        notes.append("Target zone unavailable")
    if risk_reward is None or risk_reward.get("reward_risk_ratio") is None:
        notes.append("Reward/risk ratio unavailable")

    strategy_notes = strategy_summary.get("notes")
    if isinstance(strategy_notes, list):
        notes.extend(str(note) for note in strategy_notes)

    return notes or ["Trade plan derived from prediction and strategy summaries"]


def _dict_value(value: object) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _optional_float(value: object) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
