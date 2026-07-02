from __future__ import annotations

from dataclasses import dataclass
import unittest

from src.statistics_engine import FeatureBucketStats
from src.gui.statistics_report_view_model import build_statistics_report_view_model


class StatisticsReportViewModelTest(unittest.TestCase):
    def test_formats_summary_and_top_feature_buckets(self) -> None:
        report = _Report(
            snapshot_count=5,
            outcome_count=3,
            skipped_count=2,
            scope=_Scope(),
            feature_stats=(
                _stats("poom_ew", "positive:10_to_25", 3, 66.6667, 2.5),
                _stats("bos_choch", "bos_up", 1, 100.0, 8.0),
                _stats("poom_squeeze", "none", 2, 50.0, -1.0),
            ),
        )

        view_model = build_statistics_report_view_model(report)

        self.assertEqual(view_model["title"], "Statistics Report")
        self.assertEqual(
            view_model["summary"],
            (
                ("Total Snapshots Analyzed", "5"),
                ("Total Outcomes Calculated", "3"),
                ("Skipped Snapshots", "2"),
            ),
        )
        self.assertEqual(view_model["top_by_sample_count"][0]["feature"], "poom_ew")
        self.assertEqual(
            dict(view_model["scope_summary"])["Scope Mode"],
            "Current Symbol (AAPL)",
        )
        self.assertEqual(
            dict(view_model["scope_summary"])["Snapshot Count per Symbol"],
            "AAPL: 5",
        )
        self.assertEqual(view_model["top_by_win_rate"][0]["bucket"], "bos_up")
        self.assertEqual(view_model["top_by_expectancy"][0]["expectancy"], "8.00%")
        self.assertEqual(
            view_model["status"],
            "Read-only SnapshotPayloadV2 statistics report.",
        )

    def test_empty_report_status_is_clear(self) -> None:
        view_model = build_statistics_report_view_model(
            _Report(snapshot_count=0, outcome_count=0, skipped_count=0),
        )

        self.assertEqual(view_model["status"], "No SnapshotPayloadV2 records found.")
        self.assertEqual(view_model["top_by_sample_count"], ())


@dataclass(frozen=True)
class _Report:
    snapshot_count: int
    outcome_count: int
    skipped_count: int
    feature_stats: tuple[FeatureBucketStats, ...] = ()
    scope: object | None = None


@dataclass(frozen=True)
class _Scope:
    scope_mode: str = "current_symbol"
    symbol_count: int = 1
    symbols_analyzed: tuple[str, ...] = ("AAPL",)
    total_snapshots: int = 5
    total_outcomes: int = 3
    skipped_snapshots: int = 2
    date_range: tuple[str, str] = ("2026-01-01", "2026-02-01")
    snapshot_count_per_symbol: tuple[tuple[str, int], ...] = (("AAPL", 5),)


def _stats(
    feature: str,
    bucket: str,
    sample_count: int,
    win_rate: float,
    expectancy: float,
) -> FeatureBucketStats:
    return FeatureBucketStats(
        feature_name=feature,
        bucket=bucket,
        sample_count=sample_count,
        win_rate=win_rate,
        average_return=expectancy,
        median_return=expectancy,
        average_max_gain=expectancy + 2,
        average_drawdown=-2.0,
        expectancy=expectancy,
    )


if __name__ == "__main__":
    unittest.main()
