from __future__ import annotations

import ast
import inspect
import json
import sys
import unittest
from dataclasses import FrozenInstanceError, is_dataclass

import src.signal_ledger as signal_ledger_module
import src.signal_ledger.contracts as contracts_module
from src.signal_ledger import SignalRecord, SignalSnapshotReference, SignalType


class SignalLedgerContractsTest(unittest.TestCase):
    def test_public_imports(self) -> None:
        self.assertIsNotNone(SignalRecord)
        self.assertIsNotNone(SignalSnapshotReference)
        self.assertIsNotNone(SignalType)

    def test_contract_shapes_are_immutable_dataclasses(self) -> None:
        self.assertTrue(is_dataclass(SignalRecord))
        self.assertTrue(is_dataclass(SignalSnapshotReference))

        signal = SignalRecord(symbol="AAPL")
        snapshot = SignalSnapshotReference(snapshot_id="snapshot-1")

        with self.assertRaises(FrozenInstanceError):
            signal.symbol = "MSFT"
        with self.assertRaises(FrozenInstanceError):
            snapshot.snapshot_id = "snapshot-2"

    def test_default_values_are_storage_neutral(self) -> None:
        signal = SignalRecord()
        snapshot = SignalSnapshotReference()

        self.assertEqual(snapshot.snapshot_id, "")
        self.assertEqual(snapshot.snapshot_date, "")
        self.assertEqual(snapshot.timeframe, "")
        self.assertEqual(snapshot.source, "")
        self.assertEqual(signal.signal_id, "")
        self.assertEqual(signal.symbol, "")
        self.assertEqual(signal.signal_date, "")
        self.assertEqual(signal.snapshot_reference, SignalSnapshotReference())
        self.assertEqual(signal.context_summary, {})
        self.assertEqual(signal.strategy_summary, {})
        self.assertEqual(signal.signal_type, SignalType.UNKNOWN)
        self.assertIsNone(signal.confidence)
        self.assertEqual(signal.notes, ())

    def test_signal_type_values_are_stable(self) -> None:
        self.assertEqual(SignalType.UNKNOWN.value, "unknown")
        self.assertEqual(SignalType.WATCH.value, "watch")
        self.assertEqual(SignalType.SETUP.value, "setup")
        self.assertEqual(SignalType.BREAKOUT.value, "breakout")
        self.assertEqual(SignalType.RISK.value, "risk")
        self.assertEqual(SignalType.INVALIDATION.value, "invalidation")
        self.assertEqual(SignalType.INFORMATIONAL.value, "informational")

    def test_to_dict_returns_plain_serializable_dict(self) -> None:
        signal = SignalRecord(
            signal_id="signal-1",
            symbol="AAPL",
            signal_date="2026-07-01",
            snapshot_reference=SignalSnapshotReference(
                snapshot_id="snapshot-1",
                snapshot_date="2026-07-01",
                timeframe="1D",
                source="analysis_pipeline",
            ),
            context_summary={
                "market": {"trend": "up", "risk_state": "risk_on"},
                "volume": {"volume_state": "high"},
            },
            strategy_summary={
                "strategy_score": 72.5,
                "trade_grade": "B",
                "risk_rating": "Moderate",
            },
            signal_type=SignalType.SETUP,
            confidence=68.5,
            notes=("deterministic signal ledger foundation",),
        )

        output = signal.to_dict()

        self.assertEqual(output["signal_id"], "signal-1")
        self.assertEqual(output["symbol"], "AAPL")
        self.assertEqual(output["signal_date"], "2026-07-01")
        self.assertEqual(output["snapshot_reference"]["snapshot_id"], "snapshot-1")
        self.assertEqual(output["context_summary"]["market"]["trend"], "up")
        self.assertEqual(output["strategy_summary"]["strategy_score"], 72.5)
        self.assertEqual(output["signal_type"], "setup")
        self.assertEqual(output["confidence"], 68.5)
        self.assertEqual(output["notes"], ["deterministic signal ledger foundation"])
        json.dumps(output, sort_keys=True)

    def test_snapshot_reference_to_dict_is_serializable(self) -> None:
        output = SignalSnapshotReference(
            snapshot_id="snapshot-1",
            snapshot_date="2026-07-01",
            timeframe="1D",
            source="fixture",
        ).to_dict()

        self.assertEqual(output["snapshot_id"], "snapshot-1")
        json.dumps(output, sort_keys=True)

    def test_optional_fields_can_be_missing(self) -> None:
        output = SignalRecord(symbol="AAPL").to_dict()

        self.assertEqual(output["symbol"], "AAPL")
        self.assertEqual(output["snapshot_reference"], SignalSnapshotReference().to_dict())
        self.assertEqual(output["context_summary"], {})
        self.assertEqual(output["strategy_summary"], {})
        self.assertEqual(output["signal_type"], "unknown")
        self.assertIsNone(output["confidence"])
        self.assertEqual(output["notes"], [])
        json.dumps(output, sort_keys=True)

    def test_string_signal_type_serializes_without_validation_side_effects(self) -> None:
        signal = SignalRecord(signal_type="custom-research-signal")

        self.assertEqual(signal.to_dict()["signal_type"], "custom-research-signal")

    def test_signal_ledger_does_not_import_ai_network_broker_or_database_modules(self) -> None:
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

        for module in (signal_ledger_module, contracts_module):
            tree = ast.parse(inspect.getsource(module))
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    imported_roots.update(alias.name.split(".")[0] for alias in node.names)
                if isinstance(node, ast.ImportFrom) and node.module:
                    imported_roots.add(node.module.split(".")[0])

        self.assertTrue(blocked_module_roots.isdisjoint(imported_roots))

    def test_importing_signal_ledger_does_not_load_ai_network_broker_or_database_modules(self) -> None:
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

        import src.signal_ledger  # noqa: F401

        imported = set(sys.modules) - before
        imported_roots = {name.split(".")[0] for name in imported}
        self.assertTrue(blocked_module_roots.isdisjoint(imported_roots))


if __name__ == "__main__":
    unittest.main()
