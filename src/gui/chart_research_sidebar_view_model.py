from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any, Mapping

from src.gui.chart_action_overlay_view_model import build_chart_action_overlay
from src.gui.performance_view_model import DEFAULT_PERFORMANCE_DATABASE_PATH
from src.research import build_entry_strength, build_research_reasoning
from src.statistics_engine import build_statistics_report_from_connection, extract_feature_buckets


def load_chart_research_sidebar_view_model(
    *,
    symbol: str | None,
    database_path: Path | str = DEFAULT_PERFORMANCE_DATABASE_PATH,
) -> dict[str, object]:
    safe_symbol = str(symbol or "").strip().upper()
    if not safe_symbol:
        return empty_chart_research_sidebar_view_model("No symbol selected.")

    path = Path(database_path)
    if not path.exists():
        return empty_chart_research_sidebar_view_model("Research summary unavailable: database not found.", symbol=safe_symbol)

    connection = sqlite3.connect(path)
    try:
        snapshot = _latest_snapshot_payload(connection, safe_symbol)
        if snapshot is None:
            return empty_chart_research_sidebar_view_model("No saved SnapshotPayloadV2 found.", symbol=safe_symbol)
        statistics_report = build_statistics_report_from_connection(
            connection,
            min_sample_count=1,
            scope_mode="current_symbol",
            current_symbol=safe_symbol,
        )
    finally:
        connection.close()
    return build_chart_research_sidebar_view_model(
        snapshot["payload"],
        symbol=safe_symbol,
        snapshot_record=snapshot,
        statistics_report=statistics_report,
    )


def empty_chart_research_sidebar_view_model(
    status: str,
    *,
    symbol: str = "",
) -> dict[str, object]:
    display_symbol = symbol or "-"
    return {
        "title": "Research Summary",
        "status": status,
        "identity": (
            ("Symbol", display_symbol),
            ("Latest Snapshot Date", "-"),
            ("Timeframe", "-"),
        ),
        "overall_assessment": (
            ("Rating", "-"),
            ("Recommendation", "-"),
            ("Confidence", "-"),
        ),
        "poom_combo": _empty_items(("EW", "Volume Pressure", "POOM Trend Slope", "Squeeze", "BOS / CHoCH")),
        "trend_structure": _empty_items(("Trend", "EMA Alignment", "Market Structure", "Support", "Resistance")),
        "historical_edge": _empty_items(("Matched Pattern", "Sample Count", "Win Rate", "Average Return", "Expectancy", "Average Drawdown")),
        "reasoning": (),
        "summary_cards": (),
        "detail_sections": (),
        "chart_action_overlay": None,
        "zones": _empty_zones(),
    }


