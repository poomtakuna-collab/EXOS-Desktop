from __future__ import annotations

import json
from datetime import date, timedelta
import unittest

from src.gui.research_view_model import (
    PLACEHOLDER_TEXT,
    SIGNAL_SUMMARY_PLACEHOLDER,
    build_research_view_model,
    load_desktop_research_view_model,
)
from src.data_source import MemoryDataSource


class ResearchSurfaceTest(unittest.TestCase):
    def test_empty_state_without_selected_symbol_uses_card_placeholders(self) -> None:
        view_model = build_research_view_model()

        self.assertEqual(view_model["symbol"], "No symbol selected")
        self.assertFalse(view_model["has_symbol"])
        self.assertFalse(view_model["has_snapshot"])
        self.assertFalse(view_model["can_save_signal"])
        self.assertEqual(
            view_model["status"],
            "Select a dashboard symbol to view research context.",
        )
        self.assertEqual(_item(view_model, "symbol", "Selected")["value"], PLACEHOLDER_TEXT)
        self.assertTrue(_item(view_model, "symbol", "Selected")["is_placeholder"])
        self.assertEqual(_item(view_model, "market_context", "Trend")["value"], PLACEHOLDER_TEXT)
        self.assertEqual(_item(view_model, "sector_context", "Trend")["value"], PLACEHOLDER_TEXT)
        self.assertEqual(_item(view_model, "relative_strength", "Rating")["value"], PLACEHOLDER_TEXT)
        self.assertEqual(_item(view_model, "volume_context", "State")["value"], PLACEHOLDER_TEXT)
        self.assertEqual(_item(view_model, "support_resistance", "Support")["value"], PLACEHOLDER_TEXT)
        json.dumps(view_model, sort_keys=True)

    def test_selected_symbol_is_displayed_in_symbol_card(self) -> None:
        view_model = build_research_view_model(selected_symbol="aapl")

        self.assertEqual(view_model["symbol"], "AAPL")
        self.assertTrue(view_model["has_symbol"])
        self.assertEqual(_item(view_model, "symbol", "Selected")["value"], "AAPL")
        self.assertFalse(_item(view_model, "symbol", "Selected")["is_placeholder"])
        self.assertEqual(
            view_model["status"],
            "Selected symbol has no loaded deterministic research data yet.",
        )

    def test_card_titles_are_stable_and_future_ready(self) -> None:
        view_model = build_research_view_model()

        self.assertEqual(
            [(card["id"], card["title"]) for card in view_model["cards"]],
            [
                ("symbol", "Symbol"),
                ("market_context", "Market Context"),
                ("sector_context", "Sector Context"),
                ("relative_strength", "Relative Strength"),
                ("volume_context", "Volume"),
                ("support_resistance", "Support / Resistance"),
                ("prediction_summary", "Prediction"),
                ("strategy_summary", "Strategy"),
                ("signal_summary", "Signal Summary"),
            ],
        )
        self.assertIn("Confidence", _labels(view_model, "prediction_summary"))
        self.assertIn("Similarity", _labels(view_model, "prediction_summary"))
        self.assertIn("Notes", _labels(view_model, "strategy_summary"))
        self.assertIn("Score", _labels(view_model, "signal_summary"))

    def test_context_cards_use_existing_snapshot_calculators(self) -> None:
        snapshot = {
            "trend": {"state": "bullish", "score": 80},
            "trend_slope": {"direction": "up"},
            "squeeze": {"state": "none", "compression_ratio": 1.2},
            "score": {"overall_score": 75, "confidence": 60},
            "volume": {"relative_volume": 1.8},
            "market_structure": {
                "nearest_support": 100.0,
                "nearest_resistance": 120.0,
            },
            "price": {"current_price": 110.0},
        }

        view_model = build_research_view_model(
            selected_symbol="AAPL",
            indicator_snapshot=snapshot,
        )

        self.assertEqual(
            view_model["status"],
            "Read-only deterministic research context.",
        )
        self.assertEqual(_item(view_model, "market_context", "Trend")["value"], "up")
        self.assertEqual(
            _item(view_model, "market_context", "Momentum")["value"],
            "positive",
        )
        self.assertEqual(
            _item(view_model, "market_context", "Risk State")["value"],
            "risk_on",
        )
        self.assertEqual(_item(view_model, "volume_context", "Relative Volume")["value"], "1.8")
        self.assertEqual(_item(view_model, "support_resistance", "Support")["value"], "100")
        self.assertEqual(
            _item(view_model, "support_resistance", "Resistance")["value"],
            "120",
        )
        self.assertEqual(
            _item(view_model, "support_resistance", "Support Distance")["value"],
            "9.0909%",
        )

    def test_prediction_strategy_and_signal_cards_are_empty_safe(self) -> None:
        view_model = build_research_view_model(selected_symbol="MSFT")

        self.assertEqual(_item(view_model, "prediction_summary", "Confidence")["value"], "0%")
        self.assertEqual(_item(view_model, "prediction_summary", "Evidence")["value"], "0")
        self.assertEqual(_item(view_model, "prediction_summary", "Target Zone")["value"], PLACEHOLDER_TEXT)
        self.assertEqual(_item(view_model, "strategy_summary", "Bias")["value"], PLACEHOLDER_TEXT)
        self.assertEqual(_item(view_model, "strategy_summary", "Risk")["value"], PLACEHOLDER_TEXT)
        self.assertEqual(
            _item(view_model, "strategy_summary", "Notes")["value"],
            "Market bias: unknown; Risk level: unknown; Reward/risk ratio unavailable",
        )
        self.assertEqual(
            _item(view_model, "signal_summary", "Status")["value"],
            SIGNAL_SUMMARY_PLACEHOLDER,
        )

    def test_view_model_is_deterministic(self) -> None:
        snapshot = {"trend": {"state": "bearish"}, "trend_slope": {"direction": "down"}}

        first = build_research_view_model(
            selected_symbol="TSLA",
            indicator_snapshot=snapshot,
        )
        second = build_research_view_model(
            selected_symbol="TSLA",
            indicator_snapshot=snapshot,
        )

        self.assertEqual(first, second)

    def test_loader_populates_real_analysis_and_context_from_data_source_rows(self) -> None:
        view_model = load_desktop_research_view_model(
            selected_symbol="AAPL",
            data_source=MemoryDataSource(_ohlcv_rows("AAPL")),
            row_limit=40,
        )

        self.assertTrue(view_model["has_analysis"])
        self.assertTrue(view_model["can_save_signal"])
        self.assertIsNotNone(view_model["canonical_result"])
        self.assertEqual(view_model["source"], "memory")
        self.assertEqual(
            view_model["status"],
            "Read-only deterministic research context from memory.",
        )
        self.assertEqual(_item(view_model, "symbol", "Data")["value"], "analysis loaded")
        self.assertEqual(_item(view_model, "symbol", "Source")["value"], "memory")
        self.assertNotEqual(_item(view_model, "market_context", "Trend")["value"], PLACEHOLDER_TEXT)
        self.assertNotEqual(_item(view_model, "volume_context", "State")["value"], PLACEHOLDER_TEXT)
        self.assertNotEqual(_item(view_model, "support_resistance", "Support")["value"], PLACEHOLDER_TEXT)
        self.assertEqual(_item(view_model, "prediction_summary", "Evidence")["value"], "0")

    def test_loader_uses_analysis_cutoff_for_same_day_latest_row(self) -> None:
        view_model = load_desktop_research_view_model(
            selected_symbol="AAPL",
            data_source=MemoryDataSource(_ohlcv_rows_through("AAPL", date(2026, 7, 1))),
            row_limit=40,
            as_of_date="2026-07-01",
        )

        canonical_result = view_model["canonical_result"]

        self.assertTrue(view_model["has_analysis"])
        self.assertEqual(view_model["chart_latest_date"], "2026-07-01")
        self.assertEqual(view_model["analysis_cutoff_date"], "2026-06-30")
        self.assertEqual(canonical_result.diagnostics.row_count, 39)

    def test_loader_handles_empty_data_source_rows_gracefully(self) -> None:
        view_model = load_desktop_research_view_model(
            selected_symbol="AAPL",
            data_source=MemoryDataSource([]),
        )

        self.assertFalse(view_model["has_analysis"])
        self.assertFalse(view_model["can_save_signal"])
        self.assertEqual(view_model["source"], "memory")
        self.assertEqual(
            view_model["status"],
            "Selected symbol has no loaded deterministic research data yet.",
        )
        self.assertEqual(_item(view_model, "symbol", "Data")["value"], "not loaded")
        self.assertEqual(_item(view_model, "market_context", "Trend")["value"], PLACEHOLDER_TEXT)

    def test_loader_handles_analysis_load_failure_gracefully(self) -> None:
        view_model = load_desktop_research_view_model(
            selected_symbol="AAPL",
            data_source=_FailingDataSource(),
        )

        self.assertFalse(view_model["has_analysis"])
        self.assertFalse(view_model["can_save_signal"])
        self.assertEqual(view_model["error"], "Research analysis unavailable: fixture failure")
        self.assertEqual(view_model["status"], "Research analysis unavailable: fixture failure")
        self.assertEqual(_item(view_model, "symbol", "Data")["value"], "error")


