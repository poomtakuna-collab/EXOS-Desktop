from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from src.context.types import SectorContext


UPTREND_THRESHOLD_PCT = 2.0
DOWNTREND_THRESHOLD_PCT = -2.0
STRONG_THRESHOLD_PCT = 2.0
WEAK_THRESHOLD_PCT = -2.0


def calculate_sector_context(
    *,
    sector_symbol: str | None = None,
    symbol_rows: Sequence[Mapping[str, Any]] | None = None,
    sector_rows: Sequence[Mapping[str, Any]] | None = None,
    industry_rows: Sequence[Mapping[str, Any]] | None = None,
    symbol_performance: Any = None,
    sector_performance: Any = None,
    industry_performance: Any = None,
) -> SectorContext:
    """Calculate deterministic sector context from local performance inputs."""
    symbol_return = _performance(symbol_performance, symbol_rows)
    sector_return = _performance(sector_performance, sector_rows)
    industry_return = _performance(industry_performance, industry_rows)

    return SectorContext(
        sector_symbol=sector_symbol,
        trend=_trend(sector_return),
        relative_to_market=_sector_strength(
            sector_return=sector_return,
            industry_return=industry_return,
            symbol_return=symbol_return,
        ),
    )


def calculate_sector_context_from_analysis(analysis_result: Any) -> SectorContext:
    """Calculate sector context from an AnalysisResult-like object or dict."""
    if isinstance(analysis_result, Mapping):
        request = _mapping_or_none(analysis_result.get("request"))
        return calculate_sector_context(
            sector_symbol=_sector_symbol(analysis_result, request),
            symbol_rows=_rows_from_request(request, "ohlcv_rows"),
            sector_rows=_rows_from_request(request, "sector_ohlcv_rows"),
            industry_rows=_rows_from_request(request, "industry_ohlcv_rows"),
            symbol_performance=analysis_result.get("symbol_performance"),
            sector_performance=analysis_result.get("sector_performance"),
            industry_performance=analysis_result.get("industry_performance"),
        )

    request = getattr(analysis_result, "request", None)
    return calculate_sector_context(
        sector_symbol=_sector_symbol(analysis_result, request),
        symbol_rows=_rows_from_request(request, "ohlcv_rows"),
        sector_rows=_rows_from_request(request, "sector_ohlcv_rows"),
        industry_rows=_rows_from_request(request, "industry_ohlcv_rows"),
        symbol_performance=getattr(analysis_result, "symbol_performance", None),
        sector_performance=getattr(analysis_result, "sector_performance", None),
        industry_performance=getattr(analysis_result, "industry_performance", None),
    )


def _trend(sector_return: float | None) -> str:
    if sector_return is None:
        return "unknown"
    if sector_return > UPTREND_THRESHOLD_PCT:
        return "up"
    if sector_return < DOWNTREND_THRESHOLD_PCT:
        return "down"
    return "sideways"


def _sector_strength(
    *,
    sector_return: float | None,
    industry_return: float | None,
    symbol_return: float | None,
) -> str:
    if sector_return is None:
        return "unknown"

    comparison_return = industry_return
    if comparison_return is None:
        comparison_return = symbol_return
    if comparison_return is None:
        return "unknown"

    spread = sector_return - comparison_return
    if spread > STRONG_THRESHOLD_PCT:
        return "strong"
    if spread < WEAK_THRESHOLD_PCT:
        return "weak"
    return "neutral"


def _performance(
    explicit_performance: Any,
    rows: Sequence[Mapping[str, Any]] | None,
) -> float | None:
    explicit = _number(explicit_performance)
    if explicit is not None:
        return explicit

    valid_rows = _valid_rows(rows)
    if len(valid_rows) < 2:
        return None

    start = _positive_number(valid_rows[0].get("close"))
    end = _positive_number(valid_rows[-1].get("close"))
    if start is None or end is None:
        return None
    return (end - start) / start * 100


def _sector_symbol(analysis_result: Any, request: Any) -> str | None:
    for source in (analysis_result, request):
        value = _field(source, "sector_symbol")
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def _valid_rows(
    rows: Sequence[Mapping[str, Any]] | None,
) -> tuple[Mapping[str, Any], ...]:
    if not isinstance(rows, Sequence) or isinstance(rows, (str, bytes)):
        return ()
    return tuple(row for row in rows if isinstance(row, Mapping))


def _rows_from_request(
    request: Any,
    name: str,
) -> Sequence[Mapping[str, Any]] | None:
    rows = _field(request, name)
    return rows if isinstance(rows, Sequence) and not isinstance(rows, (str, bytes)) else None


def _field(source: Any, name: str) -> Any:
    if isinstance(source, Mapping):
        return source.get(name)
    return getattr(source, name, None)


def _positive_number(value: Any) -> float | None:
    number = _number(value)
    if number is None or number <= 0:
        return None
    return number


def _number(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _mapping_or_none(value: Any) -> Mapping[str, Any] | None:
    return value if isinstance(value, Mapping) else None
