from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Protocol

from src.outcome_tracking import OutcomeRecord, OutcomeStatus
from src.signal_ledger import SignalRecord, SignalType


CONFIDENCE_BUCKETS = (
    "unknown",
    "0-20",
    "20-40",
    "40-60",
    "60-80",
    "80-100",
)


class SignalRecordRepository(Protocol):
    def list_signals(
        self,
        *,
        symbol: str | None = None,
    ) -> tuple[SignalRecord, ...]:
        """List saved signal records."""


class OutcomeRecordRepository(Protocol):
    def list_outcomes(
        self,
        *,
        symbol: str | None = None,
    ) -> tuple[OutcomeRecord, ...]:
        """List saved outcome records."""

    def list_outcomes_for_signal(self, signal_id: str) -> tuple[OutcomeRecord, ...]:
        """List saved outcome records linked to a signal id."""


@dataclass(frozen=True)
class PerformanceReport:
    total_signals: int = 0
    total_outcomes: int = 0
    completed_outcomes: int = 0
    pending_outcomes: int = 0
    outcome_coverage: float = 0.0
    duplicate_snapshots: int = 0
    last_snapshot_date: str = ""
    last_outcome_evaluation_date: str = ""
    win_rate: float = 0.0
    average_return: float = 0.0
    average_max_drawdown: float = 0.0
    outcome_status_distribution: dict[str, int] = field(default_factory=dict)
    signal_type_breakdown: dict[str, int] = field(default_factory=dict)
    confidence_bucket_breakdown: dict[str, int] = field(
        default_factory=lambda: {bucket: 0 for bucket in CONFIDENCE_BUCKETS}
    )

    def to_dict(self) -> dict[str, object]:
        return {
            "total_signals": self.total_signals,
            "total_outcomes": self.total_outcomes,
            "completed_outcomes": self.completed_outcomes,
            "pending_outcomes": self.pending_outcomes,
            "outcome_coverage": self.outcome_coverage,
            "duplicate_snapshots": self.duplicate_snapshots,
            "last_snapshot_date": self.last_snapshot_date,
            "last_outcome_evaluation_date": self.last_outcome_evaluation_date,
            "win_rate": self.win_rate,
            "average_return": self.average_return,
            "average_max_drawdown": self.average_max_drawdown,
            "outcome_status_distribution": dict(self.outcome_status_distribution),
            "signal_type_breakdown": dict(self.signal_type_breakdown),
            "confidence_bucket_breakdown": dict(self.confidence_bucket_breakdown),
        }


def build_performance_report(
    signal_repository: SignalRecordRepository,
    outcome_repository: OutcomeRecordRepository,
    *,
    symbol: str | None = None,
) -> PerformanceReport:
    safe_symbol = _symbol_filter(symbol)
    signals = tuple(signal_repository.list_signals(symbol=safe_symbol))
    outcomes = tuple(outcome_repository.list_outcomes(symbol=safe_symbol))

    return_values = [
        float(outcome.return_pct)
        for outcome in outcomes
        if outcome.return_pct is not None
    ]
    drawdown_values = [
        float(outcome.max_drawdown_pct)
        for outcome in outcomes
        if outcome.max_drawdown_pct is not None
    ]

    return PerformanceReport(
        total_signals=len(signals),
        total_outcomes=len(outcomes),
        completed_outcomes=len(outcomes),
        pending_outcomes=_pending_outcome_count(signals, outcome_repository),
        outcome_coverage=_outcome_coverage(signals, outcome_repository),
        duplicate_snapshots=_duplicate_snapshot_count(signals),
        last_snapshot_date=_last_snapshot_date(signals),
        last_outcome_evaluation_date=_last_outcome_evaluation_date(outcomes),
        win_rate=_percentage(_winning_outcome_count(outcomes), len(outcomes)),
        average_return=_average(return_values),
        average_max_drawdown=_average(drawdown_values),
        outcome_status_distribution=_outcome_status_distribution(outcomes),
        signal_type_breakdown=_signal_type_breakdown(signals),
        confidence_bucket_breakdown=_confidence_bucket_breakdown(signals),
    )


def _pending_outcome_count(
    signals: tuple[SignalRecord, ...],
    outcome_repository: OutcomeRecordRepository,
) -> int:
    return sum(
        1
        for signal in signals
        if not _linked_outcomes(signal, outcome_repository)
    )


def _outcome_coverage(
    signals: tuple[SignalRecord, ...],
    outcome_repository: OutcomeRecordRepository,
) -> float:
    completed = sum(
        1
        for signal in signals
        if _linked_outcomes(signal, outcome_repository)
    )
    return _percentage(completed, len(signals))


