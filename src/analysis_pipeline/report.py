from __future__ import annotations

from dataclasses import dataclass, field

from src.analysis_pipeline.contracts import AnalysisResult


@dataclass(frozen=True)
class AnalysisReport:
    symbol: str
    timeframe: str
    snapshot_status: str
    probability_status: str
    prediction_status: str
    strategy_status: str
    backtest_status: str
    notes: list[str] = field(default_factory=list)


def build_analysis_report(result: AnalysisResult) -> AnalysisReport:
    return AnalysisReport(
        symbol=result.symbol,
        timeframe=result.timeframe,
        snapshot_status=_status(result.snapshot, "snapshot"),
        probability_status=_status(result.probability, "probability"),
        prediction_status=_status(result.prediction, "prediction"),
        strategy_status=_status(result.strategy, "strategy"),
        backtest_status=_backtest_status(result),
        notes=list(result.notes),
    )


def _status(value: object, label: str) -> str:
    if value:
        return f"{label}: available"
    return f"{label}: unavailable"


def _backtest_status(result: AnalysisResult) -> str:
    if result.backtest:
        report = result.backtest.get("report") if isinstance(result.backtest, dict) else None
        if isinstance(report, dict):
            attempted_trades = report.get("attempted_trades", 0)
            completed_trades = report.get("completed_trades", 0)
            return (
                "backtest: available "
                f"({attempted_trades} attempted, {completed_trades} completed)"
            )
        return "backtest: available"
    return "backtest: unavailable"
