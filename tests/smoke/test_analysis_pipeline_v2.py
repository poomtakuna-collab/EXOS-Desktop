from __future__ import annotations

import sqlite3
import unittest

from src.backtest import (
    BACKTEST_PERSISTENCE_SCHEMA_SQL,
    read_backtest_run_record,
    read_backtest_trade_result_records_by_run_id,
)
from src.analysis_pipeline import (
    AnalysisPipelineV2Request,
    AnalysisRequest,
    CanonicalAnalysisResultV2,
    analyze_symbol,
    analyze_symbol_v2,
)


class AnalysisPipelineV2SmokeTest(unittest.TestCase):
    def test_provided_rows_path_is_canonical_and_additive(self) -> None:
        legacy_request = AnalysisRequest(
            symbol="AAPL",
            ohlcv_rows=_ohlcv_rows(),
            similar_patterns=_legacy_similar_patterns(),
        )
        v2_request = AnalysisPipelineV2Request(
            symbol="AAPL",
            ohlcv_rows=_ohlcv_rows(),
            future_rows=_future_rows(),
            similar_patterns=_canonical_pattern_library(),
        )

        legacy_before = analyze_symbol(legacy_request)
        v2_result = analyze_symbol_v2(v2_request)
        legacy_after = analyze_symbol(legacy_request)

        self.assertEqual(legacy_before, legacy_after)
        self.assertIsInstance(v2_result, CanonicalAnalysisResultV2)
        self.assertEqual(v2_result.metadata["entry_point"], "analyze_symbol_v2")
        self.assertEqual(
            v2_result.canonical_brain.metadata["adapter"],
            "canonical_brain_adapter_v1",
        )
        self.assertIsNotNone(v2_result.strategy)
        self.assertIsNotNone(v2_result.backtest)
        self.assertIsNotNone(v2_result.validation_report)
        self.assertIsNone(v2_result.persistence)

    def test_opt_in_persistence_path_uses_backtest_persistence_v1(self) -> None:
        with _connection() as connection:
            request = AnalysisPipelineV2Request(
                symbol="AAPL",
                ohlcv_rows=_ohlcv_rows(),
                future_rows=_future_rows(),
                similar_patterns=_canonical_pattern_library(),
                persist_results=True,
                persistence_connection=connection,
                run_id="analysis-v2-smoke-run",
                run_name="Analysis Pipeline v2 Smoke Run",
            )

            result = analyze_symbol_v2(request)
            run_record = read_backtest_run_record(connection, "analysis-v2-smoke-run")
            trade_records = read_backtest_trade_result_records_by_run_id(
                connection,
                "analysis-v2-smoke-run",
            )

            self.assertIsNotNone(result.backtest_run)
            self.assertIsNotNone(result.validation_report)
            self.assertIsNotNone(result.persistence)
            self.assertEqual(result.persistence.run_records_written, 1)
            self.assertEqual(result.persistence.evaluation_records_written, 1)
            self.assertEqual(result.persistence.trade_result_records_written, 1)
            self.assertIsNotNone(run_record)
            self.assertEqual(run_record.run_name, "Analysis Pipeline v2 Smoke Run")
            self.assertEqual(run_record.symbols_json, '["AAPL"]')
            self.assertEqual(len(trade_records), 1)


def _ohlcv_rows(count: int = 240) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for index in range(count):
        close = 100.0 + index * 0.25
        rows.append(
            {
                "date": f"2026-04-{index % 28 + 1:02d}",
                "open": close - 0.25,
                "high": close + 1.0,
                "low": close - 1.0,
                "close": close,
                "volume": 1_000_000 + index,
            }
        )
    return rows


def _future_rows(count: int = 10) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for index in range(count):
        close = 160.0 + index
        rows.append(
            {
                "date": f"2026-05-{index + 1:02d}",
                "open": close - 0.5,
                "high": close + 8.0,
                "low": close - 1.0,
                "close": close,
                "volume": 1_100_000 + index,
            }
        )
    return rows


def _legacy_similar_patterns() -> list[dict[str, object]]:
    return [
        {
            "pattern_id": 101,
            "similarity_score": 92.0,
            "confidence": 80.0,
            "sample_count": 30,
            "average_5d_return": 2.0,
            "average_10d_return": 4.0,
            "average_20d_return": 6.0,
            "hit_5pct_rate": 55.0,
            "hit_10pct_rate": 25.0,
            "average_max_gain": 8.0,
            "average_drawdown": -3.0,
        }
    ]


def _canonical_pattern_library() -> list[dict[str, object]]:
    return [
        {
            "pattern_id": "positive-pattern",
            "trend": "bullish",
            "trend_slope": 95.0,
            "squeeze": "NONE",
            "market_structure": "BULLISH",
            "dominant_label": "Bull",
            "sample_count": 5,
            "average_5d_return": 2.0,
            "average_10d_return": 4.0,
            "average_20d_return": 6.0,
            "average_max_gain": 7.0,
            "average_drawdown": -2.0,
        }
    ]


def _connection() -> sqlite3.Connection:
    connection = sqlite3.connect(":memory:")
    connection.execute("PRAGMA foreign_keys = ON")
    for statement in BACKTEST_PERSISTENCE_SCHEMA_SQL:
        connection.execute(statement)
    connection.commit()
    return connection


if __name__ == "__main__":
    unittest.main()