def build_chart_research_sidebar_view_model(
    payload: Mapping[str, Any],
    *,
    symbol: str = "",
    snapshot_record: Mapping[str, Any] | None = None,
    statistics_report: object | None = None,
) -> dict[str, object]:
    record = snapshot_record if isinstance(snapshot_record, Mapping) else {}
    identity = _section(payload, "identity")
    analysis = _section(payload, "analysis")
    brain = _section(analysis, "brain_snapshot")
    indicators = _section(brain, "indicators")
    score = _section(brain, "score")
    poom = _section(analysis, "poom_combo")
    context = _section(payload, "context")
    support_resistance = _section(context, "support_resistance")
    display_summary = _section(payload, "display_summary")
    latest_symbol = _first_text(record.get("symbol"), identity.get("symbol"), symbol).upper()
    latest_date = _first_text(record.get("market_date"), identity.get("market_date"))

    edge = _best_matching_statistics_bucket(payload, statistics_report)
    reasoning = build_research_reasoning(
        {
            "snapshot": payload,
            "statistics": statistics_report,
        }
    )
    entry_strength = build_entry_strength(
        {
            "snapshot": payload,
            "statistics": statistics_report,
            "reasoning": reasoning,
        }
    )
    overall_assessment = (
        ("Rating", _display_text(_first_text(score.get("rating"), score.get("bias"), display_summary.get("signal_type"))) or "-"),
        ("Recommendation", _display_text(_first_text(score.get("recommendation"), display_summary.get("recommendation"))) or "-"),
        ("Confidence", _confidence_text(score, display_summary)),
    )
    historical_edge = (
        ("Matched Pattern", edge["bucket_name"]),
        ("Sample Count", edge["sample_count"]),
        ("Win Rate", edge["win_rate"]),
        ("Average Return", edge["average_return"]),
        ("Expectancy", edge["expectancy"]),
        ("Average Drawdown", edge["average_drawdown"]),
    )
    reasoning_items = _reasoning_items(reasoning)
    zones = _zone_cards(analysis)
    return {
        "title": "Research Summary",
        "status": "Read-only chart research summary.",
        "identity": (
            ("Symbol", latest_symbol or "-"),
            ("Latest Snapshot Date", latest_date or "-"),
            ("Timeframe", _first_text(record.get("timeframe"), identity.get("timeframe")) or "-"),
        ),
        "overall_assessment": overall_assessment,
        "poom_combo": (
            ("EW", _format_value(poom.get("ew_norm"))),
            ("Volume Pressure", _format_value(poom.get("volume_pressure"))),
            ("POOM Trend Slope", _format_value(poom.get("trend_slope"))),
            ("Squeeze", _poom_squeeze_status(poom)),
            ("BOS / CHoCH", _poom_structure_status(poom)),
        ),
        "trend_structure": (
            ("Trend", _display_text(_state_text(_section(brain, "trend")))),
            ("EMA Alignment", _display_text(_format_text(indicators.get("ema_alignment")))),
            ("Market Structure", _display_text(_state_text(_section(brain, "market_structure")))),
            ("Support", _support_text(support_resistance)),
            ("Resistance", _resistance_text(support_resistance)),
        ),
        "historical_edge": historical_edge,
        "entry_strength": _entry_strength_items(entry_strength),
        "reasoning": reasoning_items,
        "summary_cards": _summary_cards(
            overall_assessment=overall_assessment,
            entry_strength=entry_strength,
            reasoning=reasoning,
            historical_edge=historical_edge,
        ),
        "chart_action_overlay": build_chart_action_overlay(
            overall_assessment=overall_assessment,
            entry_strength=entry_strength,
            reasoning=reasoning,
            historical_edge=historical_edge,
            zones=zones,
        ),
        "detail_sections": _detail_sections(
            identity=(
                ("Symbol", latest_symbol or "-"),
                ("Latest Snapshot Date", latest_date or "-"),
                ("Timeframe", _first_text(record.get("timeframe"), identity.get("timeframe")) or "-"),
            ),
            poom_combo=(
                ("EW", _format_value(poom.get("ew_norm"))),
                ("Volume Pressure", _format_value(poom.get("volume_pressure"))),
                ("POOM Trend Slope", _format_value(poom.get("trend_slope"))),
                ("Squeeze", _poom_squeeze_status(poom)),
                ("BOS / CHoCH", _poom_structure_status(poom)),
            ),
            trend_structure=(
                ("Trend", _display_text(_state_text(_section(brain, "trend")))),
                ("EMA Alignment", _display_text(_format_text(indicators.get("ema_alignment")))),
                ("Market Structure", _display_text(_state_text(_section(brain, "market_structure")))),
                ("Support", _support_text(support_resistance)),
                ("Resistance", _resistance_text(support_resistance)),
            ),
            historical_edge=historical_edge,
            reasoning=reasoning_items,
            zones=zones,
        ),
        "zones": zones,
    }


def _latest_snapshot_payload(
    connection: sqlite3.Connection,
    symbol: str,
) -> dict[str, Any] | None:
    if not _table_exists(connection, "daily_research_snapshots"):
        return None
    row = connection.execute(
        """
        SELECT snapshot_record_id, symbol, market_date, timeframe, canonical_snapshot_json
        FROM daily_research_snapshots
        WHERE symbol = ?
        ORDER BY market_date DESC, created_at DESC
        LIMIT 1
        """,
        (symbol,),
    ).fetchone()
    if row is None:
        return None
    payload = json.loads(row[4])
    if not isinstance(payload, dict):
        return None
    if _section(payload, "identity").get("payload_schema_version") != "snapshot_payload_v2":
        return None
    return {
        "snapshot_record_id": row[0],
        "symbol": row[1],
        "market_date": row[2],
        "timeframe": row[3],
        "payload": payload,
    }


