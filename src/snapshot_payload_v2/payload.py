from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field, fields, is_dataclass
from datetime import UTC, datetime
from typing import Any

from src.canonical_result import CanonicalResultV1
from src.analysis.poom_combo import calculate_poom_combo_snapshot


SNAPSHOT_PAYLOAD_SCHEMA_VERSION_V2 = "snapshot_payload_v2"
FORBIDDEN_PAYLOAD_KEYS = {
    "cache",
    "cache_tables",
    "market_data_cache",
    "ohlcv_daily",
    "outcome",
    "outcomes",
    "outcome_records",
    "settings",
    "ui",
    "ui_state",
}


@dataclass(frozen=True)
class SnapshotPayloadV2:
    identity: dict[str, Any] = field(default_factory=dict)
    provenance: dict[str, Any] = field(default_factory=dict)
    input: dict[str, Any] = field(default_factory=dict)
    analysis: dict[str, Any] = field(default_factory=dict)
    context: dict[str, Any] = field(default_factory=dict)
    strategy: dict[str, Any] = field(default_factory=dict)
    display_summary: dict[str, Any] = field(default_factory=dict)
    diagnostics: dict[str, Any] = field(default_factory=dict)
    compatibility: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return _plain_dict(self)


def build_snapshot_payload_v2(
    *,
    analysis_result: object | None = None,
    canonical_result: CanonicalResultV1 | None = None,
    request: object | None = None,
    ohlcv_rows: Sequence[Mapping[str, Any]] | None = None,
    similar_patterns: Sequence[Mapping[str, Any]] | None = None,
    context: object | None = None,
    strategy: object | None = None,
    signal_summary: object | None = None,
    provenance: Mapping[str, Any] | None = None,
    compatibility: Mapping[str, Any] | None = None,
    created_at: datetime | str | None = None,
) -> SnapshotPayloadV2:
    canonical = canonical_result if isinstance(canonical_result, CanonicalResultV1) else None
    canonical_payload = canonical.to_dict() if canonical is not None else {}
    source_request = request or _field(analysis_result, "request")
    source_context = context if context is not None else _field(canonical, "context")
    source_strategy = strategy if strategy is not None else _field(canonical, "strategy")
    source_signal_summary = signal_summary if signal_summary is not None else _field(canonical, "signal_summary")
    safe_rows = _rows(ohlcv_rows if ohlcv_rows is not None else _field(source_request, "ohlcv_rows"))
    safe_patterns = _rows(
        similar_patterns
        if similar_patterns is not None
        else _field(source_request, "similar_patterns")
    )

    identity = _identity_section(
        analysis_result=analysis_result,
        canonical_payload=canonical_payload,
        request=source_request,
        signal_summary=source_signal_summary,
        ohlcv_rows=safe_rows,
    )
    provenance_section = _provenance_section(
        analysis_result=analysis_result,
        provenance=provenance,
        created_at=created_at,
    )
    input_section = _input_section(
        request=source_request,
        ohlcv_rows=safe_rows,
        similar_patterns=safe_patterns,
    )
    analysis_section = _analysis_section(
        analysis_result=analysis_result,
        canonical_payload=canonical_payload,
        ohlcv_rows=safe_rows,
    )
    context_section = _mapping_from(source_context)
    strategy_section = _strategy_section(analysis_result, source_strategy)
    display_summary = _display_summary_section(
        signal_summary=source_signal_summary,
        canonical_payload=canonical_payload,
    )
    diagnostics = _diagnostics_section(
        analysis_result=analysis_result,
        canonical_payload=canonical_payload,
        ohlcv_rows=safe_rows,
        similar_patterns=safe_patterns,
    )
    compatibility_section = _compatibility_section(
        compatibility=compatibility,
        canonical_payload=canonical_payload,
        signal_summary=source_signal_summary,
    )

    return SnapshotPayloadV2(
        identity=identity,
        provenance=provenance_section,
        input=input_section,
        analysis=analysis_section,
        context=context_section,
        strategy=strategy_section,
        display_summary=display_summary,
        diagnostics=diagnostics,
        compatibility=compatibility_section,
    )


