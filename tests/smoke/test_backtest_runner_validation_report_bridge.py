from __future__ import annotations

import unittest

from src.backtest import BacktestRunV1, ValidationReportV1, build_validation_report
from src.backtest import run_backtest_v1


class BacktestRunnerValidationReportBridgeSmokeTest(unittest.TestCase):
    def test_backtest_runner_feeds_validation_report(self) -> None:
        run = run_backtest_v1(
            [
                {
                    "trade_setup": _trade_setup(),
                    "future_rows": [_ohlcv(high=106.0, low=99.0, close=105.0)],
                },
                {
                    "trade_setup": _trade_setup(),
                    "future_rows": [_ohlcv(high=103.0, low=96.0, close=101.0)],
                },
            ]
        )
        report = build_validation_report(run)

        self.assertIsInstance(run, BacktestRunV1)
        self.assertIsInstance(report, ValidationReportV1)
        self.assertIn("Validated 2 trades", report.summary)
        self.assertEqual(report.performance_metrics["total_trades"], 2)
        self.assertEqual(report.performance_metrics["net_return_percent"], 6.0)
        self.assertEqual(report.trade_quality["evaluated_trades"], 2)


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
