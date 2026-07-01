from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from src.context.types import VolumeContext


def calculate_volume_context(
    *,
    snapshot: Mapping[str, Any] | None = None,
    indicators: Mapping[str, Any] | None = None,
    price_rows: Sequence[Mapping[str, Any]] | None = None,
    current_volume: Any = None,
    average_volume: Any = None,
    relative_volume: Any = None,
) -> VolumeContext:
    """Calculate deterministic volume context from local analysis inputs."""
    snapshot_data = snapshot if isinstance(snapshot, Mapping) else {}
    indicator_data = indicators if isinstance(indicators, Mapping) else {}
    rows = _valid_rows(price_rows)

    relative = _relative_volume(
        explicit_relative_volume=relative_volume,
        current_volume=current_volume,
        average_volume=average_volume,
        snapshot=snapshot_data,
        indicators=indicator_data,
        rows=rows,
    )
    if relative is None:
        return VolumeContext()

    rounded_relative = round(relative, 4)
    return VolumeContext(
        relative_volume=rounded_relative,
        volume_state=_volume_state(rounded_relative),
    )


def calculate_volume_context_from_analysis(analysis_result: Any) -> VolumeContext:
    """Calculate volume context from an AnalysisResult-like object or dict."""
    if isinstance(analysis_result, Mapping):
        request = _mapping_or_none(analysis_result.get("request"))
        return calculate_volume_context(
            snapshot=_mapping_or_none(analysis_result.get("snapshot")),
            indicators=_mapping_or_none(analysis_result.get("indicators")),
            price_rows=_rows_from_request(request),
            current_volume=analysis_result.get("current_volume"),
            average_volume=analysis_result.get("average_volume"),
            relative_volume=analysis_result.get("relative_volume"),
        )

    request = getattr(analysis_result, "request", None)
    return calculate_volume_context(
        snapshot=_mapping_or_none(getattr(analysis_result, "snapshot", None)),
        indicators=_mapping_or_none(getattr(analysis_result, "indicators", None)),
        price_rows=_rows_from_request(request),
        current_volume=getattr(analysis_result, "current_volume", None),
        average_volume=getattr(analysis_result, "average_volume", None),
        relative_volume=getattr(analysis_result, "relative_volume", None),
    )


def _relative_volume(
    *,
    explicit_relative_volume: Any,
    current_volume: Any,
    average_volume: Any,
    snapshot: Mapping[str, Any],
    indicators: Mapping[str, Any],
    rows: Sequence[Mapping[str, Any]],
) -> float | None:
    explicit = _positive_number(explicit_relative_volume)
    if explicit is not None:
        return explicit

    for source in _volume_sources(snapshot, indicators):
        value = _positive_number(source.get("relative_volume"))
        if value is not None:
            return value

    current = _current_volume(current_volume, snapshot, indicators, rows)
    average = _average_volume(average_volume, snapshot, indicators, rows)
    if current is None or average is None or average <= 0:
        return None
    return current / average


def _volume_state(relative_volume: float) -> str:
    if relative_volume < 0.7:
        return "low"
    if relative_volume < 1.5:
        return "normal"
    if relative_volume < 2.5:
        return "high"
    return "spike"


def _current_volume(
    current_volume: Any,
    snapshot: Mapping[str, Any],
    indicators: Mapping[str, Any],
    rows: Sequence[Mapping[str, Any]],
) -> float | None:
    explicit = _positive_number(current_volume)
    if explicit is not None:
        return explicit

    for source in _volume_sources(snapshot, indicators):
        for name in ("current_volume", "volume", "last_volume"):
            value = _positive_number(source.get(name))
            if value is not None:
                return value

    if rows:
        return _positive_number(rows[-1].get("volume"))
    return None


def _average_volume(
    average_volume: Any,
    snapshot: Mapping[str, Any],
    indicators: Mapping[str, Any],
    rows: Sequence[Mapping[str, Any]],
) -> float | None:
    explicit = _positive_number(average_volume)
    if explicit is not None:
        return explicit

    for source in _volume_sources(snapshot, indicators):
        for name in ("average_volume", "avg_volume", "volume_average", "volume_sma20"):
            value = _positive_number(source.get(name))
            if value is not None:
                return value

    historical_volumes = [
        volume
        for volume in (_positive_number(row.get("volume")) for row in rows[:-1])
        if volume is not None
    ]
    if len(historical_volumes) < 2:
        return None
    return sum(historical_volumes) / len(historical_volumes)


def _volume_sources(
    snapshot: Mapping[str, Any],
    indicators: Mapping[str, Any],
) -> tuple[Mapping[str, Any], ...]:
    return (
        snapshot,
        indicators,
        _section(snapshot, "volume"),
        _section(snapshot, "indicators"),
        _section(indicators, "volume"),
    )


def _valid_rows(
    price_rows: Sequence[Mapping[str, Any]] | None,
) -> tuple[Mapping[str, Any], ...]:
    if not isinstance(price_rows, Sequence) or isinstance(price_rows, (str, bytes)):
        return ()
    return tuple(row for row in price_rows if isinstance(row, Mapping))


def _rows_from_request(request: Any) -> Sequence[Mapping[str, Any]] | None:
    if isinstance(request, Mapping):
        rows = request.get("ohlcv_rows")
        return rows if isinstance(rows, Sequence) and not isinstance(rows, (str, bytes)) else None

    rows = getattr(request, "ohlcv_rows", None)
    return rows if isinstance(rows, Sequence) and not isinstance(rows, (str, bytes)) else None


def _section(source: Mapping[str, Any], name: str) -> Mapping[str, Any]:
    value = source.get(name)
    return value if isinstance(value, Mapping) else {}


def _positive_number(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if number > 0 else None


def _mapping_or_none(value: Any) -> Mapping[str, Any] | None:
    return value if isinstance(value, Mapping) else None
