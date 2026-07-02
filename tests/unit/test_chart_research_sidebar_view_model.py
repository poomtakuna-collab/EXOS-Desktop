from __future__ import annotations

import unittest
from pathlib import Path

from src.gui.chart_action_overlay_view_model import build_chart_action_overlay
from src.gui.chart_research_sidebar_view_model import (
    build_chart_research_sidebar_view_model,
    empty_chart_research_sidebar_view_model,
)
from src.statistics_engine import FeatureBucketStats, StatisticsEngineReport

try:
    from src.gui.chart_research_sidebar import _value_style
except ModuleNotFoundError:
    _value_style = None


class ChartResearchSidebarViewModelTest(unittest.TestCase):
    @unittest.skipIf(_value_style is None, "PySide6 is not installed.")
    def test_poom_numeric_sidebar_values_have_directional_styles(self) -> None:
        assert _value_style is not None
        self.assertIn("#22c55e", _value_style("EW", "1.5"))
        self.assertIn("#facc15", _value_style("Volume Pressure", "0"))
        self.assertIn("#ef4444", _value_style("POOM Trend Slope", "-2.5"))
        self.assertEqual(_value_style("Recommendation", "Watchlist"), "")

    def test_formats_snapshot_payload_v2_research_summary(self) -> None:
        view_model = build_chart_research_sidebar_view_model(
            _payload(),
            symbol="AAPL",
            snapshot_record={
                "symbol": "AAPL",
                "market_date": "2026-07-01",
                "timeframe": "1D",
            },
            statistics_report=_statistics_report(),
        )

        self.assertEqual(view_model["title"], "Research Summary")
        self.assertEqual(dict(view_model["identity"])["Symbol"], "AAPL")
        self.assertEqual(dict(view_model["identity"])["Latest Snapshot Date"], "2026-07-01")
        self.assertEqual(dict(view_model["identity"])["Timeframe"], "1D")
        self.assertEqual(dict(view_model["overall_assessment"])["Rating"], "A")
        self.assertEqual(dict(view_model["overall_assessment"])["Recommendation"], "Watchlist")
        self.assertEqual(dict(view_model["overall_assessment"])["Confidence"], "72.50%")
        self.assertNotIn("Setup Strength", dict(view_model["overall_assessment"]))
        self.assertEqual(dict(view_model["poom_combo"])["EW"], "12")
        self.assertEqual(dict(view_model["poom_combo"])["Volume Pressure"], "-35")
        self.assertEqual(dict(view_model["poom_combo"])["POOM Trend Slope"], "6")
        self.assertEqual(dict(view_model["poom_combo"])["Squeeze"], "Bullish Squeeze Release")
        self.assertEqual(dict(view_model["poom_combo"])["BOS / CHoCH"], "Break of Structure Up")
        self.assertEqual(dict(view_model["trend_structure"])["Trend"], "Bullish")
        self.assertEqual(dict(view_model["trend_structure"])["EMA Alignment"], "Bullish")
        self.assertEqual(dict(view_model["trend_structure"])["Market Structure"], "Higher High")
        self.assertEqual(dict(view_model["trend_structure"])["Support"], "96")
        self.assertEqual(dict(view_model["trend_structure"])["Resistance"], "112")
        self.assertEqual(dict(view_model["historical_edge"])["Matched Pattern"], "Elliott Wave: Positive (10 to 25)")
        self.assertEqual(dict(view_model["historical_edge"])["Sample Count"], "42")
        self.assertEqual(dict(view_model["historical_edge"])["Win Rate"], "61.50%")
        self.assertEqual(dict(view_model["historical_edge"])["Average Return"], "3.25%")
        self.assertEqual(dict(view_model["historical_edge"])["Expectancy"], "2.75%")
        self.assertEqual(dict(view_model["historical_edge"])["Average Drawdown"], "-4.50%")
        reasoning = dict(view_model["reasoning"])
        self.assertEqual(tuple(reasoning)[0], "Recommendation Reason")
        self.assertIn("Watchlist", reasoning["Recommendation Reason"])
        self.assertIn("Price remains above the main moving average", reasoning["Bullish Factors"])
        self.assertIn("Volume pressure is negative", reasoning["Bearish Factors"])
        self.assertIn("No major additional risk notes", reasoning["Risk Notes"])
        self.assertIn("positive expectancy", reasoning["Historical Edge Explanation"])
        summary_cards = view_model["summary_cards"]
        self.assertEqual(
            [card["title"] for card in summary_cards],
            ["EXOS Summary", "Entry Strength", "Why / Reasoning", "Historical Edge Summary"],
        )
        self.assertEqual(summary_cards[0]["items"][0][0], "Rating")
        self.assertEqual(summary_cards[1]["items"][0][0], "Strength")
        self.assertIn("Watchlist", summary_cards[2]["body"])
        self.assertIn("positive expectancy", summary_cards[3]["body"])
        overlay = view_model["chart_action_overlay"]
        self.assertEqual(overlay["state"], "neutral")
        self.assertEqual(overlay["title"], "Neutral / Wait Zone")
        self.assertEqual(overlay["price_range"], "No price zone available")
        self.assertTrue(any("Recommendation: Watchlist" in item for item in overlay["summary_lines"]))
        detail_sections = view_model["detail_sections"]
        self.assertEqual(
            [section["title"] for section in detail_sections],
            ["Snapshot", "POOM Raw", "Technical Details", "Full Historical Edge", "Full Reasoning", "Zones"],
        )
        self.assertFalse(any(section["expanded"] for section in detail_sections))
        zones = {zone["title"]: zone["value"] for zone in view_model["zones"]}
        self.assertEqual(zones["Target / Upside Zone"], "110 - 120")
        self.assertEqual(zones["Neutral / Decision Zone"], "Not available")
        self.assertEqual(zones["Risk / Downside Zone"], "94 - 90")

    def test_unavailable_zones_and_statistics_are_safe(self) -> None:
        payload = _payload()
        payload["analysis"].pop("target_zone")
        payload["analysis"].pop("risk_zone")

        view_model = build_chart_research_sidebar_view_model(payload)

        self.assertEqual(dict(view_model["historical_edge"])["Matched Pattern"], "Not available")
        self.assertIn("Historical edge data is not available yet.", dict(view_model["reasoning"])["Historical Edge Explanation"])
        compact_titles = [card["title"] for card in view_model["summary_cards"]]
        self.assertIn("EXOS Summary", compact_titles)
        self.assertIn("Entry Strength", compact_titles)
        self.assertIn("Why / Reasoning", compact_titles)
        self.assertIn("Historical Edge Summary", compact_titles)
        detail_titles = [section["title"] for section in view_model["detail_sections"]]
        self.assertNotIn("Zones", detail_titles)
        zones = {zone["title"]: zone["value"] for zone in view_model["zones"]}
        self.assertEqual(zones["Target / Upside Zone"], "Not available")
        self.assertEqual(zones["Neutral / Decision Zone"], "Not available")
        self.assertEqual(zones["Risk / Downside Zone"], "Not available")

    def test_historical_edge_uses_readable_squeeze_description(self) -> None:
        payload = _payload()
        payload["analysis"]["poom_combo"]["squeeze_up"] = False

        view_model = build_chart_research_sidebar_view_model(
            payload,
            statistics_report=StatisticsEngineReport(
                snapshot_count=1,
                outcome_count=1,
                skipped_count=0,
                feature_stats=(
                    FeatureBucketStats(
                        feature_name="poom_squeeze",
                        bucket="none",
                        sample_count=30,
                        win_rate=55.0,
                        average_return=1.25,
                        median_return=1.0,
                        average_max_gain=4.0,
                        average_drawdown=-2.0,
                        expectancy=0.75,
                    ),
                ),
            ),
        )

        self.assertEqual(dict(view_model["poom_combo"])["Squeeze"], "No Active Squeeze")
        self.assertEqual(dict(view_model["historical_edge"])["Matched Pattern"], "Squeeze: No Active Squeeze")

    def test_empty_summary_has_placeholders(self) -> None:
        view_model = empty_chart_research_sidebar_view_model(
            "No saved SnapshotPayloadV2 found.",
            symbol="AAPL",
        )

        self.assertEqual(dict(view_model["identity"])["Symbol"], "AAPL")
        self.assertEqual(dict(view_model["poom_combo"])["EW"], "-")
        self.assertEqual(dict(view_model["historical_edge"])["Matched Pattern"], "-")
        self.assertEqual(view_model["reasoning"], ())
        self.assertEqual(view_model["summary_cards"], ())
        self.assertEqual(view_model["detail_sections"], ())
        self.assertIsNone(view_model["chart_action_overlay"])
        self.assertEqual(view_model["status"], "No saved SnapshotPayloadV2 found.")

    def test_action_overlay_avoid_uses_bearish_risk_state(self) -> None:
        payload = _payload()
        payload["analysis"]["brain_snapshot"]["score"] = {
            "rating": "Weak",
            "recommendation": "avoid",
            "confidence": 1.0,
        }
        payload["analysis"]["poom_combo"].update(
            {
                "ew_norm": -12.0,
                "volume_pressure": -18.0,
                "trend_slope": -6.0,
                "squeeze_up": False,
                "squeeze_down": True,
                "bos_up": False,
                "bos_down": True,
                "msb_dir": -1,
            }
        )

        overlay = build_chart_research_sidebar_view_model(payload)["chart_action_overlay"]

        self.assertEqual(overlay["state"], "bearish")
        self.assertEqual(overlay["title"], "Bearish / Risk Zone")
        self.assertEqual(overlay["price_range"], "94 - 90")

    def test_action_overlay_watch_or_mixed_uses_neutral_wait_state(self) -> None:
        payload = _payload()
        payload["analysis"]["brain_snapshot"]["score"] = {
            "rating": "Neutral",
            "recommendation": "watch",
            "confidence": 0.55,
        }
        payload["analysis"]["projection"] = {"neutral_low": 98.0, "neutral_high": 104.0}
        payload["analysis"]["poom_combo"]["squeeze_up"] = False
        payload["analysis"]["poom_combo"]["bos_up"] = False

        overlay = build_chart_research_sidebar_view_model(payload)["chart_action_overlay"]

        self.assertEqual(overlay["state"], "neutral")
        self.assertEqual(overlay["title"], "Neutral / Wait Zone")
        self.assertEqual(overlay["price_range"], "98 - 104")

    def test_action_overlay_watchlist_rating_a_stays_neutral(self) -> None:
        payload = _payload()
        payload["analysis"]["brain_snapshot"]["score"] = {
            "rating": "A",
            "recommendation": "watchlist",
            "confidence": 0.72,
        }

        overlay = build_chart_research_sidebar_view_model(payload)["chart_action_overlay"]

        self.assertEqual(overlay["state"], "neutral")
        self.assertEqual(overlay["title"], "Neutral / Wait Zone")

    def test_action_overlay_strong_buy_uses_bullish_target_state(self) -> None:
        payload = _payload()
        payload["analysis"]["brain_snapshot"]["score"] = {
            "rating": "Strong",
            "recommendation": "buy",
            "confidence": 0.82,
        }

        overlay = build_chart_research_sidebar_view_model(payload)["chart_action_overlay"]

        self.assertEqual(overlay["state"], "bullish")
        self.assertEqual(overlay["title"], "Bullish / Target Zone")
        self.assertEqual(overlay["price_range"], "110 - 120")

    def test_action_overlay_missing_data_defaults_to_neutral_wait_state(self) -> None:
        overlay = build_chart_research_sidebar_view_model(
            {"analysis": {}, "input": {}, "context": {}}
        )["chart_action_overlay"]

        self.assertEqual(overlay["state"], "neutral")
        self.assertEqual(overlay["title"], "Neutral / Wait Zone")
        self.assertEqual(overlay["price_range"], "No price zone available")

    def test_action_overlay_logic_lives_in_split_pure_module(self) -> None:
        sidebar_source = Path("src/gui/chart_research_sidebar_view_model.py").read_text(encoding="utf-8")
        overlay = build_chart_action_overlay(
            overall_assessment=(
                ("Rating", "A"),
                ("Recommendation", "Watchlist"),
            ),
            entry_strength={"entry_strength_label": "Strong", "entry_timing": "Valid"},
            reasoning={"reasoning_summary": "Setup is strong but still on watch."},
            historical_edge=(),
            zones=(),
        )

        self.assertEqual(overlay["state"], "neutral")
        self.assertIn("build_chart_action_overlay", sidebar_source)
        self.assertNotIn("def _overlay_state", sidebar_source)


