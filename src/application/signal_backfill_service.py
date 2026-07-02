from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass, replace
from datetime import UTC, date, datetime
from pathlib import Path
import traceback
from typing import Any

from src.analysis_pipeline import AnalysisPipelineV2Request, PipelineConfig, analyze_symbol_v2
from src.analysis.indicator_engine import calculate_indicator_snapshot
from src.canonical_result import (
    CanonicalBrainResultV1,
    CanonicalIdentityV1,
    CanonicalResultV1,
    CanonicalSignalSummaryV1,
    build_canonical_result_v1,
)
from src.context import (
    calculate_market_context,
    calculate_relative_strength_context,
    calculate_sector_context,
    calculate_support_resistance_context,
    calculate_volume_context,
)
from src.data_source import MarketDataRequest, MarketDataSource
from src.data_source.analysis_cutoff import (
    determine_analysis_cutoff_date,
    rows_through_analysis_cutoff,
)
from src.gui.research_signal_save import (
    DailyResearchSnapshotRepository,
    ManualSignalSaveResult,
    SignalRepository,
    save_manual_signal_candidate,
    signal_exists_for_market_date,
)


DEFAULT_BACKFILL_TIMEFRAME = "1D"
EVIDENCE_LOOP_LOG_PATH = Path("logs/evidence_loop.log")


class SignalBackfillSnapshotError(RuntimeError):
    def __init__(
        self,
        *,
        symbol: str,
        market_date: str,
        current: int,
        total: int,
        error: BaseException,
    ) -> None:
        self.symbol = symbol
        self.market_date = market_date
        self.current = current
        self.total = total
        self.original_error = error
        super().__init__(
            f"{symbol} {market_date} failed at snapshot {current} / {total}: {error}"
        )


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


@dataclass(frozen=True)
class SignalBackfillProgress:
    symbol: str
    current: int
    total: int
    market_date: str = ""

    def to_dict(self) -> dict[str, object]:
        return {
            "symbol": self.symbol,
            "current": self.current,
            "total": self.total,
            "market_date": self.market_date,
        }


