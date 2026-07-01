from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from src.analysis import build_prediction_summary, build_strategy_summary
from src.context import (
    calculate_market_context,
    calculate_relative_strength_context,
    calculate_sector_context,
    calculate_support_resistance_context,
    calculate_volume_context,
)


PLACEHOLDER_TEXT = "-"
SIGNAL_SUMMARY_PLACEHOLDER = "Signal summary is not available in v1."


def build_research_view_model(
    *,
    selected_symbol: str | None = None,
    indicator_snapshot: Mapping[str, Any] | None = None,
) -> dict[str, object]:
    symbol = str(selected_symbol or "").strip().upper()
    snapshot = indicator_snapshot if isinstance(indicator_snapshot, Mapping) else {}
    prediction_summary = build_prediction_summary()
    strategy_summary = build_strategy_summary(prediction_summary)

    market_context = calculate_market_context(snapshot=snapshot).to_dict()
    sector_context = calculate_sector_context().to_dict()
    relative_strength = calculate_relative_strength_context().to_dict()
    volume_context = calculate_volume_context(snapshot=snapshot).to_dict()
    support_resistance = calculate_support_resistance_context(
        snapshot=snapshot,
        indicators=snapshot,
    ).to_dict()

    cards = (
        _card(
            "symbol",
            "Symbol",
            (
                _item("Selected", symbol),
                _item("Data", "loaded" if snapshot else "not loaded"),
            ),
        ),
        _card(
            "market_context",
            "Market Context",
            (
                _item("Trend", market_context.get("trend")),
                _item("Momentum", market_context.get("momentum")),
                _item("Volatility", market_context.get("volatility")),
                _item("Risk State", market_context.get("risk_state")),
            ),
        ),
        _card(
            "sector_context",
            "Sector Context",
            (
                _item("Sector", sector_context.get("sector_symbol")),
                _item("Trend", sector_context.get("trend")),
                _item("Relative", sector_context.get("relative_to_market")),
            ),
        ),
        _card(
            "relative_strength",
            "Relative Strength",
            (
                _item("Vs Market", relative_strength.get("stock_vs_market")),
                _item("Vs Sector", relative_strength.get("stock_vs_sector")),
                _item("Rating", relative_strength.get("rating")),
            ),
        ),
        _card(
            "volume_context",
            "Volume",
            (
                _item("Relative Volume", volume_context.get("relative_volume")),
                _item("State", volume_context.get("volume_state")),
            ),
        ),
        _card(
            "support_resistance",
            "Support / Resistance",
            (
                _item("Support", support_resistance.get("nearest_support")),
                _item("Resistance", support_resistance.get("nearest_resistance")),
                _item(
                    "Support Distance",
                    support_resistance.get("support_distance_pct"),
                    suffix="%",
                ),
                _item(
                    "Resistance Distance",
                    support_resistance.get("resistance_distance_pct"),
                    suffix="%",
                ),
            ),
        ),
        _card(
            "prediction_summary",
            "Prediction",
            (
                _item("Confidence", prediction_summary.get("confidence"), suffix="%"),
                _item("Evidence", prediction_summary.get("evidence_count")),
                _item("Similarity", prediction_summary.get("best_similarity"), suffix="%"),
                _item("Target Zone", prediction_summary.get("target_zone")),
                _item("Risk Zone", prediction_summary.get("risk_zone")),
            ),
        ),
        _card(
            "strategy_summary",
            "Strategy",
            (
                _item("Bias", strategy_summary.get("market_bias")),
                _item("Risk", strategy_summary.get("risk_level")),
                _item("Reward/Risk", strategy_summary.get("reward_risk_ratio")),
                _item("Notes", strategy_summary.get("notes")),
            ),
        ),
        _card(
            "signal_summary",
            "Signal Summary",
            (
                _item("Status", SIGNAL_SUMMARY_PLACEHOLDER),
                _item("Confidence", None),
                _item("Score", None),
            ),
        ),
    )

    return {
        "symbol": symbol or "No symbol selected",
        "has_symbol": bool(symbol),
        "has_snapshot": bool(snapshot),
        "cards": cards,
        "status": _status_text(symbol=symbol, snapshot=snapshot),
    }


def _status_text(
    *,
    symbol: str,
    snapshot: Mapping[str, Any],
) -> str:
    if not symbol:
        return "Select a dashboard symbol to view research context."
    if not snapshot:
        return "Selected symbol has no loaded deterministic research data yet."
    return "Read-only deterministic research context."


def _card(
    card_id: str,
    title: str,
    items: tuple[dict[str, object], ...],
) -> dict[str, object]:
    return {
        "id": card_id,
        "title": title,
        "items": items,
    }


def _item(
    label: str,
    value: Any,
    *,
    suffix: str = "",
) -> dict[str, object]:
    placeholder = _is_placeholder(value)
    return {
        "label": label,
        "value": PLACEHOLDER_TEXT if placeholder else _format_value(value, suffix=suffix),
        "is_placeholder": placeholder,
    }


def _format_value(value: Any, *, suffix: str = "") -> str:
    if isinstance(value, float):
        formatted = f"{value:.4f}".rstrip("0").rstrip(".")
        return f"{formatted}{suffix}"
    if isinstance(value, int):
        return f"{value}{suffix}"
    if isinstance(value, Mapping):
        return _format_mapping(value)
    if isinstance(value, (list, tuple)):
        return _format_sequence(value)
    return str(value)


def _format_mapping(values: Mapping[str, Any]) -> str:
    visible_items = [
        f"{_format_label(str(key))}: {_format_value(value)}"
        for key, value in values.items()
        if not _is_placeholder(value)
    ]
    return "; ".join(visible_items) if visible_items else PLACEHOLDER_TEXT


def _format_sequence(values: list[Any] | tuple[Any, ...]) -> str:
    visible_items = [
        str(value)
        for value in values
        if not _is_placeholder(value)
    ]
    return "; ".join(visible_items) if visible_items else PLACEHOLDER_TEXT


def _format_label(value: str) -> str:
    return value.replace("_", " ").replace("-", " ").title()


def _is_placeholder(value: Any) -> bool:
    if value is None:
        return True
    if value in ("", {}, [], ()):
        return True
    if isinstance(value, str) and value.strip().lower() in {"unknown", "none", "n/a"}:
        return True
    return False
