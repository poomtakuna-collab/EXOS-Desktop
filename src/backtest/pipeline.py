from __future__ import annotations

from src.backtest.contracts import BacktestInput, BacktestResult, SimulationConfig
from src.backtest.engine import replay_trade
from src.backtest.metrics import analyze_backtest_results


def run_backtest(
    backtest_inputs: list[BacktestInput],
    config: SimulationConfig | None = None,
) -> BacktestResult:
    simulation_results = [
        replay_trade(backtest_input, config)
        for backtest_input in backtest_inputs
    ]
    return analyze_backtest_results(simulation_results)
