from __future__ import annotations

import unittest

from src.backtest import TradeOutcomeV1, generate_trade_outcome


class TradeOutcomeModelTest(unittest.TestCase):
    def test_empty_input_returns_safe_defaults(self) -> None:
        outcome = generate_trade_outcome(None)

        _assert_valid_outcome(self, outcome)
        self.assertEqual(outcome.entry_price, 0.0)
        self.assertEqual(outcome.exit_price, 0.0)
        self.assertEqual(outcome.stop_price, 0.0)
        self.assertEqual(outcome.target_price, 0.0)
        self.assertEqual(outcome.position_size, 0.0)
        self.assertEqual(outcome.gross_return_percent, 0.0)
        self.assertEqual(outcome.gross_pnl, 0.0)
        self.assertEqual(outcome.risk_amount, 0.0)
        self.assertEqual(outcome.reward_amount, 0.0)
        self.assertEqual(outcome.outcome_label, "Invalid")

    def test_winning_trade_outcome(self) -> None:
        outcome = generate_trade_outcome(
            {
                "entry_price": 100.0,
                "exit_price": 110.0,
                "stop_price": 95.0,
                "target_price": 112.0,
                "position_size": 10,
            }
        )

        _assert_valid_outcome(self, outcome)
        self.assertEqual(outcome.entry_price, 100.0)
        self.assertEqual(outcome.exit_price, 110.0)
        self.assertEqual(outcome.stop_price, 95.0)
        self.assertEqual(outcome.target_price, 112.0)
        self.assertEqual(outcome.position_size, 10.0)
        self.assertEqual(outcome.gross_return_percent, 10.0)
        self.assertEqual(outcome.gross_pnl, 100.0)
        self.assertEqual(outcome.risk_amount, 50.0)
        self.assertEqual(outcome.reward_amount, 120.0)
        self.assertEqual(outcome.outcome_label, "Win")

    def test_losing_trade_outcome(self) -> None:
        outcome = generate_trade_outcome(
            {
                "entry_price": 50.0,
                "exit_price": 45.0,
                "stop_price": 44.0,
                "target_price": 60.0,
                "position_size": 20,
            }
        )

        _assert_valid_outcome(self, outcome)
        self.assertEqual(outcome.gross_return_percent, -10.0)
        self.assertEqual(outcome.gross_pnl, -100.0)
        self.assertEqual(outcome.risk_amount, 120.0)
        self.assertEqual(outcome.reward_amount, 200.0)
        self.assertEqual(outcome.outcome_label, "Loss")

    def test_breakeven_trade_outcome(self) -> None:
        outcome = generate_trade_outcome(
            {
                "entry_price": 25.0,
                "exit_price": 25.0,
                "stop_price": 22.5,
                "target_price": 30.0,
                "position_size": 4,
            }
        )

        _assert_valid_outcome(self, outcome)
        self.assertEqual(outcome.gross_return_percent, 0.0)
        self.assertEqual(outcome.gross_pnl, 0.0)
        self.assertEqual(outcome.outcome_label, "Breakeven")

    def test_malformed_values_are_coerced_to_safe_defaults(self) -> None:
        outcome = generate_trade_outcome(
            {
                "entry_price": "bad",
                "exit_price": -10,
                "stop_price": None,
                "target_price": "12.5",
                "position_size": -3,
            }
        )

        _assert_valid_outcome(self, outcome)
        self.assertEqual(outcome.entry_price, 0.0)
        self.assertEqual(outcome.exit_price, 0.0)
        self.assertEqual(outcome.stop_price, 0.0)
        self.assertEqual(outcome.target_price, 12.5)
        self.assertEqual(outcome.position_size, 0.0)
        self.assertEqual(outcome.gross_return_percent, 0.0)
        self.assertEqual(outcome.gross_pnl, 0.0)
        self.assertEqual(outcome.risk_amount, 0.0)
        self.assertEqual(outcome.reward_amount, 0.0)
        self.assertEqual(outcome.outcome_label, "Invalid")

    def test_malformed_container_is_safe(self) -> None:
        outcome = generate_trade_outcome("bad-row")

        _assert_valid_outcome(self, outcome)
        self.assertEqual(outcome.entry_price, 0.0)
        self.assertEqual(outcome.exit_price, 0.0)
        self.assertEqual(outcome.outcome_label, "Invalid")

    def test_deterministic_outcome(self) -> None:
        trade_row = {
            "entry_price": "100",
            "exit_price": "103.5",
            "stop_price": "97.5",
            "target_price": "106",
            "position_size": "2",
        }

        first_outcome = generate_trade_outcome(trade_row)
        second_outcome = generate_trade_outcome(trade_row)

        self.assertEqual(first_outcome, second_outcome)

    def test_stable_outcome_shape(self) -> None:
        outcome = generate_trade_outcome(
            {
                "entry_price": 100.0,
                "exit_price": 101.0,
                "stop_price": 98.0,
                "target_price": 104.0,
                "position_size": 1.0,
            }
        )

        self.assertEqual(
            set(outcome.__dict__),
            {
                "entry_price",
                "exit_price",
                "stop_price",
                "target_price",
                "position_size",
                "gross_return_percent",
                "gross_pnl",
                "risk_amount",
                "reward_amount",
                "outcome_label",
            },
        )


def _assert_valid_outcome(
    test_case: unittest.TestCase,
    outcome: TradeOutcomeV1,
) -> None:
    test_case.assertIsInstance(outcome, TradeOutcomeV1)
    test_case.assertGreaterEqual(outcome.entry_price, 0.0)
    test_case.assertGreaterEqual(outcome.exit_price, 0.0)
    test_case.assertGreaterEqual(outcome.stop_price, 0.0)
    test_case.assertGreaterEqual(outcome.target_price, 0.0)
    test_case.assertGreaterEqual(outcome.position_size, 0.0)
    test_case.assertGreaterEqual(outcome.risk_amount, 0.0)
    test_case.assertGreaterEqual(outcome.reward_amount, 0.0)
    test_case.assertIn(
        outcome.outcome_label,
        {"Win", "Loss", "Breakeven", "Invalid"},
    )


if __name__ == "__main__":
    unittest.main()
