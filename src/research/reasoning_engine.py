from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from src.statistics_engine import extract_feature_buckets


RESEARCH_REASONING_SCHEMA_KEYS = (
    "reasoning_summary",
    "bullish_factors",
    "bearish_factors",
    "neutral_factors",
    "historical_edge_explanation",
    "risk_notes",
    "confidence_explanation",
    "recommendation_reason",
)


def build_research_reasoning(research_payload: Mapping[str, Any]) -> dict[str, object]:
    payload = _snapshot_payload(research_payload)
    poom = _poom_payload(research_payload, payload)
    brain = _section(_section(payload, "analysis"), "brain_snapshot")
    indicators = _section(brain, "indicators")
    score = _score_payload(research_payload, payload)
    edge = _historical_edge(research_payload, payload)

    bullish = _bullish_factors(payload, poom, brain, indicators)
    bearish = _bearish_factors(payload, poom, brain, indicators)
    neutral = _neutral_factors(payload, poom, brain, indicators, edge)
    risk_notes = _risk_notes(payload, poom, edge)
    summary = _reasoning_summary(bullish, bearish, neutral, score)

    return {
        "reasoning_summary": summary,
        "bullish_factors": bullish,
        "bearish_factors": bearish,
        "neutral_factors": neutral,
        "historical_edge_explanation": _historical_edge_explanation(edge),
        "risk_notes": risk_notes,
        "confidence_explanation": _confidence_explanation(score),
        "recommendation_reason": _recommendation_reason(score, summary),
    }


def _bullish_factors(
    payload: Mapping[str, Any],
    poom: Mapping[str, Any],
    brain: Mapping[str, Any],
    indicators: Mapping[str, Any],
) -> list[str]:
    factors: list[str] = []
    close = _latest_close(payload)
    main_average = _first_number(indicators.get("ema50"), indicators.get("ema200"), indicators.get("ema20"))

    if _number(poom.get("ew_norm"), 0.0) > 0:
        factors.append("POOM Elliott Wave pressure is positive, which supports upside participation.")
    if _number(poom.get("volume_pressure"), 0.0) > 0:
        factors.append("Volume pressure is positive, showing demand is stronger than supply in the current setup.")
    if _number(poom.get("trend_slope"), 0.0) > 0:
        factors.append("Trend slope is positive, so short-term trend pressure is supportive.")
    if close is not None and main_average is not None and close > main_average:
        factors.append("Price remains above the main moving average, which keeps trend structure supportive.")
    if poom.get("squeeze_up"):
        factors.append("Squeeze pressure has released upward, adding momentum support.")
    if poom.get("bos_up") or poom.get("choch_up"):
        factors.append("Market structure has confirmed upward with a break or change of character.")
    elif _number(poom.get("msb_dir"), 0.0) > 0:
        factors.append("Market structure direction is bullish even without a fresh breakout confirmation.")
    if _state_is(_section(brain, "trend"), "bullish") or _text(indicators.get("ema_alignment")).lower() == "bullish":
        factors.append("Trend and moving-average alignment are bullish.")

    return factors


def _bearish_factors(
    payload: Mapping[str, Any],
    poom: Mapping[str, Any],
    brain: Mapping[str, Any],
    indicators: Mapping[str, Any],
) -> list[str]:
    factors: list[str] = []
    close = _latest_close(payload)
    main_average = _first_number(indicators.get("ema50"), indicators.get("ema200"), indicators.get("ema20"))

    if _number(poom.get("ew_norm"), 0.0) < 0:
        factors.append("POOM Elliott Wave pressure is negative, which weighs against upside continuation.")
    if _number(poom.get("volume_pressure"), 0.0) < 0:
        factors.append("Volume pressure is negative, showing supply is stronger than demand in the current setup.")
    if _number(poom.get("trend_slope"), 0.0) < 0:
        factors.append("Trend slope is negative, so short-term trend pressure is weak.")
    if close is not None and main_average is not None and close < main_average:
        factors.append("Price is below the main moving average, which weakens trend structure.")
    if poom.get("squeeze_down"):
        factors.append("Squeeze pressure has released downward, adding downside momentum risk.")
    if poom.get("bos_down") or poom.get("choch_down"):
        factors.append("Market structure has confirmed downward with a break or change of character.")
    elif _number(poom.get("msb_dir"), 0.0) < 0:
        factors.append("Market structure direction is bearish even without a fresh downside break.")
    if _state_is(_section(brain, "trend"), "bearish") or _text(indicators.get("ema_alignment")).lower() == "bearish":
        factors.append("Trend and moving-average alignment are bearish.")

    return factors


