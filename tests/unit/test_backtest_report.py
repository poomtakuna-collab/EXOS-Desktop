from __future__ import annotations

import unittest

from src.backtest import BacktestReport, BacktestResult, build_backtest_report


class BacktestReportTest(unittest.TestCase):
    def test_empty_backtest_result(self) -> None:
        report = build_backtest_report(_backtest_result(total_trades=0))

        _assert_valid_backtest_report(self, report)
        self.assertEqual(report.summary, "No completed backtest trades available.")
        self.assertIn("unavailable", report.risk_comment)
        self.assertIn("unavailable", report.quality_comment)

    def test_strong_positive_result(self) -> None:
        report = build_backtest_report(
            _backtest_result(
                total_trades=10,
                winning_trades=7,
                losing_trades=3,
                win_rate=70.0,
                average_return=3.5,
                expectancy=2.0,
                max_drawdown=-4.0,
            )
        )

        _assert_valid_backtest_report(self, report)
        self.assertIn("10 completed trades", report.summary)
        self.assertIn("strong", report.quality_comment)
        self.assertIn("limited", report.risk_comment)

    def test_weak_negative_result(self) -> None:
        report = build_backtest_report(
            _backtest_result(
                total_trades=8,
                winning_trades=2,
                losing_trades=6,
                win_rate=25.0,
                average_return=-2.5,
                expectancy=-1.5,
                max_drawdown=-18.0,
            )
        )

        _assert_valid_backtest_report(self, report)
        self.assertIn("weak", report.quality_comment)
        self.assertIn("High drawdown", report.risk_comment)

    def test_skipped_or_insufficient_data_notes_are_preserved(self) -> None:
        report = build_backtest_report(
            _backtest_result(
                total_trades=1,
                notes=["Skipped / insufficient-data simulations: 2"],
            )
        )

        _assert_valid_backtest_report(self, report)
        self.assertIn("Skipped / insufficient-data simulations: 2", report.notes)

    def test_deterministic_report_output(self) -> None:
        backtest_result = _backtest_result(
            total_trades=3,
            winning_trades=2,
            losing_trades=1,
            win_rate=66.6667,
            average_return=2.3333,
            expectancy=2.3333,
            max_drawdown=-3.0,
        )

        first_report = build_backtest_report(backtest_result)
        second_report = build_backtest_report(backtest_result)

        self.assertEqual(first_report, second_report)

    def test_stable_backtest_report_shape(self) -> None:
        report = build_backtest_report(_backtest_result(total_trades=1))

        self.assertEqual(
            set(report.__dict__),
            {
                "summary",
                "total_trades",
                "win_rate",
                "average_return",
                "expectancy",
                "max_drawdown",
                "risk_comment",
                "quality_comment",
                "notes",
            },
        )
        _assert_valid_backtest_report(self, report)


def _assert_valid_backtest_report(
    test_case: unittest.TestCase,
    report: BacktestReport,
) -> None:
    test_case.assertIsInstance(report, BacktestReport)
    test_case.assertIsInstance(report.summary, str)
    test_case.assertGreaterEqual(report.total_trades, 0)
    test_case.assertGreaterEqual(report.win_rate, 0.0)
    test_case.assertLessEqual(report.win_rate, 100.0)
    test_case.assertIsInstance(report.risk_comment, str)
    test_case.assertIsInstance(report.quality_comment, str)
    test_case.assertIsInstance(report.notes, list)


def _backtest_result(
    total_trades: int,
    winning_trades: int = 0,
    losing_trades: int = 0,
    win_rate: float = 0.0,
    average_return: float = 0.0,
    average_drawdown: float = 0.0,
    expectancy: float = 0.0,
    max_drawdown: float = 0.0,
    notes: list[str] | None = None,
) -> BacktestResult:
    return BacktestResult(
        total_trades=total_trades,
        winning_trades=winning_trades,
        losing_trades=losing_trades,
        win_rate=win_rate,
        average_return=average_return,
        average_drawdown=average_drawdown,
        expectancy=expectancy,
        max_drawdown=max_drawdown,
        notes=notes or [],
    )


if __name__ == "__main__":
    unittest.main()
