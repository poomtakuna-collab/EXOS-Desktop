from __future__ import annotations

import ast
import inspect
import sys
import unittest

import src.outcome_tracking.calculator as calculator_module
from src.outcome_tracking import OutcomeRecord, OutcomeStatus, calculate_outcome_record


def _row(
    date: str,
    high: object,
    low: object,
    close: object,
) -> dict[str, object]:
    return {
        "date": date,
        "open": close,
        "high": high,
        "low": low,
        "close": close,
        "volume": 1_000_000,
    }


class OutcomeCalculatorTest(unittest.TestCase):
    def test_public_import(self) -> None:
        self.assertTrue(callable(calculate_outcome_record))

    def test_positive_outcome_at_horizon(self) -> None:
        outcome = calculate_outcome_record(
            symbol="AAPL",
            signal_date="2026-07-01",
            entry_price=100.0,
            future_rows=[
                _row("2026-07-02", 103.0, 98.0, 102.0),
                _row("2026-07-03", 106.0, 99.0, 105.0),
                _row("2026-07-06", 109.0, 101.0, 108.0),
            ],
            horizon_days=3,
            notes=("fixture",),
        )

        self.assertEqual(
            outcome,
            OutcomeRecord(
                symbol="AAPL",
                signal_date="2026-07-01",
                evaluation_date="2026-07-06",
                horizon_days=3,
                entry_price=100.0,
                close_price=108.0,
                return_pct=8.0,
                max_runup_pct=9.0,
                max_drawdown_pct=-2.0,
                hit_target=None,
                hit_stop=None,
                outcome_status=OutcomeStatus.POSITIVE,
                notes=("fixture",),
            ),
        )

    def test_negative_outcome_at_horizon(self) -> None:
        outcome = calculate_outcome_record(
            symbol="MSFT",
            signal_date="2026-07-01",
            entry_price=100.0,
            future_rows=[
                _row("2026-07-02", 101.0, 96.0, 98.0),
                _row("2026-07-03", 99.0, 94.0, 95.0),
            ],
            horizon_days=2,
        )

        self.assertEqual(outcome.close_price, 95.0)
        self.assertEqual(outcome.return_pct, -5.0)
        self.assertEqual(outcome.max_runup_pct, 1.0)
        self.assertEqual(outcome.max_drawdown_pct, -6.0)
        self.assertEqual(outcome.outcome_status, OutcomeStatus.NEGATIVE)

    def test_target_hit_classification(self) -> None:
        outcome = calculate_outcome_record(
            symbol="NVDA",
            signal_date="2026-07-01",
            entry_price=100.0,
            target_price=110.0,
            stop_price=95.0,
            future_rows=[
                _row("2026-07-02", 108.0, 98.0, 106.0),
                _row("2026-07-03", 111.0, 101.0, 109.0),
            ],
            horizon_days=2,
        )

        self.assertTrue(outcome.hit_target)
        self.assertFalse(outcome.hit_stop)
        self.assertEqual(outcome.outcome_status, OutcomeStatus.TARGET_HIT)

    def test_stop_hit_classification(self) -> None:
        outcome = calculate_outcome_record(
            symbol="TSLA",
            signal_date="2026-07-01",
            entry_price=100.0,
            target_price=110.0,
            stop_price=96.0,
            future_rows=[
                _row("2026-07-02", 103.0, 97.0, 99.0),
                _row("2026-07-03", 101.0, 94.0, 95.0),
            ],
            horizon_days=2,
        )

        self.assertFalse(outcome.hit_target)
        self.assertTrue(outcome.hit_stop)
        self.assertEqual(outcome.outcome_status, OutcomeStatus.STOP_HIT)

    def test_neutral_outcome_when_return_is_zero(self) -> None:
        outcome = calculate_outcome_record(
            entry_price=100.0,
            future_rows=[_row("2026-07-02", 101.0, 99.0, 100.0)],
            horizon_days=1,
        )

        self.assertEqual(outcome.return_pct, 0.0)
        self.assertEqual(outcome.outcome_status, OutcomeStatus.NEUTRAL)

    def test_open_outcome_when_future_rows_do_not_reach_horizon(self) -> None:
        outcome = calculate_outcome_record(
            symbol="AAPL",
            signal_date="2026-07-01",
            entry_price=100.0,
            target_price=105.0,
            stop_price=95.0,
            future_rows=[_row("2026-07-02", 106.0, 99.0, 104.0)],
            horizon_days=3,
        )

        self.assertEqual(outcome.symbol, "AAPL")
        self.assertEqual(outcome.signal_date, "2026-07-01")
        self.assertEqual(outcome.horizon_days, 3)
        self.assertEqual(outcome.entry_price, 100.0)
        self.assertIsNone(outcome.close_price)
        self.assertIsNone(outcome.return_pct)
        self.assertTrue(outcome.hit_target)
        self.assertFalse(outcome.hit_stop)
        self.assertEqual(outcome.outcome_status, OutcomeStatus.OPEN)
        self.assertIn("not enough future rows for horizon", outcome.notes)

    def test_missing_entry_price_returns_unknown(self) -> None:
        outcome = calculate_outcome_record(
            symbol="AAPL",
            signal_date="2026-07-01",
            future_rows=[_row("2026-07-02", 101.0, 99.0, 100.0)],
            horizon_days=1,
        )

        self.assertEqual(outcome.symbol, "AAPL")
        self.assertIsNone(outcome.entry_price)
        self.assertEqual(outcome.outcome_status, OutcomeStatus.UNKNOWN)
        self.assertIn("entry price unavailable", outcome.notes)

    def test_missing_horizon_returns_unknown(self) -> None:
        outcome = calculate_outcome_record(
            entry_price=100.0,
            future_rows=[_row("2026-07-02", 101.0, 99.0, 100.0)],
        )

        self.assertEqual(outcome.entry_price, 100.0)
        self.assertIsNone(outcome.horizon_days)
        self.assertEqual(outcome.outcome_status, OutcomeStatus.UNKNOWN)
        self.assertIn("horizon unavailable", outcome.notes)

    def test_malformed_future_rows_are_ignored_without_raising(self) -> None:
        outcome = calculate_outcome_record(
            symbol="AAPL",
            signal_date="2026-07-01",
            entry_price="100",
            target_price="bad",
            stop_price=False,
            future_rows=[
                "not-a-row",
                {"date": "2026-07-02", "high": object(), "low": "98", "close": "102"},
                {"date": "2026-07-03", "high": "bad", "low": [], "close": "104"},
            ],
            horizon_days="2",
            notes=("ok", None),
        )

        self.assertEqual(outcome.evaluation_date, "2026-07-03")
        self.assertEqual(outcome.entry_price, 100.0)
        self.assertEqual(outcome.close_price, 104.0)
        self.assertEqual(outcome.return_pct, 4.0)
        self.assertIsNone(outcome.max_runup_pct)
        self.assertEqual(outcome.max_drawdown_pct, -2.0)
        self.assertIsNone(outcome.hit_target)
        self.assertIsNone(outcome.hit_stop)
        self.assertEqual(outcome.outcome_status, OutcomeStatus.POSITIVE)
        self.assertEqual(outcome.notes, ("ok",))

    def test_horizon_close_missing_returns_unknown_with_partial_flags(self) -> None:
        outcome = calculate_outcome_record(
            entry_price=100.0,
            target_price=105.0,
            stop_price=95.0,
            future_rows=[
                _row("2026-07-02", 106.0, 97.0, 104.0),
                {"date": "2026-07-03", "high": 107.0, "low": 96.0, "close": "bad"},
            ],
            horizon_days=2,
        )

        self.assertEqual(outcome.evaluation_date, "2026-07-03")
        self.assertIsNone(outcome.close_price)
        self.assertTrue(outcome.hit_target)
        self.assertFalse(outcome.hit_stop)
        self.assertEqual(outcome.outcome_status, OutcomeStatus.UNKNOWN)
        self.assertIn("horizon close unavailable", outcome.notes)

    def test_short_target_and_stop_are_supported(self) -> None:
        outcome = calculate_outcome_record(
            entry_price=100.0,
            target_price=92.0,
            stop_price=106.0,
            future_rows=[
                _row("2026-07-02", 104.0, 95.0, 98.0),
                _row("2026-07-03", 105.0, 91.0, 93.0),
            ],
            horizon_days=2,
        )

        self.assertTrue(outcome.hit_target)
        self.assertFalse(outcome.hit_stop)
        self.assertEqual(outcome.outcome_status, OutcomeStatus.TARGET_HIT)

    def test_calculator_is_deterministic_for_fixed_inputs(self) -> None:
        rows = [_row("2026-07-02", 101.0, 99.0, 100.5)]

        first = calculate_outcome_record(entry_price=100.0, future_rows=rows, horizon_days=1)
        second = calculate_outcome_record(entry_price=100.0, future_rows=rows, horizon_days=1)

        self.assertEqual(first, second)

    def test_calculator_does_not_import_ai_network_broker_or_database_modules(self) -> None:
        blocked_module_roots = {
            "openai",
            "anthropic",
            "yfinance",
            "requests",
            "httpx",
            "urllib3",
            "alpaca",
            "ib_insync",
            "sqlite3",
        }
        imported_roots: set[str] = set()

        tree = ast.parse(inspect.getsource(calculator_module))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported_roots.update(alias.name.split(".")[0] for alias in node.names)
            if isinstance(node, ast.ImportFrom) and node.module:
                imported_roots.add(node.module.split(".")[0])

        self.assertTrue(blocked_module_roots.isdisjoint(imported_roots))

    def test_running_calculator_does_not_load_ai_network_broker_or_database_modules(self) -> None:
        blocked_module_roots = {
            "openai",
            "anthropic",
            "yfinance",
            "requests",
            "httpx",
            "urllib3",
            "alpaca",
            "ib_insync",
            "sqlite3",
        }
        before = set(sys.modules)

        calculate_outcome_record(
            entry_price=100.0,
            future_rows=[_row("2026-07-02", 101.0, 99.0, 100.0)],
            horizon_days=1,
        )

        imported = set(sys.modules) - before
        imported_roots = {name.split(".")[0] for name in imported}
        self.assertTrue(blocked_module_roots.isdisjoint(imported_roots))


if __name__ == "__main__":
    unittest.main()
