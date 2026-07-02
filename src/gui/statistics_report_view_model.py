from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Callable

from src.gui.performance_view_model import DEFAULT_PERFORMANCE_DATABASE_PATH
from src.statistics_engine import FeatureBucketStats, build_statistics_report_from_connection


def load_statistics_report_view_model(
    database_path: Path | str = DEFAULT_PERFORMANCE_DATABASE_PATH,
    *,
    scope_mode: str = "all_symbols",
    current_symbol: str | None = None,
) -> dict[str, object]:
    path = Path(database_path)
    if not path.exists():
        return _empty_view_model(
            "Statistics Report unavailable: database not found.",
            scope_mode=scope_mode,
            current_symbol=current_symbol,
        )

    connection = sqlite3.connect(path)
    try:
        report = build_statistics_report_from_connection(
            connection,
            scope_mode=scope_mode,
            current_symbol=current_symbol,
        )
    finally:
        connection.close()
    return build_statistics_report_view_model(report)


def build_statistics_report_view_model(report: object) -> dict[str, object]:
    feature_stats = tuple(getattr(report, "feature_stats", ()) or ())
    return {
        "title": "Statistics Report",
        "summary": (
            ("Total Snapshots Analyzed", _format_int(getattr(report, "snapshot_count", 0))),
            ("Total Outcomes Calculated", _format_int(getattr(report, "outcome_count", 0))),
            ("Skipped Snapshots", _format_int(getattr(report, "skipped_count", 0))),
        ),
        "scope_summary": _scope_items(getattr(report, "scope", None)),
        "top_by_sample_count": _top_bucket_rows(
            feature_stats,
            sort_key=lambda item: (
                int(getattr(item, "sample_count", 0)),
                float(getattr(item, "expectancy", 0.0)),
            ),
        ),
        "top_by_win_rate": _top_bucket_rows(
            feature_stats,
            sort_key=lambda item: (
                float(getattr(item, "win_rate", 0.0)),
                int(getattr(item, "sample_count", 0)),
            ),
        ),
        "top_by_expectancy": _top_bucket_rows(
            feature_stats,
            sort_key=lambda item: (
                float(getattr(item, "expectancy", 0.0)),
                int(getattr(item, "sample_count", 0)),
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
        "title": "Statistics Report",
        "summary": (
            ("Total Snapshots Analyzed", "0"),
            ("Total Outcomes Calculated", "0"),
            ("Skipped Snapshots", "0"),
        ),
        "scope_summary": (
            ("Scope Mode", _scope_label(scope_mode, current_symbol)),
            ("Symbol Count", "0"),
            ("Symbols Analyzed", "-"),
            ("Date Range", "-"),
            ("Snapshot Count per Symbol", "-"),
        ),
        "top_by_sample_count": (),
        "top_by_win_rate": (),
        "top_by_expectancy": (),
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


def _top_bucket_rows(
    feature_stats: tuple[object, ...],
    *,
    sort_key: Callable[[object], tuple[float | int, float | int]],
    limit: int = 10,
) -> tuple[dict[str, str], ...]:
    rows = sorted(
        feature_stats,
        key=sort_key,
        reverse=True,
    )[:limit]
    return tuple(_bucket_row(item) for item in rows if isinstance(item, FeatureBucketStats))


def _bucket_row(item: FeatureBucketStats) -> dict[str, str]:
    return {
        "feature": item.feature_name,
        "bucket": item.bucket,
        "sample_count": _format_int(item.sample_count),
        "win_rate": _format_percent(item.win_rate),
        "average_return": _format_percent(item.average_return),
        "median_return": _format_percent(item.median_return),
        "average_max_gain": _format_percent(item.average_max_gain),
        "average_drawdown": _format_percent(item.average_drawdown),
        "expectancy": _format_percent(item.expectancy),
    }


def _status_text(report: object) -> str:
    snapshot_count = int(getattr(report, "snapshot_count", 0) or 0)
    outcome_count = int(getattr(report, "outcome_count", 0) or 0)
    if snapshot_count == 0:
        return "No SnapshotPayloadV2 records found."
    if outcome_count == 0:
        return "No complete forward OHLCV windows available for statistics."
    return "Read-only SnapshotPayloadV2 statistics report."


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