def _identity_section(
    *,
    analysis_result: object | None,
    canonical_payload: Mapping[str, Any],
    request: object | None,
    signal_summary: object | None,
    ohlcv_rows: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    canonical_identity = _mapping(canonical_payload.get("identity"))
    summary = _mapping_from(signal_summary)
    symbol = _first_text(
        canonical_identity.get("symbol"),
        _field(analysis_result, "symbol"),
        _field(request, "symbol"),
        summary.get("symbol"),
    ).upper()
    timeframe = _first_text(
        canonical_identity.get("timeframe"),
        _field(analysis_result, "timeframe"),
        _field(_field(request, "config"), "timeframe"),
        summary.get("timeframe"),
    )
    market_date = _first_text(
        canonical_identity.get("analysis_date"),
        canonical_identity.get("snapshot_date"),
        summary.get("signal_date"),
        summary.get("snapshot_date"),
        _last_row_date(ohlcv_rows),
    )
    return {
        "payload_schema_version": SNAPSHOT_PAYLOAD_SCHEMA_VERSION_V2,
        "symbol": symbol,
        "market_date": market_date,
        "timeframe": timeframe,
        "canonical_schema_version": str(canonical_payload.get("schema_version") or ""),
        "source": _first_text(
            canonical_identity.get("source"),
            canonical_identity.get("pipeline_name"),
            _mapping(canonical_payload.get("diagnostics")).get("source_pipeline"),
        ),
        "run_id": _first_text(canonical_identity.get("run_id"), _field(request, "run_id")),
        "legacy_snapshot_id": _first_text(
            canonical_identity.get("snapshot_id"),
            summary.get("snapshot_id"),
        ),
    }


def _provenance_section(
    *,
    analysis_result: object | None,
    provenance: Mapping[str, Any] | None,
    created_at: datetime | str | None,
) -> dict[str, Any]:
    provided = _mapping(provenance)
    return {
        "created_at": _created_at(created_at),
        "source": str(provided.get("source") or ""),
        "app_version": str(provided.get("app_version") or ""),
        "code_revision": str(provided.get("code_revision") or ""),
        "adapter_versions": _plain(provided.get("adapter_versions") or {}),
        "engine_versions": _plain(provided.get("engine_versions") or {}),
        "data_source": _plain(
            provided.get("data_source")
            or _field(analysis_result, "data_source_metadata")
            or {}
        ),
        "query": _plain(provided.get("query") or {}),
        "analysis_cutoff": _plain(provided.get("analysis_cutoff") or {}),
    }


def _input_section(
    *,
    request: object | None,
    ohlcv_rows: Sequence[Mapping[str, Any]],
    similar_patterns: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    config = _mapping_from(_field(request, "config"))
    return {
        "config": config,
        "query": {
            "symbol": _first_text(_field(request, "symbol")),
            "start_date": _field(request, "start_date"),
            "end_date": _field(request, "end_date"),
            "limit": _field(request, "limit"),
            "run_id": _field(request, "run_id"),
            "run_name": _field(request, "run_name"),
        },
        "ohlcv_window": {
            "row_count": len(ohlcv_rows),
            "first_date": _first_row_date(ohlcv_rows),
            "last_date": _last_row_date(ohlcv_rows),
            "rows": [_plain(row) for row in ohlcv_rows],
        },
        "similar_pattern_inputs": {
            "count": len(similar_patterns),
            "patterns": [_plain(pattern) for pattern in similar_patterns],
        },
    }


def _analysis_section(
    *,
    analysis_result: object | None,
    canonical_payload: Mapping[str, Any],
    ohlcv_rows: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    brain = _mapping(canonical_payload.get("brain"))
    canonical_brain = _field(analysis_result, "canonical_brain")
    return {
        "brain_snapshot": _first_mapping(brain.get("snapshot"), _field(canonical_brain, "snapshot")),
        "resolver_output": _first_mapping(brain.get("resolver_output"), _field(canonical_brain, "resolver_output")),
        "probability": _first_mapping(brain.get("probability"), _field(canonical_brain, "probability")),
        "projection": _first_mapping(brain.get("projection"), _field(canonical_brain, "projection")),
        "target_zone": _first_mapping(brain.get("target_zone"), _field(canonical_brain, "target_zone")),
        "risk_zone": _first_mapping(brain.get("risk_zone"), _field(canonical_brain, "risk_zone")),
        "prediction_summary": _first_mapping(
            brain.get("prediction_summary"),
            _field(canonical_brain, "prediction_summary"),
        ),
        "poom_combo": calculate_poom_combo_snapshot(ohlcv_rows) if ohlcv_rows else {},
    }


def _strategy_section(
    analysis_result: object | None,
    strategy: object | None,
) -> dict[str, Any]:
    if strategy is None:
        strategy = _field(analysis_result, "strategy")
    output = _mapping_from(strategy)
    reward_risk = _field(strategy, "reward_risk_estimate")
    if isinstance(reward_risk, Mapping):
        output.setdefault("reward_risk", _plain(reward_risk))
    return output


def _display_summary_section(
    *,
    signal_summary: object | None,
    canonical_payload: Mapping[str, Any],
) -> dict[str, Any]:
    summary = _mapping_from(signal_summary)
    prediction = _mapping(canonical_payload.get("prediction"))
    return {
        "signal_type": _first_text(summary.get("signal_type")),
        "confidence": _first_present(summary.get("confidence"), prediction.get("confidence")),
        "compact_context": _plain(summary.get("context_summary") or {}),
        "compact_prediction": _plain(summary.get("prediction_summary") or {}),
        "compact_strategy": _plain(summary.get("strategy_summary") or {}),
        "notes": _plain(summary.get("notes") or []),
    }


def _diagnostics_section(
    *,
    analysis_result: object | None,
    canonical_payload: Mapping[str, Any],
    ohlcv_rows: Sequence[Mapping[str, Any]],
    similar_patterns: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    diagnostics = _mapping(canonical_payload.get("diagnostics"))
    return {
        "row_counts": {
            "ohlcv_rows": len(ohlcv_rows),
            "future_rows": int(_field(analysis_result, "metadata") and _mapping(_field(analysis_result, "metadata")).get("future_rows") or 0),
            "similar_patterns": len(similar_patterns),
        },
        "available_sections": _plain(diagnostics.get("available_sections") or []),
        "skipped_sections": _plain(diagnostics.get("skipped_sections") or []),
        "warnings": _plain(diagnostics.get("warnings") or []),
        "notes": _plain(
            diagnostics.get("notes")
            or _field(analysis_result, "notes")
            or []
        ),
    }


def _compatibility_section(
    *,
    compatibility: Mapping[str, Any] | None,
    canonical_payload: Mapping[str, Any],
    signal_summary: object | None,
) -> dict[str, Any]:
    provided = _mapping(compatibility)
    summary = _mapping_from(signal_summary)
    identity = _mapping(canonical_payload.get("identity"))
    return {
        "signal_id": str(provided.get("signal_id") or ""),
        "legacy_snapshot_id": _first_text(
            provided.get("legacy_snapshot_id"),
            summary.get("snapshot_id"),
            identity.get("snapshot_id"),
        ),
        "legacy_signal_record_projection": _plain(
            provided.get("legacy_signal_record_projection") or {}
        ),
    }


def _created_at(value: datetime | str | None) -> str:
    if isinstance(value, datetime):
        safe_value = value if value.tzinfo is not None else value.replace(tzinfo=UTC)
        return safe_value.astimezone(UTC).isoformat()
    if isinstance(value, str) and value.strip():
        return value.strip()
    return datetime.now(UTC).isoformat()


def _rows(value: object) -> tuple[Mapping[str, Any], ...]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return ()
    return tuple(item for item in value if isinstance(item, Mapping))


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _mapping_from(value: object) -> dict[str, Any]:
    plain = _plain(value)
    return dict(plain) if isinstance(plain, Mapping) else {}


def _first_mapping(*values: object) -> dict[str, Any]:
    for value in values:
        mapped = _mapping_from(value)
        if mapped:
            return mapped
    return {}


def _field(source: object, name: str) -> Any:
    if source is None:
        return None
    if isinstance(source, Mapping):
        return source.get(name)
    return getattr(source, name, None)


def _first_text(*values: object) -> str:
    for value in values:
        text = str(value or "").strip()
        if text:
            return text
    return ""


def _first_present(*values: object) -> object:
    for value in values:
        if value is not None:
            return _plain(value)
    return None


def _first_row_date(rows: Sequence[Mapping[str, Any]]) -> str:
    if not rows:
        return ""
    return str(rows[0].get("date") or "")


def _last_row_date(rows: Sequence[Mapping[str, Any]]) -> str:
    if not rows:
        return ""
    return str(rows[-1].get("date") or "")


def _plain_dict(value: object) -> dict[str, Any]:
    plain = _plain(value)
    return dict(plain) if isinstance(plain, Mapping) else {}


def _plain(value: object) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return {
            item.name: _plain(getattr(value, item.name))
            for item in fields(value)
        }
    if isinstance(value, Mapping):
        return {
            str(key): _plain(item)
            for key, item in value.items()
            if str(key) not in FORBIDDEN_PAYLOAD_KEYS
        }
    if isinstance(value, tuple):
        return [_plain(item) for item in value]
    if isinstance(value, list):
        return [_plain(item) for item in value]
    return value
