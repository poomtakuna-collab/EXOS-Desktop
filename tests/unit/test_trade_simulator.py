from __future__ import annotations

import unittest

from src.backtest import TradeOutcomeV1, simulate_trade


class TradeSimulatorTest(unittest.TestCase):
    def test_empty_inputs_return_invalid_outcome(self) -> None:
        outcome = simulate_trade(None, None)

        _assert_valid_outcome(self, outcome)
        self.assertEqual(outcome.entry_price, 0.0)
        self.assertEqual(outcome.exit_price, 0.0)
        self.assertEqual(outcome.outcome_label, "Invalid")

    def test_target_hit_returns_target_exit(self) -> None:
        outcome = simulate_trade(
            _trade_setup(),
            [
                _ohlcv(high=104.0, low=99.0, close=103.0),
                _ohlcv(high=106.0, low=101.0, close=105.5),
            ],
        )

        _assert_valid_outcome(self, outcome)
        self.assertEqual(outcome.exit_price, 105.0)
        self.assertEqual(outcome.gross_return_percent, 5.0)
        self.assertEqual(outcome.gross_pnl, 50.0)
        self.assertEqual(outcome.outcome_label, "Win")

    def test_stop_hit_returns_stop_exit(self) -> None:
        outcome = simulate_trade(
            _trade_setup(),
            [
                _ohlcv(high=102.0, low=98.0, close=99.0),
                _ohlcv(high=101.0, low=94.0, close=95.0),
            ],
        )

        _assert_valid_outcome(self, outcome)
        self.assertEqual(outcome.exit_price, 95.0)
        self.assertEqual(outcome.gross_return_percent, -5.0)
        self.assertEqual(outcome.gross_pnl, -50.0)
        self.assertEqual(outcome.outcome_label, "Loss")

    def test_stop_before_later_target_returns_stop_exit(self) -> None:
        outcome = simulate_trade(
            _trade_setup(),
            [
                _ohlcv(high=104.0, low=94.0, close=96.0),
                _ohlcv(high=107.0, low=100.0, close=106.0),
            ],
        )

        _assert_valid_outcome(self, outcome)
        self.assertEqual(outcome.exit_price, 95.0)
        self.assertEqual(outcome.outcome_label, "Loss")

    def test_target_before_later_stop_returns_target_exit(self) -> None:
        outcome = simulate_trade(
            _trade_setup(),
            [
                _ohlcv(high=106.0, low=99.0, close=105.0),
                _ohlcv(high=101.0, low=94.0, close=95.0),
            ],
        )

        _assert_valid_outcome(self, outcome)
        self.assertEqual(outcome.exit_price, 105.0)
        self.assertEqual(outcome.outcome_label, "Win")

    def test_same_row_target_and_stop_uses_conservative_stop(self) -> None:
        outcome = simulate_trade(
            _trade_setup(),
            [_ohlcv(high=106.0, low=94.0, close=100.0)],
        )

        _assert_valid_outcome(self, outcome)
        self.assertEqual(outcome.exit_price, 95.0)
        self.assertEqual(outcome.outcome_label, "Loss")

    def test_no_hit_exits_at_final_close(self) -> None:
        outcome = simulate_trade(
            _trade_setup(),
            [
                _ohlcv(high=103.0, low=97.0, close=101.0),
                _ohlcv(high=104.0, low=96.0, close=102.0),
            ],
        )

        _assert_valid_outcome(self, outcome)
        self.assertEqual(outcome.exit_price, 102.0)
        self.assertEqual(outcome.gross_return_percent, 2.0)
        self.assertEqual(outcome.outcome_label, "Win")

    def test_malformed_rows_are_ignored_until_valid_final_close(self) -> None:
        outcome = simulate_trade(
            _trade_setup(),
            [
                {"high": "bad", "low": None, "close": "also-bad"},
                _ohlcv(high=103.0, low=97.0, close=101.5),
            ],
        )

        _assert_valid_outcome(self, outcome)
        self.assertEqual(outcome.exit_price, 101.5)
        self.assertEqual(outcome.outcome_label, "Win")

    def test_malformed_setup_container_is_safe(self) -> None:
        outcome = simulate_trade("bad-setup", [])

        _assert_valid_outcome(self, outcome)
        self.assertEqual(outcome.entry_price, 0.0)
        self.assertEqual(outcome.outcome_label, "Invalid")

    def test_malformed_future_rows_container_is_safe(self) -> None:
        outcome = simulate_trade(_trade_setup(), 123)  # type: ignore[arg-type]

        _assert_valid_outcome(self, outcome)
        self.assertEqual(outcome.entry_price, 100.0)
        self.assertEqual(outcome.exit_price, 0.0)
        self.assertEqual(outcome.outcome_label, "Invalid")

    def test_malformed_future_row_is_safe(self) -> None:
        outcome = simulate_trade(_trade_setup(), ["bad-row"])

        _assert_valid_outcome(self, outcome)
        self.assertEqual(outcome.exit_price, 0.0)
        self.assertEqual(outcome.outcome_label, "Invalid")

    def test_deterministic_simulation(self) -> None:
        trade_setup = _trade_setup()
        future_rows = [_ohlcv(high=104.0, low=97.0, close=101.0)]

        first_outcome = simulate_trade(trade_setup, future_rows)
        second_outcome = simulate_trade(trade_setup, future_rows)

        self.assertEqual(first_outcome, second_outcome)


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
    test_case.assertIn(
        outcome.outcome_label,
        {"Win", "Loss", "Breakeven", "Invalid"},
    )


def _trade_setup() -> dict[str, object]:
    return {
        "entry_price": 100.0,
        "stop_price": 95.0,
        "target_price": 105.0,
        "position_size": 10.0,
    }


def _ohlcv(high: float, low: float, close: float) -> dict[str, object]:
    return {
        "open": 100.0,
        "high": high,
        "low": low,
        "close": close,
        "volume": 1_000_000,
    }


if __name__ == "__main__":
    unittest.main()
