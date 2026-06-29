from __future__ import annotations

from src.backtest.contracts import BacktestResult, SimulationResult
from src.backtest.types import SimulationStatus, TradeOutcome


def analyze_backtest_results(
    simulation_results: list[SimulationResult],
) -> BacktestResult:
    completed_results = [
        result
        for result in simulation_results
        if result.status == SimulationStatus.SUCCESS
    ]
    winning_results = [
        result
        for result in completed_results
        if result.trade_outcome == TradeOutcome.WIN
    ]
    losing_results = [
        result
        for result in completed_results
        if result.trade_outcome == TradeOutcome.LOSS
    ]
    breakeven_results = [
        result
        for result in completed_results
        if result.trade_outcome == TradeOutcome.BREAKEVEN
    ]
    skipped_count = len(simulation_results) - len(completed_results)
    win_loss_count = len(winning_results) + len(losing_results)
    returns = [
        value
        for value in (_optional_float(result.return_percent) for result in completed_results)
        if value is not None
    ]
    drawdowns = [
        value
        for value in (
            _optional_float(result.max_drawdown_percent)
            for result in completed_results
        )
        if value is not None
    ]

    notes = [
        f"Completed simulations: {len(completed_results)}",
        f"Skipped / insufficient-data simulations: {skipped_count}",
        f"Breakeven simulations: {len(breakeven_results)}",
    ]
    if not simulation_results:
        notes.append("No simulation results supplied")

    return BacktestResult(
        total_trades=len(completed_results),
        winning_trades=len(winning_results),
        losing_trades=len(losing_results),
        win_rate=_percentage(len(winning_results), win_loss_count),
        average_return=_average(returns),
        average_drawdown=_average(drawdowns),
        expectancy=_average(returns),
        max_drawdown=min(drawdowns) if drawdowns else 0.0,
        notes=notes,
    )


def _percentage(numerator: int, denominator: int) -> float:
    if denominator <= 0:
        return 0.0
    return round((numerator / denominator) * 100, 4)


def _average(values: list[float]) -> float:
    if not values:
        return 0.0
    return round(sum(values) / len(values), 4)


def _optional_float(value: object) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
