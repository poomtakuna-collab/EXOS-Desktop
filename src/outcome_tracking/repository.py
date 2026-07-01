from __future__ import annotations

from collections import defaultdict
from copy import deepcopy
from typing import Protocol

from src.outcome_tracking.contracts import OutcomeRecord


class OutcomeRepository(Protocol):
    def save_outcome(
        self,
        signal_id: str,
        outcome: OutcomeRecord,
        *,
        outcome_id: str | None = None,
    ) -> OutcomeRecord:
        """Save an outcome associated with a signal id."""

    def load_outcome(self, outcome_id: str) -> OutcomeRecord | None:
        """Load an outcome by repository outcome id."""

    def list_outcomes(
        self,
        *,
        symbol: str | None = None,
    ) -> tuple[OutcomeRecord, ...]:
        """List saved outcomes, optionally filtered by symbol."""

    def list_outcomes_for_signal(self, signal_id: str) -> tuple[OutcomeRecord, ...]:
        """List outcomes associated with a signal id."""


class InMemoryOutcomeRepository:
    def __init__(self) -> None:
        self._outcomes_by_id: dict[str, OutcomeRecord] = {}
        self._signal_ids_by_outcome_id: dict[str, str] = {}
        self._outcome_ids_by_signal_id: dict[str, list[str]] = defaultdict(list)
        self._next_outcome_number = 1

    def save_outcome(
        self,
        signal_id: str,
        outcome: OutcomeRecord,
        *,
        outcome_id: str | None = None,
    ) -> OutcomeRecord:
        safe_signal_id = _required_id(signal_id, "signal_id")
        safe_outcome_id = _outcome_id(outcome_id, self._next_outcome_number)
        if outcome_id is None:
            self._next_outcome_number += 1

        previous_signal_id = self._signal_ids_by_outcome_id.get(safe_outcome_id)
        if previous_signal_id and previous_signal_id != safe_signal_id:
            self._outcome_ids_by_signal_id[previous_signal_id] = [
                stored_id
                for stored_id in self._outcome_ids_by_signal_id[previous_signal_id]
                if stored_id != safe_outcome_id
            ]
        if safe_outcome_id not in self._outcome_ids_by_signal_id[safe_signal_id]:
            self._outcome_ids_by_signal_id[safe_signal_id].append(safe_outcome_id)

        stored = _copy_outcome(outcome)
        self._outcomes_by_id[safe_outcome_id] = stored
        self._signal_ids_by_outcome_id[safe_outcome_id] = safe_signal_id
        return _copy_outcome(stored)

    def load_outcome(self, outcome_id: str) -> OutcomeRecord | None:
        stored = self._outcomes_by_id.get(str(outcome_id or ""))
        return _copy_outcome(stored) if stored is not None else None

    def list_outcomes(
        self,
        *,
        symbol: str | None = None,
    ) -> tuple[OutcomeRecord, ...]:
        outcomes = tuple(self._outcomes_by_id.values())
        if symbol is not None:
            outcomes = tuple(outcome for outcome in outcomes if outcome.symbol == symbol)
        return tuple(_copy_outcome(outcome) for outcome in outcomes)

    def list_outcomes_for_signal(self, signal_id: str) -> tuple[OutcomeRecord, ...]:
        outcome_ids = self._outcome_ids_by_signal_id.get(signal_id, [])
        return tuple(
            _copy_outcome(self._outcomes_by_id[outcome_id])
            for outcome_id in outcome_ids
            if outcome_id in self._outcomes_by_id
        )


def _required_id(value: str, name: str) -> str:
    safe_value = str(value or "").strip()
    if not safe_value:
        raise ValueError(f"{name} is required")
    return safe_value


def _outcome_id(value: str | None, next_outcome_number: int) -> str:
    if value is None:
        return str(next_outcome_number)
    return _required_id(value, "outcome_id")


def _copy_outcome(outcome: OutcomeRecord) -> OutcomeRecord:
    return deepcopy(outcome)
