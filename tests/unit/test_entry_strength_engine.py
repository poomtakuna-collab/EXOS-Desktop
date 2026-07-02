from __future__ import annotations

import unittest

from src.research import ENTRY_STRENGTH_SCHEMA_KEYS, build_entry_strength
from src.statistics_engine import FeatureBucketStats, StatisticsEngineReport


class EntryStrengthEngineTest(unittest.TestCase):
    def test_strong_valid_entry_setup(self) -> None:
        result = build_entry_strength(
            {
                "snapshot": _payload(),
                "statistics": _statistics_report(
                    _stats("poom_ew", "positive:10_to_25", 50, 62.0, 4.0, 3.5, -3.0),
                ),
            }
        )

        self.assertGreaterEqual(result["entry_strength_score"], 85)
        self.assertEqual(result["entry_strength_label"], "Excellent")
        self.assertEqual(result["entry_timing"], "Valid")
        self.assertTrue(any("Squeeze has released upward" in item for item in result["entry_reasons"]))
        self.assertNotIn("recommendation", result)
        self.assertNotIn("zone", " ".join(result.keys()).lower())

    def test_early_entry_when_setup_has_not_confirmed(self) -> None:
        result = build_entry_strength(
            {
                "snapshot": _payload(
                    poom={
                        "ew_norm": 10.0,
                        "volume_pressure": 8.0,
                        "trend_slope": 4.0,
                        "in_squeeze": True,
                        "squeeze_up": False,
                        "squeeze_down": False,
                        "bos_up": False,
                        "bos_down": False,
                        "choch_up": False,
                        "choch_down": False,
                        "msb_dir": 1,
                    },
                ),
                "historical_edge": _edge(sample_count=35, win_rate=58.0, average_return=2.0, expectancy=1.5),
            }
        )

        self.assertEqual(result["entry_timing"], "Early")
        self.assertIn(result["entry_strength_label"], {"Moderate", "Strong"})
        self.assertTrue(any("timing may be early" in item for item in result["entry_risks"]))

    def test_late_entry_when_price_is_extended(self) -> None:
        result = build_entry_strength(
            {
                "snapshot": _payload(
                    close=112.0,
                    indicators={"ema20": 100.0, "ema50": 98.0, "ema200": 90.0, "ema_alignment": "bullish"},
                ),
                "historical_edge": _edge(sample_count=40, win_rate=60.0, average_return=3.0, expectancy=2.0),
            }
        )

        self.assertEqual(result["entry_timing"], "Late")
        self.assertGreaterEqual(result["entry_strength_score"], 65)
        self.assertTrue(any("extended" in item for item in result["entry_risks"]))

    def test_avoid_entry_for_weak_bearish_setup(self) -> None:
        result = build_entry_strength(
            {
                "snapshot": _payload(
                    poom={
                        "ew_norm": -16.0,
                        "volume_pressure": -18.0,
                        "trend_slope": -5.0,
                        "in_squeeze": False,
                        "squeeze_up": False,
                        "squeeze_down": True,
                        "bos_up": False,
                        "bos_down": True,
                        "choch_up": False,
                        "choch_down": False,
                        "msb_dir": -1,
                    },
                    indicators={"ema20": 105.0, "ema50": 108.0, "ema200": 120.0, "ema_alignment": "bearish"},
                    trend={"state": "bearish"},
                    close=100.0,
                ),
                "historical_edge": _edge(sample_count=32, win_rate=39.0, average_return=-2.0, expectancy=-1.0, average_drawdown=-8.0),
            }
        )

        self.assertLess(result["entry_strength_score"], 40)
        self.assertEqual(result["entry_strength_label"], "Weak")
        self.assertEqual(result["entry_timing"], "Avoid")
        self.assertTrue(any("downward" in item for item in result["entry_risks"]))

    def test_missing_data_schema_stability(self) -> None:
        result = build_entry_strength({"snapshot": {"analysis": {}, "input": {}, "context": {}}})

        self.assertEqual(tuple(result.keys()), ENTRY_STRENGTH_SCHEMA_KEYS)
        self.assertIsInstance(result["entry_strength_score"], int)
        self.assertIsInstance(result["entry_strength_label"], str)
        self.assertIsInstance(result["entry_timing"], str)
        self.assertIsInstance(result["entry_reasons"], list)
        self.assertIsInstance(result["entry_risks"], list)
        self.assertIn(result["entry_strength_label"], {"Weak", "Moderate", "Strong", "Excellent"})
        self.assertIn(result["entry_timing"], {"Early", "Valid", "Late", "Avoid"})


def _payload(
    *,
    poom: dict[str, object] | None = None,
    indicators: dict[str, object] | None = None,
    trend: dict[str, object] | None = None,
    close: float = 100.0,
) -> dict[str, object]:
    return {
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
                "volume_pressure": 14.0,
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
                "score": {"rating": "GOOD", "recommendation": "watch", "confidence": 70.0},
            },
        },
        "context": {
            "support_resistance": {
                "nearest_support": 94.0,
                "nearest_resistance": 112.0,
            }
        },
    }


def _edge(
    *,
    sample_count: int,
    win_rate: float,
    average_return: float,
    expectancy: float,
    average_drawdown: float = -3.0,
) -> dict[str, object]:
    return {
        "feature_name": "poom_ew",
        "bucket": "positive:10_to_25",
        "sample_count": sample_count,
        "win_rate": win_rate,
        "average_return": average_return,
        "expectancy": expectancy,
        "average_drawdown": average_drawdown,
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
