from __future__ import annotations

import unittest

from src.statistics_engine import (
    FeatureBucketStats,
    StatisticsEngineReport,
    build_pattern_statistics_report,
)


class PatternStatisticsTest(unittest.TestCase):
    def test_filters_and_ranks_buckets_by_minimum_sample_count(self) -> None:
        report = build_pattern_statistics_report(
            _statistics_report(
                _stats("poom_ew", "positive", 50, 62.0, 4.0, -3.0),
                _stats("volume_pressure", "negative", 40, 35.0, -2.0, -8.0),
                _stats("bos_choch", "bos_up", 10, 70.0, 6.0, -4.0),
                _stats("poom_squeeze", "none", 30, 72.0, 0.5, -2.0),
            ),
            min_sample_count=20,
        )

        self.assertEqual(report.min_sample_count, 20)
        self.assertEqual(report.total_buckets, 4)
        self.assertEqual(report.eligible_bucket_count, 3)
        self.assertEqual(report.top_by_sample_count[0].bucket, "positive")
        self.assertEqual(report.top_by_win_rate[0].bucket, "none")
        self.assertEqual(report.top_by_average_return_10d[0].bucket, "positive")
        self.assertEqual(report.top_by_expectancy[0].bucket, "positive")
        self.assertEqual(report.top_by_average_drawdown[0].bucket, "none")

    def test_generates_readable_insight_categories(self) -> None:
        report = build_pattern_statistics_report(
            _statistics_report(
                _stats("poom_ew", "positive", 50, 62.0, 4.0, -3.0),
                _stats("volume_pressure", "negative", 40, 35.0, -2.0, -8.0),
                _stats("poom_squeeze", "none", 30, 72.0, 0.5, -2.0),
                _stats("bos_choch", "bos_up", 10, 70.0, 6.0, -4.0),
            ),
            min_sample_count=20,
        )

        self.assertEqual(report.strong_historical_buckets[0].category, "Strong historical bucket")
        self.assertEqual(report.weak_historical_buckets[0].bucket, "negative")
        self.assertEqual(
            report.high_win_rate_low_expectancy_buckets[0].category,
            "High win-rate but low expectancy",
        )
        self.assertEqual(
            report.high_expectancy_low_sample_buckets[0].category,
            "High expectancy but low sample",
        )
        self.assertIn("under-sampled", report.high_expectancy_low_sample_buckets[0].interpretation)


def _statistics_report(*stats: FeatureBucketStats) -> StatisticsEngineReport:
    return StatisticsEngineReport(
        snapshot_count=100,
        outcome_count=100,
        skipped_count=0,
        feature_stats=stats,
    )


def _stats(
    feature: str,
    bucket: str,
    sample_count: int,
    win_rate: float,
    expectancy: float,
    average_drawdown: float,
) -> FeatureBucketStats:
    return FeatureBucketStats(
        feature_name=feature,
        bucket=bucket,
        sample_count=sample_count,
        win_rate=win_rate,
        average_return=expectancy,
        median_return=expectancy,
        average_max_gain=expectancy + 2.0,
        average_drawdown=average_drawdown,
        expectancy=expectancy,
    )


if __name__ == "__main__":
    unittest.main()
