from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass, field
from typing import Any

from src.analysis_pipeline.canonical_brain_adapter import (
    CanonicalBrainAdapterResult,
    build_canonical_brain_analysis,
)
from src.analysis_pipeline.contracts import AnalysisRequest, PipelineConfig
from src.backtest import (
    BacktestInput,
    BacktestPersistenceSummaryV1,
    BacktestReport,
    BacktestResult,
    BacktestRunV1,
    ValidationReportV1,
    build_backtest_report,
    build_validation_report,
    persist_backtest_run_v1,
    run_backtest,
    run_backtest_v1,
)
from src.data import MarketDataRow
from src.data_source import (
    FutureRowsRequest,
    MarketDataRequest,
    MarketDataSource,
)
from src.strategy import StrategyInput, StrategyResult, analyze_strategy


@dataclass(frozen=True)
class AnalysisPipelineV2Request:
    symbol: str
    config: PipelineConfig = field(default_factory=PipelineConfig)
    ohlcv_rows: list[MarketDataRow] = field(default_factory=list)
    future_rows: list[MarketDataRow] = field(default_factory=list)
    similar_patterns: list[dict[str, Any]] = field(default_factory=list)
    data_source: MarketDataSource | None = None
    start_date: str | None = None
    end_date: str | None = None
    limit: int | None = None
    persist_results: bool = False
    persistence_connection: Any | None = None
    run_id: str = ""
    run_name: str = ""


@dataclass(frozen=True)
class CanonicalAnalysisResultV2:
    request: AnalysisPipelineV2Request
    config: PipelineConfig
    symbol: str
    timeframe: str
    canonical_brain: CanonicalBrainAdapterResult
    strategy: StrategyResult | None = None
    backtest: BacktestResult | None = None
    backtest_report: BacktestReport | None = None
    backtest_run: BacktestRunV1 | None = None
    validation_report: ValidationReportV1 | None = None
    persistence: BacktestPersistenceSummaryV1 | None = None
    data_source_metadata: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)


def analyze_symbol_v2(request: AnalysisPipelineV2Request) -> CanonicalAnalysisResultV2:
    ohlcv_rows, market_metadata, market_notes = _load_ohlcv_rows(request)
    future_rows, future_metadata, future_notes = _load_future_rows(request, ohlcv_rows)
    normalized_request = AnalysisRequest(
        symbol=request.symbol,
        config=request.config,
        ohlcv_rows=ohlcv_rows,
        future_rows=future_rows,
        similar_patterns=request.similar_patterns,
    )
    canonical_brain = build_canonical_brain_analysis(normalized_request)
    strategy_result = _build_strategy(request, canonical_brain)
    backtest_result, backtest_report = _build_backtest(
        request=request,
        canonical_brain=canonical_brain,
        strategy_result=strategy_result,
        future_rows=future_rows,
        ohlcv_rows=ohlcv_rows,
    )
    backtest_run, validation_report = _build_validation(
        request=request,
        canonical_brain=canonical_brain,
        strategy_result=strategy_result,
        future_rows=future_rows,
        ohlcv_rows=ohlcv_rows,
    )
    persistence_summary, persistence_notes = _persist_v2_result(
        request=request,
        backtest_run=backtest_run,
        validation_report=validation_report,
        ohlcv_rows=ohlcv_rows,
        market_metadata=market_metadata,
        future_metadata=future_metadata,
    )

    notes = [
        "Analysis Pipeline v2 canonical orchestration.",
        *market_notes,
        *future_notes,
        *canonical_brain.notes,
        *persistence_notes,
    ]
    if request.config.include_strategy and strategy_result is None:
        notes.append("Strategy was skipped because canonical Brain output was incomplete.")
    if request.config.include_backtest and not future_rows:
        notes.append("Backtest and validation were skipped because no deterministic future rows were available.")

    return CanonicalAnalysisResultV2(
        request=request,
        config=request.config,
        symbol=request.symbol,
        timeframe=request.config.timeframe,
        canonical_brain=canonical_brain,
        strategy=strategy_result,
        backtest=backtest_result,
        backtest_report=backtest_report,
        backtest_run=backtest_run,
        validation_report=validation_report,
        persistence=persistence_summary,
        data_source_metadata={
            "market_data": market_metadata,
            "future_rows": future_metadata,
        },
        metadata={
            "entry_point": "analyze_symbol_v2",
            "result_type": "CanonicalAnalysisResultV2",
            "uses_adapter": "canonical_brain_adapter_v1",
            "persistence": "persisted" if persistence_summary is not None else "skipped",
            "rows": len(ohlcv_rows),
            "future_rows": len(future_rows),
            "similar_patterns": len(request.similar_patterns),
            "strategy_available": strategy_result is not None,
            "backtest_available": backtest_result is not None,
            "validation_available": validation_report is not None,
            "persistence_available": persistence_summary is not None,
        },
        notes=notes,
    )


