from __future__ import annotations

from typing import Any

from src.backtest.contracts import BacktestInput, SimulationConfig, SimulationResult
from src.backtest.types import ExitReason, SimulationStatus, TradeOutcome


def replay_trade(
    backtest_input: BacktestInput,
    config: SimulationConfig | None = None,
) -> SimulationResult:
    simulation_config = config or SimulationConfig()
    if simulation_config.horizon_days <= 0:
        return _insufficient_data_result("Simulation horizon must be greater than zero")

    entry_price = _entry_price(backtest_input)
    if entry_price is None or entry_price <= 0:
        return _insufficient_data_result("Entry price is missing or invalid")

    future_rows = backtest_input.future_rows
    if len(future_rows) < simulation_config.horizon_days:
        return _insufficient_data_result("Not enough future OHLCV rows")

    horizon_rows = future_rows[: simulation_config.horizon_days]
    target_price = _target_price(backtest_input)
    stop_price = _stop_price(backtest_input)
    lowest_low = entry_price

    for row in horizon_rows:
        high = _row_float(row, "high")
        low = _row_float(row, "low")
        if high is None or low is None:
            return _insufficient_data_result("Future OHLCV row is missing high or low")

        lowest_low = min(lowest_low, low)
        target_hit = target_price is not None and high >= target_price
        stop_hit = stop_price is not None and low <= stop_price

        if target_hit and stop_hit:
            if simulation_config.conservative_same_window_rule:
                return _exit_result(
                    entry_price=entry_price,
                    exit_price=stop_price,
                    lowest_low=lowest_low,
                    trade_outcome=TradeOutcome.LOSS,
                    exit_reason=ExitReason.STOP_HIT,
                    note="Target and stop hit in same candle; conservative stop outcome used",
                )
            return _exit_result(
                entry_price=entry_price,
                exit_price=target_price,
                lowest_low=lowest_low,
                trade_outcome=TradeOutcome.WIN,
                exit_reason=ExitReason.TARGET_HIT,
                note="Target and stop hit in same candle; target outcome used by config",
            )

        if stop_hit:
            return _exit_result(
                entry_price=entry_price,
                exit_price=stop_price,
                lowest_low=lowest_low,
                trade_outcome=TradeOutcome.LOSS,
                exit_reason=ExitReason.STOP_HIT,
                note="Stop/risk zone hit",
            )

        if target_hit:
            return _exit_result(
                entry_price=entry_price,
                exit_price=target_price,
                lowest_low=lowest_low,
                trade_outcome=TradeOutcome.WIN,
                exit_reason=ExitReason.TARGET_HIT,
                note="Target zone hit",
            )

    final_close = _row_float(horizon_rows[-1], "close")
    if final_close is None:
        return _insufficient_data_result("Final future OHLCV row is missing close")

    return_percent = _return_percent(entry_price, final_close)
    if return_percent > 0:
        trade_outcome = TradeOutcome.WIN
    elif return_percent < 0:
        trade_outcome = TradeOutcome.LOSS
    else:
        trade_outcome = TradeOutcome.BREAKEVEN

    return _exit_result(
        entry_price=entry_price,
        exit_price=final_close,
        lowest_low=lowest_low,
        trade_outcome=trade_outcome,
        exit_reason=(
            ExitReason.BREAKEVEN
            if trade_outcome == TradeOutcome.BREAKEVEN
            else ExitReason.TIMEOUT
        ),
        note="Simulation horizon reached without target or stop",
    )


def _entry_price(backtest_input: BacktestInput) -> float | None:
    strategy_entry_price = _strategy_reward_risk_float(
        backtest_input,
        "entry_price",
    )
    if strategy_entry_price is not None:
        return strategy_entry_price
    return _optional_float(backtest_input.snapshot.get("close"))


def _target_price(backtest_input: BacktestInput) -> float | None:
    target_zone = _zone(backtest_input, "target_zone")
    return _first_valid(target_zone.get("low"), target_zone.get("high"))


def _stop_price(backtest_input: BacktestInput) -> float | None:
    risk_zone = _zone(backtest_input, "risk_zone")
    return _first_valid(risk_zone.get("low"), risk_zone.get("high"))


def _zone(backtest_input: BacktestInput, key: str) -> dict[str, object]:
    reward_risk_estimate = backtest_input.strategy_result.reward_risk_estimate
    value = reward_risk_estimate.get(key)
    return value if isinstance(value, dict) else {}


def _strategy_reward_risk_float(
    backtest_input: BacktestInput,
    key: str,
) -> float | None:
    return _optional_float(backtest_input.strategy_result.reward_risk_estimate.get(key))


def _first_valid(*values: object) -> float | None:
    for value in values:
        number = _optional_float(value)
        if number is not None and number > 0:
            return number
    return None


def _row_float(row: dict[str, Any], key: str) -> float | None:
    return _optional_float(row.get(key))


def _exit_result(
    entry_price: float,
    exit_price: float | None,
    lowest_low: float,
    trade_outcome: TradeOutcome,
    exit_reason: ExitReason,
    note: str,
) -> SimulationResult:
    if exit_price is None:
        return _insufficient_data_result("Exit price is missing")

    return SimulationResult(
        status=SimulationStatus.SUCCESS,
        trade_outcome=trade_outcome,
        exit_reason=exit_reason,
        entry_price=round(entry_price, 4),
        exit_price=round(exit_price, 4),
        return_percent=_return_percent(entry_price, exit_price),
        max_drawdown_percent=_return_percent(entry_price, lowest_low),
        notes=[note],
    )


def _insufficient_data_result(note: str) -> SimulationResult:
    return SimulationResult(
        status=SimulationStatus.INSUFFICIENT_DATA,
        trade_outcome=TradeOutcome.OPEN,
        exit_reason=ExitReason.INSUFFICIENT_DATA,
        notes=[note],
    )


def _return_percent(start_price: float, end_price: float) -> float:
    return round(((end_price - start_price) / start_price) * 100, 4)


def _optional_float(value: object) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