def _neutral_factors(
    payload: Mapping[str, Any],
    poom: Mapping[str, Any],
    brain: Mapping[str, Any],
    indicators: Mapping[str, Any],
    edge: Mapping[str, Any],
) -> list[str]:
    factors: list[str] = []
    close = _latest_close(payload)
    ema20 = _to_number(indicators.get("ema20"))
    ema50 = _to_number(indicators.get("ema50"))

    if poom.get("in_squeeze") and not poom.get("squeeze_up") and not poom.get("squeeze_down"):
        factors.append("Squeeze is still active, so momentum has not released in either direction.")
    if not any(poom.get(key) for key in ("bos_up", "bos_down", "choch_up", "choch_down")):
        factors.append("Market structure has not produced a fresh break or change of character.")
    if close is not None and ema20 is not None and ema50 is not None and min(ema20, ema50) <= close <= max(ema20, ema50):
        factors.append("Price is between key moving averages, which makes trend evidence mixed.")
    if _state_is(_section(brain, "trend"), "neutral") or _text(indicators.get("ema_alignment")).lower() == "neutral":
        factors.append("Trend alignment is neutral rather than clearly directional.")
    if not edge:
        factors.append("Historical edge data is not available yet.")
    elif _number(edge.get("sample_count"), 0.0) < 20:
        factors.append("Historical edge is limited because similar past setups do not yet have enough samples.")

    return factors


def _risk_notes(
    payload: Mapping[str, Any],
    poom: Mapping[str, Any],
    edge: Mapping[str, Any],
) -> list[str]:
    notes: list[str] = []
    support_resistance = _section(_section(payload, "context"), "support_resistance")
    if _to_number(support_resistance.get("nearest_support")) is None:
        notes.append("Nearest support is not available, so downside reference levels are incomplete.")
    if _to_number(support_resistance.get("nearest_resistance")) is None:
        notes.append("Nearest resistance is not available, so upside reference levels are incomplete.")
    if poom.get("squeeze_down") or poom.get("bos_down") or poom.get("choch_down"):
        notes.append("Downside structure or momentum is active; treat the current recommendation with added caution.")
    if edge and _number(edge.get("average_drawdown"), 0.0) < -5.0:
        notes.append("Similar historical setups carried meaningful drawdown, so risk control matters.")
    if not notes:
        notes.append("No major additional risk notes are present in the available research payload.")
    return notes


def _reasoning_summary(
    bullish: Sequence[str],
    bearish: Sequence[str],
    neutral: Sequence[str],
    score: Mapping[str, Any],
) -> str:
    recommendation = _display_text(_recommendation(score))
    if len(bullish) >= 4 and len(bearish) <= 1:
        setup = "strong"
    elif len(bearish) >= 4 and len(bullish) <= 1:
        setup = "weak"
    elif bullish and bearish:
        setup = "mixed"
    elif len(neutral) >= 2:
        setup = "unclear"
    elif bullish:
        setup = "constructive"
    elif bearish:
        setup = "defensive"
    else:
        setup = "unclear"

    if recommendation:
        return f"The current recommendation is {recommendation}. The setup is {setup} based on the available trend, momentum, structure, and historical evidence."
    return f"The setup is {setup} based on the available trend, momentum, structure, and historical evidence."


