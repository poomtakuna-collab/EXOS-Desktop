from __future__ import annotations

import unittest

from src.strategy import (
    EntryQuality,
    RiskRating,
    StrategyInput,
    TradeGrade,
    analyze_strategy,
)


class StrategyContractRegressionTest(unittest.TestCase):
    def test_strategy_result_public_shape_is_stable(self) -> None:
        result = analyze_strategy(
            StrategyInput(
                snapshot={"snapshot_id": "snapshot-1"},
                probability={
                    "expected_return_10d": 3.0,
                    "probability_down_5pct_10d": 15.0,
                    "expected_drawdown_10d": -2.0,
                    "confidence": 60.0,
                    "evidence_count": 40,
                },
                prediction={
                    "expected_return": 3.0,
                    "confidence": 60.0,
                    "target_zone_low": 102.0,
                    "target_zone_high": 105.0,
                    "risk_zone_low": 97.0,
                    "risk_zone_high": 99.0,
                },
            )
        )

        self.assertEqual(
            set(result.__dict__),
            {
                "strategy_score",
                "trade_grade",
                "entry_quality",
                "risk_rating",
                "reward_risk_estimate",
                "notes",
            },
        )
        self.assertIn(result.trade_grade, set(TradeGrade))
        self.assertIn(result.entry_quality, set(EntryQuality))
        self.assertIn(result.risk_rating, set(RiskRating))
        self.assertEqual(
            set(result.reward_risk_estimate),
            {
                "expected_reward_percent",
                "expected_risk_percent",
                "reward_risk_ratio",
                "target_zone",
                "risk_zone",
            },
        )

    def test_strategy_result_does_not_emit_trade_recommendations(self) -> None:
        result = analyze_strategy(
            StrategyInput(
                snapshot={},
                probability={},
                prediction={},
            )
        )

        result_text = str(result.__dict__).lower()
        self.assertNotIn("buy", result_text)
        self.assertNotIn("sell", result_text)
        self.assertNotIn("hold", result_text)


if __name__ == "__main__":
    unittest.main()
