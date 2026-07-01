from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
from typing import Any


class OutcomeStatus(str, Enum):
    UNKNOWN = "unknown"
    OPEN = "open"
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"
    TARGET_HIT = "target_hit"
    STOP_HIT = "stop_hit"


@dataclass(frozen=True)
class OutcomeRecord:
    symbol: str = ""
    signal_date: str = ""
    evaluation_date: str = ""
    horizon_days: int | None = None
    entry_price: float | None = None
    close_price: float | None = None
    return_pct: float | None = None
    max_runup_pct: float | None = None
    max_drawdown_pct: float | None = None
    hit_target: bool | None = None
    hit_stop: bool | None = None
    outcome_status: OutcomeStatus | str = OutcomeStatus.UNKNOWN
    notes: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["outcome_status"] = _outcome_status_value(self.outcome_status)
        result["notes"] = list(self.notes)
        return result


def _outcome_status_value(outcome_status: OutcomeStatus | str) -> str:
    if isinstance(outcome_status, OutcomeStatus):
        return outcome_status.value
    return str(outcome_status or OutcomeStatus.UNKNOWN.value)
