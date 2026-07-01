from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import date
from typing import Any

from src.application.signal_backfill_service import (
    SignalBackfillSummary,
    backfill_missing_research_signals,
)
from src.data_source import MarketDataRequest, MarketDataSource
from src.outcome_tracking import OutcomeEvaluationSummary, evaluate_saved_signal_outcomes
from src.outcome_tracking.repository import OutcomeRepository
from src.signal_ledger.contracts import SignalRecord
from src.signal_ledger.repository import SignalLedgerRepository


@dataclass(frozen=True)
class ManualEvidenceLoopSummary:
    symbol: str
    backfill: SignalBackfillSummary
    outcome_evaluation: OutcomeEvaluationSummary

    @property
    def signals_created(self) -> int:
        return self.backfill.saved

    @property
    def outcomes_evaluated(self) -> int:
        return self.outcome_evaluation.evaluated

    def to_dict(self) -> dict[str, object]:
        return {
            "symbol": self.symbol,
            "signals_created": self.signals_created,
            "outcomes_evaluated": self.outcomes_evaluated,
            "backfill": self.backfill.to_dict(),
            "outcome_evaluation": self.outcome_evaluation.to_dict(),
        }


def run_manual_evidence_loop(
    *,
    symbol: str,
    data_source: MarketDataSource,
    signal_repository: SignalLedgerRepository,
    outcome_repository: OutcomeRepository,
    row_limit: int | None = None,
    timeframe: str = "1D",
    as_of_date: date | str | None = None,
    default_horizon_days: int = 10,
    future_rows_by_signal_id: Mapping[str, Sequence[Mapping[str, Any]]] | None = None,
) -> ManualEvidenceLoopSummary:
    normalized_symbol = str(symbol or "").strip().upper()
    backfill_summary = backfill_missing_research_signals(
        symbol=normalized_symbol,
        data_source=data_source,
        signal_repository=signal_repository,
        row_limit=row_limit,
        timeframe=timeframe,
        as_of_date=as_of_date,
    )
    future_rows = future_rows_by_signal_id or _future_rows_by_signal_id(
        symbol=normalized_symbol,
        data_source=data_source,
        signal_repository=signal_repository,
        row_limit=row_limit,
        timeframe=timeframe,
    )
    outcome_summary = evaluate_saved_signal_outcomes(
        signal_repository=signal_repository,
        outcome_repository=outcome_repository,
        future_rows_by_signal_id=future_rows,
        symbol=normalized_symbol or None,
        default_horizon_days=default_horizon_days,
    )
    return ManualEvidenceLoopSummary(
        symbol=normalized_symbol,
        backfill=backfill_summary,
        outcome_evaluation=outcome_summary,
    )


def _future_rows_by_signal_id(
    *,
    symbol: str,
    data_source: MarketDataSource,
    signal_repository: SignalLedgerRepository,
    row_limit: int | None,
    timeframe: str,
) -> dict[str, list[dict[str, Any]]]:
    market_data = data_source.load_ohlcv(
        MarketDataRequest(
            symbol=symbol,
            timeframe=timeframe,
            limit=row_limit,
        )
    )
    rows = [dict(row) for row in market_data.rows if isinstance(row, Mapping)]
    return {
        signal.signal_id: rows
        for signal in signal_repository.list_signals(symbol=symbol)
        if _has_signal_id(signal)
    }


def _has_signal_id(signal: SignalRecord) -> bool:
    return bool(str(signal.signal_id or "").strip())
