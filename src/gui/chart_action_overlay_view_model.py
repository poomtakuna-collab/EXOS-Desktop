from __future__ import annotations

from typing import Any, Mapping


def build_chart_action_overlay(
    *,
    overall_assessment: tuple[tuple[str, str], ...],
    entry_strength: Mapping[str, Any],
    reasoning: Mapping[str, Any],
    historical_edge: tuple[tuple[str, str], ...],
    zones: tuple[dict[str, object], ...],
) -> dict[str, object]:
    overall = dict(overall_assessment)
    recommendation = _display_text(overall.get("Recommendation", ""))
    rating = _display_text(overall.get("Rating", ""))
    entry_label = _display_text(entry_strength.get("entry_strength_label"))
    entry_timing = _display_text(entry_strength.get("entry_timing"))
    state = _overlay_state(
        recommendation=recommendation,
        entry_timing=entry_timing,
        reasoning=reasoning,
    )
    zone = _active_zone(state, zones)
    zone_value = str(zone.get("value", "")).strip() if zone else ""
    price_range = zone_value if zone_value and zone_value != "Not available" else "No price zone available"
    summary_lines = _overlay_summary_lines(
        recommendation=recommendation,
        rating=rating,
        entry_label=entry_label,
        entry_timing=entry_timing,
        reasoning=reasoning,
        historical_edge=historical_edge,
        state=state,
    )
    return {
        "state": state,
        "title": _overlay_title(state),
        "price_range": price_range,
        "summary_lines": tuple(summary_lines),
    }


def _overlay_state(
    *,
    recommendation: str,
    entry_timing: str,
    reasoning: Mapping[str, Any],
) -> str:
    rec = recommendation.lower()
    timing = entry_timing.lower()
    summary = _format_text(reasoning.get("reasoning_summary")).lower()
    if rec == "avoid" or timing == "avoid":
        return "bearish"
    if rec in {"watch", "watchlist", "hold"} or "mixed" in summary:
        return "neutral"
    if rec in {"buy", "strong buy"}:
        return "bullish"
    return "neutral"


def _overlay_title(state: str) -> str:
    titles = {
        "bullish": "Bullish / Target Zone",
        "bearish": "Bearish / Risk Zone",
        "neutral": "Neutral / Wait Zone",
    }
    return titles.get(state, "Neutral / Wait Zone")


def _active_zone(state: str, zones: tuple[dict[str, object], ...]) -> dict[str, object]:
    title_fragment = {
        "bullish": "Target",
        "bearish": "Risk",
        "neutral": "Neutral",
    }.get(state, "Neutral")
    for zone in zones:
        if not isinstance(zone, dict):
            continue
        if title_fragment in str(zone.get("title", "")):
            return zone
    return {}


def _overlay_summary_lines(
    *,
    recommendation: str,
    rating: str,
    entry_label: str,
    entry_timing: str,
    reasoning: Mapping[str, Any],
    historical_edge: tuple[tuple[str, str], ...],
    state: str,
) -> list[str]:
    lines = [
        f"Recommendation: {recommendation or '-'}",
        f"Rating: {rating or '-'}",
        f"Entry: {entry_label or '-'} / {entry_timing or '-'}",
    ]
    edge_values = dict(historical_edge)
    edge_line = _short_edge_line(edge_values)
    if edge_line:
        lines.append(edge_line)

    if state == "bullish":
        source = reasoning.get("bullish_factors")
    elif state == "bearish":
        source = reasoning.get("bearish_factors") or reasoning.get("risk_notes")
    else:
        source = reasoning.get("neutral_factors") or reasoning.get("risk_notes")
    lines.extend(_short_reasons(source, limit=4))
    return lines[:7]


def _short_edge_line(values: dict[str, str]) -> str:
    pattern = values.get("Matched Pattern", "")
    win_rate = values.get("Win Rate", "")
    expectancy = values.get("Expectancy", "")
    parts = []
    if pattern and pattern not in {"-", "Not available"}:
        parts.append(pattern)
    if win_rate and win_rate != "-":
        parts.append(f"Win {win_rate}")
    if expectancy and expectancy != "-":
        parts.append(f"Exp {expectancy}")
    if not parts:
        return ""
    return "Historical Edge: " + " | ".join(parts)


def _short_reasons(value: object, *, limit: int) -> list[str]:
    if not isinstance(value, list):
        return []
    reasons = [str(item).strip().rstrip(".") for item in value if str(item).strip()]
    return [f"- {reason}" for reason in reasons[: max(limit, 0)]]


def _display_text(value: Any) -> str:
    text = _format_text(value)
    if text == "-":
        return text
    return text.replace("_", " ").replace("-", " ").title()


def _format_text(value: Any) -> str:
    if value is None:
        return "-"
    text = str(value).strip()
    return text if text else "-"
