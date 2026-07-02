from __future__ import annotations

import unittest

from src.research import RESEARCH_REASONING_SCHEMA_KEYS, build_research_reasoning
from src.statistics_engine import FeatureBucketStats, StatisticsEngineReport


class ResearchReasoningEngineTest(unittest.TestCase):
    def test_bullish_aligned_setup(self) -> None:
        reasoning = build_research_reasoning(
            {
                "snapshot": _payload(),
                "statistics": _statistics_report(
                    _stats("poom_ew", "positive:10_to_25", 42, 61.5, 3.25, 2.75, -4.5),
                ),
            }
        )

        self.assertIn("Watch", reasoning["reasoning_summary"])
        self.assertIn("strong", reasoning["reasoning_summary"])
        self.assertTrue(any("main moving average" in item for item in reasoning["bullish_factors"]))
        self.assertIn("positive expectancy", reasoning["historical_edge_explanation"])
        self.assertEqual(reasoning["bearish_factors"], [])
        self.assertIn("moderate", reasoning["confidence_explanation"])
        self.assertIn("without changing it", reasoning["recommendation_reason"])

    def test_bearish_weak_setup(self) -> None:
        payload = _payload(
            poom={
                "ew_norm": -18.0,
                "volume_pressure": -22.0,
                "trend_slope": -7.0,
                "in_squeeze": False,
                "squeeze_up": False,
                "squeeze_down": True,
                "bos_up": False,
                "bos_down": True,
                "choch_up": False,
                "choch_down": False,
                "msb_dir": -1,
            },
            indicators={"ema20": 104.0, "ema50": 108.0, "ema200": 120.0, "ema_alignment": "bearish"},
            trend={"state": "bearish"},
            score={"rating": "WEAK", "recommendation": "avoid", "confidence": 35.0},
            close=100.0,
        )
        reasoning = build_research_reasoning(
            {
                "snapshot": payload,
                "statistics": _statistics_report(
                    _stats("bos_choch", "bos_down", 35, 38.0, -1.5, -2.0, -8.0),
                ),
            }
        )

        self.assertIn("Avoid", reasoning["reasoning_summary"])
        self.assertIn("weak", reasoning["reasoning_summary"])
        self.assertGreaterEqual(len(reasoning["bearish_factors"]), 5)
        self.assertTrue(any("downward" in item for item in reasoning["bearish_factors"]))
        self.assertIn("cautious", reasoning["historical_edge_explanation"])
        self.assertTrue(any("Downside structure" in item for item in reasoning["risk_notes"]))

    def test_mixed_setup(self) -> None:
        payload = _payload(
            poom={
                "ew_norm": 14.0,
                "volume_pressure": -20.0,
                "trend_slope": 5.0,
                "in_squeeze": True,
                "squeeze_up": False,
                "squeeze_down": False,
                "bos_up": False,
                "bos_down": False,
                "choch_up": False,
                "choch_down": False,
                "msb_dir": 0,
            },
            indicators={"ema20": 101.0, "ema50": 99.0, "ema200": 95.0, "ema_alignment": "neutral"},
            trend={"state": "neutral"},
            score={"rating": "NEUTRAL", "recommendation": "hold", "confidence": 0.52},
            close=100.0,
        )

        reasoning = build_research_reasoning(
            {
                "snapshot": payload,
                "historical_edge": {
                    "feature_name": "poom_squeeze",
                    "bucket": "in_squeeze",
                    "sample_count": 12,
                    "win_rate": 52.0,
                    "average_return": 0.3,
                    "expectancy": 0.1,
                    "average_drawdown": -3.0,
                },
            }
        )

        self.assertIn("mixed", reasoning["reasoning_summary"])
        self.assertTrue(reasoning["bullish_factors"])
        self.assertTrue(reasoning["bearish_factors"])
        self.assertTrue(any("Squeeze is still active" in item for item in reasoning["neutral_factors"]))
        self.assertIn("limited", reasoning["historical_edge_explanation"])

    def test_missing_historical_edge_is_graceful(self) -> None:
        reasoning = build_research_reasoning({"snapshot": _payload()})

        self.assertEqual(
            reasoning["historical_edge_explanation"],
            "Historical edge data is not available yet.",
        )
        self.assertIn("Historical edge data is not available yet.", reasoning["neutral_factors"])

    def test_output_schema_stability(self) -> None:
        reasoning = build_research_reasoning({"snapshot": _payload()})

        self.assertEqual(tuple(reasoning.keys()), RESEARCH_REASONING_SCHEMA_KEYS)
        self.assertIsInstance(reasoning["reasoning_summary"], str)
        self.assertIsInstance(reasoning["bullish_factors"], list)
        self.assertIsInstance(reasoning["bearish_factors"], list)
        self.assertIsInstance(reasoning["neutral_factors"], list)
        self.assertIsInstance(reasoning["historical_edge_explanation"], str)
        self.assertIsInstance(reasoning["risk_notes"], list)
        self.assertIsInstance(reasoning["confidence_explanation"], str)
        self.assertIsInstance(reasoning["recommendation_reason"], str)


def _payload(
    *,
    poom: dict[str, object] | None = None,
    indicators: dict[str, object] | None = None,
    trend: dict[str, object] | None = None,
    score: dict[str, object] | None = None,
    close: float = 100.0,
) -> dict[str, object]:
    return {
        "identity": {"payload_schema_version": "snapshot_payload_v2", "symbol": "AAPL"},
        "input": {
            "ohlcv_window": {
                "rows": [
                    {
                        "date": "2026-07-01",
                        "open": close - 1.0,
                        "high": close + 1.0,
                        "low": close - 2.0,
                        "close": close,
                        "volume": 1000.0,
                    }
                ]
            }
        },
        "analysis": {
            "poom_combo": poom
            or {
                "ew_norm": 12.0,
                "volume_pressure": 16.0,
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
                "indicators": indicators
                or {
                    "ema20": 98.0,
                    "ema50": 95.0,
                    "ema200": 90.0,
                    "ema_alignment": "bullish",
                },
                "trend": trend or {"state": "bullish"},
                "market_structure": {"state": "higher_high"},
                "score": score or {"rating": "GOOD", "recommendation": "watch", "confidence": 68.0},
            },
        },
        "context": {
            "support_resistance": {
                "nearest_support": 94.0,
                "nearest_resistance": 112.0,
            }
        },
    }


def _statistics_report(*stats: FeatureBucketStats) -> StatisticsEngineReport:
    return StatisticsEngineReport(
        snapshot_count=100,
        outcome_count=100,
        skipped_count=0,
        feature_stats=stats,
    )


def _stats(
    feature_name: str,
    bucket: str,
    sample_count: int,
    win_rate: float,
    average_return: float,
    expectancy: float,
    average_drawdown: float,
) -> FeatureBucketStats:
    return FeatureBucketStats(
        feature_name=feature_name,
        bucket=bucket,
        sample_count=sample_count,
        win_rate=win_rate,
        average_return=average_return,
        median_return=average_return,
        average_max_gain=max(average_return, 0.0) + 2.0,
        average_drawdown=average_drawdown,
        expectancy=expectancy,
    )


if __name__ == "__main__":
    unittest.main()
