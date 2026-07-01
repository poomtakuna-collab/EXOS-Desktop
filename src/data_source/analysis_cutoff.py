from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from typing import Any, Mapping


@dataclass(frozen=True)
class AnalysisCutoffPolicyResult:
    chart_latest_date: str
    analysis_cutoff_date: str

    def to_dict(self) -> dict[str, str]:
        return {
            "chart_latest_date": self.chart_latest_date,
            "analysis_cutoff_date": self.analysis_cutoff_date,
        }


def determine_analysis_cutoff_date(
    rows: list[Mapping[str, Any]] | tuple[Mapping[str, Any], ...],
    *,
    as_of_date: date | str | None = None,
) -> AnalysisCutoffPolicyResult:
    latest = _latest_row_date(rows)
    if latest is None:
        return AnalysisCutoffPolicyResult(
            chart_latest_date="",
            analysis_cutoff_date="",
        )

    today = _parse_date(as_of_date) or date.today()
    cutoff = _previous_completed_trading_day(latest) if latest == today else latest
    return AnalysisCutoffPolicyResult(
        chart_latest_date=latest.isoformat(),
        analysis_cutoff_date=cutoff.isoformat(),
    )


def rows_through_analysis_cutoff(
    rows: list[Mapping[str, Any]] | tuple[Mapping[str, Any], ...],
    cutoff_date: str | date,
) -> list[dict[str, Any]]:
    cutoff = _parse_date(cutoff_date)
    if cutoff is None:
        return [dict(row) for row in rows if isinstance(row, Mapping)]
    return [
        dict(row)
        for row in rows
        if isinstance(row, Mapping)
        and (row_date := _parse_date(row.get("date"))) is not None
        and row_date <= cutoff
    ]


def _latest_row_date(
    rows: list[Mapping[str, Any]] | tuple[Mapping[str, Any], ...],
) -> date | None:
    parsed_dates = [
        parsed
        for row in rows
        if isinstance(row, Mapping)
        and (parsed := _parse_date(row.get("date"))) is not None
    ]
    return max(parsed_dates) if parsed_dates else None


def _previous_completed_trading_day(value: date) -> date:
    candidate = value - timedelta(days=1)
    while candidate.weekday() >= 5:
        candidate -= timedelta(days=1)
    return candidate


def _parse_date(value: object) -> date | None:
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        try:
            return date.fromisoformat(value[:10])
        except ValueError:
            return None
    return None