def _load_ohlcv_rows(
    request: AnalysisPipelineV2Request,
) -> tuple[list[MarketDataRow], dict[str, Any], list[str]]:
    if request.ohlcv_rows:
        return (
            [dict(row) for row in request.ohlcv_rows],
            {"source": "provided_rows", "row_count": len(request.ohlcv_rows)},
            [],
        )
    if request.data_source is None:
        return (
            [],
            {"source": "none", "row_count": 0},
            ["No OHLCV rows or MarketDataSource supplied."],
        )

    result = request.data_source.load_ohlcv(
        MarketDataRequest(
            symbol=request.symbol,
            timeframe=request.config.timeframe,
            start_date=request.start_date,
            end_date=request.end_date,
            limit=request.limit,
        )
    )
    return [dict(row) for row in result.rows], dict(result.metadata), list(result.notes)


def _load_future_rows(
    request: AnalysisPipelineV2Request,
    ohlcv_rows: list[MarketDataRow],
) -> tuple[list[MarketDataRow], dict[str, Any], list[str]]:
    if request.future_rows:
        return (
            [dict(row) for row in request.future_rows],
            {"source": "provided_rows", "row_count": len(request.future_rows)},
            [],
        )
    if not request.config.include_backtest or request.data_source is None:
        return ([], {"source": "none", "row_count": 0}, [])

    snapshot_date = _snapshot_date(ohlcv_rows)
    if not snapshot_date:
        return (
            [],
            {"source": "none", "row_count": 0},
            ["Future rows were not loaded because snapshot date was unavailable."],
        )

    result = request.data_source.load_future_rows(
        FutureRowsRequest(
            symbol=request.symbol,
            snapshot_date=snapshot_date,
            timeframe=request.config.timeframe,
        )
    )
    return [dict(row) for row in result.rows], dict(result.metadata), list(result.notes)


def _build_strategy(
    request: AnalysisPipelineV2Request,
    canonical_brain: CanonicalBrainAdapterResult,
) -> StrategyResult | None:
    if not request.config.include_strategy:
        return None
    if not request.config.include_prediction:
        return None
    if not canonical_brain.snapshot or not canonical_brain.probability:
        return None

    prediction = _strategy_prediction(canonical_brain)
    if not prediction or not canonical_brain.projection:
        return None

    return analyze_strategy(
        StrategyInput(
            snapshot=canonical_brain.snapshot,
            probability=canonical_brain.probability,
            prediction=prediction,
        )
    )


def _build_backtest(
    request: AnalysisPipelineV2Request,
    canonical_brain: CanonicalBrainAdapterResult,
    strategy_result: StrategyResult | None,
    future_rows: list[MarketDataRow],
    ohlcv_rows: list[MarketDataRow],
) -> tuple[BacktestResult | None, BacktestReport | None]:
    if not request.config.include_backtest or strategy_result is None or not future_rows:
        return None, None

    result = run_backtest(
        [
            BacktestInput(
                snapshot={**canonical_brain.snapshot, "close": _latest_close(ohlcv_rows)},
                probability=canonical_brain.probability,
                prediction=_strategy_prediction(canonical_brain),
                strategy_result=strategy_result,
                outcome={},
                future_rows=future_rows,
            )
        ]
    )
    return result, build_backtest_report(result)


def _build_validation(
    request: AnalysisPipelineV2Request,
    canonical_brain: CanonicalBrainAdapterResult,
    strategy_result: StrategyResult | None,
    future_rows: list[MarketDataRow],
    ohlcv_rows: list[MarketDataRow],
) -> tuple[BacktestRunV1 | None, ValidationReportV1 | None]:
    if not request.config.include_backtest or strategy_result is None or not future_rows:
        return None, None

    run = run_backtest_v1(
        [
            {
                "trade_setup": _trade_setup(
                    canonical_brain=canonical_brain,
                    strategy_result=strategy_result,
                    ohlcv_rows=ohlcv_rows,
                ),
                "future_rows": future_rows,
            }
        ]
    )
    return run, build_validation_report(run)


