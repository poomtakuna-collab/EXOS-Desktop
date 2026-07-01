from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any, Protocol

from src.outcome_tracking.calculator import calculate_outcome_record
from src.outcome_tracking.contracts import OutcomeRecord
from src.outcome_tracking.repository import OutcomeRepository
from src.signal_ledger.contracts import SignalRecord


DEFAULT_OUTCOME_HORIZON_DAYS = 10


class SignalRepository(Protocol):
    def list_signals(
        self,
        *,
        symbol: str | None = None,
    ) -> tuple[SignalRecord, ...]:
        pass


@dataclass(frozen=True)
class OutcomeEvaluationSummary:
    evaluated: int = 0
    skipped_existing: int = 0
    skipped_insufficient_future_rows: int = 0
    skipped_unavailable_inputs: int = 0
    outcomes: tuple[OutcomeRecord, ...] = ()

    def to_dict(self) -> dict[str, object]:
        return {
            "evaluated": self.evaluated,
            "skipped_existing": self.skipped_existing,
            "skipped_insufficient_future_rows": self.skipped_insufficient_future_rows,
            "skipped_unavailable_inputs": self.skipped_unavailable_inputs,
            "outcomes": [outcome.to_dict() for outcome in self.outcomes],
        }


def evaluate_saved_signal_outcomes(
    *,
    signal_repository: SignalRepository,
    outcome_repository: OutcomeRepository,
    future_rows_by_signal_id: Mapping[str, Sequence[Mapping[str, Any]]],
    symbol: str | None = None,
    default_horizon_days: int = DEFAULT_OUTCOME_HORIZON_DAYS,
) -> OutcomeEvaluationSummary:
    evaluated: list[OutcomeRecord] = []
    skipped_existing = 0
    skipped_insufficient = 0
    skipped_unavailable = 0

    for signal in signal_repository.list_signals(symbol=symbol):
        if outcome_repository.list_outcomes_for_signal(signal.signal_id):
            skipped_existing += 1
            continue

        horizon = _horizon_days(signal, default_horizon_days)
        entry_price = _entry_price(signal)
        rows = _future_rows_after_signal_date(
            future_rows_by_signal_id.get(signal.signal_id, ()),
            signal.signal_date,
        )
        if horizon is None or entry_price is None:
            skipped_unavailable += 1
            continue
        if len(rows) < horizon:
            skipped_insufficient += 1
            continue

        outcome = calculate_outcome_record(
            symbol=signal.symbol,
            signal_date=signal.signal_date,
            entry_price=entry_price,
            future_rows=rows,
            horizon_days=horizon,
            target_price=_target_price(signal),
            stop_price=_stop_price(signal),
            notes=("evaluated from saved signal",),
        )
        saved = outcome_repository.save_outcome(signal.signal_id, outcome)
        evaluated.append(saved)

    return OutcomeEvaluationSummary(
        evaluated=len(evaluated),
        skipped_existing=skipped_existing,
        skipped_insufficient_future_rows=skipped_insufficient,
        skipped_unavailable_inputs=skipped_unavailable,
        outcomes=tuple(evaluated),
    )


def _future_rows_after_signal_date(
    rows: Sequence[Mapping[str, Any]],
    signal_date: str,
) -> tuple[Mapping[str, Any], ...]:
    safe_signal_date = str(signal_date or "")
    valid_rows = [
        row
        for row in rows
        if isinstance(row, Mapping)
        and str(row.get("date") or "") > safe_signal_date
    ]
    return tuple(sorted(valid_rows, key=lambda row: str(row.get("date") or "")))


def _horizon_days(signal: SignalRecord, default_horizon_days: int) -> int | None:
    return _positive_int(
        _first_value(
            signal.strategy_summary.get("horizon_days"),
            signal.strategy_summary.get("evaluation_horizon_days"),
            signal.strategy_summary.get("horizon"),
            default_horizon_days,
        )
    )


def _entry_price(signal: SignalRecord) -> float | None:
    return _positive_number(
        _first_value(
            signal.strategy_summary.get("entry_price"),
            signal.strategy_summary.get("entry"),
            signal.strategy_summary.get("current_price"),
        )
    )


def _target_price(signal: SignalRecord) -> float | None:
    return _positive_number(
        _first_value(
            signal.strategy_summary.get("target_price"),
            signal.strategy_summary.get("target"),
        )
    )


def _stop_price(signal: SignalRecord) -> float | None:
    return _positive_number(
        _first_value(
            signal.strategy_summary.get("stop_price"),
            signal.strategy_summary.get("stop"),
        )
    )


def _first_value(*values: object) -> object:
    for value in values:
        if value is not None and value != "":
            return value
    return None


def _positive_int(value: object) -> int | None:
    number = _positive_number(value)
    if number is None:
        return None
    return int(number)


def _positive_number(value: object) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if number > 0 else None
