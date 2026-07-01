from __future__ import annotations

from dataclasses import dataclass, field, fields, is_dataclass
from typing import Any


CANONICAL_RESULT_SCHEMA_VERSION_V1 = "canonical_result_v1"


@dataclass(frozen=True)
class CanonicalIdentityV1:
    symbol: str = ""
    timeframe: str = ""
    snapshot_id: str = ""
    snapshot_date: str = ""
    analysis_date: str = ""
    source: str = ""
    pipeline_name: str = ""
    pipeline_version: str = ""
    run_id: str = ""

    def to_dict(self) -> dict[str, Any]:
        return _to_plain_dict(self)


@dataclass(frozen=True)
class CanonicalBrainResultV1:
    snapshot: dict[str, Any] = field(default_factory=dict)
    resolver_output: dict[str, Any] = field(default_factory=dict)
    probability: dict[str, Any] = field(default_factory=dict)
    projection: dict[str, Any] = field(default_factory=dict)
    target_zone: dict[str, Any] = field(default_factory=dict)
    risk_zone: dict[str, Any] = field(default_factory=dict)
    prediction_summary: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    notes: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return _to_plain_dict(self)


@dataclass(frozen=True)
class CanonicalPredictionResultV1:
    confidence: float = 0.0
    evidence_count: int = 0
    probability_positive: float | None = None
    probability_negative: float | None = None
    probability_neutral: float | None = None
    expected_return_5d: float | None = None
    expected_return_10d: float | None = None
    expected_return_20d: float | None = None
    expected_price_5d: float | None = None
    expected_price_10d: float | None = None
    expected_price_20d: float | None = None
    target_conservative: float | None = None
    target_base: float | None = None
    target_aggressive: float | None = None
    risk_conservative: float | None = None
    risk_base: float | None = None
    risk_aggressive: float | None = None
    best_pattern_id: str | None = None
    best_similarity: float | None = None
    notes: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return _to_plain_dict(self)


@dataclass(frozen=True)
class CanonicalContextResultV1:
    market: dict[str, Any] = field(default_factory=dict)
    sector: dict[str, Any] = field(default_factory=dict)
    relative_strength: dict[str, Any] = field(default_factory=dict)
    volume: dict[str, Any] = field(default_factory=dict)
    support_resistance: dict[str, Any] = field(default_factory=dict)
    warnings: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return _to_plain_dict(self)


@dataclass(frozen=True)
class CanonicalStrategyResultV1:
    strategy_score: float | None = None
    trade_grade: str = ""
    entry_quality: str = ""
    risk_rating: str = ""
    expected_reward_percent: float | None = None
    expected_risk_percent: float | None = None
    reward_risk_ratio: float | None = None
    target_zone_low: float | None = None
    target_zone_high: float | None = None
    risk_zone_low: float | None = None
    risk_zone_high: float | None = None
    notes: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return _to_plain_dict(self)


@dataclass(frozen=True)
class CanonicalBacktestResultV1:
    attempted_trades: int | None = None
    completed_trades: int | None = None
    total_trades: int | None = None
    winning_trades: int | None = None
    losing_trades: int | None = None
    skipped_trades: int | None = None
    breakeven_trades: int | None = None
    win_rate: float | None = None
    average_return: float | None = None
    expectancy: float | None = None
    max_drawdown: float | None = None
    net_return_percent: float | None = None
    profit_factor: float | None = None
    summary: str = ""
    validation_summary: str = ""
    notes: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return _to_plain_dict(self)


@dataclass(frozen=True)
class CanonicalSignalSummaryV1:
    symbol: str = ""
    signal_date: str = ""
    timeframe: str = ""
    signal_type: str = "unknown"
    confidence: float | None = None
    snapshot_id: str = ""
    snapshot_date: str = ""
    context_summary: dict[str, Any] = field(default_factory=dict)
    strategy_summary: dict[str, Any] = field(default_factory=dict)
    prediction_summary: dict[str, Any] = field(default_factory=dict)
    notes: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return _to_plain_dict(self)


@dataclass(frozen=True)
class CanonicalDiagnosticsV1:
    source_pipeline: str = ""
    available_sections: tuple[str, ...] = ()
    skipped_sections: tuple[str, ...] = ()
    data_source_metadata: dict[str, Any] = field(default_factory=dict)
    row_count: int = 0
    future_row_count: int = 0
    similar_pattern_count: int = 0
    warnings: tuple[str, ...] = ()
    notes: tuple[str, ...] = ()
    legacy_payload_keys: tuple[str, ...] = ()
    adapter_version: str = ""

    def to_dict(self) -> dict[str, Any]:
        return _to_plain_dict(self)


@dataclass(frozen=True)
class CanonicalResultV1:
    identity: CanonicalIdentityV1 = field(default_factory=CanonicalIdentityV1)
    brain: CanonicalBrainResultV1 = field(default_factory=CanonicalBrainResultV1)
    diagnostics: CanonicalDiagnosticsV1 = field(default_factory=CanonicalDiagnosticsV1)
    prediction: CanonicalPredictionResultV1 | None = None
    context: CanonicalContextResultV1 | None = None
    strategy: CanonicalStrategyResultV1 | None = None
    backtest: CanonicalBacktestResultV1 | None = None
    signal_summary: CanonicalSignalSummaryV1 | None = None
    schema_version: str = CANONICAL_RESULT_SCHEMA_VERSION_V1

    def to_dict(self) -> dict[str, Any]:
        return _to_plain_dict(self)


def _to_plain_dict(value: object) -> dict[str, Any]:
    plain = _to_plain(value)
    return plain if isinstance(plain, dict) else {}


def _to_plain(value: object) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return {
            item.name: _to_plain(getattr(value, item.name))
            for item in fields(value)
        }
    if isinstance(value, dict):
        return {
            str(key): _to_plain(item)
            for key, item in value.items()
        }
    if isinstance(value, tuple):
        return [_to_plain(item) for item in value]
    if isinstance(value, list):
        return [_to_plain(item) for item in value]
    return value
