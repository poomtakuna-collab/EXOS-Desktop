from __future__ import annotations

from collections.abc import Iterable as IterableABC
from typing import Iterable, Mapping

from src.backtest.trade_outcome import TradeOutcomeV1, generate_trade_outcome


def simulate_trade(
    trade_setup: Mapping[str, object] | object | None,
    future_rows: Iterable[Mapping[str, object] | None] | object | None,
) -> TradeOutcomeV1:
    setup = trade_setup if isinstance(trade_setup, Mapping) else {}
    entry_price = _positive_float(setup.get("entry_price"))
    stop_price = _positive_float(setup.get("stop_price"))
    target_price = _positive_float(setup.get("target_price"))
    position_size = _non_negative_float(setup.get("position_size"))

    if entry_price <= 0:
        return _trade_outcome(
            entry_price=entry_price,
            exit_price=0.0,
            stop_price=stop_price,
            target_price=target_price,
            position_size=position_size,
        )

    final_close = 0.0
    for row in _safe_iterable(future_rows):
        normalized_row = row if isinstance(row, Mapping) else {}
        high = _positive_float(normalized_row.get("high"))
        low = _positive_float(normalized_row.get("low"))
        close = _positive_float(normalized_row.get("close"))
        if close > 0:
            final_close = close

        stop_hit = stop_price > 0 and low > 0 and low <= stop_price
        target_hit = target_price > 0 and high >= target_price

        if stop_hit:
            return _trade_outcome(
                entry_price=entry_price,
                exit_price=stop_price,
                stop_price=stop_price,
                target_price=target_price,
                position_size=position_size,
            )
        if target_hit:
            return _trade_outcome(
                entry_price=entry_price,
                exit_price=target_price,
                stop_price=stop_price,
                target_price=target_price,
                position_size=position_size,
            )

    return _trade_outcome(
        entry_price=entry_price,
        exit_price=final_close,
        stop_price=stop_price,
        target_price=target_price,
        position_size=position_size,
    )


def _trade_outcome(
    entry_price: float,
    exit_price: float,
    stop_price: float,
    target_price: float,
    position_size: float,
) -> TradeOutcomeV1:
    return generate_trade_outcome(
        {
            "entry_price": entry_price,
            "exit_price": exit_price,
            "stop_price": stop_price,
            "target_price": target_price,
            "position_size": position_size,
        }
    )


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


def _safe_iterable(value: object) -> IterableABC[object]:
    if isinstance(value, IterableABC):
        return value
    return []
