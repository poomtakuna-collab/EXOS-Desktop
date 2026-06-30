import unittest

from src.analysis import calculate_position_sizing


class PositionSizingEngineTest(unittest.TestCase):
    def test_empty_trade_plan_returns_safe_position_sizing(self) -> None:
        result = calculate_position_sizing({}, account_size=10_000.0)

        self.assertEqual(
            result,
            {
                "account_risk_percent": 1.0,
                "risk_per_share": 0.0,
                "position_size_shares": 0,
                "estimated_capital_required": 0.0,
                "max_loss_amount": 100.0,
            },
        )

    def test_calculates_position_sizing_from_trade_plan(self) -> None:
        result = calculate_position_sizing(
            _trade_plan(),
            account_size=10_000.0,
            account_risk_percent=1.0,
        )

        self.assertEqual(result["account_risk_percent"], 1.0)
        self.assertEqual(result["risk_per_share"], 8.0)
        self.assertEqual(result["position_size_shares"], 12)
        self.assertEqual(result["estimated_capital_required"], 1248.0)
        self.assertEqual(result["max_loss_amount"], 100.0)

    def test_supports_configurable_account_risk(self) -> None:
        result = calculate_position_sizing(
            _trade_plan(),
            account_size=25_000.0,
            account_risk_percent=2.0,
        )

        self.assertEqual(result["account_risk_percent"], 2.0)
        self.assertEqual(result["max_loss_amount"], 500.0)
        self.assertEqual(result["position_size_shares"], 62)

    def test_missing_stop_zone_does_not_crash(self) -> None:
        result = calculate_position_sizing(
            {"entry_zone": {"low": 100.0, "high": 104.0}},
            account_size=10_000.0,
        )

        self.assertEqual(result["risk_per_share"], 0.0)
        self.assertEqual(result["position_size_shares"], 0)
        self.assertEqual(result["estimated_capital_required"], 0.0)

    def test_invalid_risk_inputs_are_safe(self) -> None:
        result = calculate_position_sizing(
            _trade_plan(),
            account_size=-10_000.0,
            account_risk_percent=-1.0,
        )

        self.assertEqual(result["account_risk_percent"], 0.0)
        self.assertEqual(result["max_loss_amount"], 0.0)
        self.assertEqual(result["position_size_shares"], 0)

    def test_output_has_no_trade_decision(self) -> None:
        result = calculate_position_sizing(_trade_plan(), account_size=10_000.0)

        values = {str(value).upper() for value in result.values()}
        self.assertNotIn("BUY", values)
        self.assertNotIn("SELL", values)
        self.assertNotIn("HOLD", values)


def _trade_plan() -> dict[str, object]:
    return {
        "entry_zone": {"low": 100.0, "high": 104.0},
        "stop_zone": {
            "conservative": 99.0,
            "base": 98.0,
            "aggressive": 96.0,
        },
        "target_zone": {
            "conservative": 102.0,
            "base": 104.0,
            "aggressive": 108.0,
        },
        "risk_reward": {
            "reward_risk_ratio": 2.0,
            "market_bias": "positive",
            "risk_level": "medium",
        },
        "invalidation_notes": [],
    }


if __name__ == "__main__":
    unittest.main()
