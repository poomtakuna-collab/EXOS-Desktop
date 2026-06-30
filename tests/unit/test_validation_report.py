from __future__ import annotations

import unittest

from src.backtest import (
    BacktestRunV1,
    ValidationReportV1,
    build_validation_report,
    run_backtest_v1,
)


class ValidationReportV1Test(unittest.TestCase):
    def test_empty_input_returns_safe_report(self) -> None:
        report = build_validation_report(None)

        _assert_valid_report(self, report)
        self.assertEqual(report.summary, "No completed trades available for validation.")
        self.assertEqual(report.performance_metrics["total_trades"], 0)
        self.assertEqual(report.performance_metrics["net_return_percent"], 0.0)
        self.assertEqual(report.risk_metrics["max_drawdown"], 0.0)
        self.assertEqual(report.trade_quality["evaluated_trades"], 0)
        self.assertIn("No valid BacktestRunV1 supplied.", report.notes)

    def test_preserves_backtest_result_fields_in_performance_metrics(self) -> None:
        run = run_backtest_v1(
            [
                {
                    "trade_setup": _trade_setup(),
                    "future_rows": [_ohlcv(high=106.0, low=99.0, close=105.0)],
                },
                {
                    "trade_setup": _trade_setup(),
                    "future_rows": [_ohlcv(high=102.0, low=94.0, close=95.0)],
                },
            ]
        )

        report = build_validation_report(run)

        _assert_valid_report(self, report)
        self.assertEqual(
            report.performance_metrics,
            {
                "total_trades": run.result.total_trades,
                "winning_trades": run.result.winning_trades,
                "losing_trades": run.result.losing_trades,
                "win_rate": run.result.win_rate,
                "net_return_percent": run.result.net_return_percent,
                "average_return": run.result.average_return,
                "max_drawdown": run.result.max_drawdown,
                "profit_factor": run.result.profit_factor,
                "expectancy": run.result.expectancy,
            },
        )

    def test_risk_metrics_are_derived_from_trade_outcomes(self) -> None:
        run = run_backtest_v1(
            [
                {
                    "trade_setup": _trade_setup(),
                    "future_rows": [_ohlcv(high=106.0, low=99.0, close=105.0)],
                },
                {
                    "trade_setup": _trade_setup(),
                    "future_rows": [_ohlcv(high=102.0, low=94.0, close=95.0)],
                },
            ]
        )

        report = build_validation_report(run)

        _assert_valid_report(self, report)
        self.assertEqual(report.risk_metrics["total_risk_amount"], 100.0)
        self.assertEqual(report.risk_metrics["average_risk_amount"], 50.0)
        self.assertEqual(report.risk_metrics["total_reward_amount"], 100.0)
        self.assertEqual(report.risk_metrics["average_reward_amount"], 50.0)

    def test_trade_quality_counts_invalid_and_breakeven_trades(self) -> None:
        run = run_backtest_v1(
            [
                None,
                {
                    "trade_setup": _trade_setup(),
                    "future_rows": [_ohlcv(high=104.0, low=96.0, close=100.0)],
                },
            ]
        )

        report = build_validation_report(run)

        _assert_valid_report(self, report)
        self.assertEqual(report.trade_quality["evaluated_trades"], 2)
        self.assertEqual(report.trade_quality["valid_trades"], 1)
        self.assertEqual(report.trade_quality["invalid_trades"], 1)
        self.assertEqual(report.trade_quality["breakeven_trades"], 1)

    def test_malformed_run_fields_are_ignored_safely(self) -> None:
        malformed_run = BacktestRunV1(  # type: ignore[arg-type]
            trades=["bad"],
            result="bad",
        )

        report = build_validation_report(malformed_run)

        _assert_valid_report(self, report)
        self.assertEqual(report.performance_metrics["total_trades"], 0)
        self.assertEqual(report.trade_quality["evaluated_trades"], 0)

    def test_deterministic_report(self) -> None:
        run = run_backtest_v1(
            [
                {
                    "trade_setup": _trade_setup(),
                    "future_rows": [_ohlcv(high=106.0, low=99.0, close=105.0)],
                }
            ]
        )

        first_report = build_validation_report(run)
        second_report = build_validation_report(run)

        self.assertEqual(first_report, second_report)

    def test_stable_report_shape(self) -> None:
        report = build_validation_report(run_backtest_v1([]))

        self.assertEqual(
            set(report.__dict__),
            {
                "summary",
                "performance_metrics",
                "risk_metrics",
                "trade_quality",
                "notes",
            },
        )


def _assert_valid_report(
    test_case: unittest.TestCase,
    report: ValidationReportV1,
) -> None:
    test_case.assertIsInstance(report, ValidationReportV1)
    test_case.assertIsInstance(report.summary, str)
    test_case.assertIsInstance(report.performance_metrics, dict)
    test_case.assertIsInstance(report.risk_metrics, dict)
    test_case.assertIsInstance(report.trade_quality, dict)
    test_case.assertIsInstance(report.notes, list)
    test_case.assertEqual(
        set(report.performance_metrics),
        {
            "total_trades",
            "winning_trades",
            "losing_trades",
            "win_rate",
            "net_return_percent",
            "average_return",
            "max_drawdown",
            "profit_factor",
            "expectancy",
        },
    )


def _trade_setup() -> dict[str, object]:
    return {
        "entry_price": 100.0,
        "stop_price": 95.0,
        "target_price": 105.0,
        "position_size": 10.0,
    }


def _ohlcv(high: float, low: float, close: float) -> dict[str, object]:
    return {
        "open": 100.0,
        "high": high,
        "low": low,
        "close": close,
        "volume": 1_000_000,
    }


if __name__ == "__main__":
    unittest.main()
