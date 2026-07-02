from __future__ import annotations

import json
import sqlite3
from tempfile import TemporaryDirectory
import unittest
from pathlib import Path

from src.developer import (
    validate_snapshot_payload_v2_payload,
    validate_snapshot_payload_v2_records,
)


class SnapshotPayloadV2ValidationTest(unittest.TestCase):
    def test_valid_payload_reports_pass(self) -> None:
        result = validate_snapshot_payload_v2_payload(
            _valid_payload(),
            snapshot_record_id="snapshot-1",
        )

        self.assertTrue(result.passed)
        self.assertEqual(result.status, "PASS")
        self.assertEqual(result.errors, ())
        self.assertEqual(result.report(), "PASS: 1 SnapshotPayloadV2 record(s) valid.")

    def test_invalid_payload_reports_readable_errors(self) -> None:
        payload = _valid_payload()
        payload.pop("diagnostics")
        payload["identity"]["payload_schema_version"] = "canonical_result_v1"
        payload["input"]["ohlcv_window"]["row_count"] = 0
        payload["analysis"]["brain_snapshot"]["indicators"] = {}
        payload["context"].pop("volume")

        result = validate_snapshot_payload_v2_payload(
            payload,
            snapshot_record_id="snapshot-bad",
        )

        self.assertFalse(result.passed)
        self.assertEqual(result.status, "FAIL")
        self.assertIn(
            "snapshot-bad: missing required section: diagnostics",
            result.errors,
        )
        self.assertIn(
            "snapshot-bad: identity.payload_schema_version must be snapshot_payload_v2",
            result.errors,
        )
        self.assertIn(
            "snapshot-bad: input.ohlcv_window.row_count must be greater than 0",
            result.errors,
        )
        self.assertIn(
            "snapshot-bad: analysis.brain_snapshot.indicators must be populated",
            result.errors,
        )
        self.assertIn(
            "snapshot-bad: context.volume must be populated",
            result.errors,
        )
        self.assertTrue(result.report().startswith("FAIL: 1 SnapshotPayloadV2 record(s) checked;"))

    def test_database_validation_scans_saved_daily_snapshot_rows(self) -> None:
        with TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "exos.db"
            connection = sqlite3.connect(db_path)
            try:
                _create_daily_snapshot_table(connection)
                _insert_snapshot_payload(
                    connection,
                    snapshot_record_id="snapshot-good",
                    payload=_valid_payload(),
                )
                bad_payload = _valid_payload()
                bad_payload["context"]["market"] = {}
                _insert_snapshot_payload(
                    connection,
                    snapshot_record_id="snapshot-bad",
                    payload=bad_payload,
                )
                connection.commit()
            finally:
                connection.close()

            result = validate_snapshot_payload_v2_records(db_path)

        self.assertFalse(result.passed)
        self.assertEqual(result.checked_count, 2)
        self.assertEqual(
            result.errors,
            ("snapshot-bad: context.market must be populated",),
        )

    def test_missing_database_reports_fail_without_creating_file(self) -> None:
        with TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "missing.db"

            result = validate_snapshot_payload_v2_records(db_path)

            self.assertFalse(result.passed)
            self.assertEqual(result.checked_count, 0)
            self.assertIn("database not found", result.errors[0])
            self.assertFalse(db_path.exists())


def _valid_payload() -> dict[str, object]:
    return {
        "identity": {
            "payload_schema_version": "snapshot_payload_v2",
            "symbol": "AAPL",
            "market_date": "2026-07-02",
            "timeframe": "1D",
        },
        "provenance": {
            "created_at": "2026-07-02T09:30:00+00:00",
        },
        "input": {
            "ohlcv_window": {
                "row_count": 2,
                "first_date": "2026-07-01",
                "last_date": "2026-07-02",
                "rows": [
                    {"date": "2026-07-01", "close": 100.0},
                    {"date": "2026-07-02", "close": 101.0},
                ],
            },
        },
        "analysis": {
            "brain_snapshot": {
                "indicators": {
                    "ema20": 100.5,
                },
            },
        },
        "context": {
            "market": {"trend": "up"},
            "sector": {"trend": "unknown"},
            "relative_strength": {"rating": "unknown"},
            "volume": {"volume_state": "normal"},
            "support_resistance": {"nearest_support": 100.0},
        },
        "strategy": {},
        "display_summary": {},
        "diagnostics": {},
        "compatibility": {},
    }


def _create_daily_snapshot_table(connection: sqlite3.Connection) -> None:
    connection.execute(
        """
        CREATE TABLE daily_research_snapshots (
            snapshot_record_id TEXT PRIMARY KEY,
            symbol TEXT NOT NULL,
            market_date TEXT NOT NULL,
            timeframe TEXT NOT NULL,
            canonical_schema_version TEXT NOT NULL,
            persistence_version TEXT NOT NULL,
            canonical_snapshot_json TEXT NOT NULL,
            signal_id TEXT,
            payload_hash TEXT NOT NULL,
            source TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )


def _insert_snapshot_payload(
    connection: sqlite3.Connection,
    *,
    snapshot_record_id: str,
    payload: dict[str, object],
) -> None:
    connection.execute(
        """
        INSERT INTO daily_research_snapshots (
            snapshot_record_id,
            symbol,
            market_date,
            timeframe,
            canonical_schema_version,
            persistence_version,
            canonical_snapshot_json,
            signal_id,
            payload_hash,
            source,
            created_at
        )
        VALUES (?, 'AAPL', '2026-07-02', '1D', 'canonical_result_v1',
                'daily_research_snapshot_v2', ?, 'signal-1', 'hash',
                'test', '2026-07-02T09:30:00+00:00')
        """,
        (snapshot_record_id, json.dumps(payload, sort_keys=True)),
    )


if __name__ == "__main__":
    unittest.main()
