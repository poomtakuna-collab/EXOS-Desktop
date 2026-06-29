from dataclasses import FrozenInstanceError, is_dataclass
import sys
import unittest

from src.analysis_pipeline import (
    AnalysisRequest,
    AnalysisReport,
    AnalysisResult,
    PipelineConfig,
    analyze_symbol,
    build_analysis_report,
)


def _fake_ohlcv_rows(count: int = 240) -> list[dict[str, object]]:
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


def _fake_similar_patterns() -> list[dict[str, object]]:
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
        },
        {
            "pattern_id": 202,
            "similarity_score": 84.0,
            "confidence": 70.0,
            "sample_count": 20,
            "average_5d_return": 1.0,
            "average_10d_return": 2.0,
            "average_20d_return": 3.0,
            "hit_5pct_rate": 45.0,
            "hit_10pct_rate": 15.0,
            "average_max_gain": 5.0,
            "average_drawdown": -2.0,
        },
    ]


def _fake_future_rows(count: int = 10) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for index in range(count):
        close = 160.0 + index * 1.0
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


def _flatten_values(value: object) -> list[str]:
    if isinstance(value, dict):
        flattened: list[str] = []
        for item in value.values():
            flattened.extend(_flatten_values(item))
        return flattened
    if isinstance(value, list):
        flattened = []
        for item in value:
            flattened.extend(_flatten_values(item))
        return flattened
    return [str(value)]


