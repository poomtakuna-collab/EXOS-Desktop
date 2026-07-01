from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from src.canonical_result.types import (
    CanonicalBrainResultV1,
    CanonicalDiagnosticsV1,
    CanonicalIdentityV1,
    CanonicalPredictionResultV1,
    CanonicalResultV1,
)


ADAPTER_VERSION_V1 = "canonical_result_adapter_v1"


def build_canonical_result_v1(source: object | None) -> CanonicalResultV1:
    warnings: list[str] = []
    identity = build_canonical_identity_v1(source)
    brain = build_canonical_brain_result_v1(source, warnings=warnings)
    prediction = build_canonical_prediction_result_v1(source, brain=brain)
    diagnostics = build_canonical_diagnostics_v1(
        source,
        brain=brain,
        prediction=prediction,
        warnings=warnings,
    )

    return CanonicalResultV1(
        identity=identity,
        brain=brain,
        prediction=prediction,
        diagnostics=diagnostics,
    )


def build_canonical_identity_v1(source: object | None) -> CanonicalIdentityV1:
    root = _source_mapping(source)
    request = _source_mapping(_value(source, "request"))
    config = _source_mapping(_value(request, "config"))
    metadata = _source_mapping(_value(source, "metadata"))
    brain_source = _brain_source(source)
    brain_metadata = _source_mapping(_value(brain_source, "metadata"))
    snapshot = _source_mapping(_value(brain_source, "snapshot"))

    return CanonicalIdentityV1(
        symbol=_string(
            _first_value(
                _value(source, "symbol"),
                _value(request, "symbol"),
                _value(snapshot, "symbol"),
                _value(brain_metadata, "symbol"),
            )
        ),
        timeframe=_string(
            _first_value(
                _value(source, "timeframe"),
                _value(config, "timeframe"),
                _value(snapshot, "timeframe"),
                _value(brain_metadata, "timeframe"),
            )
        ),
        snapshot_id=_string(
            _first_value(
                _value(snapshot, "snapshot_id"),
                _value(snapshot, "id"),
                _value(root, "snapshot_id"),
            )
        ),
        snapshot_date=_string(
            _first_value(
                _value(snapshot, "snapshot_date"),
                _value(snapshot, "date"),
                _value(snapshot, "candle_date"),
                _value(root, "snapshot_date"),
            )
        ),
        analysis_date=_string(
            _first_value(
                _value(root, "analysis_date"),
                _value(metadata, "analysis_date"),
                _value(metadata, "created_at"),
            )
        ),
        source=_string(
            _first_value(
                _value(metadata, "source"),
                _value(brain_metadata, "canonical_path"),
                _value(root, "source"),
            )
        ),
        pipeline_name=_string(
            _first_value(
                _value(metadata, "entry_point"),
                _value(metadata, "result_type"),
                _value(root, "pipeline_name"),
            )
        ),
        pipeline_version=_string(
            _first_value(
                _value(metadata, "pipeline_version"),
                _value(metadata, "result_type"),
                _value(root, "pipeline_version"),
            )
        ),
        run_id=_string(
            _first_value(
                _value(root, "run_id"),
                _value(request, "run_id"),
                _value(metadata, "run_id"),
            )
        ),
    )


