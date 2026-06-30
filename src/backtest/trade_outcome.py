from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


@dataclass(frozen=True)
class TradeOutcomeV1:
    entry_price: float
    exit_price: float
    stop_price: float
    target_price: float
    position_size: float
    gross_return_percent: float
    gross_pnl: float
    risk_amount: float
    reward_amount: float
    outcome_label: str


def generate_trade_outcome(
    trade_row: Mapping[str, object] | object | None,
) -> TradeOutcomeV1:
    row = trade_row if isinstance(trade_row, Mapping) else {}
    entry_price = _positive_float(row.get("entry_price"))
    exit_price = _positive_float(row.get("exit_price"))
    stop_price = _positive_float(row.get("stop_price"))
    target_price = _positive_float(row.get("target_price"))
    position_size = _non_negative_float(row.get("position_size"))

    gross_return_percent = _gross_return_percent(entry_price, exit_price)
    gross_pnl = _gross_pnl(entry_price, exit_price, position_size)

    return TradeOutcomeV1(
        entry_price=entry_price,
        exit_price=exit_price,
        stop_price=stop_price,
        target_price=target_price,
        position_size=position_size,
        gross_return_percent=gross_return_percent,
        gross_pnl=gross_pnl,
        risk_amount=_price_distance_amount(entry_price, stop_price, position_size),
        reward_amount=_price_distance_amount(entry_price, target_price, position_size),
        outcome_label=_outcome_label(entry_price, exit_price, gross_pnl),
    )


def _gross_return_percent(entry_price: float, exit_price: float) -> float:
    if entry_price <= 0 or exit_price <= 0:
        return 0.0
    return round(((exit_price - entry_price) / entry_price) * 100, 4)


def _gross_pnl(entry_price: float, exit_price: float, position_size: float) -> float:
    if entry_price <= 0 or exit_price <= 0 or position_size <= 0:
        return 0.0
    return round((exit_price - entry_price) * position_size, 4)


def _price_distance_amount(
    first_price: float,
    second_price: float,
    position_size: float,
) -> float:
    if first_price <= 0 or second_price <= 0 or position_size <= 0:
        return 0.0
    return round(abs(first_price - second_price) * position_size, 4)


def _outcome_label(entry_price: float, exit_price: float, gross_pnl: float) -> str:
    if entry_price <= 0 or exit_price <= 0:
        return "Invalid"
    if gross_pnl > 0:
        return "Win"
    if gross_pnl < 0:
        return "Loss"
    return "Breakeven"


def _positive_float(value: object) -> float:
    parsed_value = _optional_float(value)
    if parsed_value is None or parsed_value <= 0:
        return 0.0
    return parsed_value


def _non_negative_float(value: object) -> float:
    parsed_value = _optional_float(value)
    if parsed_value is None or parsed_value < 0:
        return 0.0
    return parsed_value


def _optional_float(value: object) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
