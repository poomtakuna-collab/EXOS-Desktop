from __future__ import annotations

import ast
import inspect
import json
import sys
import unittest

import src.outcome_tracking.repository as repository_module
from src.outcome_tracking import (
    InMemoryOutcomeRepository,
    OutcomeRecord,
    OutcomeRepository,
    OutcomeStatus,
)


class OutcomeRepositoryTest(unittest.TestCase):
    def test_public_imports(self) -> None:
        self.assertIsNotNone(OutcomeRepository)
        self.assertIsNotNone(InMemoryOutcomeRepository)

    def test_repository_protocol_shape(self) -> None:
        expected_methods = {
            "save_outcome",
            "load_outcome",
            "list_outcomes",
            "list_outcomes_for_signal",
        }

        for method_name in expected_methods:
            self.assertTrue(hasattr(OutcomeRepository, method_name))
            self.assertTrue(callable(getattr(InMemoryOutcomeRepository(), method_name)))

    def test_save_and_load_outcome(self) -> None:
        repository = InMemoryOutcomeRepository()
        outcome = _outcome("AAPL", "2026-07-11", 5.0)

        saved = repository.save_outcome("signal-1", outcome, outcome_id="outcome-1")
        loaded = repository.load_outcome("outcome-1")

        self.assertEqual(saved, outcome)
        self.assertEqual(loaded, outcome)

    def test_load_missing_outcome_returns_none(self) -> None:
        repository = InMemoryOutcomeRepository()

        self.assertIsNone(repository.load_outcome("missing"))

    def test_list_outcomes_preserves_insert_order_and_filters_by_symbol(self) -> None:
        repository = InMemoryOutcomeRepository()
        first = _outcome("AAPL", "2026-07-11", 5.0)
        second = _outcome("MSFT", "2026-07-12", 2.0)
        third = _outcome("AAPL", "2026-07-21", -2.5)

        repository.save_outcome("signal-1", first, outcome_id="outcome-1")
        repository.save_outcome("signal-2", second, outcome_id="outcome-2")
        repository.save_outcome("signal-1", third, outcome_id="outcome-3")

        self.assertEqual(repository.list_outcomes(), (first, second, third))
        self.assertEqual(repository.list_outcomes(symbol="AAPL"), (first, third))

    def test_list_outcomes_for_signal_preserves_insert_order(self) -> None:
        repository = InMemoryOutcomeRepository()
        first = _outcome("AAPL", "2026-07-11", 5.0)
        second = _outcome("AAPL", "2026-07-21", -2.5)

        repository.save_outcome("signal-1", first, outcome_id="outcome-1")
        repository.save_outcome("signal-2", _outcome("MSFT", "2026-07-12", 2.0), outcome_id="outcome-2")
        repository.save_outcome("signal-1", second, outcome_id="outcome-3")

        self.assertEqual(repository.list_outcomes_for_signal("signal-1"), (first, second))

    def test_save_outcome_replaces_existing_outcome_id(self) -> None:
        repository = InMemoryOutcomeRepository()
        original = _outcome("AAPL", "2026-07-11", 5.0)
        updated = _outcome("MSFT", "2026-07-12", -1.5)

        repository.save_outcome("signal-1", original, outcome_id="outcome-1")
        repository.save_outcome("signal-2", updated, outcome_id="outcome-1")

        self.assertEqual(repository.load_outcome("outcome-1"), updated)
        self.assertEqual(repository.list_outcomes_for_signal("signal-1"), ())
        self.assertEqual(repository.list_outcomes_for_signal("signal-2"), (updated,))

    def test_save_outcome_requires_signal_id_and_outcome_id_when_supplied(self) -> None:
        repository = InMemoryOutcomeRepository()

        with self.assertRaises(ValueError):
            repository.save_outcome("", _outcome("AAPL", "2026-07-11", 5.0))
        with self.assertRaises(ValueError):
            repository.save_outcome("signal-1", _outcome("AAPL", "2026-07-11", 5.0), outcome_id="")

    def test_auto_outcome_ids_support_direct_loads(self) -> None:
        repository = InMemoryOutcomeRepository()
        outcome = _outcome("AAPL", "2026-07-11", 5.0)

        repository.save_outcome("signal-1", outcome)

        self.assertEqual(repository.load_outcome("1"), outcome)

    def test_outcome_repository_does_not_import_ai_network_broker_or_database_modules(self) -> None:
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

        tree = ast.parse(inspect.getsource(repository_module))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported_roots.update(alias.name.split(".")[0] for alias in node.names)
            if isinstance(node, ast.ImportFrom) and node.module:
                imported_roots.add(node.module.split(".")[0])

        self.assertTrue(blocked_module_roots.isdisjoint(imported_roots))

    def test_running_repository_is_json_safe_and_does_not_load_database_modules(self) -> None:
        before = set(sys.modules)
        repository = InMemoryOutcomeRepository()
        repository.save_outcome(
            "signal-1",
            _outcome("AAPL", "2026-07-11", 5.0),
            outcome_id="outcome-1",
        )

        output = {
            "outcomes": [
                outcome.to_dict()
                for outcome in repository.list_outcomes()
            ],
            "signal_outcomes": [
                outcome.to_dict()
                for outcome in repository.list_outcomes_for_signal("signal-1")
            ],
        }

        self.assertEqual(output["outcomes"][0]["outcome_status"], "positive")
        json.dumps(output, sort_keys=True)
        imported = set(sys.modules) - before
        imported_roots = {name.split(".")[0] for name in imported}
        self.assertNotIn("sqlite3", imported_roots)


def _outcome(symbol: str, evaluation_date: str, return_pct: float) -> OutcomeRecord:
    return OutcomeRecord(
        symbol=symbol,
        signal_date="2026-07-01",
        evaluation_date=evaluation_date,
        horizon_days=10,
        entry_price=100.0,
        close_price=100.0 + return_pct,
        return_pct=return_pct,
        max_runup_pct=max(return_pct, 0.0),
        max_drawdown_pct=min(return_pct, 0.0),
        hit_target=False,
        hit_stop=False,
        outcome_status=OutcomeStatus.POSITIVE if return_pct > 0 else OutcomeStatus.NEGATIVE,
        notes=("fixture",),
    )


if __name__ == "__main__":
    unittest.main()