def build_canonical_brain_result_v1(
    source: object | None,
    *,
    warnings: list[str] | None = None,
) -> CanonicalBrainResultV1:
    brain_source = _brain_source(source)
    root_source = source
    warning_sink = warnings if warnings is not None else []

    snapshot = _dict_section(brain_source, "snapshot", warning_sink)
    if not snapshot:
        snapshot = _dict_section(root_source, "snapshot", warning_sink)

    resolver_output = _dict_section(brain_source, "resolver_output", warning_sink)
    probability = _dict_section(brain_source, "probability", warning_sink)
    if not probability:
        probability = _dict_section(root_source, "probability", warning_sink)

    projection = _dict_section(brain_source, "projection", warning_sink)
    if not projection:
        projection = _dict_section(root_source, "projection", warning_sink)
    if not projection:
        projection = _dict_section(root_source, "prediction", warning_sink)

    target_zone = _dict_section(brain_source, "target_zone", warning_sink)
    risk_zone = _dict_section(brain_source, "risk_zone", warning_sink)

    prediction_summary = _dict_section(brain_source, "prediction_summary", warning_sink)
    if not prediction_summary:
        prediction_summary = _dict_section(root_source, "prediction_summary", warning_sink)
    if not prediction_summary:
        prediction_summary = _dict_section(root_source, "prediction", warning_sink)

    metadata = _dict_section(brain_source, "metadata", warning_sink)
    notes = _string_tuple(_value(brain_source, "notes"))

    return CanonicalBrainResultV1(
        snapshot=snapshot,
        resolver_output=resolver_output,
        probability=probability,
        projection=projection,
        target_zone=target_zone,
        risk_zone=risk_zone,
        prediction_summary=prediction_summary,
        metadata=metadata,
        notes=notes,
    )


def build_canonical_prediction_result_v1(
    source: object | None,
    *,
    brain: CanonicalBrainResultV1 | None = None,
) -> CanonicalPredictionResultV1 | None:
    brain_result = brain or build_canonical_brain_result_v1(source)
    probability = brain_result.probability
    projection = brain_result.projection
    summary = brain_result.prediction_summary
    target_zone = _zone_section(brain_result.target_zone, "target_zone")
    risk_zone = _zone_section(brain_result.risk_zone, "risk_zone")

    if not any((probability, projection, summary, target_zone, risk_zone)):
        return None

    return CanonicalPredictionResultV1(
        confidence=_float(
            _first_value(
                _value(summary, "confidence"),
                _value(projection, "confidence"),
                _value(probability, "confidence"),
            ),
            default=0.0,
        )
        or 0.0,
        evidence_count=_int(
            _first_value(
                _value(summary, "evidence_count"),
                _value(projection, "evidence_count"),
                _value(probability, "evidence_count"),
            ),
            default=0,
        )
        or 0,
        probability_positive=_float(_value(probability, "probability_positive")),
        probability_negative=_float(_value(probability, "probability_negative")),
        probability_neutral=_float(_value(probability, "probability_neutral")),
        expected_return_5d=_float(
            _first_value(
                _value(projection, "expected_return_5d"),
                _value(probability, "expected_return_5d"),
            )
        ),
        expected_return_10d=_float(
            _first_value(
                _value(projection, "expected_return_10d"),
                _value(probability, "expected_return_10d"),
                _value(projection, "expected_return"),
            )
        ),
        expected_return_20d=_float(
            _first_value(
                _value(projection, "expected_return_20d"),
                _value(probability, "expected_return_20d"),
            )
        ),
        expected_price_5d=_float(_value(projection, "expected_price_5d")),
        expected_price_10d=_float(_value(projection, "expected_price_10d")),
        expected_price_20d=_float(_value(projection, "expected_price_20d")),
        target_conservative=_float(_value(target_zone, "conservative")),
        target_base=_float(_value(target_zone, "base")),
        target_aggressive=_float(_value(target_zone, "aggressive")),
        risk_conservative=_float(_value(risk_zone, "conservative")),
        risk_base=_float(_value(risk_zone, "base")),
        risk_aggressive=_float(_value(risk_zone, "aggressive")),
        best_pattern_id=_optional_string(
            _first_value(
                _value(summary, "best_pattern_id"),
                _value(projection, "best_pattern_id"),
                _value(probability, "best_pattern_id"),
            )
        ),
        best_similarity=_float(
            _first_value(
                _value(summary, "best_similarity"),
                _value(projection, "best_similarity"),
                _value(probability, "best_similarity"),
            )
        ),
    )