def _persist_v2_result(
    request: AnalysisPipelineV2Request,
    backtest_run: BacktestRunV1 | None,
    validation_report: ValidationReportV1 | None,
    ohlcv_rows: list[MarketDataRow],
    market_metadata: dict[str, Any],
    future_metadata: dict[str, Any],
) -> tuple[BacktestPersistenceSummaryV1 | None, list[str]]:
    if not request.persist_results:
        return None, ["Persistence skipped because persist_results is False."]
    if not isinstance(request.persistence_connection, sqlite3.Connection):
        return None, ["Persistence skipped because no SQLite connection was supplied."]
    if not isinstance(backtest_run, BacktestRunV1):
        return None, ["Persistence skipped because BacktestRunV1 is unavailable."]
    if not isinstance(validation_report, ValidationReportV1):
        return None, ["Persistence skipped because ValidationReportV1 is unavailable."]

    summary = persist_backtest_run_v1(
        request.persistence_connection,
        backtest_run,
        validation_report,
        run_id=request.run_id or _default_run_id(request),
        run_name=request.run_name,
        symbols_json=json.dumps([request.symbol], sort_keys=True),
        timeframe=request.config.timeframe,
        start_date=request.start_date or _first_row_date(ohlcv_rows),
        end_date=request.end_date or _snapshot_date(ohlcv_rows),
        snapshot_query_json=_snapshot_query_json(
            request=request,
            ohlcv_rows=ohlcv_rows,
            market_metadata=market_metadata,
            future_metadata=future_metadata,
        ),
    )
    return summary, ["Persistence completed through Backtest Persistence v1."]


def _strategy_prediction(
    canonical_brain: CanonicalBrainAdapterResult,
) -> dict[str, Any]:
    projection = dict(canonical_brain.projection)
    prediction_summary = dict(canonical_brain.prediction_summary)
    target_zone = _zone_dict(canonical_brain.target_zone.get("target_zone"))
    risk_zone = _zone_dict(canonical_brain.risk_zone.get("risk_zone"))

    if prediction_summary:
        projection.setdefault("confidence", prediction_summary.get("confidence"))
        projection.setdefault("evidence_count", prediction_summary.get("evidence_count"))
        projection.setdefault("best_pattern_id", prediction_summary.get("best_pattern_id"))
        projection.setdefault("best_similarity", prediction_summary.get("best_similarity"))

    projection["expected_return"] = projection.get("expected_return_10d", 0.0)
    projection["target_zone_low"] = target_zone.get("conservative")
    projection["target_zone_high"] = target_zone.get("aggressive")
    projection["risk_zone_low"] = risk_zone.get("aggressive")
    projection["risk_zone_high"] = risk_zone.get("conservative")
    return projection


def _trade_setup(
    canonical_brain: CanonicalBrainAdapterResult,
    strategy_result: StrategyResult,
    ohlcv_rows: list[MarketDataRow],
) -> dict[str, object]:
    reward_risk = strategy_result.reward_risk_estimate
    target_zone = reward_risk.get("target_zone", {})
    risk_zone = reward_risk.get("risk_zone", {})
    return {
        "entry_price": _latest_close(ohlcv_rows),
        "stop_price": _first_positive_value(risk_zone, "low", "high"),
        "target_price": _first_positive_value(target_zone, "low", "high"),
        "position_size": 1.0,
        "snapshot_version": canonical_brain.snapshot.get("version", ""),
    }


def _snapshot_query_json(
    request: AnalysisPipelineV2Request,
    ohlcv_rows: list[MarketDataRow],
    market_metadata: dict[str, Any],
    future_metadata: dict[str, Any],
) -> str:
    return json.dumps(
        {
            "adapter": "canonical_brain_adapter_v1",
            "entry_point": "analyze_symbol_v2",
            "future_rows": int(future_metadata.get("row_count") or 0),
            "limit": request.limit,
            "market_data_source": market_metadata.get("source", ""),
            "rows": len(ohlcv_rows),
            "symbol": request.symbol,
            "timeframe": request.config.timeframe,
        },
        sort_keys=True,
    )


def _default_run_id(request: AnalysisPipelineV2Request) -> str:
    return f"analysis-pipeline-v2:{request.symbol}:{request.config.timeframe}"


def _first_row_date(ohlcv_rows: list[MarketDataRow]) -> str:
    if not ohlcv_rows:
        return ""
    return str(ohlcv_rows[0].get("date", ""))


def _zone_dict(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}


def _first_positive_value(values: object, *keys: str) -> float:
    value_dict = values if isinstance(values, dict) else {}
    for key in keys:
        number = _optional_float(value_dict.get(key))
        if number is not None and number > 0:
            return number
    return 0.0


def _snapshot_date(ohlcv_rows: list[MarketDataRow]) -> str:
    if not ohlcv_rows:
        return ""
    return str(ohlcv_rows[-1].get("date", ""))


def _latest_close(ohlcv_rows: list[MarketDataRow]) -> float:
    if not ohlcv_rows:
        return 0.0
    return _optional_float(ohlcv_rows[-1].get("close")) or 0.0


def _optional_float(value: object) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
