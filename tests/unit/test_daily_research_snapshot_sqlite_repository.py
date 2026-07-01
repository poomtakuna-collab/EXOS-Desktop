from __future__ import annotations

from contextlib import closing
import hashlib
import json
import sqlite3
import unittest

from src.canonical_result import (
    CANONICAL_RESULT_SCHEMA_VERSION_V1,
    CanonicalBrainResultV1,
    CanonicalDiagnosticsV1,
    CanonicalIdentityV1,
    CanonicalPredictionResultV1,
    CanonicalResultV1,
    CanonicalSignalSummaryV1,
)
from src.daily_research_snapshot import (
    DAILY_RESEARCH_SNAPSHOT_PERSISTENCE_VERSION_V2,
    DailyResearchSnapshotConflictError,
    SQLiteDailyResearchSnapshotRepository,
    initialize_daily_research_snapshot_schema,
)


class SQLiteDailyResearchSnapshotRepositoryTest(unittest.TestCase):
    def test_schema_initialization_creates_daily_research_snapshots_table(self) -> None:
        with closing(_connection()) as connection:
            initialize_daily_research_snapshot_schema(connection)

            table_names = {
                row[0]
                for row in connection.execute(
                    """
                    SELECT name
                    FROM sqlite_master
                    WHERE type = 'table'
                    """
                ).fetchall()
            }
            index_names = {
                row[0]
                for row in connection.execute(
                    """
                    SELECT name
                    FROM sqlite_master
                    WHERE type = 'index'
                    """
                ).fetchall()
            }

            self.assertIn("daily_research_snapshots", table_names)
            self.assertIn("idx_daily_research_snapshot_identity", index_names)

    def test_save_and_load_full_canonical_result_json(self) -> None:
        with closing(_connection()) as connection:
            repository = SQLiteDailyResearchSnapshotRepository(connection)
            repository.initialize_schema()
            canonical = _canonical_result()

            saved = repository.save_snapshot(
                canonical,
                signal_id="signal-1",
                created_at="2026-07-02T00:00:00",
            )
            loaded = repository.load_snapshot(
                symbol="aapl",
                market_date="2026-07-02",
                timeframe="1D",
            )

            self.assertEqual(loaded, saved)
            self.assertEqual(saved.symbol, "AAPL")
            self.assertEqual(saved.market_date, "2026-07-02")
            self.assertEqual(saved.timeframe, "1D")
            self.assertEqual(saved.signal_id, "signal-1")
            self.assertEqual(saved.canonical_schema_version, CANONICAL_RESULT_SCHEMA_VERSION_V1)
            self.assertEqual(saved.persistence_version, DAILY_RESEARCH_SNAPSHOT_PERSISTENCE_VERSION_V2)
            self.assertEqual(saved.source, "analysis_pipeline_v2")
            self.assertEqual(saved.canonical_snapshot, canonical.to_dict())
            self.assertEqual(
                saved.payload_hash,
                hashlib.sha256(saved.canonical_snapshot_json.encode("utf-8")).hexdigest(),
            )
            self.assertTrue(saved.canonical_snapshot_json.startswith("{\n"))
            json.loads(saved.canonical_snapshot_json)

    def test_list_snapshots_filters_and_orders_deterministically(self) -> None:
        with closing(_connection()) as connection:
            repository = SQLiteDailyResearchSnapshotRepository(connection)
            repository.initialize_schema()
            repository.save_snapshot(_canonical_result(symbol="MSFT", market_date="2026-07-03"))
            repository.save_snapshot(_canonical_result(symbol="AAPL", market_date="2026-07-02"))
            repository.save_snapshot(_canonical_result(symbol="AAPL", market_date="2026-07-01"))

            all_records = repository.list_snapshots()
            aapl_records = repository.list_snapshots(symbol="aapl")
            date_records = repository.list_snapshots(market_date="2026-07-02")
            timeframe_records = repository.list_snapshots(timeframe="1D")

            self.assertEqual(
                [(record.symbol, record.market_date) for record in all_records],
                [("AAPL", "2026-07-01"), ("AAPL", "2026-07-02"), ("MSFT", "2026-07-03")],
            )
            self.assertEqual(
                [(record.symbol, record.market_date) for record in aapl_records],
                [("AAPL", "2026-07-01"), ("AAPL", "2026-07-02")],
            )
            self.assertEqual(
                [(record.symbol, record.market_date) for record in date_records],
                [("AAPL", "2026-07-02")],
            )
            self.assertEqual(len(timeframe_records), 3)

    def test_same_identity_and_same_payload_is_idempotent(self) -> None:
        with closing(_connection()) as connection:
            repository = SQLiteDailyResearchSnapshotRepository(connection)
            repository.initialize_schema()
            canonical = _canonical_result()

            first = repository.save_snapshot(canonical, created_at="first")
            second = repository.save_snapshot(canonical, created_at="second")

            self.assertEqual(second, first)
            self.assertEqual(repository.list_snapshots(), (first,))

    def test_same_identity_and_different_payload_conflicts(self) -> None:
        with closing(_connection()) as connection:
            repository = SQLiteDailyResearchSnapshotRepository(connection)
            repository.initialize_schema()
            repository.save_snapshot(_canonical_result(confidence=70.0))

            with self.assertRaises(DailyResearchSnapshotConflictError):
                repository.save_snapshot(_canonical_result(confidence=71.0))

            self.assertEqual(len(repository.list_snapshots()), 1)

    def test_same_date_with_different_schema_version_can_coexist(self) -> None:
        with closing(_connection()) as connection:
            repository = SQLiteDailyResearchSnapshotRepository(connection)
            repository.initialize_schema()
            first = repository.save_snapshot(_canonical_result(schema_version="canonical_result_v1"))
            second = repository.save_snapshot(_canonical_result(schema_version="canonical_result_v1_1"))

            self.assertNotEqual(first.snapshot_record_id, second.snapshot_record_id)
            self.assertEqual(
                [record.canonical_schema_version for record in repository.list_snapshots()],
                ["canonical_result_v1", "canonical_result_v1_1"],
            )

    def test_snapshot_record_id_is_stable_and_independent_of_old_snapshot_id(self) -> None:
        with closing(_connection()) as connection:
            repository = SQLiteDailyResearchSnapshotRepository(connection)
            repository.initialize_schema()
            without_old_snapshot_id = repository.save_snapshot(
                _canonical_result(snapshot_id="")
            )

        with closing(_connection()) as connection:
            repository = SQLiteDailyResearchSnapshotRepository(connection)
            repository.initialize_schema()
            regenerated = repository.save_snapshot(_canonical_result(snapshot_id=""))

            self.assertEqual(
                regenerated.snapshot_record_id,
                without_old_snapshot_id.snapshot_record_id,
            )
            self.assertTrue(regenerated.snapshot_record_id.startswith("snapshot-v2:aapl:2026-07-02:1d:"))