def _best_matching_statistics_bucket(
    payload: Mapping[str, Any],
    statistics_report: object | None,
) -> dict[str, str]:
    feature_buckets = set(extract_feature_buckets(payload))
    stats = tuple(getattr(statistics_report, "feature_stats", ()) or ())
    matches = [
        item
        for item in stats
        if (getattr(item, "feature_name", ""), getattr(item, "bucket", "")) in feature_buckets
    ]
    if not matches:
        return {
            "bucket_name": "Not available",
            "sample_count": "-",
            "win_rate": "-",
            "average_return": "-",
            "expectancy": "-",
            "average_drawdown": "-",
        }
    best = sorted(
        matches,
        key=lambda item: (
            int(getattr(item, "sample_count", 0)),
            float(getattr(item, "expectancy", 0.0)),
        ),
        reverse=True,
    )[0]
    return {
        "bucket_name": _readable_statistics_bucket(
            str(getattr(best, "feature_name", "")),
            str(getattr(best, "bucket", "")),
        ),
        "sample_count": str(best.sample_count),
        "win_rate": _format_percent(best.win_rate),
        "average_return": _format_percent(best.average_return),
        "expectancy": _format_percent(best.expectancy),
        "average_drawdown": _format_percent(best.average_drawdown),
    }


def _zone_cards(analysis: Mapping[str, Any]) -> tuple[dict[str, object], ...]:
    target = _target_zone(_section(analysis, "target_zone"))
    neutral = _neutral_zone(analysis)
    risk = _risk_zone(_section(analysis, "risk_zone"))
    return (
        {
            "title": "Target / Upside Zone",
            "tone": "upside",
            "value": target or "Not available",
        },
        {
            "title": "Neutral / Decision Zone",
            "tone": "neutral",
            "value": neutral or "Not available",
        },
        {
            "title": "Risk / Downside Zone",
            "tone": "risk",
            "value": risk or "Not available",
        },
    )


def _target_zone(value: Mapping[str, Any]) -> str:
    zone = _section(value, "target_zone")
    candidates = zone or value
    low = _number(_first_present(candidates.get("low"), candidates.get("base"), candidates.get("target_1")))
    high = _number(_first_present(candidates.get("high"), candidates.get("target"), candidates.get("target_2")))
    if low is None and high is None:
        return ""
    if low is not None and high is not None and low != high:
        return f"{_format_value(low)} - {_format_value(high)}"
    return _format_value(_first_present(high, low))


def _risk_zone(value: Mapping[str, Any]) -> str:
    zone = _section(value, "risk_zone")
    candidates = zone or value
    low = _number(_first_present(candidates.get("low"), candidates.get("risk_2"), candidates.get("stop")))
    high = _number(_first_present(candidates.get("high"), candidates.get("base"), candidates.get("risk_1")))
    if low is None and high is None:
        return ""
    if low is not None and high is not None and low != high:
        return f"{_format_value(high)} - {_format_value(low)}"
    return _format_value(_first_present(high, low))


def _neutral_zone(analysis: Mapping[str, Any]) -> str:
    projection = _section(analysis, "projection")
    low = _number(projection.get("neutral_low"))
    high = _number(projection.get("neutral_high"))
    if low is not None and high is not None:
        return f"{_format_value(low)} - {_format_value(high)}"
    return ""


def _poom_squeeze_status(poom: Mapping[str, Any]) -> str:
    if poom.get("squeeze_up"):
        return "Bullish Squeeze Release"
    if poom.get("squeeze_down"):
        return "Bearish Squeeze Release"
    if poom.get("in_squeeze"):
        return "Squeeze Active"
    return "No Active Squeeze"


def _poom_structure_status(poom: Mapping[str, Any]) -> str:
    parts: list[str] = []
    if poom.get("bos_up"):
        parts.append("Break of Structure Up")
    if poom.get("bos_down"):
        parts.append("Break of Structure Down")
    if poom.get("choch_up"):
        parts.append("Change of Character Up")
    if poom.get("choch_down"):
        parts.append("Change of Character Down")
    if parts:
        return " | ".join(parts)
    direction = _number(poom.get("msb_dir"))
    if direction is not None and direction > 0:
        return "Bullish Structure"
    if direction is not None and direction < 0:
        return "Bearish Structure"
    return "Neutral Structure"


def _support_text(value: Mapping[str, Any]) -> str:
    support = _format_value(value.get("nearest_support"))
    return support if support != "-" else "Not available"


def _resistance_text(value: Mapping[str, Any]) -> str:
    resistance = _format_value(value.get("nearest_resistance"))
    return resistance if resistance != "-" else "Not available"


def _confidence_text(
    score: Mapping[str, Any],
    display_summary: Mapping[str, Any],
) -> str:
    value = _first_present(
        score.get("confidence"),
        score.get("confidence_score"),
        display_summary.get("confidence"),
        display_summary.get("probability"),
    )
    number = _number(value)
    if number is None:
        return _display_text(_format_text(value))
    if 0 <= number <= 1:
        return _format_percent(number * 100)
    return _format_percent(number)


