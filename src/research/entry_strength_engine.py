from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from src.research.reasoning_engine import build_research_reasoning
from src.statistics_engine import extract_feature_buckets


ENTRY_STRENGTH_SCHEMA_KEYS = (
    "entry_strength_score",
    "entry_strength_label",
    "entry_timing",
    "entry_reasons",
    "entry_risks",
)


def build_entry_strength(research_payload: Mapping[str, Any]) -> dict[str, object]:
    payload = _snapshot_payload(research_payload)
    poom = _poom_payload(research_payload, payload)
    brain = _section(_section(payload, "analysis"), "brain_snapshot")
    indicators = _section(brain, "indicators")
    reasoning = _reasoning_payload(research_payload)
    edge = _historical_edge(research_payload, payload)

    score = 50
    reasons: list[str] = []
    risks: list[str] = []

    score = _apply_poom_score(score, poom, reasons, risks)
    score = _apply_trend_score(score, payload, brain, indicators, reasons, risks)
    score = _apply_reasoning_score(score, reasoning, reasons, risks)
    score = _apply_historical_edge_score(score, edge, reasons, risks)

    safe_score = _clamp(score)
    timing = _entry_timing(safe_score, payload, poom, indicators, reasoning)
    if timing == "Early":
        safe_score = min(safe_score, 84)
    elif timing == "Avoid":
        safe_score = min(safe_score, 39)
    if timing == "Late":
        risks.append("Entry timing may be late because price is extended from the nearest moving-average reference.")
    elif timing == "Early":
        risks.append("Entry timing is early because momentum or structure confirmation is incomplete.")
    elif timing == "Avoid":
        risks.append("Entry timing should be avoided until downside pressure or weak evidence improves.")

    if not reasons:
        reasons.append("Entry strength is based on limited available setup evidence.")
    if not risks:
        risks.append("No major entry-specific risks are present in the available research payload.")

    return {
        "entry_strength_score": safe_score,
        "entry_strength_label": _entry_strength_label(safe_score),
        "entry_timing": timing,
        "entry_reasons": reasons,
        "entry_risks": risks,
    }


def _apply_poom_score(
    score: int,
    poom: Mapping[str, Any],
    reasons: list[str],
    risks: list[str],
) -> int:
    if _number(poom.get("ew_norm"), 0.0) > 0:
        score += 8
        reasons.append("POOM Elliott Wave pressure supports entry strength.")
    elif _number(poom.get("ew_norm"), 0.0) < 0:
        score -= 8
        risks.append("POOM Elliott Wave pressure is negative.")

    if _number(poom.get("volume_pressure"), 0.0) > 0:
        score += 8
        reasons.append("Volume pressure supports entry because demand is positive.")
    elif _number(poom.get("volume_pressure"), 0.0) < 0:
        score -= 8
        risks.append("Volume pressure is negative, so demand confirmation is weak.")

    if _number(poom.get("trend_slope"), 0.0) > 0:
        score += 10
        reasons.append("Trend slope is positive, which improves entry quality.")
    elif _number(poom.get("trend_slope"), 0.0) < 0:
        score -= 10
        risks.append("Trend slope is negative, which weakens entry quality.")

    if poom.get("squeeze_up"):
        score += 12
        reasons.append("Squeeze has released upward, giving the setup actionable momentum confirmation.")
    elif poom.get("squeeze_down"):
        score -= 14
        risks.append("Squeeze has released downward, which argues against entry.")
    elif poom.get("in_squeeze"):
        score -= 4
        risks.append("Squeeze is still active, so timing may be early.")

    if poom.get("bos_up") or poom.get("choch_up"):
        score += 12
        reasons.append("Market structure has confirmed upward with a break or change of character.")
    elif poom.get("bos_down") or poom.get("choch_down"):
        score -= 14
        risks.append("Market structure has confirmed downward.")
    elif _number(poom.get("msb_dir"), 0.0) > 0:
        score += 5
        reasons.append("Market structure direction is constructive.")
    elif _number(poom.get("msb_dir"), 0.0) < 0:
        score -= 5
        risks.append("Market structure direction is bearish.")

    return score


def _apply_trend_score(
    score: int,
    payload: Mapping[str, Any],
    brain: Mapping[str, Any],
    indicators: Mapping[str, Any],
    reasons: list[str],
    risks: list[str],
) -> int:
    close = _latest_close(payload)
    main_average = _first_number(indicators.get("ema50"), indicators.get("ema200"), indicators.get("ema20"))
    if close is not None and main_average is not None:
        if close > main_average:
            score += 7
            reasons.append("Price is above the main moving-average reference.")
        elif close < main_average:
            score -= 7
            risks.append("Price is below the main moving-average reference.")

    trend_text = _state_text(_section(brain, "trend"), indicators.get("ema_alignment"))
    if "bullish" in trend_text:
        score += 6
        reasons.append("Trend alignment is bullish.")
    elif "bearish" in trend_text:
        score -= 6
        risks.append("Trend alignment is bearish.")
    elif "neutral" in trend_text:
        score -= 2
        risks.append("Trend alignment is neutral, so entry quality is less decisive.")

    return score