def _connection() -> sqlite3.Connection:
    return sqlite3.connect(":memory:")


def _canonical_result(
    *,
    symbol: str = "AAPL",
    market_date: str = "2026-07-02",
    timeframe: str = "1D",
    snapshot_id: str = "snapshot-1",
    confidence: float = 70.0,
    schema_version: str = CANONICAL_RESULT_SCHEMA_VERSION_V1,
) -> CanonicalResultV1:
    return CanonicalResultV1(
        identity=CanonicalIdentityV1(
            symbol=symbol,
            timeframe=timeframe,
            snapshot_id=snapshot_id,
            snapshot_date="2026-07-01",
            analysis_date=market_date,
            source="analysis_pipeline_v2",
            pipeline_name="analysis_pipeline_v2",
            pipeline_version="v2",
            run_id="run-1",
        ),
        brain=CanonicalBrainResultV1(
            snapshot={"metadata": {"symbol": symbol, "timeframe": timeframe}},
            resolver_output={"matches": [{"pattern_id": "pattern-1"}]},
            probability={"positive": 0.64},
            projection={"expected_return_10d": 5.0},
            target_zone={"base": 110.0},
            risk_zone={"base": 95.0},
            prediction_summary={"confidence": confidence, "evidence_count": 12},
            metadata={"fixture": True},
            notes=("brain note",),
        ),
        diagnostics=CanonicalDiagnosticsV1(
            source_pipeline="analysis_pipeline_v2",
            available_sections=("brain", "prediction"),
            row_count=250,
            warnings=("fixture warning",),
            adapter_version="canonical-adapter-v1",
        ),
        prediction=CanonicalPredictionResultV1(
            confidence=confidence,
            evidence_count=12,
            probability_positive=64.0,
            expected_return_10d=5.0,
            best_pattern_id="pattern-1",
            best_similarity=89.0,
        ),
        signal_summary=CanonicalSignalSummaryV1(
            symbol=symbol,
            signal_date=market_date,
            timeframe=timeframe,
            signal_type="setup",
            confidence=confidence,
            snapshot_id=snapshot_id,
            snapshot_date=market_date,
            prediction_summary={"confidence": confidence},
            notes=("candidate",),
        ),
        schema_version=schema_version,
    )


if __name__ == "__main__":
    unittest.main()
