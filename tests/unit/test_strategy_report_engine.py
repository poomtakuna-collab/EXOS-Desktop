import unittest

from src.analysis import build_strategy_report


class StrategyReportEngineTest(unittest.TestCase):
    def test_empty_inputs_return_safe_report(self) -> None:
        result = build_strategy_report()

        self.assertEqual(
            result,
            {
                "confidence": 0.0,
                "evidence_count": 0,
                "best_pattern_id": None,
                "best_similarity": 0.0,
                "prediction_summary": {},
                "strategy_summary": {},
                "trade_plan": {},
                "position_sizing": {},
            },
        )

    def test_builds_report_sections(self) -> None:
        prediction_summary = _prediction_summary()
        strategy_summary = _strategy_summary()
        trade_plan = _trade_plan()
        position_sizing = _position_sizing()

        result = build_strategy_report(
            prediction_summary=prediction_summary,
            strategy_summary=strategy_summary,
            trade_plan=trade_plan,
            position_sizing=position_sizing,
        )

        self.assertEqual(result["prediction_summary"], prediction_summary)
        self.assertEqual(result["strategy_summary"], strategy_summary)
        self.assertEqual(result["trade_plan"], trade_plan)
        self.assertEqual(result["position_sizing"], position_sizing)

    def test_preserves_prediction_metadata(self) -> None:
        result = build_strategy_report(prediction_summary=_prediction_summary())

        self.assertEqual(result["confidence"], 72.0)
        self.assertEqual(result["evidence_count"], 30)
        self.assertEqual(result["best_pattern_id"], "pattern-1")
        self.assertEqual(result["best_similarity"], 91.0)

    def test_clamps_metadata_bounds(self) -> None:
        result = build_strategy_report(
            prediction_summary={
                "confidence": 150.0,
                "evidence_count": -4,
                "best_pattern_id": "pattern-2",
                "best_similarity": -10.0,
            }
        )

        self.assertEqual(result["confidence"], 100.0)
        self.assertEqual(result["evidence_count"], 0)
        self.assertEqual(result["best_similarity"], 0.0)

    def test_output_has_no_trade_decision(self) -> None:
        result = build_strategy_report(
            prediction_summary=_prediction_summary(),
            strategy_summary=_strategy_summary(),
            trade_plan=_trade_plan(),
            position_sizing=_position_sizing(),
        )

        flattened = [str(value).upper() for value in _flatten_values(result)]
        self.assertNotIn("BUY", flattened)
        self.assertNotIn("SELL", flattened)
        self.assertNotIn("HOLD", flattened)


def _prediction_summary() -> dict[str, object]:
    return {
        "confidence": 72.0,
        "evidence_count": 30,
        "best_pattern_id": "pattern-1",
        "best_similarity": 91.0,
        "probability": {},
        "projection": {},
        "target_zone": {},
        "risk_zone": {},
    }


def _strategy_summary() -> dict[str, object]:
    return {
        "market_bias": "positive",
        "risk_level": "medium",
        "reward_risk_ratio": 2.0,
        "notes": [],
    }


def _trade_plan() -> dict[str, object]:
    return {
        "entry_zone": {"low": 100.0, "high": 104.0},
        "stop_zone": {"conservative": 99.0, "base": 98.0, "aggressive": 96.0},
        "target_zone": {"conservative": 102.0, "base": 104.0, "aggressive": 108.0},
        "risk_reward": {"reward_risk_ratio": 2.0},
        "invalidation_notes": [],
    }


def _position_sizing() -> dict[str, object]:
    return {
        "account_risk_percent": 1.0,
        "risk_per_share": 8.0,
        "position_size_shares": 12,
        "estimated_capital_required": 1248.0,
        "max_loss_amount": 100.0,
    }


def _flatten_values(value: object) -> list[object]:
    if isinstance(value, dict):
        flattened: list[object] = []
        for item in value.values():
            flattened.extend(_flatten_values(item))
        return flattened
    if isinstance(value, list):
        flattened = []
        for item in value:
            flattened.extend(_flatten_values(item))
        return flattened
    return [value]


if __name__ == "__main__":
    unittest.main()
