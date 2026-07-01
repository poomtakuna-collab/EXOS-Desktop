from __future__ import annotations

import ast
import inspect
import json
import sys
import unittest

import src.signal_ledger.repository as repository_module
from src.outcome_tracking import OutcomeRecord, OutcomeStatus
from src.signal_ledger import (
    InMemorySignalLedgerRepository,
    SignalLedgerRepository,
    SignalRecord,
    SignalSnapshotReference,
    SignalType,
)


class SignalLedgerRepositoryTest(unittest.TestCase):
    def test_public_imports(self) -> None:
        self.assertIsNotNone(SignalLedgerRepository)
        self.assertIsNotNone(InMemorySignalLedgerRepository)

    def test_repository_protocol_shape(self) -> None:
        expected_methods = {
            "save_signal",
            "load_signal",
            "list_signals",
            "save_outcome",
            "list_outcomes_for_signal",
        }

        for method_name in expected_methods:
            self.assertTrue(hasattr(SignalLedgerRepository, method_name))
            self.assertTrue(callable(getattr(InMemorySignalLedgerRepository(), method_name)))

    def test_save_and_load_signal(self) -> None:
        repository = InMemorySignalLedgerRepository()
        signal = _signal(signal_id="signal-1", symbol="AAPL")

        saved = repository.save_signal(signal)
        loaded = repository.load_signal("signal-1")

        self.assertEqual(saved, signal)
        self.assertEqual(loaded, signal)

    def test_load_missing_signal_returns_none(self) -> None:
        repository = InMemorySignalLedgerRepository()

        self.assertIsNone(repository.load_signal("missing"))

    def test_list_signals_preserves_insertion_order_and_filters_by_symbol(self) -> None:
        repository = InMemorySignalLedgerRepository()
        first = _signal(signal_id="signal-1", symbol="AAPL")
        second = _signal(signal_id="signal-2", symbol="MSFT")
        third = _signal(signal_id="signal-3", symbol="AAPL")

        repository.save_signal(first)
        repository.save_signal(second)
        repository.save_signal(third)

        self.assertEqual(repository.list_signals(), (first, second, third))
        self.assertEqual(repository.list_signals(symbol="AAPL"), (first, third))

    def test_save_signal_replaces_existing_id(self) -> None:
        repository = InMemorySignalLedgerRepository()
        original = _signal(signal_id="signal-1", symbol="AAPL")
        updated = _signal(signal_id="signal-1", symbol="MSFT")

        repository.save_signal(original)
        repository.save_signal(updated)

        self.assertEqual(repository.load_signal("signal-1"), updated)
        self.assertEqual(repository.list_signals(), (updated,))

    def test_save_signal_requires_signal_id(self) -> None:
        repository = InMemorySignalLedgerRepository()

        with self.assertRaises(ValueError):
            repository.save_signal(SignalRecord())

    def test_save_and_list_outcomes_for_signal(self) -> None:
        repository = InMemorySignalLedgerRepository()
        first = _outcome("AAPL", "2026-07-11", 5.0)
        second = _outcome("AAPL", "2026-07-21", -2.5)

        saved_first = repository.save_outcome("signal-1", first)
        saved_second = repository.save_outcome("signal-1", second)

        self.assertEqual(saved_first, first)
        self.assertEqual(saved_second, second)
        self.assertEqual(repository.list_outcomes_for_signal("signal-1"), (first, second))

    def test_list_outcomes_for_missing_signal_is_empty(self) -> None:
        repository = InMemorySignalLedgerRepository()

        self.assertEqual(repository.list_outcomes_for_signal("missing"), ())

    def test_save_outcome_requires_signal_id(self) -> None:
        repository = InMemorySignalLedgerRepository()

        with self.assertRaises(ValueError):
            repository.save_outcome("", _outcome("AAPL", "2026-07-11", 5.0))

    def test_to_dict_is_json_safe(self) -> None:
        repository = InMemorySignalLedgerRepository()
        repository.save_signal(_signal(signal_id="signal-1", symbol="AAPL"))
        repository.save_outcome("signal-1", _outcome("AAPL", "2026-07-11", 5.0))

        output = repository.to_dict()

        self.assertEqual(output["signals"][0]["signal_id"], "signal-1")
        self.assertEqual(
            output["outcomes_by_signal_id"]["signal-1"][0]["outcome_status"],
            "positive",
        )
        json.dumps(output, sort_keys=True)

    def test_repository_returns_defensive_copies(self) -> None:
        repository = InMemorySignalLedgerRepository()
        signal = _signal(
            signal_id="signal-1",
            symbol="AAPL",
            context_summary={"market": {"trend": "up"}},
        )
        outcome = _outcome("AAPL", "2026-07-11", 5.0)

        repository.save_signal(signal)
        repository.save_outcome("signal-1", outcome)
        loaded_signal = repository.load_signal("signal-1")
        loaded_outcome = repository.list_outcomes_for_signal("signal-1")[0]

        self.assertIsNot(loaded_signal, signal)
        self.assertIsNot(loaded_outcome, outcome)
        self.assertEqual(loaded_signal, signal)
        self.assertEqual(loaded_outcome, outcome)

    def test_repository_does_not_import_ai_network_broker_or_database_modules(self) -> None:
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

    def test_running_repository_does_not_load_ai_network_broker_or_database_modules(self) -> None:
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

        repository = InMemorySignalLedgerRepository()
        repository.save_signal(_signal(signal_id="signal-1", symbol="AAPL"))
        repository.save_outcome("signal-1", _outcome("AAPL", "2026-07-11", 5.0))

        imported = set(sys.modules) - before
        imported_roots = {name.split(".")[0] for name in imported}
        self.assertTrue(blocked_module_roots.isdisjoint(imported_roots))


def _signal(
    *,
    signal_id: str,
    symbol: str,
    context_summary: dict[str, object] | None = None,
) -> SignalRecord:
    return SignalRecord(
        signal_id=signal_id,
        symbol=symbol,
        signal_date="2026-07-01",
        snapshot_reference=SignalSnapshotReference(
            snapshot_id="snapshot-1",
            snapshot_date="2026-07-01",
            timeframe="1D",
            source="fixture",
        ),
        context_summary=context_summary or {"market": {"trend": "up"}},
        strategy_summary={"strategy_score": 72.5},
        signal_type=SignalType.SETUP,
        confidence=75.0,
        notes=("fixture",),
    )


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
