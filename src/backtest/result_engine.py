from __future__ import annotations

from collections.abc import Iterable as IterableABC
from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class BacktestResultV1:
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    net_return_percent: float
    average_return: float
    max_drawdown: float
    profit_factor: float
    expectancy: float


def generate_backtest_result(
    trade_returns: Iterable[float | int | str | None] | None,
) -> BacktestResultV1:
    returns = [
        value
        for value in (
            _optional_float(trade_return)
            for trade_return in _safe_iterable(trade_returns)
        )
        if value is not None
    ]

    total_trades = len(returns)
    winning_returns = [value for value in returns if value > 0]
    losing_returns = [value for value in returns if value < 0]
    net_return = sum(returns)
    gross_profit = sum(winning_returns)
    gross_loss = abs(sum(losing_returns))

    return BacktestResultV1(
        total_trades=total_trades,
        winning_trades=len(winning_returns),
        losing_trades=len(losing_returns),
        win_rate=_percentage(len(winning_returns), total_trades),
        net_return_percent=round(net_return, 4),
        average_return=_average(returns),
        max_drawdown=_max_drawdown(returns),
        profit_factor=_profit_factor(gross_profit, gross_loss),
        expectancy=_expectancy(winning_returns, losing_returns, total_trades),
    )


def _percentage(numerator: int, denominator: int) -> float:
    if denominator <= 0:
        return 0.0
    return round((numerator / denominator) * 100, 4)


def _average(values: list[float]) -> float:
    if not values:
        return 0.0
    return round(sum(values) / len(values), 4)


def _max_drawdown(returns: list[float]) -> float:
    if not returns:
        return 0.0

    equity = 0.0
    peak = 0.0
    worst_drawdown = 0.0
    for trade_return in returns:
        equity += trade_return
        peak = max(peak, equity)
        worst_drawdown = min(worst_drawdown, equity - peak)
    return round(worst_drawdown, 4)


def _profit_factor(gross_profit: float, gross_loss: float) -> float:
    if gross_loss == 0:
        if gross_profit > 0:
            return float("inf")
        return 0.0
    return round(gross_profit / gross_loss, 4)


def _expectancy(
    winning_returns: list[float],
    losing_returns: list[float],
    total_trades: int,
) -> float:
    if total_trades <= 0:
        return 0.0

    win_rate = len(winning_returns) / total_trades
    loss_rate = len(losing_returns) / total_trades
    average_win = sum(winning_returns) / len(winning_returns) if winning_returns else 0.0
    average_loss = abs(sum(losing_returns) / len(losing_returns)) if losing_returns else 0.0
    return round((average_win * win_rate) - (average_loss * loss_rate), 4)


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
