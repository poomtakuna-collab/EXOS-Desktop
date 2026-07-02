from __future__ import annotations

from collections.abc import Mapping
from dataclasses import replace
from datetime import date
from pathlib import Path
import sqlite3
from typing import Any

from src.analysis import build_prediction_summary, build_strategy_summary
from src.analysis_pipeline import AnalysisPipelineV2Request, PipelineConfig, analyze_symbol_v2
from src.canonical_result import (
    CanonicalContextResultV1,
    CanonicalResultV1,
    CanonicalSignalSummaryV1,
    CanonicalStrategyResultV1,
    build_canonical_result_v1,
)
from src.context import (
    calculate_market_context,
    calculate_relative_strength_context,
    calculate_sector_context,
    calculate_support_resistance_context,
    calculate_volume_context,
)
from src.data import REQUIRED_ROW_COUNT
from src.data_source import (
    MarketDataRequest,
    MarketDataSource,
    SQLiteDataSource,
    determine_analysis_cutoff_date,
    rows_through_analysis_cutoff,
)


PLACEHOLDER_TEXT = "-"
SIGNAL_SUMMARY_PLACEHOLDER = "Snapshot summary is not available in v1."
DEFAULT_RESEARCH_DATABASE_PATH = Path("database") / "exos.db"
DEFAULT_RESEARCH_TIMEFRAME = "1D"


