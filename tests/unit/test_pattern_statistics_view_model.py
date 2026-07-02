from __future__ import annotations

from dataclasses import dataclass
import unittest

from src.statistics_engine import PatternBucketInsight
from src.gui.pattern_statistics_view_model import build_pattern_statistics_view_model


class PatternStatisticsViewModelTest(unittest.TestCase):
    def test_formats_rankings_and_insights_for_ui(self) -> None:
        insight = PatternBucketInsight(
            category="Strong historical bucket",
            feature_name="poom_ew",
            bucket="positive:10_to_25",
            sample_count=25,
            win_rate=64.0,
            average_return_10d=3.5,
            expectancy=2.75,
            average_drawdown=-4.0,
            interpretation="Historically favorable bucket.",
        )
        report = _Report(
            min_sample_count=20,
            total_buckets=3,
            eligible_bucket_count=1,
            scope=_Scope(),
            top_by_sample_count=(insight,),
            top_by_win_rate=(insight,),
            top_by_average_return_10d=(insight,),
            top_by_expectancy=(insight,),
            top_by_average_drawdown=(insight,),
            strong_historical_buckets=(insight,),
        )

        view_model = build_pattern_statistics_view_model(report)

        self.assertEqual(view_model["title"], "Pattern Statistics")
        self.assertEqual(
            view_model["summary"],
            (
                ("Minimum Sample Count", "20"),
                ("Total Buckets", "3"),
                ("Eligible Buckets", "1"),
            ),
        )
        self.assertEqual(view_model["rankings"][0][0], "Top by Sample Count")
        self.assertEqual(
            dict(view_model["scope_summary"])["Scope Mode"],
            "All Symbols",
        )
        self.assertEqual(
            dict(view_model["scope_summary"])["Symbols Analyzed"],
            "AAPL, MSFT",
        )
        row = view_model["rankings"][0][1][0]
        self.assertEqual(row["bucket_name"], "poom_ew: positive:10_to_25")
        self.assertEqual(row["sample_count"], "25")
        self.assertEqual(row["win_rate"], "64.00%")
        self.assertEqual(row["average_return_10d"], "3.50%")
        self.assertEqual(row["expectancy"], "2.75%")
        self.assertEqual(row["average_drawdown"], "-4.00%")
        self.assertEqual(row["interpretation"], "Historically favorable bucket.")
        self.assertEqual(view_model["insights"][0][0], "Strong Historical Buckets")

    def test_empty_pattern_report_status_is_clear(self) -> None:
        view_model = build_pattern_statistics_view_model(
            _Report(min_sample_count=20, total_buckets=0, eligible_bucket_count=0),
        )

        self.assertEqual(view_model["status"], "No feature bucket statistics available.")


@dataclass(frozen=True)
class _Report:
    min_sample_count: int
    total_buckets: int
    eligible_bucket_count: int
    top_by_sample_count: tuple[PatternBucketInsight, ...] = ()
    top_by_win_rate: tuple[PatternBucketInsight, ...] = ()
    top_by_average_return_10d: tuple[PatternBucketInsight, ...] = ()
    top_by_expectancy: tuple[PatternBucketInsight, ...] = ()
    top_by_average_drawdown: tuple[PatternBucketInsight, ...] = ()
    strong_historical_buckets: tuple[PatternBucketInsight, ...] = ()
    weak_historical_buckets: tuple[PatternBucketInsight, ...] = ()
    high_win_rate_low_expectancy_buckets: tuple[PatternBucketInsight, ...] = ()
    high_expectancy_low_sample_buckets: tuple[PatternBucketInsight, ...] = ()
    scope: object | None = None


@dataclass(frozen=True)
class _Scope:
    scope_mode: str = "all_symbols"
    symbol_count: int = 2
    symbols_analyzed: tuple[str, ...] = ("AAPL", "MSFT")
    total_snapshots: int = 8
    total_outcomes: int = 6
    skipped_snapshots: int = 2
    date_range: tuple[str, str] = ("2026-01-01", "2026-03-01")
    snapshot_count_per_symbol: tuple[tuple[str, int], ...] = (("AAPL", 5), ("MSFT", 3))


if __name__ == "__main__":
    unittest.main()
