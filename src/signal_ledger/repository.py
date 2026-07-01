from __future__ import annotations

from collections import defaultdict
from copy import deepcopy
from typing import Protocol

from src.outcome_tracking import OutcomeRecord
from src.signal_ledger.contracts import SignalRecord


class SignalLedgerRepository(Protocol):
    def save_signal(self, signal: SignalRecord) -> SignalRecord:
        """Save a signal record and return the stored record."""

    def load_signal(self, signal_id: str) -> SignalRecord | None:
        """Load a signal record by id."""

    def list_signals(
        self,
        *,
        symbol: str | None = None,
    ) -> tuple[SignalRecord, ...]:
        """List saved signal records, optionally filtered by symbol."""

    def save_outcome(self, signal_id: str, outcome: OutcomeRecord) -> OutcomeRecord:
        """Save an outcome associated with a signal id."""

    def list_outcomes_for_signal(self, signal_id: str) -> tuple[OutcomeRecord, ...]:
        """List outcomes associated with a signal id."""


class InMemorySignalLedgerRepository:
    def __init__(self) -> None:
        self._signals: dict[str, SignalRecord] = {}
        self._outcomes_by_signal_id: dict[str, list[OutcomeRecord]] = defaultdict(list)

    def save_signal(self, signal: SignalRecord) -> SignalRecord:
        signal_id = _required_id(signal.signal_id, "signal.signal_id")
        stored = _copy_signal(signal)
        self._signals[signal_id] = stored
        return stored

    def load_signal(self, signal_id: str) -> SignalRecord | None:
        stored = self._signals.get(signal_id)
        return _copy_signal(stored) if stored is not None else None

    def list_signals(
        self,
        *,
        symbol: str | None = None,
    ) -> tuple[SignalRecord, ...]:
        signals = tuple(self._signals.values())
        if symbol is not None:
            signals = tuple(signal for signal in signals if signal.symbol == symbol)
        return tuple(_copy_signal(signal) for signal in signals)

    def save_outcome(self, signal_id: str, outcome: OutcomeRecord) -> OutcomeRecord:
        safe_signal_id = _required_id(signal_id, "signal_id")
        stored = _copy_outcome(outcome)
        self._outcomes_by_signal_id[safe_signal_id].append(stored)
        return stored

    def list_outcomes_for_signal(self, signal_id: str) -> tuple[OutcomeRecord, ...]:
        outcomes = self._outcomes_by_signal_id.get(signal_id, [])
        return tuple(_copy_outcome(outcome) for outcome in outcomes)

    def to_dict(self) -> dict[str, object]:
        return {
            "signals": [
                signal.to_dict()
                for signal in self.list_signals()
            ],
            "outcomes_by_signal_id": {
                signal_id: [
                    outcome.to_dict()
                    for outcome in self.list_outcomes_for_signal(signal_id)
                ]
                for signal_id in sorted(self._outcomes_by_signal_id)
            },
        }


def _required_id(value: str, name: str) -> str:
    safe_value = str(value or "").strip()
    if not safe_value:
        raise ValueError(f"{name} is required")
    return safe_value


def _copy_signal(signal: SignalRecord) -> SignalRecord:
    return deepcopy(signal)


def _copy_outcome(outcome: OutcomeRecord) -> OutcomeRecord:
    return deepcopy(outcome)
