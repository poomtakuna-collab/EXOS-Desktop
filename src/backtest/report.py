from __future__ import annotations

from src.backtest.contracts import BacktestReport, BacktestResult


def build_backtest_report(backtest_result: BacktestResult) -> BacktestReport:
    return BacktestReport(
        summary=_summary(backtest_result),
        total_trades=backtest_result.total_trades,
        win_rate=round(backtest_result.win_rate, 4),
        average_return=round(backtest_result.average_return, 4),
        expectancy=round(backtest_result.expectancy, 4),
        max_drawdown=round(backtest_result.max_drawdown, 4),
        risk_comment=_risk_comment(backtest_result),
        quality_comment=_quality_comment(backtest_result),
        notes=list(backtest_result.notes),
    )


def _summary(backtest_result: BacktestResult) -> str:
    if backtest_result.total_trades <= 0:
        return "No completed backtest trades available."

    return (
        f"{backtest_result.total_trades} completed trades, "
        f"{round(backtest_result.win_rate, 2)}% win rate, "
        f"{round(backtest_result.average_return, 2)}% average return."
    )


def _risk_comment(backtest_result: BacktestResult) -> str:
    max_drawdown = backtest_result.max_drawdown
    if backtest_result.total_trades <= 0:
        return "Risk unavailable because no completed trades were evaluated."
    if max_drawdown <= -15:
        return "High drawdown risk observed."
    if max_drawdown <= -7:
        return "Moderate drawdown risk observed."
    return "Drawdown risk was limited in this backtest sample."


def _quality_comment(backtest_result: BacktestResult) -> str:
    if backtest_result.total_trades <= 0:
        return "Quality unavailable because no completed trades were evaluated."
    if backtest_result.win_rate >= 60 and backtest_result.expectancy > 0:
        return "Backtest quality is strong for this sample."
    if backtest_result.win_rate >= 45 and backtest_result.expectancy >= 0:
        return "Backtest quality is mixed but constructive for this sample."
    return "Backtest quality is weak for this sample."
