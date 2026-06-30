from __future__ import annotations

from typing import Any


DEFAULT_ACCOUNT_RISK_PERCENT = 1.0

EMPTY_POSITION_SIZING: dict[str, object] = {
    "account_risk_percent": DEFAULT_ACCOUNT_RISK_PERCENT,
    "risk_per_share": 0.0,
    "position_size_shares": 0,
    "estimated_capital_required": 0.0,
    "max_loss_amount": 0.0,
}


def calculate_position_sizing(
    trade_plan: dict[str, Any] | None,
    account_size: float = 0.0,
    account_risk_percent: float = DEFAULT_ACCOUNT_RISK_PERCENT,
) -> dict[str, object]:
    plan = trade_plan if isinstance(trade_plan, dict) else {}
    risk_percent = _safe_risk_percent(account_risk_percent)
    account_value = max(_optional_float(account_size) or 0.0, 0.0)
    max_loss_amount = round(account_value * risk_percent / 100.0, 4)

    entry_price = _entry_price(plan)
    stop_price = _stop_price(plan)
    if entry_price is None or stop_price is None or max_loss_amount <= 0:
        return _empty_result(risk_percent, max_loss_amount)

    risk_per_share = round(max(entry_price - stop_price, 0.0), 4)
    if risk_per_share <= 0:
        return _empty_result(risk_percent, max_loss_amount)

    position_size_shares = int(max_loss_amount // risk_per_share)
    estimated_capital_required = round(position_size_shares * entry_price, 4)

    return {
        "account_risk_percent": risk_percent,
        "risk_per_share": risk_per_share,
        "position_size_shares": position_size_shares,
        "estimated_capital_required": estimated_capital_required,
        "max_loss_amount": max_loss_amount,
    }


def _entry_price(trade_plan: dict[str, Any]) -> float | None:
    entry_zone = _dict_value(trade_plan.get("entry_zone"))
    return _optional_float(entry_zone.get("high"))


def _stop_price(trade_plan: dict[str, Any]) -> float | None:
    stop_zone = _dict_value(trade_plan.get("stop_zone"))
    return _optional_float(stop_zone.get("aggressive"))


def _empty_result(
    account_risk_percent: float,
    max_loss_amount: float,
) -> dict[str, object]:
    return {
        **EMPTY_POSITION_SIZING,
        "account_risk_percent": account_risk_percent,
        "max_loss_amount": max_loss_amount,
    }


def _safe_risk_percent(value: object) -> float:
    risk_percent = _optional_float(value)
    if risk_percent is None or risk_percent < 0:
        return 0.0
    return round(risk_percent, 4)


def _dict_value(value: object) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _optional_float(value: object) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
