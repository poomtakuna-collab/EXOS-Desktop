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


@dataclass(frozen=True)
class PerformanceReport:
    total_signals: int = 0
    total_outcomes: int = 0
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
        win_rate=_percentage(_winning_outcome_count(outcomes), len(outcomes)),
        average_return=_average(return_values),
        average_max_drawdown=_average(drawdown_values),
        outcome_status_distribution=_outcome_status_distribution(outcomes),
        signal_type_breakdown=_signal_type_breakdown(signals),
        confidence_bucket_breakdown=_confidence_bucket_breakdown(signals),
    )


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
