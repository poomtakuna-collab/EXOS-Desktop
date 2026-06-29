from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from src.strategy import StrategyResult
from src.backtest.types import ExitReason, SimulationStatus, TradeOutcome


@dataclass(frozen=True)
class BacktestInput:
    snapshot: dict[str, Any]
    probability: dict[str, Any]
    prediction: dict[str, Any]
    strategy_result: StrategyResult
    outcome: dict[str, Any]
    future_rows: list[dict[str, Any]] = field(default_factory=list)


@dataclass(frozen=True)
class SimulationConfig:
    horizon_days: int = 10
    entry_price_source: str = "snapshot_close"
    conservative_same_window_rule: bool = True


@dataclass(frozen=True)
class SimulationRule:
    name: str
    version: str
    config: SimulationConfig = field(default_factory=SimulationConfig)


@dataclass(frozen=True)
class SimulationResult:
    status: SimulationStatus
    trade_outcome: TradeOutcome
    exit_reason: ExitReason
    entry_price: float | None = None
    exit_price: float | None = None
    return_percent: float | None = None
    max_drawdown_percent: float | None = None
    notes: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class BacktestResult:
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    average_return: float
    average_drawdown: float
    expectancy: float
    max_drawdown: float
    notes: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class BacktestReport:
    summary: str
    total_trades: int
    win_rate: float
    average_return: float
    expectancy: float
    max_drawdown: float
    risk_comment: str
    quality_comment: str
    notes: list[str] = field(default_factory=list)