def build_research_view_model(
    *,
    selected_symbol: str | None = None,
    indicator_snapshot: Mapping[str, Any] | None = None,
    analysis_result: Any | None = None,
    canonical_result: CanonicalResultV1 | None = None,
    price_rows: list[Mapping[str, Any]] | tuple[Mapping[str, Any], ...] | None = None,
    chart_latest_date: str = "",
    analysis_cutoff_date: str = "",
    source: str = "",
    error: str = "",
    chart_research_summary: Mapping[str, Any] | None = None,
) -> dict[str, object]:
    symbol = str(selected_symbol or "").strip().upper()
    loaded = _analysis_sections(analysis_result)
    snapshot = loaded["snapshot"] or (
        indicator_snapshot if isinstance(indicator_snapshot, Mapping) else {}
    )
    rows = _valid_rows(price_rows)
    prediction_summary = loaded["prediction_summary"] or build_prediction_summary()
    strategy_summary = loaded["strategy_summary"] or build_strategy_summary(prediction_summary)

    market_context = calculate_market_context(
        snapshot=snapshot,
        probability=loaded["probability"],
        prediction=loaded["projection"],
    ).to_dict()
    sector_context = calculate_sector_context(symbol_rows=rows).to_dict()
    relative_strength = calculate_relative_strength_context(symbol_rows=rows).to_dict()
    volume_context = calculate_volume_context(snapshot=snapshot, price_rows=rows).to_dict()
    support_resistance = calculate_support_resistance_context(
        snapshot=snapshot,
        indicators=snapshot,
        price_rows=rows,
    ).to_dict()

    cards = (
        _card(
            "symbol",
            "Symbol",
            (
                _item("Selected", symbol),
                _item("Data", _data_state(snapshot=snapshot, rows=rows, error=error)),
                _item("Source", source),
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
            "Snapshot Summary",
            (
                _item("Status", SIGNAL_SUMMARY_PLACEHOLDER),
                _item("Confidence", None),
                _item("Score", None),
            ),
        ),
        _research_details_card(chart_research_summary),
    )

    return {
        "symbol": symbol or "No symbol selected",
        "has_symbol": bool(symbol),
        "has_snapshot": bool(snapshot),
        "has_analysis": bool(analysis_result) and not error,
        "can_save_signal": isinstance(canonical_result, CanonicalResultV1) and not error,
        "canonical_result": canonical_result,
        "chart_latest_date": str(chart_latest_date or ""),
        "analysis_cutoff_date": str(analysis_cutoff_date or ""),
        "source": source,
        "error": error,
        "cards": cards,
        "status": _status_text(
            symbol=symbol,
            snapshot=snapshot,
            rows=rows,
            source=source,
            error=error,
        ),
    }


def load_desktop_research_view_model(
    *,
    selected_symbol: str | None = None,
    indicator_snapshot: Mapping[str, Any] | None = None,
    data_source: MarketDataSource | None = None,
    database_path: Path | str | None = None,
    row_limit: int = REQUIRED_ROW_COUNT,
    as_of_date: date | str | None = None,
) -> dict[str, object]:
    symbol = str(selected_symbol or "").strip().upper()
    if not symbol:
        return build_research_view_model(
            selected_symbol=symbol,
            indicator_snapshot=indicator_snapshot,
        )

    if data_source is not None:
        return _load_from_data_source(
            selected_symbol=symbol,
            indicator_snapshot=indicator_snapshot,
            data_source=data_source,
            row_limit=row_limit,
            source_label="Data Source v1",
            as_of_date=as_of_date,
        )

    path = Path(database_path or DEFAULT_RESEARCH_DATABASE_PATH)
    if not path.exists():
        return build_research_view_model(
            selected_symbol=symbol,
            indicator_snapshot=indicator_snapshot,
            source="",
        )
    chart_research_summary = _load_snapshot_research_details(symbol, path)

    uri = path.resolve().as_uri() + "?mode=ro"
    try:
        connection = sqlite3.connect(uri, uri=True)
    except sqlite3.Error as error:
        return build_research_view_model(
            selected_symbol=symbol,
            indicator_snapshot=indicator_snapshot,
            error=f"Research analysis unavailable: {error}",
            chart_research_summary=chart_research_summary,
        )

    try:
        return _load_from_data_source(
            selected_symbol=symbol,
            indicator_snapshot=indicator_snapshot,
            data_source=SQLiteDataSource(connection),
            row_limit=row_limit,
            source_label="sqlite",
            as_of_date=as_of_date,
            chart_research_summary=chart_research_summary,
        )
    finally:
        connection.close()


def _status_text(
    *,
    symbol: str,
    snapshot: Mapping[str, Any],
    rows: tuple[Mapping[str, Any], ...],
    source: str,
    error: str,
) -> str:
    if not symbol:
        return "Select a dashboard symbol to view research context."
    if error:
        return error
    if rows:
        source_text = f" from {source}" if source else ""
        return f"Read-only deterministic research context{source_text}."
    if not snapshot:
        return "Selected symbol has no loaded deterministic research data yet."
    return "Read-only deterministic research context."


def _load_from_data_source(
    *,
    selected_symbol: str,
    indicator_snapshot: Mapping[str, Any] | None,
    data_source: MarketDataSource,
    row_limit: int,
    source_label: str,
    as_of_date: date | str | None,
    chart_research_summary: Mapping[str, Any] | None = None,
) -> dict[str, object]:
    try:
        market_data = data_source.load_ohlcv(
            MarketDataRequest(
                symbol=selected_symbol,
                timeframe=DEFAULT_RESEARCH_TIMEFRAME,
                limit=row_limit,
            )
        )
    except (RuntimeError, ValueError, sqlite3.Error) as error:
        return build_research_view_model(
            selected_symbol=selected_symbol,
            indicator_snapshot=indicator_snapshot,
            error=f"Research analysis unavailable: {error}",
            chart_research_summary=chart_research_summary,
        )

    rows = [dict(row) for row in market_data.rows]
    source = str(market_data.metadata.get("source") or source_label)
    if not rows:
        return build_research_view_model(
            selected_symbol=selected_symbol,
            indicator_snapshot=indicator_snapshot,
            source=source,
            chart_research_summary=chart_research_summary,
        )

    cutoff = determine_analysis_cutoff_date(rows, as_of_date=as_of_date)
    analysis_rows = rows_through_analysis_cutoff(rows, cutoff.analysis_cutoff_date)
    if not analysis_rows:
        return build_research_view_model(
            selected_symbol=selected_symbol,
            indicator_snapshot=indicator_snapshot,
            price_rows=rows,
            chart_latest_date=cutoff.chart_latest_date,
            analysis_cutoff_date=cutoff.analysis_cutoff_date,
            source=source,
            chart_research_summary=chart_research_summary,
        )

    try:
        analysis_result = analyze_symbol_v2(
            AnalysisPipelineV2Request(
                symbol=selected_symbol,
                config=PipelineConfig(
                    timeframe=DEFAULT_RESEARCH_TIMEFRAME,
                    include_backtest=False,
                ),
                ohlcv_rows=analysis_rows,
            )
        )
    except (RuntimeError, ValueError, TypeError, KeyError) as error:
        return build_research_view_model(
            selected_symbol=selected_symbol,
            indicator_snapshot=indicator_snapshot,
            price_rows=analysis_rows,
            chart_latest_date=cutoff.chart_latest_date,
            analysis_cutoff_date=cutoff.analysis_cutoff_date,
            source=source,
            error=f"Research analysis unavailable: {error}",
            chart_research_summary=chart_research_summary,
        )

    canonical_result = _canonical_result_from_analysis(
        analysis_result=analysis_result,
        context_summary=_context_summary_for_signal(
            analysis_result=analysis_result,
            price_rows=analysis_rows,
        ),
        strategy_summary=_strategy_summary_for_signal(analysis_result),
    )

    return build_research_view_model(
        selected_symbol=selected_symbol,
        indicator_snapshot=indicator_snapshot,
        analysis_result=analysis_result,
        canonical_result=canonical_result,
        price_rows=analysis_rows,
        chart_latest_date=cutoff.chart_latest_date,
        analysis_cutoff_date=cutoff.analysis_cutoff_date,
        source=source,
        chart_research_summary=chart_research_summary,
    )


def _canonical_result_from_analysis(
    *,
    analysis_result: Any,
    context_summary: dict[str, Any],
    strategy_summary: dict[str, Any],
) -> CanonicalResultV1:
    canonical = build_canonical_result_v1(analysis_result)
    prediction_summary = dict(canonical.brain.prediction_summary)
    signal_type = "setup" if prediction_summary or strategy_summary else "informational"
    return replace(
        canonical,
        context=CanonicalContextResultV1(
            market=_summary_section(context_summary, "market"),
            sector=_summary_section(context_summary, "sector"),
            relative_strength=_summary_section(context_summary, "relative_strength"),
            volume=_summary_section(context_summary, "volume"),
            support_resistance=_summary_section(context_summary, "support_resistance"),
        ),
        strategy=CanonicalStrategyResultV1(
            strategy_score=_optional_float(strategy_summary.get("strategy_score")),
            trade_grade=str(strategy_summary.get("trade_grade") or ""),
            entry_quality=str(strategy_summary.get("entry_quality") or ""),
            risk_rating=str(strategy_summary.get("risk_rating") or strategy_summary.get("risk_level") or ""),
            expected_reward_percent=_optional_float(strategy_summary.get("expected_reward_percent")),
            expected_risk_percent=_optional_float(strategy_summary.get("expected_risk_percent")),
            reward_risk_ratio=_optional_float(strategy_summary.get("reward_risk_ratio")),
            notes=_notes_tuple(strategy_summary.get("notes")),
        ),
        signal_summary=CanonicalSignalSummaryV1(
            symbol=canonical.identity.symbol,
            signal_date=canonical.identity.analysis_date or canonical.identity.snapshot_date,
            timeframe=canonical.identity.timeframe,
            signal_type=signal_type,
            confidence=_optional_float(prediction_summary.get("confidence")),
            snapshot_id=canonical.identity.snapshot_id,
            snapshot_date=canonical.identity.snapshot_date,
            context_summary=context_summary,
            strategy_summary=strategy_summary,
            prediction_summary=prediction_summary,
            notes=("Manual save candidate only; not persisted automatically.",),
        ),
    )


def _context_summary_for_signal(
    *,
    analysis_result: Any,
    price_rows: list[Mapping[str, Any]],
) -> dict[str, Any]:
    loaded = _analysis_sections(analysis_result)
    snapshot = loaded["snapshot"]
    probability = loaded["probability"]
    projection = loaded["projection"]
    return {
        "market": calculate_market_context(
            snapshot=snapshot,
            probability=probability,
            prediction=projection,
        ).to_dict(),
        "sector": calculate_sector_context(symbol_rows=price_rows).to_dict(),
        "relative_strength": calculate_relative_strength_context(symbol_rows=price_rows).to_dict(),
        "volume": calculate_volume_context(
            snapshot=snapshot,
            price_rows=price_rows,
        ).to_dict(),
        "support_resistance": calculate_support_resistance_context(
            snapshot=snapshot,
            indicators=snapshot,
            price_rows=price_rows,
        ).to_dict(),
    }


def _strategy_summary_for_signal(analysis_result: Any) -> dict[str, Any]:
    loaded = _analysis_sections(analysis_result)
    strategy_summary = dict(loaded["strategy_summary"])
    strategy = getattr(analysis_result, "strategy", None)
    if strategy is None:
        return strategy_summary

    reward_risk = getattr(strategy, "reward_risk_estimate", None)
    if isinstance(reward_risk, Mapping):
        strategy_summary.update(
            {
                "expected_reward_percent": reward_risk.get("expected_reward_percent"),
                "expected_risk_percent": reward_risk.get("expected_risk_percent"),
                "reward_risk_ratio": reward_risk.get("reward_risk_ratio"),
                "target_zone": reward_risk.get("target_zone"),
                "risk_zone": reward_risk.get("risk_zone"),
            }
        )
    strategy_summary["strategy_score"] = getattr(strategy, "strategy_score", None)
    strategy_summary["trade_grade"] = _enum_value(getattr(strategy, "trade_grade", None))
    strategy_summary["entry_quality"] = _enum_value(getattr(strategy, "entry_quality", None))
    strategy_summary["risk_rating"] = _enum_value(getattr(strategy, "risk_rating", None))
    strategy_summary["notes"] = getattr(strategy, "notes", None) or strategy_summary.get("notes")
    return strategy_summary


def _analysis_sections(analysis_result: Any) -> dict[str, Mapping[str, Any]]:
    if analysis_result is None:
        return {
            "snapshot": {},
            "probability": {},
            "projection": {},
            "prediction_summary": {},
            "strategy_summary": {},
        }

    canonical_brain = getattr(analysis_result, "canonical_brain", None)
    snapshot = _mapping(getattr(canonical_brain, "snapshot", None))
    probability = _mapping(getattr(canonical_brain, "probability", None))
    projection = _mapping(getattr(canonical_brain, "projection", None))
    prediction_summary = _mapping(getattr(canonical_brain, "prediction_summary", None))

    strategy_summary = build_strategy_summary(dict(prediction_summary))
    strategy = getattr(analysis_result, "strategy", None)
    if strategy is not None:
        reward_risk = getattr(strategy, "reward_risk_estimate", None)
        if isinstance(reward_risk, Mapping):
            strategy_summary = {
                **strategy_summary,
                "risk_level": _enum_value(getattr(strategy, "risk_rating", None))
                or strategy_summary.get("risk_level"),
                "reward_risk_ratio": reward_risk.get("reward_risk_ratio"),
                "notes": getattr(strategy, "notes", None)
                or strategy_summary.get("notes"),
            }

    return {
        "snapshot": snapshot,
        "probability": probability,
        "projection": projection,
        "prediction_summary": prediction_summary,
        "strategy_summary": _mapping(strategy_summary),
    }


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _summary_section(source: Mapping[str, Any], name: str) -> dict[str, Any]:
    value = source.get(name)
    return dict(value) if isinstance(value, Mapping) else {}


def _optional_float(value: object) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _notes_tuple(value: object) -> tuple[str, ...]:
    if isinstance(value, str):
        text = value.strip()
        return (text,) if text else ()
    if isinstance(value, (list, tuple)):
        return tuple(str(item) for item in value if item is not None)
    return ()


def _valid_rows(
    rows: list[Mapping[str, Any]] | tuple[Mapping[str, Any], ...] | None,
) -> tuple[Mapping[str, Any], ...]:
    if not isinstance(rows, (list, tuple)):
        return ()
    return tuple(row for row in rows if isinstance(row, Mapping))


def _data_state(
    *,
    snapshot: Mapping[str, Any],
    rows: tuple[Mapping[str, Any], ...],
    error: str,
) -> str:
    if error:
        return "error"
    if rows:
        return "analysis loaded"
    if snapshot:
        return "snapshot loaded"
    return "not loaded"


def _load_snapshot_research_details(symbol: str, database_path: Path) -> Mapping[str, Any] | None:
    try:
        from src.gui.chart_research_sidebar_view_model import load_chart_research_sidebar_view_model

        view_model = load_chart_research_sidebar_view_model(
            symbol=symbol,
            database_path=database_path,
        )
    except (RuntimeError, ValueError, OSError, sqlite3.Error):
        return None
    return view_model if isinstance(view_model, Mapping) else None


def _enum_value(value: Any) -> str:
    raw_value = getattr(value, "value", value)
    return str(raw_value) if raw_value else ""


def _research_details_card(summary: Mapping[str, Any] | None) -> dict[str, object]:
    summary = summary if isinstance(summary, Mapping) else {}
    overall = _items_map(summary.get("overall_assessment"))
    entry = _items_map(summary.get("entry_strength"))
    reasoning = _items_map(summary.get("reasoning"))
    historical_edge = _items_map(summary.get("historical_edge"))
    recommendation = overall.get("Recommendation")
    rating = overall.get("Rating")
    entry_strength = entry.get("Strength") or entry.get("Score")
    entry_timing = entry.get("Timing")
    recommendation_reason = reasoning.get("Recommendation Reason")
    edge_text = _historical_edge_summary_text(historical_edge, reasoning)
    return _card(
        "research_details",
        "Research Details",
        (
            _item("Recommendation", _join_visible(recommendation, rating)),
            _item("Entry Strength", _join_visible(entry_strength, entry_timing)),
            _item("Why", recommendation_reason),
            _item("Historical Edge", edge_text),
        ),
    )


def _items_map(value: object) -> dict[str, str]:
    if not isinstance(value, (list, tuple)):
        return {}
    items: dict[str, str] = {}
    for item in value:
        if not isinstance(item, (list, tuple)) or len(item) != 2:
            continue
        label = str(item[0]).strip()
        item_value = str(item[1]).strip()
        if label:
            items[label] = item_value
    return items


def _historical_edge_summary_text(
    historical_edge: Mapping[str, str],
    reasoning: Mapping[str, str],
) -> str:
    explanation = reasoning.get("Historical Edge Explanation", "")
    if explanation and explanation != PLACEHOLDER_TEXT:
        return explanation
    parts = [
        historical_edge.get("Matched Pattern", ""),
        historical_edge.get("Win Rate", ""),
        historical_edge.get("Expectancy", ""),
    ]
    return " | ".join(part for part in parts if part and part != PLACEHOLDER_TEXT)


def _join_visible(*values: object) -> str:
    visible = [str(value).strip() for value in values if str(value or "").strip() and str(value).strip() != PLACEHOLDER_TEXT]
    return " / ".join(visible)


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
