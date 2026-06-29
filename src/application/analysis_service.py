from __future__ import annotations

from dataclasses import dataclass, replace

from src.analysis_pipeline import (
    AnalysisRequest,
    AnalysisReport,
    AnalysisResult,
    PipelineConfig,
    analyze_symbol as run_analysis_pipeline,
    build_analysis_report,
)
from src.data_source import FutureRowsRequest, MarketDataRequest, MarketDataSource


@dataclass(frozen=True)
class AnalysisServiceResult:
    analysis_result: AnalysisResult
    analysis_report: AnalysisReport


class AnalysisService:
    def __init__(
        self,
        data_source: MarketDataSource,
        default_config: PipelineConfig | None = None,
    ) -> None:
        self._data_source = data_source
        self._default_config = default_config or PipelineConfig()

    def analyze_symbol(self, symbol: str, timeframe: str = "1D") -> AnalysisResult:
        config = replace(self._default_config, timeframe=timeframe)
        market_data = self._data_source.load_ohlcv(
            MarketDataRequest(symbol=symbol, timeframe=timeframe)
        )
        future_rows = self._load_future_rows(
            symbol=symbol,
            timeframe=timeframe,
            enabled=config.include_backtest,
            ohlcv_rows=market_data.rows,
        )

        request = AnalysisRequest(
            symbol=symbol,
            config=config,
            ohlcv_rows=market_data.rows,
            future_rows=future_rows,
        )
        return run_analysis_pipeline(request)

    def analyze_symbol_with_report(
        self,
        symbol: str,
        timeframe: str = "1D",
    ) -> AnalysisServiceResult:
        analysis_result = self.analyze_symbol(symbol=symbol, timeframe=timeframe)
        analysis_report = build_analysis_report(analysis_result)
        return AnalysisServiceResult(
            analysis_result=analysis_result,
            analysis_report=analysis_report,
        )

    def _load_future_rows(
        self,
        symbol: str,
        timeframe: str,
        enabled: bool,
        ohlcv_rows: list[dict[str, object]],
    ) -> list[dict[str, object]]:
        if not enabled or not ohlcv_rows:
            return []

        snapshot_date = str(ohlcv_rows[-1].get("date", ""))
        if not snapshot_date:
            return []

        try:
            result = self._data_source.load_future_rows(
                FutureRowsRequest(
                    symbol=symbol,
                    snapshot_date=snapshot_date,
                    timeframe=timeframe,
                )
            )
        except (AttributeError, NotImplementedError):
            return []

        return result.rows