def _apply_reasoning_score(
    score: int,
    reasoning: Mapping[str, Any],
    reasons: list[str],
    risks: list[str],
) -> int:
    bullish_count = len(_string_list(reasoning.get("bullish_factors")))
    bearish_count = len(_string_list(reasoning.get("bearish_factors")))
    risk_count = len(_string_list(reasoning.get("risk_notes")))

    if bullish_count >= 4:
        score += 8
        reasons.append("Reasoning layer shows multiple bullish factors aligned.")
    elif bullish_count >= 2:
        score += 4
        reasons.append("Reasoning layer shows some bullish support.")

    if bearish_count >= 4:
        score -= 10
        risks.append("Reasoning layer shows several bearish factors.")
    elif bearish_count >= 1:
        score -= 4
        risks.append("Reasoning layer includes bearish evidence that reduces entry quality.")

    meaningful_risks = [
        item for item in _string_list(reasoning.get("risk_notes"))
        if "No major additional risk notes" not in item
    ]
    if risk_count and meaningful_risks:
        score -= min(len(meaningful_risks) * 3, 9)
        risks.append("Reasoning layer includes entry-relevant risk notes.")

    return score


def _apply_historical_edge_score(
    score: int,
    edge: Mapping[str, Any],
    reasons: list[str],
    risks: list[str],
) -> int:
    if not edge:
        risks.append("Historical edge is not available, so entry strength has less supporting evidence.")
        return score - 3

    sample_count = int(_number(edge.get("sample_count"), 0.0))
    win_rate = _number(edge.get("win_rate"), 0.0)
    average_return = _number(edge.get("average_return"), 0.0)
    expectancy = _number(edge.get("expectancy"), 0.0)
    average_drawdown = _number(edge.get("average_drawdown"), 0.0)

    if sample_count < 20:
        risks.append("Historical edge is under-sampled, so entry evidence is provisional.")
        score -= 4
    elif win_rate >= 55.0 and average_return > 0 and expectancy > 0:
        reasons.append("Historical edge supports entry strength as secondary evidence.")
        score += 8
    elif win_rate <= 45.0 or average_return < 0 or expectancy < 0:
        risks.append("Historical edge is unfavorable as secondary evidence.")
        score -= 8

    if average_drawdown < -6.0:
        risks.append("Similar historical setups had meaningful drawdown.")
        score -= 4

    return score


def _entry_timing(
    score: int,
    payload: Mapping[str, Any],
    poom: Mapping[str, Any],
    indicators: Mapping[str, Any],
    reasoning: Mapping[str, Any],
) -> str:
    bearish_count = len(_string_list(reasoning.get("bearish_factors")))
    if score < 40 or poom.get("squeeze_down") or poom.get("bos_down") or poom.get("choch_down") or bearish_count >= 4:
        return "Avoid"
    if _is_late(payload, indicators) and score >= 60:
        return "Late"
    if poom.get("in_squeeze") and not poom.get("squeeze_up") and not poom.get("squeeze_down"):
        return "Early"
    if not any(poom.get(key) for key in ("bos_up", "choch_up", "squeeze_up")) and score < 75:
        return "Early"
    return "Valid"


def _is_late(payload: Mapping[str, Any], indicators: Mapping[str, Any]) -> bool:
    close = _latest_close(payload)
    if close is None:
        return False
    ema20 = _to_number(indicators.get("ema20"))
    ema50 = _to_number(indicators.get("ema50"))
    if ema20 is not None and ema20 > 0 and close >= ema20 * 1.08:
        return True
    return ema50 is not None and ema50 > 0 and close >= ema50 * 1.12


def _entry_strength_label(score: int) -> str:
    if score >= 85:
        return "Excellent"
    if score >= 65:
        return "Strong"
    if score >= 40:
        return "Moderate"
    return "Weak"


def _reasoning_payload(research_payload: Mapping[str, Any]) -> Mapping[str, Any]:
    reasoning = research_payload.get("reasoning")
    if isinstance(reasoning, Mapping):
        return reasoning
    return build_research_reasoning(research_payload)


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
    stats = research_payload.get("statistics") or research_payload.get("statistics_summary")
    match = _best_matching_statistics_bucket(payload, stats)
    return match if match else {}


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


def _latest_close(payload: Mapping[str, Any]) -> float | None:
    rows = _section(_section(payload, "input"), "ohlcv_window").get("rows")
    if isinstance(rows, Sequence) and not isinstance(rows, (str, bytes)) and rows:
        last = rows[-1]
        if isinstance(last, Mapping):
            return _to_number(last.get("close"))
    return None


def _state_text(value: Mapping[str, Any], fallback: object = "") -> str:
    for key in ("state", "structure_state", "trend", "direction", "status"):
        text = _text(value.get(key)).lower()
        if text:
            return text
    return _text(fallback).lower()


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


def _string_list(value: object) -> list[str]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


def _field(source: object, name: str) -> Any:
    if isinstance(source, Mapping):
        return source.get(name)
    return getattr(source, name, None)


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


def _text(value: object) -> str:
    return str(value or "").strip()


def _clamp(value: int) -> int:
    return max(0, min(100, int(value)))
