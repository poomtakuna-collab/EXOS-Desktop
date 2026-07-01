from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from src.context.types import SupportResistanceContext


def calculate_support_resistance_context(
    *,
    snapshot: Mapping[str, Any] | None = None,
    indicators: Mapping[str, Any] | None = None,
    price_rows: Sequence[Mapping[str, Any]] | None = None,
    current_price: Any = None,
) -> SupportResistanceContext:
    """Calculate deterministic support/resistance context from local inputs."""
    snapshot_data = snapshot if isinstance(snapshot, Mapping) else {}
    indicator_data = indicators if isinstance(indicators, Mapping) else {}
    rows = _valid_rows(price_rows)
    price = _current_price(current_price, snapshot_data, indicator_data, rows)
    if price is None or price <= 0:
        return SupportResistanceContext()

    candidates = _level_candidates(snapshot_data, indicator_data, rows)
    support = _nearest_below_or_equal(price, candidates)
    resistance = _nearest_above_or_equal(price, candidates)

    return SupportResistanceContext(
        nearest_support=support,
        nearest_resistance=resistance,
        support_distance_pct=_distance_pct(price, support),
        resistance_distance_pct=_distance_pct(price, resistance),
    )


def calculate_support_resistance_context_from_analysis(
    analysis_result: Any,
) -> SupportResistanceContext:
    """Calculate support/resistance context from an AnalysisResult-like object or dict."""
    if isinstance(analysis_result, Mapping):
        request = _mapping_or_none(analysis_result.get("request"))
        return calculate_support_resistance_context(
            snapshot=_mapping_or_none(analysis_result.get("snapshot")),
            indicators=_mapping_or_none(analysis_result.get("indicators")),
            price_rows=_rows_from_request(request),
            current_price=analysis_result.get("current_price"),
        )

    request = getattr(analysis_result, "request", None)
    return calculate_support_resistance_context(
        snapshot=_mapping_or_none(getattr(analysis_result, "snapshot", None)),
        indicators=_mapping_or_none(getattr(analysis_result, "indicators", None)),
        price_rows=_rows_from_request(request),
        current_price=getattr(analysis_result, "current_price", None),
    )


def _level_candidates(
    snapshot: Mapping[str, Any],
    indicators: Mapping[str, Any],
    rows: Sequence[Mapping[str, Any]],
) -> tuple[float, ...]:
    candidates: list[float] = []
    candidates.extend(_snapshot_levels(snapshot))
    candidates.extend(_indicator_levels(snapshot))
    candidates.extend(_indicator_levels(indicators))
    candidates.extend(_row_levels(rows))
    return tuple(sorted({_rounded(level) for level in candidates if level > 0}))


def _snapshot_levels(snapshot: Mapping[str, Any]) -> list[float]:
    structure = _section(snapshot, "market_structure")
    names = (
        "swing_high",
        "swing_low",
        "last_pivot_high",
        "last_pivot_low",
        "nearest_support",
        "nearest_resistance",
    )
    levels: list[float] = []
    for name in names:
        value = _number(structure.get(name))
        if value is not None:
            levels.append(value)
    return levels


def _indicator_levels(source: Mapping[str, Any]) -> list[float]:
    levels: list[float] = []
    sections = (source, _section(source, "indicators"), _section(source, "trend"))
    for section in sections:
        for name in ("ema20", "ema50", "ema200", "sma20", "sma50", "sma200", "vwap"):
            value = _number(section.get(name))
            if value is not None:
                levels.append(value)
    return levels


def _row_levels(rows: Sequence[Mapping[str, Any]]) -> list[float]:
    if not rows:
        return []

    levels: list[float] = []
    highs = [_number(row.get("high")) for row in rows]
    lows = [_number(row.get("low")) for row in rows]
    valid_highs = [value for value in highs if value is not None and value > 0]
    valid_lows = [value for value in lows if value is not None and value > 0]
    if valid_highs:
        levels.append(max(valid_highs))
        levels.extend(valid_highs)
    if valid_lows:
        levels.append(min(valid_lows))
        levels.extend(valid_lows)

    for index in range(1, len(rows) - 1):
        high = _number(rows[index].get("high"))
        low = _number(rows[index].get("low"))
        left_high = _number(rows[index - 1].get("high"))
        right_high = _number(rows[index + 1].get("high"))
        left_low = _number(rows[index - 1].get("low"))
        right_low = _number(rows[index + 1].get("low"))

        if (
            high is not None
            and left_high is not None
            and right_high is not None
            and high >= left_high
            and high >= right_high
        ):
            levels.append(high)
        if (
            low is not None
            and left_low is not None
            and right_low is not None
            and low <= left_low
            and low <= right_low
        ):
            levels.append(low)

    return levels


def _nearest_below_or_equal(price: float, candidates: Sequence[float]) -> float | None:
    supports = [candidate for candidate in candidates if candidate <= price]
    return max(supports) if supports else None


def _nearest_above_or_equal(price: float, candidates: Sequence[float]) -> float | None:
    resistances = [candidate for candidate in candidates if candidate >= price]
    return min(resistances) if resistances else None


def _distance_pct(price: float, level: float | None) -> float | None:
    if level is None:
        return None
    return round(abs(price - level) / price * 100, 4)


def _current_price(
    current_price: Any,
    snapshot: Mapping[str, Any],
    indicators: Mapping[str, Any],
    rows: Sequence[Mapping[str, Any]],
) -> float | None:
    explicit = _number(current_price)
    if explicit is not None:
        return explicit

    for source in (snapshot, indicators, _section(snapshot, "metadata"), _section(snapshot, "price")):
        for name in ("current_price", "price", "close", "last_close"):
            value = _number(source.get(name))
            if value is not None:
                return value

    if rows:
        return _number(rows[-1].get("close"))
    return None


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


def _number(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _rounded(value: float) -> float:
    return round(value, 4)


def _mapping_or_none(value: Any) -> Mapping[str, Any] | None:
    return value if isinstance(value, Mapping) else None
