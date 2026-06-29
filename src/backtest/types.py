from __future__ import annotations

from enum import StrEnum


class SimulationStatus(StrEnum):
    SUCCESS = "Success"
    SKIPPED = "Skipped"
    INSUFFICIENT_DATA = "Insufficient Data"


class TradeOutcome(StrEnum):
    WIN = "Win"
    LOSS = "Loss"
    BREAKEVEN = "Breakeven"
    OPEN = "Open"


class ExitReason(StrEnum):
    TARGET_HIT = "Target Hit"
    STOP_HIT = "Stop Hit"
    TIMEOUT = "Timeout"
    BREAKEVEN = "Breakeven"
    OPEN = "Open"
    INSUFFICIENT_DATA = "Insufficient Data"