def _readable_statistics_bucket(feature_name: str, bucket: str) -> str:
    feature = _readable_feature_name(feature_name)
    value = _readable_bucket_value(feature_name, bucket)
    if feature and value:
        return f"{feature}: {value}"
    return value or feature or "Not available"


def _readable_feature_name(feature_name: str) -> str:
    names = {
        "poom_ew": "Elliott Wave",
        "volume_pressure": "Volume Pressure",
        "poom_trend_slope": "POOM Trend Slope",
        "poom_squeeze": "Squeeze",
        "bos_choch": "BOS / CHoCH",
        "ema_alignment": "EMA Alignment",
        "price_vs_ema20": "Price vs EMA20",
        "price_vs_ema50": "Price vs EMA50",
        "price_vs_ema200": "Price vs EMA200",
        "trend_state": "Trend",
        "market_structure": "Market Structure",
        "support_resistance_distance": "Support / Resistance Distance",
    }
    return names.get(feature_name, _display_text(feature_name))


def _readable_bucket_value(feature_name: str, bucket: str) -> str:
    exact = {
        "none": "No Active Squeeze",
        "in_squeeze": "Squeeze Active",
        "release_up": "Bullish Squeeze Release",
        "release_down": "Bearish Squeeze Release",
        "bos_up": "Break of Structure Up",
        "bos_down": "Break of Structure Down",
        "choch_up": "Change of Character Up",
        "choch_down": "Change of Character Down",
        "bullish": "Bullish",
        "bearish": "Bearish",
        "neutral": "Neutral",
        "above": "Above",
        "below": "Below",
        "at": "At",
        "unknown": "Unknown",
    }
    if feature_name == "poom_squeeze" and bucket == "none":
        return "No Active Squeeze"
    if bucket in exact:
        return exact[bucket]
    if ":" in bucket:
        direction, value_bucket = bucket.split(":", 1)
        return f"{_display_text(direction)} ({_display_bucket_range(value_bucket)})"
    return _display_text(bucket)


def _display_bucket_range(value: str) -> str:
    ranges = {
        "0_to_10": "0 to 10",
        "10_to_25": "10 to 25",
        "25_to_50": "25 to 50",
        "50_plus": "50+",
        "0_to_2": "0 to 2%",
        "2_to_5": "2 to 5%",
        "5_to_10": "5 to 10%",
        "10_plus": "10%+",
    }
    return ranges.get(value, _display_text(value))


def _state_text(value: Mapping[str, Any]) -> str:
    for key in ("state", "structure_state", "trend", "direction", "status"):
        text = _format_text(value.get(key))
        if text != "-":
            return text
    return "-"


def _section(value: Mapping[str, Any], key: str) -> Mapping[str, Any]:
    candidate = value.get(key)
    return candidate if isinstance(candidate, Mapping) else {}


def _empty_items(labels: tuple[str, ...]) -> tuple[tuple[str, str], ...]:
    return tuple((label, "-") for label in labels)


def _empty_zones() -> tuple[dict[str, object], ...]:
    return (
        {"title": "Target / Upside Zone", "tone": "upside", "value": "Not available"},
        {"title": "Neutral / Decision Zone", "tone": "neutral", "value": "Not available"},
        {"title": "Risk / Downside Zone", "tone": "risk", "value": "Not available"},
    )


def _summary_cards(
    *,
    overall_assessment: tuple[tuple[str, str], ...],
    entry_strength: Mapping[str, Any],
    reasoning: Mapping[str, Any],
    historical_edge: tuple[tuple[str, str], ...],
) -> tuple[dict[str, object], ...]:
    cards: list[dict[str, object]] = []
    overall_items = _without_placeholder_items(overall_assessment)
    if overall_items:
        cards.append({"title": "EXOS Summary", "expanded": True, "items": overall_items})

    entry_items = _entry_strength_items(entry_strength)
    if entry_items:
        cards.append({"title": "Entry Strength", "expanded": True, "items": entry_items})

    recommendation_reason = _format_text(reasoning.get("recommendation_reason"))
    if recommendation_reason != "-":
        cards.append({"title": "Why / Reasoning", "expanded": True, "body": recommendation_reason})

    historical_edge_text = _format_text(reasoning.get("historical_edge_explanation"))
    edge_items = _historical_edge_summary_items(historical_edge)
    if historical_edge_text != "-" or edge_items:
        cards.append(
            {
                "title": "Historical Edge Summary",
                "expanded": True,
                "items": edge_items,
                "body": "" if historical_edge_text == "-" else historical_edge_text,
            }
        )
    return tuple(cards)


