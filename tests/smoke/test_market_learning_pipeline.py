from __future__ import annotations

import sqlite3
import unittest
from datetime import date, timedelta

from src.analysis import build_exos_snapshot
from src.analysis import resolve_similar_patterns
from src.statistics import (
    CREATE_OUTCOMES_TABLE_SQL,
    CREATE_PATTERNS_TABLE_SQL,
    CREATE_SNAPSHOTS_TABLE_SQL,
    REQUIRED_INDEX_SQL,
    calculate_outcomes_for_series,
    collect_snapshots_for_series,
    discover_patterns,
    find_similar_patterns,
    load_pattern_library,
    rebuild_pattern_library,
)


class MarketLearningPipelineSmokeTest(unittest.TestCase):
    def test_market_learning_pipeline_smoke(self) -> None:
        conn = sqlite3.connect(":memory:")
        try:
            _initialize_in_memory_statistics_db(conn)
            rows = _fake_ohlcv_rows(220)

            snapshot_summary = collect_snapshots_for_series(
                conn,
                rows,
                symbol="AAPL",
                timeframe="1D",
                window_size=80,
            )
            self.assertGreater(snapshot_summary["inserted_count"], 0)
            self.assertEqual(snapshot_summary["skipped_count"], 79)

            outcome_summary = calculate_outcomes_for_series(
                conn,
                rows,
                symbol="AAPL",
                timeframe="1D",
            )
            self.assertGreaterEqual(outcome_summary["calculated_count"], 30)
            self.assertGreaterEqual(outcome_summary["skipped_count"], 20)

            patterns = discover_patterns(conn, min_samples=30)
            self.assertGreaterEqual(len(patterns), 1)

            library_summary = rebuild_pattern_library(conn, min_samples=30)
            self.assertEqual(library_summary["total_patterns"], len(patterns))
            self.assertEqual(library_summary["inserted_patterns"], len(patterns))
            pattern_library = load_pattern_library(conn)
            self.assertEqual(len(pattern_library), len(patterns))

            latest_snapshot = build_exos_snapshot(
                rows[-80:],
                symbol="AAPL",
                timeframe="1D",
            )
            similar_patterns = find_similar_patterns(conn, latest_snapshot, top_n=5)
            self.assertGreaterEqual(len(similar_patterns), 1)
            self.assertTrue(similar_patterns[0]["pattern_id"])
            self.assertGreaterEqual(similar_patterns[0]["similarity_score"], 0)
            self.assertLessEqual(similar_patterns[0]["similarity_score"], 100)
            self.assertGreaterEqual(similar_patterns[0]["sample_count"], 30)

            resolver_result = resolve_similar_patterns(
                latest_snapshot,
                pattern_library,
                top_k=5,
            )
            self.assertIn("matches", resolver_result)
            self.assertGreaterEqual(len(resolver_result["matches"]), 1)

            previous_similarity = 100.0
            for match in resolver_result["matches"]:
                self.assertIn("pattern_id", match)
                self.assertIn("similarity", match)
                self.assertIn("outcome", match)
                self.assertIn("pattern", match)
                self.assertGreaterEqual(match["similarity"], 0.0)
                self.assertLessEqual(match["similarity"], 100.0)
                self.assertLessEqual(match["similarity"], previous_similarity)
                self.assertIsInstance(match["pattern"], dict)
                self.assertIn(match["pattern"], pattern_library)
                previous_similarity = match["similarity"]
        finally:
            conn.close()


def _initialize_in_memory_statistics_db(conn: sqlite3.Connection) -> None:
    conn.execute(CREATE_SNAPSHOTS_TABLE_SQL)
    conn.execute(CREATE_OUTCOMES_TABLE_SQL)
    conn.execute(CREATE_PATTERNS_TABLE_SQL)
    for index_sql in REQUIRED_INDEX_SQL:
        conn.execute(index_sql)


def _fake_ohlcv_rows(count: int) -> list[dict[str, object]]:
    start_date = date(2025, 1, 1)
    rows: list[dict[str, object]] = []

    for index in range(count):
        close = 100.0 + index * 0.35
        rows.append(
            {
                "date": (start_date + timedelta(days=index)).isoformat(),
                "open": close - 0.4,
                "high": close + 1.2,
                "low": close - 1.0,
                "close": close,
                "volume": 1_000_000 + index * 100,
            }
        )

    return rows


if __name__ == "__main__":
    unittest.main()
