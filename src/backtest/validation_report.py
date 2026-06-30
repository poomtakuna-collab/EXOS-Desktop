from __future__ import annotations

from dataclasses import dataclass

from src.backtest.backtest_runner import BacktestRunV1
from src.backtest.result_engine import BacktestResultV1, generate_backtest_result
from src.backtest.trade_outcome import TradeOutcomeV1


@dataclass(frozen=True)
class ValidationReportV1:
    summary: str
    performance_metrics: dict[str, float | int | str]
    risk_metrics: dict[str, float | int]
    trade_quality: dict[str, float | int]
    notes: list[str]


def build_validation_report(
    backtest_run: BacktestRunV1 | object | None,
) -> ValidationReportV1:
    trades = _trades(backtest_run)
    result = _result(backtest_run, trades)

    return ValidationReportV1(
        summary=_summary(result),
        performance_metrics=_performance_metrics(result),
        risk_metrics=_risk_metrics(trades, result),
        trade_quality=_trade_quality(trades),
        notes=_notes(backtest_run, trades),
    )


def _summary(result: BacktestResultV1) -> str:
    if result.total_trades <= 0:
        return "No completed trades available for validation."
    return (
        f"Validated {result.total_trades} trades: "
        f"{result.winning_trades} wins, {result.losing_trades} losses, "
        f"{round(result.win_rate, 2)}% win rate, "
        f"{round(result.net_return_percent, 2)}% net return."
    )


def _performance_metrics(result: BacktestResultV1) -> dict[str, float | int | str]:
    return {
        "total_trades": result.total_trades,
        "winning_trades": result.winning_trades,
        "losing_trades": result.losing_trades,
        "win_rate": result.win_rate,
        "net_return_percent": result.net_return_percent,
        "average_return": result.average_return,
        "max_drawdown": result.max_drawdown,
        "profit_factor": result.profit_factor,
        "expectancy": result.expectancy,
    }


def _risk_metrics(
    trades: list[TradeOutcomeV1],
    result: BacktestResultV1,
) -> dict[str, float | int]:
    total_risk_amount = sum(trade.risk_amount for trade in trades)
    total_reward_amount = sum(trade.reward_amount for trade in trades)
    return {
        "max_drawdown": result.max_drawdown,
        "total_risk_amount": round(total_risk_amount, 4),
        "average_risk_amount": _average([trade.risk_amount for trade in trades]),
        "total_reward_amount": round(total_reward_amount, 4),
        "average_reward_amount": _average([trade.reward_amount for trade in trades]),
    }


def _trade_quality(trades: list[TradeOutcomeV1]) -> dict[str, float | int]:
    total_trades = len(trades)
    invalid_trades = len(
        [trade for trade in trades if trade.outcome_label == "Invalid"]
    )
    breakeven_trades = len(
        [trade for trade in trades if trade.outcome_label == "Breakeven"]
    )
    return {
        "evaluated_trades": total_trades,
        "valid_trades": total_trades - invalid_trades,
        "invalid_trades": invalid_trades,
        "breakeven_trades": breakeven_trades,
        "average_gross_pnl": _average([trade.gross_pnl for trade in trades]),
    }


def _notes(backtest_run: object | None, trades: list[TradeOutcomeV1]) -> list[str]:
    if not isinstance(backtest_run, BacktestRunV1):
        return ["No valid BacktestRunV1 supplied."]
    if not trades:
        return ["BacktestRunV1 contained no trades."]
    return ["Validation report generated from BacktestRunV1."]


def _trades(backtest_run: object | None) -> list[TradeOutcomeV1]:
    if not isinstance(backtest_run, BacktestRunV1):
        return []
    return [
        trade
        for trade in backtest_run.trades
        if isinstance(trade, TradeOutcomeV1)
    ]


def _result(
    backtest_run: object | None,
    trades: list[TradeOutcomeV1],
) -> BacktestResultV1:
    if isinstance(backtest_run, BacktestRunV1) and isinstance(
        backtest_run.result,
        BacktestResultV1,
    ):
        return backtest_run.result
    return generate_backtest_result(trade.gross_return_percent for trade in trades)


def _average(values: list[float]) -> float:
    if not values:
        return 0.0
    return round(sum(values) / len(values), 4)