def _historical_edge_explanation(edge: Mapping[str, Any]) -> str:
    if not edge:
        return "Historical edge data is not available yet."

    label = _text(edge.get("label")) or _readable_statistics_bucket(
        _text(edge.get("feature_name")),
        _text(edge.get("bucket")),
    )
    sample_count = int(_number(edge.get("sample_count"), 0.0))
    win_rate = _number(edge.get("win_rate"), 0.0)
    average_return = _number(edge.get("average_return"), 0.0)
    expectancy = _number(edge.get("expectancy"), 0.0)

    if sample_count < 20:
        return f"Historical edge is limited for {label} because only {sample_count} similar samples are available."
    if win_rate >= 55.0 and average_return > 0 and expectancy > 0:
        return f"Historical edge supports the setup as supporting evidence: {label} has {sample_count} samples, a {_format_percent(win_rate)} win rate, and positive expectancy."
    if win_rate <= 45.0 or average_return < 0 or expectancy < 0:
        return f"Historical edge is cautious supporting evidence: {label} has {sample_count} samples and has not shown favorable forward results."
    return f"Historical edge is neutral supporting evidence: {label} has {sample_count} samples with mixed forward results."


def _confidence_explanation(score: Mapping[str, Any]) -> str:
    confidence = _first_number(score.get("confidence"), score.get("confidence_score"), score.get("probability"))
    if confidence is None:
        return "Confidence is not available in the current research payload."
    if 0 <= confidence <= 1:
        confidence *= 100
    if confidence >= 75:
        level = "high"
    elif confidence >= 55:
        level = "moderate"
    elif confidence >= 40:
        level = "limited"
    else:
        level = "low"
    return f"Confidence is {level} at {_format_percent(confidence)}, using the existing score or recommendation confidence."


def _recommendation_reason(score: Mapping[str, Any], summary: str) -> str:
    recommendation = _display_text(_recommendation(score))
    rating = _display_text(_first_text(score.get("rating"), score.get("bias"), score.get("trade_grade")))
    if recommendation and rating:
        return f"The existing recommendation is {recommendation} with a {rating} rating; this reasoning explains that existing output without changing it."
    if recommendation:
        return f"The existing recommendation is {recommendation}; this reasoning explains that existing output without changing it."
    return f"No existing recommendation was supplied. {summary}"


def _historical_edge(
    research_payload: Mapping[str, Any],
    payload: Mapping[str, Any],
) -> Mapping[str, Any]:
    explicit = _first_mapping(
        research_payload.get("historical_edge"),
        research_payload.get("pattern_edge"),
    )
    if explicit:
        return explicit

    stats = _first_present(research_payload.get("statistics"), research_payload.get("statistics_summary"))
    match = _best_matching_statistics_bucket(payload, stats)
    if match:
        return match

    pattern_stats = _first_mapping(research_payload.get("pattern_statistics"))
    for key in ("strong_historical_buckets", "weak_historical_buckets", "top_by_expectancy", "top_by_sample_count"):
        rows = _sequence(pattern_stats.get(key))
        if rows:
            row = _mapping(rows[0])
            if row:
                return row
    return {}


def _best_matching_statistics_bucket(
    payload: Mapping[str, Any],
    statistics_report: Any,
) -> Mapping[str, Any]:
    if statistics_report is None:
        return {}
    feature_buckets = set(extract_feature_buckets(payload))
    stats = tuple(_sequence(_field(statistics_report, "feature_stats")))
    matches = [
        _mapping(item)
        for item in stats
        if (_text(_field(item, "feature_name")), _text(_field(item, "bucket"))) in feature_buckets
    ]
    matches = [item for item in matches if item]
    if not matches:
        return {}
    return sorted(
        matches,
        key=lambda item: (
            int(_number(item.get("sample_count"), 0.0)),
            _number(item.get("expectancy"), 0.0),
        ),
        reverse=True,
    )[0]


def _snapshot_payload(research_payload: Mapping[str, Any]) -> Mapping[str, Any]:
    snapshot = research_payload.get("snapshot")
    if isinstance(snapshot, Mapping):
        return snapshot
    return research_payload