def build_canonical_diagnostics_v1(
    source: object | None,
    *,
    brain: CanonicalBrainResultV1 | None = None,
    prediction: CanonicalPredictionResultV1 | None = None,
    warnings: Sequence[str] | None = None,
) -> CanonicalDiagnosticsV1:
    brain_result = brain or build_canonical_brain_result_v1(source)
    metadata = _source_mapping(_value(source, "metadata"))
    data_source_metadata = _dict_section(source, "data_source_metadata", [])
    source_notes = _string_tuple(_value(source, "notes"))
    warning_tuple = _string_tuple(warnings)
    available_sections = _available_sections(brain_result, prediction)

    return CanonicalDiagnosticsV1(
        source_pipeline=_string(
            _first_value(
                _value(metadata, "entry_point"),
                _value(metadata, "result_type"),
                _value(metadata, "source_pipeline"),
            )
        ),
        available_sections=available_sections,
        skipped_sections=tuple(
            section
            for section in ("prediction",)
            if section not in available_sections
        ),
        data_source_metadata=data_source_metadata,
        row_count=_int(
            _first_value(
                _value(metadata, "rows"),
                _value(metadata, "row_count"),
            ),
            default=0,
        )
        or 0,
        future_row_count=_int(
            _first_value(
                _value(metadata, "future_rows"),
                _value(metadata, "future_row_count"),
            ),
            default=0,
        )
        or 0,
        similar_pattern_count=_int(
            _first_value(
                _value(metadata, "similar_patterns"),
                _value(metadata, "similar_pattern_count"),
                _value(brain_result.metadata, "pattern_count"),
            ),
            default=0,
        )
        or 0,
        warnings=warning_tuple,
        notes=source_notes,
        legacy_payload_keys=_legacy_payload_keys(source),
        adapter_version=ADAPTER_VERSION_V1,
    )


def _brain_source(source: object | None) -> object | None:
    canonical_brain = _value(source, "canonical_brain")
    return canonical_brain if canonical_brain is not None else source


def _source_mapping(value: object | None) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _dict_section(
    source: object | None,
    key: str,
    warnings: list[str],
) -> dict[str, Any]:
    value = _value(source, key)
    if value is None:
        return {}
    if isinstance(value, Mapping):
        return dict(value)
    warnings.append(f"Malformed {key} section skipped.")
    return {}


def _zone_section(payload: Mapping[str, Any], key: str) -> Mapping[str, Any]:
    nested = payload.get(key)
    if isinstance(nested, Mapping):
        return nested
    return payload


def _value(source: object | None, key: str) -> object | None:
    if isinstance(source, Mapping):
        return source.get(key)
    if source is not None and hasattr(source, key):
        return getattr(source, key)
    return None


def _first_value(*values: object | None) -> object | None:
    for value in values:
        if value is not None and value != "":
            return value
    return None


def _available_sections(
    brain: CanonicalBrainResultV1,
    prediction: CanonicalPredictionResultV1 | None,
) -> tuple[str, ...]:
    sections: list[str] = []
    if any(
        (
            brain.snapshot,
            brain.resolver_output,
            brain.probability,
            brain.projection,
            brain.target_zone,
            brain.risk_zone,
            brain.prediction_summary,
        )
    ):
        sections.append("brain")
    if prediction is not None:
        sections.append("prediction")
    return tuple(sections)


def _legacy_payload_keys(source: object | None) -> tuple[str, ...]:
    if isinstance(source, Mapping):
        return tuple(str(key) for key in source.keys())
    return tuple(
        key
        for key in (
            "request",
            "config",
            "symbol",
            "timeframe",
            "canonical_brain",
            "snapshot",
            "probability",
            "prediction",
            "metadata",
            "notes",
        )
        if _value(source, key) is not None
    )


def _string_tuple(value: object | None) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        return (value,)
    if isinstance(value, Sequence):
        return tuple(str(item) for item in value if item is not None)
    return (str(value),)


def _string(value: object | None) -> str:
    return str(value or "")


def _optional_string(value: object | None) -> str | None:
    if value is None or value == "":
        return None
    return str(value)


def _float(value: object | None, *, default: float | None = None) -> float | None:
    if value is None or isinstance(value, bool):
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _int(value: object | None, *, default: int | None = None) -> int | None:
    number = _float(value)
    if number is None:
        return default
    return int(number)