def backfill_missing_research_signals(
    *,
    symbol: str,
    data_source: MarketDataSource,
    signal_repository: SignalRepository,
    snapshot_repository: DailyResearchSnapshotRepository | None = None,
    row_limit: int | None = None,
    timeframe: str = DEFAULT_BACKFILL_TIMEFRAME,
    as_of_date: date | str | None = None,
    progress_callback: Callable[[SignalBackfillProgress], None] | None = None,
    error_log_path: Path | str = EVIDENCE_LOOP_LOG_PATH,
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

    total_dates = len(eligible_dates)
    for index, market_date in enumerate(eligible_dates, start=1):
        _emit_progress(
            progress_callback,
            SignalBackfillProgress(
                symbol=normalized_symbol,
                current=index,
                total=total_dates,
                market_date=market_date,
            ),
        )
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
        analysis_request = _analysis_request_for_market_date(
            symbol=normalized_symbol,
            timeframe=timeframe,
            market_date=market_date,
            rows=analysis_rows,
        )
        try:
            canonical_result = _canonical_result_for_market_date(
                request=analysis_request,
            )
            snapshot_context = _snapshot_context(
                canonical_result=canonical_result,
                rows=analysis_rows,
            )
            result = save_manual_signal_candidate(
                canonical_result,
                repository=signal_repository,
                snapshot_repository=snapshot_repository,
                snapshot_request=analysis_request,
                snapshot_ohlcv_rows=analysis_rows,
                snapshot_provenance=_snapshot_provenance(
                    market_data_metadata=market_data.metadata,
                    cutoff=cutoff,
                    query=analysis_request,
                ),
                snapshot_context=snapshot_context,
                snapshot_created_at=datetime.now(UTC),
            )
        except Exception as error:
            _log_snapshot_exception(
                symbol=normalized_symbol,
                market_date=market_date,
                current=index,
                total=total_dates,
                error=error,
                log_path=error_log_path,
            )
            raise SignalBackfillSnapshotError(
                symbol=normalized_symbol,
                market_date=market_date,
                current=index,
                total=total_dates,
                error=error,
            ) from error

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


def _emit_progress(
    progress_callback: Callable[[SignalBackfillProgress], None] | None,
    progress: SignalBackfillProgress,
) -> None:
    if progress_callback is None:
        return
    try:
        progress_callback(progress)
    except Exception:
        return


def _log_snapshot_exception(
    *,
    symbol: str,
    market_date: str,
    current: int,
    total: int,
    error: BaseException,
    log_path: Path | str,
) -> None:
    path = Path(log_path)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(
                "\n"
                f"Evidence Loop snapshot failure: {symbol} {market_date} "
                f"({current} / {total})\n"
            )
            handle.writelines(
                traceback.format_exception(type(error), error, error.__traceback__)
            )
    except Exception:
        return


def _canonical_result_for_market_date(
    *,
    request: AnalysisPipelineV2Request,
) -> CanonicalResultV1:
    analysis_result = analyze_symbol_v2(request)
    canonical = build_canonical_result_v1(analysis_result)
    prediction_summary = dict(canonical.brain.prediction_summary)
    symbol = str(request.symbol or "").strip().upper()
    timeframe = str(request.config.timeframe or DEFAULT_BACKFILL_TIMEFRAME).strip()
    market_date = str(request.end_date or _last_row_date(request.ohlcv_rows) or "").strip()
    enriched = replace(
        canonical,
        brain=_brain_with_indicators(canonical.brain, request.ohlcv_rows),
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
    return enriched


def _brain_with_indicators(
    brain: CanonicalBrainResultV1,
    rows: list[dict[str, Any]],
) -> CanonicalBrainResultV1:
    indicators = calculate_indicator_snapshot(rows) or {}
    if not indicators:
        return brain
    snapshot = dict(brain.snapshot)
    snapshot["indicators"] = indicators
    return replace(brain, snapshot=snapshot)


def _analysis_request_for_market_date(
    *,
    symbol: str,
    timeframe: str,
    market_date: str,
    rows: list[dict[str, Any]],
) -> AnalysisPipelineV2Request:
    return AnalysisPipelineV2Request(
        symbol=symbol,
        config=PipelineConfig(timeframe=timeframe, include_backtest=False),
        ohlcv_rows=rows,
        start_date=_first_row_date(rows) or None,
        end_date=market_date,
        limit=len(rows),
    )


def _snapshot_provenance(
    *,
    market_data_metadata: Mapping[str, Any],
    cutoff: object,
    query: AnalysisPipelineV2Request,
) -> dict[str, Any]:
    return {
        "source": "manual_evidence_loop",
        "data_source": dict(market_data_metadata),
        "analysis_cutoff": {
            "chart_latest_date": str(getattr(cutoff, "chart_latest_date", "") or ""),
            "analysis_cutoff_date": str(
                getattr(cutoff, "analysis_cutoff_date", "") or ""
            ),
        },
        "query": {
            "symbol": query.symbol,
            "timeframe": query.config.timeframe,
            "start_date": query.start_date,
            "end_date": query.end_date,
            "limit": query.limit,
            "run_id": query.run_id,
            "run_name": query.run_name,
        },
    }


def _snapshot_context(
    *,
    canonical_result: CanonicalResultV1,
    rows: list[dict[str, Any]],
) -> dict[str, Any]:
    snapshot = dict(canonical_result.brain.snapshot)
    indicators = _dict_section(snapshot, "indicators")
    prediction = (
        canonical_result.prediction.to_dict()
        if canonical_result.prediction is not None
        else {}
    )
    return {
        "market": calculate_market_context(
            snapshot=snapshot,
            probability=canonical_result.brain.probability,
            prediction=prediction,
        ).to_dict(),
        "sector": calculate_sector_context(symbol_rows=rows).to_dict(),
        "relative_strength": calculate_relative_strength_context(
            symbol_rows=rows
        ).to_dict(),
        "volume": calculate_volume_context(
            snapshot=snapshot,
            indicators=indicators,
            price_rows=rows,
        ).to_dict(),
        "support_resistance": calculate_support_resistance_context(
            snapshot=snapshot,
            indicators=indicators,
            price_rows=rows,
        ).to_dict(),
    }


def _eligible_market_dates(rows: list[dict[str, Any]]) -> tuple[str, ...]:
    return tuple(
        dict.fromkeys(
            str(row.get("date") or "").strip()
            for row in rows
            if str(row.get("date") or "").strip()
        )
    )


def _dict_section(source: Mapping[str, Any], name: str) -> dict[str, Any]:
    value = source.get(name)
    return dict(value) if isinstance(value, Mapping) else {}


def _first_row_date(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return ""
    return str(rows[0].get("date") or "").strip()


def _last_row_date(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return ""
    return str(rows[-1].get("date") or "").strip()


def _optional_float(value: object) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