def _payload() -> dict[str, object]:
    return {
        "identity": {
            "payload_schema_version": "snapshot_payload_v2",
            "symbol": "AAPL",
            "market_date": "2026-07-01",
            "timeframe": "1D",
        },
        "input": {
            "ohlcv_window": {
                "rows": [
                    {
                        "date": "2026-07-01",
                        "open": 99.0,
                        "high": 101.0,
                        "low": 98.0,
                        "close": 100.0,
                        "volume": 1000.0,
                    }
                ]
            }
        },
        "analysis": {
            "poom_combo": {
                "ew_norm": 12.0,
                "volume_pressure": -35.0,
                "trend_slope": 6.0,
                "in_squeeze": False,
                "squeeze_up": True,
                "squeeze_down": False,
                "bos_up": True,
                "bos_down": False,
                "choch_up": False,
                "choch_down": False,
                "msb_dir": 1,
            },
            "brain_snapshot": {
                "indicators": {
                    "ema20": 95.0,
                    "ema50": 90.0,
                    "ema200": 105.0,
                    "ema_alignment": "bullish",
                },
                "trend": {"state": "bullish"},
                "market_structure": {"state": "higher_high"},
                "score": {"rating": "A", "recommendation": "watchlist", "confidence": 0.725},
            },
            "target_zone": {"target_zone": {"base": 110.0, "target": 120.0}},
            "risk_zone": {"risk_zone": {"base": 94.0, "stop": 90.0}},
        },
        "context": {
            "support_resistance": {
                "nearest_support": 96.0,
                "nearest_resistance": 112.0,
            }
        },
        "display_summary": {},
    }


def _statistics_report() -> StatisticsEngineReport:
    return StatisticsEngineReport(
        snapshot_count=1,
        outcome_count=1,
        skipped_count=0,
        feature_stats=(
            FeatureBucketStats(
                feature_name="poom_ew",
                bucket="positive:10_to_25",
                sample_count=42,
                win_rate=61.5,
                average_return=3.25,
                median_return=2.5,
                average_max_gain=6.0,
                average_drawdown=-4.5,
                expectancy=2.75,
            ),
        ),
    )


if __name__ == "__main__":
    unittest.main()