def _card(view_model: dict[str, object], card_id: str) -> dict[str, object]:
    for card in view_model["cards"]:
        if card["id"] == card_id:
            return card
    raise AssertionError(f"Missing card: {card_id}")


def _item(
    view_model: dict[str, object],
    card_id: str,
    label: str,
) -> dict[str, object]:
    for item in _card(view_model, card_id)["items"]:
        if item["label"] == label:
            return item
    raise AssertionError(f"Missing item: {card_id}.{label}")


def _labels(view_model: dict[str, object], card_id: str) -> list[str]:
    return [str(item["label"]) for item in _card(view_model, card_id)["items"]]


class _FailingDataSource:
    def load_ohlcv(self, request: object) -> object:
        del request
        raise RuntimeError("fixture failure")

    def load_future_rows(self, request: object) -> object:
        del request
        raise RuntimeError("fixture failure")


def _ohlcv_rows(symbol: str) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    start_date = date(2026, 5, 1)
    for index in range(1, 41):
        close = 100.0 + index
        rows.append(
            {
                "symbol": symbol,
                "timeframe": "1D",
                "date": (start_date + timedelta(days=index - 1)).isoformat(),
                "open": close - 1.0,
                "high": close + 1.5,
                "low": close - 2.0,
                "close": close,
                "volume": 1000 + index * 100,
            }
        )
    return rows


def _ohlcv_rows_through(symbol: str, latest_date: date) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    start_date = latest_date - timedelta(days=39)
    for index in range(40):
        close = 100.0 + index
        rows.append(
            {
                "symbol": symbol,
                "timeframe": "1D",
                "date": (start_date + timedelta(days=index)).isoformat(),
                "open": close - 1.0,
                "high": close + 1.5,
                "low": close - 2.0,
                "close": close,
                "volume": 1000 + index * 100,
            }
        )
    return rows


if __name__ == "__main__":
    unittest.main()
