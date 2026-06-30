from __future__ import annotations

import sqlite3
import unittest
from datetime import date, timedelta

from src.analysis import (
    build_exos_snapshot,
    build_prediction_summary,
    calculate_price_projection,
    calculate_probability_summary,
    calculate_risk_zone,
    calculate_target_zone,
    resolve_similar_patterns,
)
from src.statistics import (
    CREATE_OUTCOMES_TABLE_SQL,
    CREATE_PATTERNS_TABLE_SQL,
    CREATE_SNAPSHOTS_TABLE_SQL,
    REQUIRED_INDEX_SQL,
    calculate_outcomes_for_series,
    collect_snapshots_for_series,
    load_pattern_library,
    rebuild_pattern_library,
)


class PatternLibraryPredictionSummaryBridgeSmokeTest(unittest.TestCase):
    def test_pattern_library_flows_to_prediction_summary(self) -> None:
        conn = sqlite3.connect(":memory:")
        try:
            _initialize_in_memory_statistics_db(conn)
            rows = _fake_ohlcv_rows(220)

            collect_snapshots_for_series(
                conn,
                rows,
                symbol="AAPL",
                timeframe="1D",
                window_size=80,
            )
            calculate_outcomes_for_series(
                conn,
                rows,
                symbol="AAPL",
                timeframe="1D",
            )
            library_summary = rebuild_pattern_library(conn, min_samples=30)
            self.assertGreaterEqual(library_summary["inserted_patterns"], 1)

            pattern_library = load_pattern_library(conn)
            latest_snapshot = build_exos_snapshot(
                rows[-80:],
                symbol="AAPL",
                timeframe="1D",
            )
            resolver_output = resolve_similar_patterns(
                latest_snapshot,
                pattern_library,
                top_k=5,
            )
            probability = calculate_probability_summary(resolver_output)
            projection = calculate_price_projection(
                float(rows[-1]["close"]),
                resolver_output,
            )
            target_zone = calculate_target_zone(projection)
            risk_zone = calculate_risk_zone(projection)

            first_summary = build_prediction_summary(
                probability=probability,
                projection=projection,
                target_zone=target_zone,
                risk_zone=risk_zone,
            )
            second_summary = build_prediction_summary(
                probability=probability,
                projection=projection,
                target_zone=target_zone,
                risk_zone=risk_zone,
            )

            self.assertEqual(first_summary, second_summary)
            self.assertEqual(
                set(first_summary),
                {
                    "confidence",
                    "evidence_count",
                    "best_pattern_id",
                    "best_similarity",
                    "probability",
                    "projection",
                    "target_zone",
                    "risk_zone",
                },
            )
            self.assertEqual(first_summary["probability"], probability)
            self.assertEqual(first_summary["projection"], projection)
            self.assertEqual(first_summary["target_zone"], target_zone["target_zone"])
            self.assertEqual(first_summary["risk_zone"], risk_zone["risk_zone"])
            self.assertEqual(first_summary["confidence"], probability["confidence"])
            self.assertEqual(
                first_summary["evidence_count"],
                probability["evidence_count"],
            )
            self.assertEqual(
                first_summary["best_pattern_id"],
                probability["best_pattern_id"],
            )
            self.assertEqual(
                first_summary["best_similarity"],
                probability["best_similarity"],
            )
            self.assertGreaterEqual(first_summary["confidence"], 0.0)
            self.assertLessEqual(first_summary["confidence"], 100.0)
            self.assertGreaterEqual(first_summary["best_similarity"], 0.0)
            self.assertLessEqual(first_summary["best_similarity"], 100.0)
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