def _poom_payload(
    research_payload: Mapping[str, Any],
    payload: Mapping[str, Any],
) -> Mapping[str, Any]:
    return _first_mapping(
        research_payload.get("poom_combo"),
        research_payload.get("poom"),
        _section(_section(payload, "analysis"), "poom_combo"),
    )


def _score_payload(
    research_payload: Mapping[str, Any],
    payload: Mapping[str, Any],
) -> Mapping[str, Any]:
    brain = _section(_section(payload, "analysis"), "brain_snapshot")
    display = _section(payload, "display_summary")
    score = dict(
        _first_mapping(
            research_payload.get("score"),
            research_payload.get("recommendation"),
            _section(brain, "score"),
            _section(payload, "score"),
        )
    )
    if "recommendation" not in score:
        display_recommendation = _first_text(display.get("recommendation"), display.get("signal_type"))
        if display_recommendation:
            score["recommendation"] = display_recommendation
    if "confidence" not in score and display.get("confidence") is not None:
        score["confidence"] = display.get("confidence")
    return score


def _latest_close(payload: Mapping[str, Any]) -> float | None:
    rows = _section(_section(payload, "input"), "ohlcv_window").get("rows")
    if isinstance(rows, Sequence) and not isinstance(rows, (str, bytes)) and rows:
        last = rows[-1]
        if isinstance(last, Mapping):
            return _to_number(last.get("close"))
    return None


def _state_is(value: Mapping[str, Any], expected: str) -> bool:
    expected_lower = expected.lower()
    for key in ("state", "structure_state", "trend", "direction", "status"):
        if expected_lower in _text(value.get(key)).lower():
            return True
    return False


def _readable_statistics_bucket(feature_name: str, bucket: str) -> str:
    feature = _readable_feature_name(feature_name)
    value = _readable_bucket_value(feature_name, bucket)
    if feature and value:
        return f"{feature}: {value}"
    return value or feature or "similar setup"


def _readable_feature_name(feature_name: str) -> str:
    names = {
        "poom_ew": "Elliott Wave",
        "volume_pressure": "Volume Pressure",
        "poom_trend_slope": "POOM Trend Slope",
        "poom_squeeze": "Squeeze",
        "bos_choch": "Market Structure",
        "ema_alignment": "Moving Average Alignment",
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


def _recommendation(score: Mapping[str, Any]) -> str:
    return _first_text(score.get("recommendation"), score.get("signal_type"), score.get("action"))


def _section(value: Mapping[str, Any], key: str) -> Mapping[str, Any]:
    candidate = value.get(key)
    return candidate if isinstance(candidate, Mapping) else {}


def _first_mapping(*values: object) -> Mapping[str, Any]:
    for value in values:
        mapped = _mapping(value)
        if mapped:
            return mapped
    return {}


def _mapping(value: object) -> Mapping[str, Any]:
    if isinstance(value, Mapping):
        return value
    to_dict = getattr(value, "to_dict", None)
    if callable(to_dict):
        mapped = to_dict()
        return mapped if isinstance(mapped, Mapping) else {}
    return {}


def _sequence(value: object) -> Sequence[Any]:
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return value
    return ()


def _field(source: object, name: str) -> Any:
    if isinstance(source, Mapping):
        return source.get(name)
    return getattr(source, name, None)


def _first_present(*values: object) -> object:
    for value in values:
        if value is not None:
            return value
    return None


def _first_number(*values: object) -> float | None:
    for value in values:
        number = _to_number(value)
        if number is not None:
            return number
    return None


def _number(value: object, default: float) -> float:
    number = _to_number(value)
    return default if number is None else number


def _to_number(value: object) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _first_text(*values: object) -> str:
    for value in values:
        text = _text(value)
        if text:
            return text
    return ""


def _text(value: object) -> str:
    return str(value or "").strip()


def _display_text(value: object) -> str:
    text = _text(value)
    if not text:
        return ""
    return " ".join(part.capitalize() for part in text.replace("_", " ").split())


def _format_percent(value: float) -> str:
    return f"{value:.2f}%"
