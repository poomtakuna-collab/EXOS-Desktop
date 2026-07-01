from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, replace
from datetime import date
from typing import Any

from src.analysis_pipeline import AnalysisPipelineV2Request, PipelineConfig, analyze_symbol_v2
from src.canonical_result import (
    CanonicalIdentityV1,
    CanonicalResultV1,
    CanonicalSignalSummaryV1,
    build_canonical_result_v1,
)
from src.data_source import MarketDataRequest, MarketDataSource
from src.data_source.analysis_cutoff import (
    determine_analysis_cutoff_date,
    rows_through_analysis_cutoff,
)
from src.gui.research_signal_save import (
    ManualSignalSaveResult,
    SignalRepository,
    save_manual_signal_candidate,
    signal_exists_for_market_date,
)


DEFAULT_BACKFILL_TIMEFRAME = "1D"


@dataclass(frozen=True)
class SignalBackfillSummary:
    symbol: str
    chart_latest_date: str = ""
    analysis_cutoff_date: str = ""
    attempted: int = 0
    saved: int = 0
    skipped_existing: int = 0
    skipped_failed: int = 0
    saved_signal_ids: tuple[str, ...] = ()
    skipped_dates: tuple[str, ...] = ()
    errors: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, object]:
        return {
            "symbol": self.symbol,
            "chart_latest_date": self.chart_latest_date,
            "analysis_cutoff_date": self.analysis_cutoff_date,
            "attempted": self.attempted,
            "saved": self.saved,
            "skipped_existing": self.skipped_existing,
            "skipped_failed": self.skipped_failed,
            "saved_signal_ids": list(self.saved_signal_ids),
            "skipped_dates": list(self.skipped_dates),
            "errors": list(self.errors),
        }


def backfill_missing_research_signals(
    *,
    symbol: str,
    data_source: MarketDataSource,
    signal_repository: SignalRepository,
    row_limit: int | None = None,
    timeframe: str = DEFAULT_BACKFILL_TIMEFRAME,
    as_of_date: date | str | None = None,
) -> SignalBackfillSummary:
    normalized_symbol = str(symbol or "").strip().upper()
    if not normalized_symbol:
        return SignalBackfillSummary(symbol="")

    market_data = data_source.load_ohlcv(
        MarketDataRequest(
            symbol=normalized_symbol,
            timeframe=timeframe,
            limit=row_limit,
        )
    )
    loaded_rows = [dict(row) for row in market_data.rows if isinstance(row, Mapping)]
    cutoff = determine_analysis_cutoff_date(loaded_rows, as_of_date=as_of_date)
    eligible_rows = rows_through_analysis_cutoff(
        loaded_rows,
        cutoff.analysis_cutoff_date,
    )
    eligible_dates = _eligible_market_dates(eligible_rows)

    saved_ids: list[str] = []
    skipped_dates: list[str] = []
    errors: list[str] = []
    attempted = 0
    skipped_existing = 0
    skipped_failed = 0

    for market_date in eligible_dates:
        if signal_exists_for_market_date(
            signal_repository,
            symbol=normalized_symbol,
            market_date=market_date,
        ):
            skipped_existing += 1
            skipped_dates.append(market_date)
            continue

        attempted += 1
        analysis_rows = [
            dict(row)
            for row in eligible_rows
            if str(row.get("date") or "") <= market_date
        ]
        try:
            canonical_result = _canonical_result_for_market_date(
                symbol=normalized_symbol,
                timeframe=timeframe,
                market_date=market_date,
                rows=analysis_rows,
            )
            result = save_manual_signal_candidate(
                canonical_result,
                repository=signal_repository,
            )
        except (RuntimeError, ValueError, TypeError, KeyError) as error:
            skipped_failed += 1
            skipped_dates.append(market_date)
            errors.append(f"{market_date}: {error}")
            continue

        if result.saved and result.signal is not None:
            saved_ids.append(result.signal.signal_id)
        elif result.duplicate:
            skipped_existing += 1
            skipped_dates.append(market_date)
        else:
            skipped_failed += 1
            skipped_dates.append(market_date)
            errors.append(f"{market_date}: {result.message}")

    return SignalBackfillSummary(
        symbol=normalized_symbol,
        chart_latest_date=cutoff.chart_latest_date,
        analysis_cutoff_date=cutoff.analysis_cutoff_date,
        attempted=attempted,
        saved=len(saved_ids),
        skipped_existing=skipped_existing,
        skipped_failed=skipped_failed,
        saved_signal_ids=tuple(saved_ids),
        skipped_dates=tuple(skipped_dates),
        errors=tuple(errors),
    )


def _canonical_result_for_market_date(
    *,
    symbol: str,
    timeframe: str,
    market_date: str,
    rows: list[dict[str, Any]],
) -> CanonicalResultV1:
    analysis_result = analyze_symbol_v2(
        AnalysisPipelineV2Request(
            symbol=symbol,
            config=PipelineConfig(timeframe=timeframe, include_backtest=False),
            ohlcv_rows=rows,
        )
    )
    canonical = build_canonical_result_v1(analysis_result)
    prediction_summary = dict(canonical.brain.prediction_summary)
    return replace(
        canonical,
        identity=replace(
            canonical.identity
            if isinstance(canonical.identity, CanonicalIdentityV1)
            else CanonicalIdentityV1(),
            symbol=symbol,
            timeframe=timeframe,
            snapshot_date=market_date,
            analysis_date=market_date,
        ),
        signal_summary=CanonicalSignalSummaryV1(
            symbol=symbol,
            signal_date=market_date,
            timeframe=timeframe,
            signal_type="setup" if prediction_summary else "informational",
            confidence=_optional_float(prediction_summary.get("confidence")),
            snapshot_date=market_date,
            prediction_summary=prediction_summary,
            notes=("Backfilled research signal.",),
        ),
    )


def _eligible_market_dates(rows: list[dict[str, Any]]) -> tuple[str, ...]:
    return tuple(
        dict.fromkeys(
            str(row.get("date") or "").strip()
            for row in rows
            if str(row.get("date") or "").strip()
        )
    )


def _optional_float(value: object) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