class AnalysisPipelineContractsTest(unittest.TestCase):
    def test_public_imports(self) -> None:
        self.assertIsNotNone(AnalysisRequest)
        self.assertIsNotNone(AnalysisReport)
        self.assertIsNotNone(AnalysisResult)
        self.assertIsNotNone(PipelineConfig)
        self.assertTrue(callable(analyze_symbol))
        self.assertTrue(callable(build_analysis_report))

    def test_contract_shapes_are_immutable_dataclasses(self) -> None:
        self.assertTrue(is_dataclass(PipelineConfig))
        self.assertTrue(is_dataclass(AnalysisRequest))
        self.assertTrue(is_dataclass(AnalysisResult))

        config = PipelineConfig()
        request = AnalysisRequest(symbol="AAPL")
        result = AnalysisResult(
            request=request,
            config=config,
            symbol="AAPL",
            timeframe="1D",
            snapshot={},
        )

        with self.assertRaises(FrozenInstanceError):
            config.timeframe = "1W"
        with self.assertRaises(FrozenInstanceError):
            request.symbol = "MSFT"
        with self.assertRaises(FrozenInstanceError):
            result.symbol = "MSFT"

    def test_default_pipeline_config(self) -> None:
        config = PipelineConfig()

        self.assertEqual(config.timeframe, "1D")
        self.assertTrue(config.include_probability)
        self.assertTrue(config.include_prediction)
        self.assertTrue(config.include_strategy)
        self.assertTrue(config.include_backtest)

    def test_analysis_request_default_config(self) -> None:
        request = AnalysisRequest(symbol="AAPL")

        self.assertEqual(request.symbol, "AAPL")
        self.assertEqual(request.config, PipelineConfig())
        self.assertEqual(request.ohlcv_rows, [])
        self.assertEqual(request.future_rows, [])
        self.assertEqual(request.similar_patterns, [])

    def test_analysis_result_defaults(self) -> None:
        request = AnalysisRequest(symbol="AAPL")
        result = AnalysisResult(
            request=request,
            config=request.config,
            symbol="AAPL",
            timeframe="1D",
            snapshot={},
        )

        self.assertEqual(result.request, request)
        self.assertEqual(result.config, request.config)
        self.assertEqual(result.probability, {})
        self.assertEqual(result.prediction, {})
        self.assertIsNone(result.strategy)
        self.assertIsNone(result.backtest)
        self.assertEqual(result.metadata, {})
        self.assertEqual(result.notes, [])

    def test_analyze_symbol_requires_rows_until_loading_is_implemented(self) -> None:
        request = AnalysisRequest(symbol="AAPL")

        with self.assertRaises(NotImplementedError):
            analyze_symbol(request)

    def test_analyze_symbol_returns_snapshot_probability_prediction_strategy_result(self) -> None:
        request = AnalysisRequest(
            symbol="AAPL",
            ohlcv_rows=_fake_ohlcv_rows(),
            similar_patterns=_fake_similar_patterns(),
        )

        result = analyze_symbol(request)

        self.assertIsInstance(result, AnalysisResult)
        self.assertEqual(result.request, request)
        self.assertEqual(result.config, request.config)
        self.assertEqual(result.symbol, "AAPL")
        self.assertEqual(result.timeframe, "1D")
        self.assertEqual(result.snapshot["metadata"]["symbol"], "AAPL")
        self.assertEqual(result.snapshot["metadata"]["timeframe"], "1D")
        self.assertEqual(result.snapshot["metadata"]["rows"], 240)
        self.assertIn("trend", result.snapshot)
        self.assertIn("score", result.snapshot)
        self.assertGreater(result.probability["confidence"], 0)
        self.assertEqual(result.probability["best_pattern_id"], 101)
        self.assertGreater(result.prediction["expected_price_10d"], 0)
        self.assertEqual(result.prediction["best_pattern_id"], 101)
        self.assertIsNotNone(result.strategy)
        self.assertGreater(result.strategy["strategy_score"], 0)
        self.assertIn("reward_risk_estimate", result.strategy)
        self.assertIsNone(result.backtest)

    def test_analyze_symbol_returns_full_backtest_flow_when_future_rows_are_supplied(self) -> None:
        request = AnalysisRequest(
            symbol="AAPL",
            ohlcv_rows=_fake_ohlcv_rows(),
            future_rows=_fake_future_rows(),
            similar_patterns=_fake_similar_patterns(),
        )

        result = analyze_symbol(request)

        self.assertNotEqual(result.snapshot, {})
        self.assertNotEqual(result.probability, {})
        self.assertNotEqual(result.prediction, {})
        self.assertIsNotNone(result.strategy)
        self.assertIsNotNone(result.backtest)
        self.assertIn("result", result.backtest)
        self.assertIn("report", result.backtest)
        self.assertEqual(result.backtest["result"]["attempted_trades"], 1)
        self.assertEqual(result.backtest["report"]["attempted_trades"], 1)

    def test_analyze_symbol_leaves_backtest_empty(self) -> None:
        request = AnalysisRequest(
            symbol="AAPL",
            ohlcv_rows=_fake_ohlcv_rows(),
            similar_patterns=_fake_similar_patterns(),
        )

        result = analyze_symbol(request)

        self.assertIsNotNone(result.strategy)
        self.assertIsNone(result.backtest)

    def test_analysis_report_from_snapshot_only_result(self) -> None:
        request = AnalysisRequest(
            symbol="AAPL",
            config=PipelineConfig(
                include_probability=False,
                include_prediction=False,
                include_strategy=False,
                include_backtest=False,
            ),
            ohlcv_rows=_fake_ohlcv_rows(),
        )
        result = analyze_symbol(request)

        report = build_analysis_report(result)

        self.assertIsInstance(report, AnalysisReport)
        self.assertEqual(report.symbol, "AAPL")
        self.assertEqual(report.timeframe, "1D")
        self.assertEqual(report.snapshot_status, "snapshot: available")
        self.assertEqual(report.probability_status, "probability: unavailable")
        self.assertEqual(report.prediction_status, "prediction: unavailable")
        self.assertEqual(report.strategy_status, "strategy: unavailable")
        self.assertEqual(report.backtest_status, "backtest: unavailable")
        self.assertEqual(report.notes, result.notes)

    def test_analysis_report_from_full_pipeline_result(self) -> None:
        request = AnalysisRequest(
            symbol="AAPL",
            ohlcv_rows=_fake_ohlcv_rows(),
            future_rows=_fake_future_rows(),
            similar_patterns=_fake_similar_patterns(),
        )
        result = analyze_symbol(request)

        report = build_analysis_report(result)

        self.assertEqual(report.snapshot_status, "snapshot: available")
        self.assertEqual(report.probability_status, "probability: available")
        self.assertEqual(report.prediction_status, "prediction: available")
        self.assertEqual(report.strategy_status, "strategy: available")
        self.assertEqual(report.backtest_status, "backtest: available (1 attempted, 1 completed)")

    def test_analysis_report_handles_missing_backtest_cleanly(self) -> None:
        request = AnalysisRequest(
            symbol="AAPL",
            ohlcv_rows=_fake_ohlcv_rows(),
            similar_patterns=_fake_similar_patterns(),
        )
        result = analyze_symbol(request)

        report = build_analysis_report(result)

        self.assertIsNone(result.backtest)
        self.assertEqual(report.backtest_status, "backtest: unavailable")

    def test_analyze_symbol_output_has_no_recommendation(self) -> None:
        request = AnalysisRequest(
            symbol="AAPL",
            ohlcv_rows=_fake_ohlcv_rows(),
            future_rows=_fake_future_rows(),
            similar_patterns=_fake_similar_patterns(),
        )

        result = analyze_symbol(request)

        output_values = {value.upper() for value in _flatten_values(result.__dict__)}
        self.assertNotIn("BUY", output_values)
        self.assertNotIn("SELL", output_values)
        self.assertNotIn("HOLD", output_values)

    def test_analysis_report_has_no_recommendation(self) -> None:
        request = AnalysisRequest(
            symbol="AAPL",
            ohlcv_rows=_fake_ohlcv_rows(),
            future_rows=_fake_future_rows(),
            similar_patterns=_fake_similar_patterns(),
        )
        result = analyze_symbol(request)

        report = build_analysis_report(result)

        output_values = {value.upper() for value in _flatten_values(report.__dict__)}
        self.assertNotIn("BUY", output_values)
        self.assertNotIn("SELL", output_values)
        self.assertNotIn("HOLD", output_values)

    def test_analyze_symbol_does_not_import_ai_network_or_broker_modules(self) -> None:
        blocked_module_roots = {
            "openai",
            "anthropic",
            "yfinance",
            "requests",
            "httpx",
            "urllib3",
            "alpaca",
            "ib_insync",
        }
        before = set(sys.modules)
        request = AnalysisRequest(
            symbol="AAPL",
            ohlcv_rows=_fake_ohlcv_rows(),
            future_rows=_fake_future_rows(),
            similar_patterns=_fake_similar_patterns(),
        )

        analyze_symbol(request)

        imported = set(sys.modules) - before
        imported_roots = {name.split(".")[0] for name in imported}
        self.assertTrue(blocked_module_roots.isdisjoint(imported_roots))

    def test_analysis_report_does_not_import_ai_network_or_broker_modules(self) -> None:
        blocked_module_roots = {
            "openai",
            "anthropic",
            "yfinance",
            "requests",
            "httpx",
            "urllib3",
            "alpaca",
            "ib_insync",
        }
        request = AnalysisRequest(
            symbol="AAPL",
            ohlcv_rows=_fake_ohlcv_rows(),
            future_rows=_fake_future_rows(),
            similar_patterns=_fake_similar_patterns(),
        )
        result = analyze_symbol(request)
        before = set(sys.modules)

        build_analysis_report(result)

        imported = set(sys.modules) - before
        imported_roots = {name.split(".")[0] for name in imported}
        self.assertTrue(blocked_module_roots.isdisjoint(imported_roots))

    def test_analyze_symbol_is_deterministic_for_fixed_inputs(self) -> None:
        request = AnalysisRequest(
            symbol="AAPL",
            ohlcv_rows=_fake_ohlcv_rows(),
            future_rows=_fake_future_rows(),
            similar_patterns=_fake_similar_patterns(),
        )

        first = analyze_symbol(request)
        second = analyze_symbol(request)

        self.assertEqual(first.snapshot, second.snapshot)
        self.assertEqual(first.probability, second.probability)
        self.assertEqual(first.prediction, second.prediction)
        self.assertEqual(first.strategy, second.strategy)
        self.assertEqual(first.backtest, second.backtest)

    def test_analysis_report_is_deterministic_for_fixed_output(self) -> None:
        request = AnalysisRequest(
            symbol="AAPL",
            ohlcv_rows=_fake_ohlcv_rows(),
            future_rows=_fake_future_rows(),
            similar_patterns=_fake_similar_patterns(),
        )
        result = analyze_symbol(request)

        first = build_analysis_report(result)
        second = build_analysis_report(result)

        self.assertEqual(first, second)

    def test_analyze_symbol_can_skip_probability_and_prediction(self) -> None:
        request = AnalysisRequest(
            symbol="AAPL",
            config=PipelineConfig(include_probability=False, include_prediction=False),
            ohlcv_rows=_fake_ohlcv_rows(),
            similar_patterns=_fake_similar_patterns(),
        )

        result = analyze_symbol(request)

        self.assertNotEqual(result.snapshot, {})
        self.assertEqual(result.probability, {})
        self.assertEqual(result.prediction, {})
        self.assertIsNone(result.strategy)
        self.assertIsNone(result.backtest)

    def test_analyze_symbol_can_skip_strategy(self) -> None:
        request = AnalysisRequest(
            symbol="AAPL",
            config=PipelineConfig(include_strategy=False),
            ohlcv_rows=_fake_ohlcv_rows(),
            similar_patterns=_fake_similar_patterns(),
        )

        result = analyze_symbol(request)

        self.assertNotEqual(result.snapshot, {})
        self.assertNotEqual(result.probability, {})
        self.assertNotEqual(result.prediction, {})
        self.assertIsNone(result.strategy)
        self.assertIsNone(result.backtest)

    def test_analyze_symbol_can_skip_backtest(self) -> None:
        request = AnalysisRequest(
            symbol="AAPL",
            config=PipelineConfig(include_backtest=False),
            ohlcv_rows=_fake_ohlcv_rows(),
            future_rows=_fake_future_rows(),
            similar_patterns=_fake_similar_patterns(),
        )

        result = analyze_symbol(request)

        self.assertNotEqual(result.snapshot, {})
        self.assertNotEqual(result.probability, {})
        self.assertNotEqual(result.prediction, {})
        self.assertIsNotNone(result.strategy)
        self.assertIsNone(result.backtest)


if __name__ == "__main__":
    unittest.main()
