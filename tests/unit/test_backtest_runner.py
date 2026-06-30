from __future__ import annotations

import unittest

from src.backtest import BacktestRunV1, TradeOutcomeV1, run_backtest_v1


class BacktestRunnerV1Test(unittest.TestCase):
    def test_empty_input_returns_safe_summary(self) -> None:
        run = run_backtest_v1(None)

        _assert_valid_run(self, run)
        self.assertEqual(run.trades, [])
        self.assertEqual(run.result.total_trades, 0)
        self.assertEqual(run.result.net_return_percent, 0.0)

    def test_runs_multiple_trade_setups(self) -> None:
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
                {
                    "trade_setup": _trade_setup(),
                    "future_rows": [_ohlcv(high=104.0, low=96.0, close=101.0)],
                },
            ]
        )

        _assert_valid_run(self, run)
        self.assertEqual(len(run.trades), 3)
        self.assertEqual(
            [trade.outcome_label for trade in run.trades],
            ["Win", "Loss", "Win"],
        )
        self.assertEqual(run.result.total_trades, 3)
        self.assertEqual(run.result.winning_trades, 2)
        self.assertEqual(run.result.losing_trades, 1)
        self.assertEqual(run.result.net_return_percent, 1.0)

    def test_supports_flat_trade_setup_rows(self) -> None:
        row = _trade_setup()
        row["future_rows"] = [_ohlcv(high=104.0, low=96.0, close=102.0)]

        run = run_backtest_v1([row])

        _assert_valid_run(self, run)
        self.assertEqual(run.trades[0].exit_price, 102.0)
        self.assertEqual(run.result.net_return_percent, 2.0)

    def test_malformed_rows_are_safe_invalid_trades(self) -> None:
        run = run_backtest_v1(
            [
                None,
                {"trade_setup": "bad", "future_rows": "also-bad"},
                {"setup": {"entry_price": "bad"}, "future_rows": []},
            ]
        )

        _assert_valid_run(self, run)
        self.assertEqual(len(run.trades), 3)
        self.assertTrue(
            all(trade.outcome_label == "Invalid" for trade in run.trades)
        )
        self.assertEqual(run.result.total_trades, 3)
        self.assertEqual(run.result.net_return_percent, 0.0)

    def test_malformed_container_is_safe(self) -> None:
        run = run_backtest_v1(123)  # type: ignore[arg-type]

        _assert_valid_run(self, run)
        self.assertEqual(run.trades, [])
        self.assertEqual(run.result.total_trades, 0)

    def test_deterministic_run(self) -> None:
        rows = [
            {
                "trade_setup": _trade_setup(),
                "future_rows": [_ohlcv(high=106.0, low=99.0, close=105.0)],
            }
        ]

        first_run = run_backtest_v1(rows)
        second_run = run_backtest_v1(rows)

        self.assertEqual(first_run, second_run)

    def test_stable_run_shape(self) -> None:
        run = run_backtest_v1([])

        self.assertEqual(set(run.__dict__), {"trades", "result"})


def _assert_valid_run(
    test_case: unittest.TestCase,
    run: BacktestRunV1,
) -> None:
    test_case.assertIsInstance(run, BacktestRunV1)
    test_case.assertIsInstance(run.trades, list)
    test_case.assertTrue(
        all(isinstance(trade, TradeOutcomeV1) for trade in run.trades)
    )
    test_case.assertEqual(run.result.total_trades, len(run.trades))


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