def _linked_outcomes(
    signal: SignalRecord,
    outcome_repository: OutcomeRecordRepository,
) -> tuple[OutcomeRecord, ...]:
    signal_id = str(signal.signal_id or "").strip()
    if not signal_id:
        return ()
    return tuple(outcome_repository.list_outcomes_for_signal(signal_id))


def _duplicate_snapshot_count(signals: tuple[SignalRecord, ...]) -> int:
    counts: dict[tuple[str, str], int] = {}
    for signal in signals:
        key = _snapshot_key(signal)
        if key is None:
            continue
        counts[key] = counts.get(key, 0) + 1
    return sum(count - 1 for count in counts.values() if count > 1)


def _snapshot_key(signal: SignalRecord) -> tuple[str, str] | None:
    symbol = str(signal.symbol or "").strip().upper()
    market_date = _snapshot_market_date(signal)
    if not symbol or not market_date:
        return None
    return symbol, market_date


def _snapshot_market_date(signal: SignalRecord) -> str:
    snapshot_date = str(signal.snapshot_reference.snapshot_date or "").strip()
    signal_date = str(signal.signal_date or "").strip()
    return snapshot_date or signal_date


def _last_snapshot_date(signals: tuple[SignalRecord, ...]) -> str:
    dates = sorted(
        date
        for date in (_snapshot_market_date(signal) for signal in signals)
        if date
    )
    return dates[-1] if dates else ""


def _last_outcome_evaluation_date(outcomes: tuple[OutcomeRecord, ...]) -> str:
    dates = sorted(
        str(outcome.evaluation_date or "").strip()
        for outcome in outcomes
        if str(outcome.evaluation_date or "").strip()
    )
    return dates[-1] if dates else ""


def _winning_outcome_count(outcomes: tuple[OutcomeRecord, ...]) -> int:
    return sum(1 for outcome in outcomes if _is_winning_outcome(outcome))


def _is_winning_outcome(outcome: OutcomeRecord) -> bool:
    if outcome.return_pct is not None:
        return float(outcome.return_pct) > 0.0
    return _outcome_status_value(outcome.outcome_status) in {
        OutcomeStatus.POSITIVE.value,
        OutcomeStatus.TARGET_HIT.value,
    }


def _outcome_status_distribution(
    outcomes: tuple[OutcomeRecord, ...],
) -> dict[str, int]:
    counts: dict[str, int] = {}
    for outcome in outcomes:
        status = _outcome_status_value(outcome.outcome_status)
        counts[status] = counts.get(status, 0) + 1
    return _sorted_counts(counts)


def _signal_type_breakdown(signals: tuple[SignalRecord, ...]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for signal in signals:
        signal_type = _signal_type_value(signal.signal_type)
        counts[signal_type] = counts.get(signal_type, 0) + 1
    return _sorted_counts(counts)


def _confidence_bucket_breakdown(
    signals: tuple[SignalRecord, ...],
) -> dict[str, int]:
    counts = {bucket: 0 for bucket in CONFIDENCE_BUCKETS}
    for signal in signals:
        counts[_confidence_bucket(signal.confidence)] += 1
    return counts


def _confidence_bucket(confidence: float | None) -> str:
    if confidence is None:
        return "unknown"
    value = _clamp(float(confidence), 0.0, 100.0)
    if value < 20.0:
        return "0-20"
    if value < 40.0:
        return "20-40"
    if value < 60.0:
        return "40-60"
    if value < 80.0:
        return "60-80"
    return "80-100"


def _percentage(numerator: int, denominator: int) -> float:
    if denominator <= 0:
        return 0.0
    return _rounded((numerator / denominator) * 100.0)


def _average(values: list[float]) -> float:
    if not values:
        return 0.0
    return _rounded(sum(values) / len(values))


def _rounded(value: float) -> float:
    return round(float(value), 4)


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def _sorted_counts(counts: dict[str, int]) -> dict[str, int]:
    return {key: counts[key] for key in sorted(counts)}


def _symbol_filter(symbol: str | None) -> str | None:
    safe_symbol = str(symbol or "").strip().upper()
    return safe_symbol or None


def _outcome_status_value(outcome_status: OutcomeStatus | str) -> str:
    if isinstance(outcome_status, OutcomeStatus):
        return outcome_status.value
    return str(outcome_status or OutcomeStatus.UNKNOWN.value)


def _signal_type_value(signal_type: SignalType | str) -> str:
    if isinstance(signal_type, SignalType):
        return signal_type.value
    return str(signal_type or SignalType.UNKNOWN.value)
