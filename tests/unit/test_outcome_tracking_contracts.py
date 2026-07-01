from __future__ import annotations

import ast
import inspect
import json
import sys
import unittest
from dataclasses import FrozenInstanceError, is_dataclass

import src.outcome_tracking as outcome_tracking_module
import src.outcome_tracking.contracts as contracts_module
from src.outcome_tracking import OutcomeRecord, OutcomeStatus


class OutcomeTrackingContractsTest(unittest.TestCase):
    def test_public_imports(self) -> None:
        self.assertIsNotNone(OutcomeRecord)
        self.assertIsNotNone(OutcomeStatus)

    def test_contract_shape_is_immutable_dataclass(self) -> None:
        self.assertTrue(is_dataclass(OutcomeRecord))

        outcome = OutcomeRecord(symbol="AAPL")

        with self.assertRaises(FrozenInstanceError):
            outcome.symbol = "MSFT"

    def test_default_values_are_storage_neutral(self) -> None:
        outcome = OutcomeRecord()

        self.assertEqual(outcome.symbol, "")
        self.assertEqual(outcome.signal_date, "")
        self.assertEqual(outcome.evaluation_date, "")
        self.assertIsNone(outcome.horizon_days)
        self.assertIsNone(outcome.entry_price)
        self.assertIsNone(outcome.close_price)
        self.assertIsNone(outcome.return_pct)
        self.assertIsNone(outcome.max_runup_pct)
        self.assertIsNone(outcome.max_drawdown_pct)
        self.assertIsNone(outcome.hit_target)
        self.assertIsNone(outcome.hit_stop)
        self.assertEqual(outcome.outcome_status, OutcomeStatus.UNKNOWN)
        self.assertEqual(outcome.notes, ())

    def test_outcome_status_values_are_stable(self) -> None:
        self.assertEqual(OutcomeStatus.UNKNOWN.value, "unknown")
        self.assertEqual(OutcomeStatus.OPEN.value, "open")
        self.assertEqual(OutcomeStatus.POSITIVE.value, "positive")
        self.assertEqual(OutcomeStatus.NEGATIVE.value, "negative")
        self.assertEqual(OutcomeStatus.NEUTRAL.value, "neutral")
        self.assertEqual(OutcomeStatus.TARGET_HIT.value, "target_hit")
        self.assertEqual(OutcomeStatus.STOP_HIT.value, "stop_hit")

    def test_to_dict_returns_plain_serializable_dict(self) -> None:
        outcome = OutcomeRecord(
            symbol="AAPL",
            signal_date="2026-07-01",
            evaluation_date="2026-07-11",
            horizon_days=10,
            entry_price=100.0,
            close_price=108.5,
            return_pct=8.5,
            max_runup_pct=12.0,
            max_drawdown_pct=-3.25,
            hit_target=True,
            hit_stop=False,
            outcome_status=OutcomeStatus.TARGET_HIT,
            notes=("target reached before horizon end",),
        )

        output = outcome.to_dict()

        self.assertEqual(output["symbol"], "AAPL")
        self.assertEqual(output["signal_date"], "2026-07-01")
        self.assertEqual(output["evaluation_date"], "2026-07-11")
        self.assertEqual(output["horizon_days"], 10)
        self.assertEqual(output["entry_price"], 100.0)
        self.assertEqual(output["close_price"], 108.5)
        self.assertEqual(output["return_pct"], 8.5)
        self.assertEqual(output["max_runup_pct"], 12.0)
        self.assertEqual(output["max_drawdown_pct"], -3.25)
        self.assertTrue(output["hit_target"])
        self.assertFalse(output["hit_stop"])
        self.assertEqual(output["outcome_status"], "target_hit")
        self.assertEqual(output["notes"], ["target reached before horizon end"])
        json.dumps(output, sort_keys=True)

    def test_optional_fields_can_be_missing(self) -> None:
        output = OutcomeRecord(symbol="AAPL", signal_date="2026-07-01").to_dict()

        self.assertEqual(output["symbol"], "AAPL")
        self.assertEqual(output["signal_date"], "2026-07-01")
        self.assertIsNone(output["evaluation_date"] or None)
        self.assertIsNone(output["horizon_days"])
        self.assertIsNone(output["entry_price"])
        self.assertIsNone(output["close_price"])
        self.assertIsNone(output["return_pct"])
        self.assertIsNone(output["max_runup_pct"])
        self.assertIsNone(output["max_drawdown_pct"])
        self.assertIsNone(output["hit_target"])
        self.assertIsNone(output["hit_stop"])
        self.assertEqual(output["outcome_status"], "unknown")
        self.assertEqual(output["notes"], [])
        json.dumps(output, sort_keys=True)

    def test_string_status_serializes_without_validation_side_effects(self) -> None:
        outcome = OutcomeRecord(outcome_status="custom-outcome-status")

        self.assertEqual(outcome.to_dict()["outcome_status"], "custom-outcome-status")

    def test_outcome_tracking_does_not_import_ai_network_broker_or_database_modules(self) -> None:
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

        for module in (outcome_tracking_module, contracts_module):
            tree = ast.parse(inspect.getsource(module))
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    imported_roots.update(alias.name.split(".")[0] for alias in node.names)
                if isinstance(node, ast.ImportFrom) and node.module:
                    imported_roots.add(node.module.split(".")[0])

        self.assertTrue(blocked_module_roots.isdisjoint(imported_roots))

    def test_importing_outcome_tracking_does_not_load_ai_network_broker_or_database_modules(self) -> None:
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

        import src.outcome_tracking  # noqa: F401

        imported = set(sys.modules) - before
        imported_roots = {name.split(".")[0] for name in imported}
        self.assertTrue(blocked_module_roots.isdisjoint(imported_roots))


if __name__ == "__main__":
    unittest.main()
