from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class ContextRequest:
    symbol: str = ""
    market_symbol: str = "QQQ"
    sector_symbol: str | None = None
    industry_symbol: str | None = None
    lookback_days: int = 252

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class MarketContext:
    trend: str = "unknown"
    momentum: str = "unknown"
    volatility: str = "unknown"
    risk_state: str = "unknown"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SectorContext:
    sector_symbol: str | None = None
    trend: str = "unknown"
    relative_to_market: str = "unknown"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class RelativeStrengthContext:
    stock_vs_market: float | None = None
    stock_vs_sector: float | None = None
    rating: str = "unknown"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class VolumeContext:
    relative_volume: float | None = None
    volume_state: str = "unknown"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SupportResistanceContext:
    nearest_support: float | None = None
    nearest_resistance: float | None = None
    support_distance_pct: float | None = None
    resistance_distance_pct: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ContextResult:
    request: ContextRequest = field(default_factory=ContextRequest)
    market: MarketContext = field(default_factory=MarketContext)
    sector: SectorContext = field(default_factory=SectorContext)
    relative_strength: RelativeStrengthContext = field(
        default_factory=RelativeStrengthContext
    )
    volume: VolumeContext = field(default_factory=VolumeContext)
    support_resistance: SupportResistanceContext = field(
        default_factory=SupportResistanceContext
    )
    warnings: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["warnings"] = list(self.warnings)
        return result
