from __future__ import annotations

from dataclasses import asdict, is_dataclass
from enum import Enum
from typing import Any

from src.analysis.snapshot_builder import build_exos_snapshot
from src.analysis_pipeline.contracts import AnalysisRequest, AnalysisResult
from src.backtest import BacktestInput, build_backtest_report, run_backtest
from src.statistics import build_prediction, calculate_probability_from_matches
from src.strategy import StrategyInput, analyze_strategy
from src.strategy.contracts import StrategyResult


def analyze_symbol(request: AnalysisRequest) -> AnalysisResult:
    if not request.ohlcv_rows:
        raise NotImplementedError(
            "Analysis Pipeline snapshot loading is not implemented yet; "
            "provide OHLCV rows on the request."
        )

    snapshot = build_exos_snapshot(
        request.ohlcv_rows,
        symbol=request.symbol,
        timeframe=request.config.timeframe,
    )
    probability = _build_probability(request)
    prediction = _build_prediction(request, probability)
    strategy_result = _build_strategy(request, snapshot, probability, prediction)
    backtest = _build_backtest(
        request=request,
        snapshot=snapshot,
        probability=probability,
        prediction=prediction,
        strategy_result=strategy_result,
    )

    return AnalysisResult(
        request=request,
        config=request.config,
        symbol=request.symbol,
        timeframe=request.config.timeframe,
        snapshot=snapshot,
        probability=probability,
        prediction=prediction,
        strategy=_serialize(strategy_result) if strategy_result else None,
        backtest=backtest,
        metadata={
            "pipeline_step": "snapshot_probability_prediction_strategy_backtest",
            "rows": len(request.ohlcv_rows),
            "future_rows": len(request.future_rows),
            "similar_patterns": len(request.similar_patterns),
        },
        notes=[
            "Analysis Pipeline step 4: snapshot, probability, prediction, strategy, and request-row backtest."
        ],
    )


def _build_probability(request: AnalysisRequest) -> dict[str, object]:
    if not request.config.include_probability:
        return {}
    return calculate_probability_from_matches(request.similar_patterns)


def _build_prediction(
    request: AnalysisRequest,
    probability: dict[str, object],
) -> dict[str, object]:
    if not request.config.include_prediction or not probability:
        return {}
    return build_prediction(probability, _latest_close(request))


def _build_strategy(
    request: AnalysisRequest,
    snapshot: dict[str, object],
    probability: dict[str, object],
    prediction: dict[str, object],
) -> StrategyResult | None:
    if not request.config.include_strategy or not probability or not prediction:
        return None
    return analyze_strategy(
        StrategyInput(
            snapshot=snapshot,
            probability=probability,
            prediction=prediction,
        )
    )


def _build_backtest(
    request: AnalysisRequest,
    snapshot: dict[str, object],
    probability: dict[str, object],
    prediction: dict[str, object],
    strategy_result: StrategyResult | None,
) -> dict[str, object] | None:
    if (
        not request.config.include_backtest
        or not request.future_rows
        or strategy_result is None
    ):
        return None

    backtest_result = run_backtest(
        [
            BacktestInput(
                snapshot={**snapshot, "close": _latest_close(request)},
                probability=probability,
                prediction=prediction,
                strategy_result=strategy_result,
                outcome={},
                future_rows=request.future_rows,
            )
        ]
    )
    backtest_report = build_backtest_report(backtest_result)
    return {
        "result": _serialize(backtest_result),
        "report": _serialize(backtest_report),
    }


def _latest_close(request: AnalysisRequest) -> float:
    return float(request.ohlcv_rows[-1]["close"])


def _serialize(value: Any) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return _serialize(asdict(value))
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, dict):
        return {key: _serialize(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_serialize(item) for item in value]
    return value
