from __future__ import annotations

import sqlite3
from pathlib import Path

from src.gui.performance_view_model import DEFAULT_PERFORMANCE_DATABASE_PATH
from src.statistics_engine import (
    DEFAULT_MIN_SAMPLE_COUNT,
    PatternBucketInsight,
    build_pattern_statistics_report,
    build_statistics_report_from_connection,
)


def load_pattern_statistics_view_model(
    database_path: Path | str = DEFAULT_PERFORMANCE_DATABASE_PATH,
    *,
    min_sample_count: int = DEFAULT_MIN_SAMPLE_COUNT,
    scope_mode: str = "all_symbols",
    current_symbol: str | None = None,
) -> dict[str, object]:
    path = Path(database_path)
    if not path.exists():
        return _empty_view_model(
            "Pattern Statistics unavailable: database not found.",
            scope_mode=scope_mode,
            current_symbol=current_symbol,
        )

    connection = sqlite3.connect(path)
    try:
        statistics_report = build_statistics_report_from_connection(
            connection,
            min_sample_count=1,
            scope_mode=scope_mode,
            current_symbol=current_symbol,
        )
    finally:
        connection.close()
    report = build_pattern_statistics_report(
        statistics_report,
        min_sample_count=min_sample_count,
    )
    return build_pattern_statistics_view_model(report)


def build_pattern_statistics_view_model(report: object) -> dict[str, object]:
    return {
        "title": "Pattern Statistics",
        "summary": (
            ("Minimum Sample Count", _format_int(getattr(report, "min_sample_count", 0))),
            ("Total Buckets", _format_int(getattr(report, "total_buckets", 0))),
            ("Eligible Buckets", _format_int(getattr(report, "eligible_bucket_count", 0))),
        ),
        "scope_summary": _scope_items(getattr(report, "scope", None)),
        "rankings": (
            (
                "Top by Sample Count",
                _rows(getattr(report, "top_by_sample_count", ())),
            ),
            (
                "Top by Win Rate",
                _rows(getattr(report, "top_by_win_rate", ())),
            ),
            (
                "Top by Average Return",
                _rows(getattr(report, "top_by_average_return_10d", ())),
            ),
            (
                "Top by Expectancy",
                _rows(getattr(report, "top_by_expectancy", ())),
            ),
            (
                "Top by Drawdown",
                _rows(getattr(report, "top_by_average_drawdown", ())),
            ),
        ),
        "insights": (
            (
                "Strong Historical Buckets",
                _rows(getattr(report, "strong_historical_buckets", ())),
            ),
            (
                "Weak Historical Buckets",
                _rows(getattr(report, "weak_historical_buckets", ())),
            ),
            (
                "High Win-Rate / Low Expectancy",
                _rows(getattr(report, "high_win_rate_low_expectancy_buckets", ())),
            ),
            (
                "High Expectancy / Low Sample",
                _rows(getattr(report, "high_expectancy_low_sample_buckets", ())),
            ),
        ),
        "status": _status_text(report),
    }


def _empty_view_model(
    status: str,
    *,
    scope_mode: str = "all_symbols",
    current_symbol: str | None = None,
) -> dict[str, object]:
    return {
        "title": "Pattern Statistics",
        "summary": (
            ("Minimum Sample Count", str(DEFAULT_MIN_SAMPLE_COUNT)),
            ("Total Buckets", "0"),
            ("Eligible Buckets", "0"),
        ),
        "scope_summary": (
            ("Scope Mode", _scope_label(scope_mode, current_symbol)),
            ("Symbol Count", "0"),
            ("Symbols Analyzed", "-"),
            ("Date Range", "-"),
            ("Snapshot Count per Symbol", "-"),
        ),
        "rankings": (),
        "insights": (),
        "status": status,
    }


def _scope_items(scope: object) -> tuple[tuple[str, str], ...]:
    if scope is None:
        return (
            ("Scope Mode", "All Symbols"),
            ("Symbol Count", "0"),
            ("Symbols Analyzed", "-"),
            ("Date Range", "-"),
            ("Snapshot Count per Symbol", "-"),
        )
    symbols = tuple(getattr(scope, "symbols_analyzed", ()) or ())
    date_range = getattr(scope, "date_range", None)
    counts = tuple(getattr(scope, "snapshot_count_per_symbol", ()) or ())
    scope_symbol = str(symbols[0]) if len(symbols) == 1 else None
    return (
        ("Scope Mode", _scope_label(getattr(scope, "scope_mode", "all_symbols"), scope_symbol)),
        ("Symbol Count", _format_int(getattr(scope, "symbol_count", 0))),
        ("Symbols Analyzed", ", ".join(str(symbol) for symbol in symbols) or "-"),
        ("Total Snapshots", _format_int(getattr(scope, "total_snapshots", 0))),
        ("Total Outcomes", _format_int(getattr(scope, "total_outcomes", 0))),
        ("Skipped Snapshots", _format_int(getattr(scope, "skipped_snapshots", 0))),
        ("Date Range", _format_date_range(date_range)),
        ("Snapshot Count per Symbol", _format_symbol_counts(counts)),
    )


def _scope_label(scope_mode: object, current_symbol: str | None) -> str:
    if str(scope_mode or "").strip() == "current_symbol":
        symbol = str(current_symbol or "").strip().upper()
        return f"Current Symbol ({symbol})" if symbol else "Current Symbol"
    return "All Symbols"


def _format_date_range(value: object) -> str:
    if isinstance(value, tuple) and len(value) == 2:
        return f"{value[0]} -> {value[1]}"
    return "-"


def _format_symbol_counts(value: tuple[object, ...]) -> str:
    parts = []
    for item in value:
        if isinstance(item, tuple) and len(item) == 2:
            parts.append(f"{item[0]}: {item[1]}")
    return ", ".join(parts) or "-"


def _rows(values: object) -> tuple[dict[str, str], ...]:
    rows = values if isinstance(values, tuple) else ()
    return tuple(_row(item) for item in rows if isinstance(item, PatternBucketInsight))


def _row(item: PatternBucketInsight) -> dict[str, str]:
    return {
        "bucket_name": f"{item.feature_name}: {item.bucket}",
        "sample_count": _format_int(item.sample_count),
        "win_rate": _format_percent(item.win_rate),
        "average_return_10d": _format_percent(item.average_return_10d),
        "expectancy": _format_percent(item.expectancy),
        "average_drawdown": _format_percent(item.average_drawdown),
        "interpretation": item.interpretation,
    }


def _status_text(report: object) -> str:
    total_buckets = int(getattr(report, "total_buckets", 0) or 0)
    eligible_buckets = int(getattr(report, "eligible_bucket_count", 0) or 0)
    if total_buckets == 0:
        return "No feature bucket statistics available."
    if eligible_buckets == 0:
        return "No buckets meet the minimum sample count yet."
    return "Read-only Pattern Statistics report."


def _format_int(value: object) -> str:
    try:
        return str(int(value))
    except (TypeError, ValueError):
        return "0"


def _format_percent(value: object) -> str:
    try:
        return f"{float(value):.2f}%"
    except (TypeError, ValueError):
        return "0.00%"
