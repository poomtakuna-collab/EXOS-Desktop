from __future__ import annotations

import http.client
import socket
import sqlite3
import sys
import unittest
import urllib.request
from collections.abc import Iterator
from contextlib import ExitStack, contextmanager
from unittest.mock import patch

from src.backtest import (
    BacktestInput,
    SimulationConfig,
    build_backtest_report,
    run_backtest,
)
from src.strategy import (
    EntryQuality,
    RiskRating,
    StrategyInput,
    StrategyResult,
    TradeGrade,
    analyze_strategy,
)


class StrategyBacktestPipelineIntegrationTest(unittest.TestCase):
    def test_strategy_result_flows_through_backtest_and_report(self) -> None:
        with _blocked_external_access():
            self.assertNotIn("src.ai", sys.modules)
            strategy_result = analyze_strategy(_strategy_input())
            _assert_valid_strategy_result(self, strategy_result)

            result = run_backtest(
                [
                    _backtest_input(strategy_result, _winning_future_rows()),
                    _backtest_input(strategy_result, _breakeven_future_rows()),
                    _backtest_input(strategy_result, []),
                ],
                SimulationConfig(horizon_days=2),
            )
            report = build_backtest_report(result)

        self.assertNotIn("src.ai", sys.modules)
        self.assertEqual(result.attempted_trades, 3)
        self.assertEqual(result.completed_trades, 2)
        self.assertEqual(result.total_trades, 2)
        self.assertEqual(result.skipped_trades, 1)
        self.assertEqual(result.breakeven_trades, 1)
        self.assertEqual(result.winning_trades, 1)
        self.assertEqual(result.losing_trades, 0)

        self.assertEqual(report.attempted_trades, 3)
        self.assertEqual(report.completed_trades, 2)
        self.assertEqual(report.total_trades, 2)
        self.assertEqual(report.skipped_trades, 1)
        self.assertEqual(report.breakeven_trades, 1)

        output_text = str(
            {
                "strategy_result": strategy_result,
                "backtest_result": result,
                "report": report,
            }
        ).lower()
        for recommendation in ("buy", "sell", "hold"):
            self.assertNotIn(recommendation, output_text)


@contextmanager
def _blocked_external_access() -> Iterator[None]:
    with ExitStack() as stack:
        stack.enter_context(
            patch.object(
                sqlite3,
                "connect",
                side_effect=AssertionError("integration test must not access a database"),
            )
        )
        stack.enter_context(
            patch.object(
                socket,
                "create_connection",
                side_effect=AssertionError("integration test must not access the network"),
            )
        )
        stack.enter_context(
            patch.object(
                urllib.request,
                "urlopen",
                side_effect=AssertionError("integration test must not access live data"),
            )
        )
        stack.enter_context(
            patch.object(
                http.client.HTTPConnection,
                "connect",
                side_effect=AssertionError("integration test must not access HTTP"),
            )
        )
        yield


def _strategy_input() -> StrategyInput:
    return StrategyInput(
        snapshot={
            "snapshot_id": "snapshot-integration-1",
            "symbol": "FAKE",
            "timeframe": "1D",
            "date": "2026-01-01",
            "close": 100.0,
        },
        probability={
            "expected_return_5d": 2.0,
            "expected_return_10d": 5.0,
            "expected_return_20d": 6.0,
            "probability_up_5pct_10d": 60.0,
            "probability_up_10pct_10d": 30.0,
            "probability_down_5pct_10d": 10.0,
            "expected_max_gain_10d": 7.0,
            "expected_drawdown_10d": -3.0,
            "confidence": 75.0,
            "evidence_count": 80,
            "best_pattern_id": "fake-pattern-1",
            "best_similarity": 82.0,
        },
        prediction={
            "expected_price_5d": 102.0,
            "expected_price_10d": 105.0,
            "expected_price_20d": 106.0,
            "target_zone_low": 105.0,
            "target_zone_high": 108.0,
            "risk_zone_low": 95.0,
            "risk_zone_high": 98.0,
            "expected_return": 5.0,
            "confidence": 75.0,
            "time_horizon": "10D",
            "best_pattern_id": "fake-pattern-1",
            "best_similarity": 82.0,
        },
    )


def _assert_valid_strategy_result(
    test_case: unittest.TestCase,
    result: StrategyResult,
) -> None:
    test_case.assertIsInstance(result, StrategyResult)
    test_case.assertEqual(
        set(result.__dict__),
        {
            "strategy_score",
            "trade_grade",
            "entry_quality",
            "risk_rating",
            "reward_risk_estimate",
            "notes",
        },
    )
    test_case.assertIn(result.trade_grade, set(TradeGrade))
    test_case.assertIn(result.entry_quality, set(EntryQuality))
    test_case.assertIn(result.risk_rating, set(RiskRating))


def _backtest_input(
    strategy_result: StrategyResult,
    future_rows: list[dict[str, object]],
) -> BacktestInput:
    return BacktestInput(
        snapshot={
            "snapshot_id": "snapshot-integration-1",
            "symbol": "FAKE",
            "timeframe": "1D",
            "date": "2026-01-01",
            "close": 100.0,
        },
        probability={},
        prediction={},
        strategy_result=strategy_result,
        outcome={},
        future_rows=future_rows,
    )


def _winning_future_rows() -> list[dict[str, object]]:
    return [
        _ohlcv(high=104.0, low=99.0, close=103.0),
        _ohlcv(high=105.0, low=100.0, close=105.0),
    ]


def _breakeven_future_rows() -> list[dict[str, object]]:
    return [
        _ohlcv(high=104.0, low=99.0, close=101.0),
        _ohlcv(high=104.0, low=99.0, close=100.0),
    ]


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
