from __future__ import annotations

from contextlib import closing
import sqlite3
from dataclasses import FrozenInstanceError, is_dataclass
import unittest

from src.backtest import (
    BACKTEST_PERSISTENCE_SCHEMA_SQL,
    BacktestPersistenceSummaryV1,
    read_backtest_run_record,
)
from src.analysis_pipeline import (
    AnalysisPipelineV2Request,
    CanonicalAnalysisResultV2,
    PipelineConfig,
    analyze_symbol_v2,
)
from src.data_source import MemoryDataSource


class AnalysisPipelineV2Test(unittest.TestCase):
    def test_public_contracts_are_immutable_dataclasses(self) -> None:
        self.assertTrue(is_dataclass(AnalysisPipelineV2Request))
        self.assertTrue(is_dataclass(CanonicalAnalysisResultV2))

        request = AnalysisPipelineV2Request(symbol="AAPL")

        with self.assertRaises(FrozenInstanceError):
            request.symbol = "MSFT"

    def test_provided_rows_path_uses_canonical_brain_and_strategy(self) -> None:
        request = AnalysisPipelineV2Request(
            symbol="AAPL",
            ohlcv_rows=_ohlcv_rows(),
            similar_patterns=_pattern_library(),
        )

        result = analyze_symbol_v2(request)

        self.assertIsInstance(result, CanonicalAnalysisResultV2)
        self.assertEqual(result.request, request)
        self.assertEqual(result.metadata["entry_point"], "analyze_symbol_v2")
        self.assertEqual(
            result.canonical_brain.metadata["adapter"],
            "canonical_brain_adapter_v1",
        )
        self.assertNotEqual(result.canonical_brain.snapshot, {})
        self.assertNotEqual(result.canonical_brain.prediction_summary, {})
        self.assertIsNotNone(result.strategy)
        self.assertIsNone(result.backtest)
        self.assertIsNone(result.validation_report)
        self.assertIsNone(result.persistence)
        self.assertEqual(result.metadata["rows"], len(_ohlcv_rows()))
        self.assertEqual(result.data_source_metadata["market_data"]["source"], "provided_rows")

    def test_market_data_source_is_used_when_rows_are_absent(self) -> None:
        source = MemoryDataSource(
            [
                {**row, "symbol": "AAPL", "timeframe": "1D"}
                for row in _ohlcv_rows()
            ]
        )
        request = AnalysisPipelineV2Request(
            symbol="AAPL",
            data_source=source,
            similar_patterns=_pattern_library(),
        )

        result = analyze_symbol_v2(request)

        self.assertEqual(result.metadata["rows"], len(_ohlcv_rows()))
        self.assertEqual(result.data_source_metadata["market_data"]["source"], "memory")
        self.assertIsNotNone(result.strategy)

    def test_market_data_source_with_future_rows_is_deterministic(self) -> None:
        source = MemoryDataSource(
            [
                {**row, "symbol": "AAPL", "timeframe": "1D"}
                for row in _ohlcv_rows()
            ]
            + [
                {**row, "symbol": "AAPL", "timeframe": "1D", "row_type": "future"}
                for row in _future_rows()
            ]
        )
        request = AnalysisPipelineV2Request(
            symbol="AAPL",
            data_source=source,
            similar_patterns=_pattern_library(),
        )

        first = analyze_symbol_v2(request)
        second = analyze_symbol_v2(request)

        self.assertEqual(first, second)
        self.assertEqual(first.data_source_metadata["market_data"]["source"], "memory")
        self.assertEqual(first.data_source_metadata["future_rows"]["source"], "memory")
        self.assertEqual(first.metadata["future_rows"], len(_future_rows()))
        self.assertIsNotNone(first.backtest)
        self.assertIsNotNone(first.validation_report)

    def test_backtest_and_validation_run_only_with_future_rows(self) -> None:
        request = AnalysisPipelineV2Request(
            symbol="AAPL",
            ohlcv_rows=_ohlcv_rows(),
            future_rows=_future_rows(),
            similar_patterns=_pattern_library(),
        )

        result = analyze_symbol_v2(request)

        self.assertIsNotNone(result.strategy)
        self.assertIsNotNone(result.backtest)
        self.assertIsNotNone(result.backtest_report)
        self.assertIsNotNone(result.backtest_run)
        self.assertIsNotNone(result.validation_report)
        self.assertEqual(result.metadata["backtest_available"], True)
        self.assertEqual(result.metadata["validation_available"], True)
        self.assertIsNone(result.persistence)

    def test_can_skip_strategy_and_backtest_with_config(self) -> None:
        request = AnalysisPipelineV2Request(
            symbol="AAPL",
            config=PipelineConfig(include_strategy=False, include_backtest=False),
            ohlcv_rows=_ohlcv_rows(),
            future_rows=_future_rows(),
            similar_patterns=_pattern_library(),
        )

        result = analyze_symbol_v2(request)

        self.assertNotEqual(result.canonical_brain.snapshot, {})
        self.assertIsNone(result.strategy)
        self.assertIsNone(result.backtest)
        self.assertIsNone(result.validation_report)

    def test_skips_strategy_when_prediction_is_disabled(self) -> None:
        request = AnalysisPipelineV2Request(
            symbol="AAPL",
            config=PipelineConfig(include_prediction=False),
            ohlcv_rows=_ohlcv_rows(),
            future_rows=_future_rows(),
            similar_patterns=_pattern_library(),
        )

        result = analyze_symbol_v2(request)

        self.assertEqual(result.canonical_brain.projection, {})
        self.assertEqual(result.canonical_brain.prediction_summary, {})
        self.assertIsNone(result.strategy)
        self.assertIsNone(result.backtest)
        self.assertIsNone(result.validation_report)

    def test_persistence_is_skipped_without_opt_in(self) -> None:
        request = AnalysisPipelineV2Request(
            symbol="AAPL",
            ohlcv_rows=_ohlcv_rows(),
            similar_patterns=_pattern_library(),
            persistence_connection=object(),
        )

        result = analyze_symbol_v2(request)

        self.assertIsNone(result.persistence)
        self.assertEqual(result.metadata["persistence"], "skipped")
        self.assertIn("Persistence skipped because persist_results is False.", result.notes)

    def test_persistence_is_skipped_without_sqlite_connection(self) -> None:
        request = AnalysisPipelineV2Request(
            symbol="AAPL",
            ohlcv_rows=_ohlcv_rows(),
            future_rows=_future_rows(),
            similar_patterns=_pattern_library(),
            persist_results=True,
        )

        result = analyze_symbol_v2(request)

        self.assertIsNone(result.persistence)
        self.assertIn(
            "Persistence skipped because no SQLite connection was supplied.",
            result.notes,
        )

    def test_persistence_is_skipped_without_backtest_run(self) -> None:
        with closing(_connection()) as connection:
            request = AnalysisPipelineV2Request(
                symbol="AAPL",
                ohlcv_rows=_ohlcv_rows(),
                similar_patterns=_pattern_library(),
                persist_results=True,
                persistence_connection=connection,
            )

            result = analyze_symbol_v2(request)

            self.assertIsNone(result.persistence)
            self.assertIn(
                "Persistence skipped because BacktestRunV1 is unavailable.",
                result.notes,
            )

    def test_persistence_adapter_uses_existing_backtest_persistence_v1(self) -> None:
        with closing(_connection()) as connection:
            request = AnalysisPipelineV2Request(
                symbol="AAPL",
                ohlcv_rows=_ohlcv_rows(),
                future_rows=_future_rows(),
                similar_patterns=_pattern_library(),
                persist_results=True,
                persistence_connection=connection,
                run_id="analysis-v2-unit-run",
                run_name="Analysis Pipeline v2 Unit Run",
            )

            result = analyze_symbol_v2(request)
            run_record = read_backtest_run_record(connection, "analysis-v2-unit-run")

            self.assertIsInstance(result.persistence, BacktestPersistenceSummaryV1)
            self.assertEqual(result.metadata["persistence"], "persisted")
            self.assertEqual(result.persistence.run_id, "analysis-v2-unit-run")
            self.assertEqual(result.persistence.run_records_written, 1)
            self.assertEqual(result.persistence.evaluation_records_written, 1)
            self.assertEqual(result.persistence.trade_result_records_written, 1)
            self.assertIsNotNone(run_record)
            self.assertEqual(run_record.run_name, "Analysis Pipeline v2 Unit Run")
            self.assertEqual(run_record.symbols_json, '["AAPL"]')
            self.assertEqual(run_record.timeframe, "1D")

    def test_v2_output_is_deterministic_for_fixed_inputs(self) -> None:
        request = AnalysisPipelineV2Request(
            symbol="AAPL",
            ohlcv_rows=_ohlcv_rows(),
            future_rows=_future_rows(),
            similar_patterns=_pattern_library(),
        )

        first = analyze_symbol_v2(request)
        second = analyze_symbol_v2(request)

        self.assertEqual(first, second)


def _ohlcv_rows(count: int = 240) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for index in range(count):
        close = 100.0 + index * 0.25
        rows.append(
            {
                "date": f"2026-01-{index % 28 + 1:02d}",
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
                "date": f"2026-02-{index + 1:02d}",
                "open": close - 0.5,
                "high": close + 8.0,
                "low": close - 1.0,
                "close": close,
                "volume": 1_100_000 + index,
            }
        )
    return rows


def _pattern_library() -> list[dict[str, object]]:
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