def _detail_sections(
    *,
    identity: tuple[tuple[str, str], ...],
    poom_combo: tuple[tuple[str, str], ...],
    trend_structure: tuple[tuple[str, str], ...],
    historical_edge: tuple[tuple[str, str], ...],
    reasoning: tuple[tuple[str, str], ...],
    zones: tuple[dict[str, object], ...],
) -> tuple[dict[str, object], ...]:
    sections: list[dict[str, object]] = []
    for title, items in (
        ("Snapshot", identity),
        ("POOM Raw", poom_combo),
        ("Technical Details", trend_structure),
        ("Full Historical Edge", historical_edge),
    ):
        visible_items = _without_placeholder_items(items)
        if visible_items:
            sections.append({"title": title, "expanded": False, "items": visible_items})
    if reasoning:
        sections.append({"title": "Full Reasoning", "expanded": False, "items": reasoning})
    visible_zones = tuple(
        zone for zone in zones
        if isinstance(zone, dict) and str(zone.get("value", "")).strip() not in {"", "Not available"}
    )
    if visible_zones:
        sections.append({"title": "Zones", "expanded": False, "zones": visible_zones})
    return tuple(sections)


def _entry_strength_items(entry_strength: Mapping[str, Any]) -> tuple[tuple[str, str], ...]:
    score = entry_strength.get("entry_strength_score")
    label = _format_text(entry_strength.get("entry_strength_label"))
    timing = _format_text(entry_strength.get("entry_timing"))
    items = (
        ("Strength", f"{score} / 100" if score is not None else "-"),
        ("Label", label),
        ("Timing", timing),
    )
    return _without_placeholder_items(items)


def _historical_edge_summary_items(
    historical_edge: tuple[tuple[str, str], ...],
) -> tuple[tuple[str, str], ...]:
    values = dict(historical_edge)
    return _without_placeholder_items(
        (
            ("Matched Pattern", values.get("Matched Pattern", "-")),
            ("Samples", values.get("Sample Count", "-")),
            ("Win Rate", values.get("Win Rate", "-")),
            ("Expectancy", values.get("Expectancy", "-")),
        )
    )


def _without_placeholder_items(items: tuple[tuple[str, str], ...]) -> tuple[tuple[str, str], ...]:
    return tuple(
        (label, value)
        for label, value in items
        if str(value).strip() not in {"", "-", "Not available"}
    )


def _reasoning_items(reasoning: Mapping[str, Any]) -> tuple[tuple[str, str], ...]:
    items: list[tuple[str, str]] = []
    recommendation_reason = _format_text(reasoning.get("recommendation_reason"))
    if recommendation_reason != "-":
        items.append(("Recommendation Reason", recommendation_reason))
    for key, label in (
        ("bullish_factors", "Bullish Factors"),
        ("bearish_factors", "Bearish Factors"),
        ("risk_notes", "Risk Notes"),
    ):
        text = _bullet_text(reasoning.get(key))
        if text:
            items.append((label, text))
    historical_edge = _format_text(reasoning.get("historical_edge_explanation"))
    if historical_edge != "-":
        items.append(("Historical Edge Explanation", historical_edge))
    return tuple(items)


def _bullet_text(value: object) -> str:
    if not isinstance(value, list):
        return ""
    lines = [str(item).strip() for item in value if str(item).strip()]
    return "\n".join(f"- {line}" for line in lines)


def _first_text(*values: object) -> str:
    for value in values:
        text = str(value or "").strip()
        if text:
            return text
    return ""


def _first_present(*values: object) -> object:
    for value in values:
        if value not in (None, ""):
            return value
    return None


def _format_text(value: object) -> str:
    text = str(value or "").strip()
    return text or "-"


def _display_text(value: object) -> str:
    text = str(value or "").strip()
    if not text or text == "-":
        return "-"
    return " ".join(part.capitalize() for part in text.replace("_", " ").split())


def _format_value(value: object) -> str:
    number = _number(value)
    if number is None:
        return _format_text(value)
    return f"{number:.4f}".rstrip("0").rstrip(".")


def _format_percent(value: object) -> str:
    number = _number(value)
    if number is None:
        return "-"
    return f"{number:.2f}%"


def _number(value: object) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _table_exists(connection: sqlite3.Connection, table_name: str) -> bool:
    row = connection.execute(
        """
        SELECT 1
        FROM sqlite_master
        WHERE type = 'table'
          AND name = ?
        LIMIT 1
        """,
        (table_name,),
    ).fetchone()
    return row is not None
