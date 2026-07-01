from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any


class SignalType(str, Enum):
    UNKNOWN = "unknown"
    WATCH = "watch"
    SETUP = "setup"
    BREAKOUT = "breakout"
    RISK = "risk"
    INVALIDATION = "invalidation"
    INFORMATIONAL = "informational"


@dataclass(frozen=True)
class SignalSnapshotReference:
    snapshot_id: str = ""
    snapshot_date: str = ""
    timeframe: str = ""
    source: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SignalRecord:
    signal_id: str = ""
    symbol: str = ""
    signal_date: str = ""
    snapshot_reference: SignalSnapshotReference = field(
        default_factory=SignalSnapshotReference
    )
    context_summary: dict[str, Any] = field(default_factory=dict)
    strategy_summary: dict[str, Any] = field(default_factory=dict)
    signal_type: SignalType | str = SignalType.UNKNOWN
    confidence: float | None = None
    notes: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["signal_type"] = _signal_type_value(self.signal_type)
        result["notes"] = list(self.notes)
        return result


def _signal_type_value(signal_type: SignalType | str) -> str:
    if isinstance(signal_type, SignalType):
        return signal_type.value
    return str(signal_type or SignalType.UNKNOWN.value)
