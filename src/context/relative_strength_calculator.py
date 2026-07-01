from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from src.context.types import RelativeStrengthContext


OUTPERFORM_THRESHOLD_PCT = 2.0
UNDERPERFORM_THRESHOLD_PCT = -2.0


def calculate_relative_strength_context(
    *,
    symbol_rows: Sequence[Mapping[str, Any]] | None = None,
    benchmark_rows: Sequence[Mapping[str, Any]] | None = None,
    sector_rows: Sequence[Mapping[str, Any]] | None = None,
    symbol_performance: Any = None,
    benchmark_performance: Any = None,
    sector_performance: Any = None,
) -> RelativeStrengthContext:
    """Calculate deterministic relative strength from local performance inputs."""
    symbol_return = _performance(symbol_performance, symbol_rows)
    benchmark_return = _performance(benchmark_performance, benchmark_rows)
    sector_return = _performance(sector_performance, sector_rows)

    stock_vs_market = _relative_spread(symbol_return, benchmark_return)
    stock_vs_sector = _relative_spread(symbol_return, sector_return)

    return RelativeStrengthContext(
        stock_vs_market=stock_vs_market,
        stock_vs_sector=stock_vs_sector,
        rating=_rating(stock_vs_market, stock_vs_sector),
    )


def calculate_relative_strength_context_from_analysis(
    analysis_result: Any,
) -> RelativeStrengthContext:
    """Calculate relative strength from an AnalysisResult-like object or dict."""
    if isinstance(analysis_result, Mapping):
        request = _mapping_or_none(analysis_result.get("request"))
        return calculate_relative_strength_context(
            symbol_rows=_rows_from_request(request, "ohlcv_rows"),
            benchmark_rows=_rows_from_request(request, "benchmark_ohlcv_rows"),
            sector_rows=_rows_from_request(request, "sector_ohlcv_rows"),
            symbol_performance=analysis_result.get("symbol_performance"),
            benchmark_performance=analysis_result.get("benchmark_performance"),
            sector_performance=analysis_result.get("sector_performance"),
        )

    request = getattr(analysis_result, "request", None)
    return calculate_relative_strength_context(
        symbol_rows=_rows_from_request(request, "ohlcv_rows"),
        benchmark_rows=_rows_from_request(request, "benchmark_ohlcv_rows"),
        sector_rows=_rows_from_request(request, "sector_ohlcv_rows"),
        symbol_performance=getattr(analysis_result, "symbol_performance", None),
        benchmark_performance=getattr(analysis_result, "benchmark_performance", None),
        sector_performance=getattr(analysis_result, "sector_performance", None),
    )


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


def _relative_spread(
    symbol_return: float | None,
    comparison_return: float | None,
) -> float | None:
    if symbol_return is None or comparison_return is None:
        return None
    return round(symbol_return - comparison_return, 4)


def _rating(
    stock_vs_market: float | None,
    stock_vs_sector: float | None,
) -> str:
    spreads = [
        spread
        for spread in (stock_vs_market, stock_vs_sector)
        if spread is not None
    ]
    if not spreads:
        return "unknown"

    average_spread = sum(spreads) / len(spreads)
    if average_spread > OUTPERFORM_THRESHOLD_PCT:
        return "outperform"
    if average_spread < UNDERPERFORM_THRESHOLD_PCT:
        return "underperform"
    return "neutral"


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
    if isinstance(request, Mapping):
        rows = request.get(name)
        return rows if isinstance(rows, Sequence) and not isinstance(rows, (str, bytes)) else None

    rows = getattr(request, name, None)
    return rows if isinstance(rows, Sequence) and not isinstance(rows, (str, bytes)) else None


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
