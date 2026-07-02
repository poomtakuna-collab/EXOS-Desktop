from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Callable, Sequence

from src.statistics_engine.engine import (
    FeatureBucketStats,
    StatisticsEngineReport,
    StatisticsScopeSummary,
)


DEFAULT_MIN_SAMPLE_COUNT = 20


@dataclass(frozen=True)
class PatternBucketInsight:
    category: str
    feature_name: str
    bucket: str
    sample_count: int
    win_rate: float
    average_return_10d: float
    expectancy: float
    average_drawdown: float
    interpretation: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class PatternStatisticsReport:
    min_sample_count: int
    total_buckets: int
    eligible_bucket_count: int
    top_by_sample_count: tuple[PatternBucketInsight, ...]
    top_by_win_rate: tuple[PatternBucketInsight, ...]
    top_by_average_return_10d: tuple[PatternBucketInsight, ...]
    top_by_expectancy: tuple[PatternBucketInsight, ...]
    top_by_average_drawdown: tuple[PatternBucketInsight, ...]
    strong_historical_buckets: tuple[PatternBucketInsight, ...]
    weak_historical_buckets: tuple[PatternBucketInsight, ...]
    high_win_rate_low_expectancy_buckets: tuple[PatternBucketInsight, ...]
    high_expectancy_low_sample_buckets: tuple[PatternBucketInsight, ...]
    scope: StatisticsScopeSummary | None = None

    def to_dict(self) -> dict[str, object]:
        return {
            "min_sample_count": self.min_sample_count,
            "total_buckets": self.total_buckets,
            "eligible_bucket_count": self.eligible_bucket_count,
            "top_by_sample_count": tuple(item.to_dict() for item in self.top_by_sample_count),
            "top_by_win_rate": tuple(item.to_dict() for item in self.top_by_win_rate),
            "top_by_average_return_10d": tuple(item.to_dict() for item in self.top_by_average_return_10d),
            "top_by_expectancy": tuple(item.to_dict() for item in self.top_by_expectancy),
            "top_by_average_drawdown": tuple(item.to_dict() for item in self.top_by_average_drawdown),
            "strong_historical_buckets": tuple(item.to_dict() for item in self.strong_historical_buckets),
            "weak_historical_buckets": tuple(item.to_dict() for item in self.weak_historical_buckets),
            "high_win_rate_low_expectancy_buckets": tuple(item.to_dict() for item in self.high_win_rate_low_expectancy_buckets),
            "high_expectancy_low_sample_buckets": tuple(item.to_dict() for item in self.high_expectancy_low_sample_buckets),
            "scope": self.scope.to_dict() if self.scope is not None else None,
        }


def build_pattern_statistics_report(
    statistics_report: StatisticsEngineReport,
    *,
    min_sample_count: int = DEFAULT_MIN_SAMPLE_COUNT,
    limit: int = 10,
) -> PatternStatisticsReport:
    safe_min_sample_count = max(int(min_sample_count), 1)
    safe_limit = max(int(limit), 1)
    buckets = tuple(statistics_report.feature_stats)
    eligible = tuple(item for item in buckets if item.sample_count >= safe_min_sample_count)
    low_sample = tuple(item for item in buckets if 0 < item.sample_count < safe_min_sample_count)

    strong = tuple(
        _insight(item, "Strong historical bucket")
        for item in sorted(
            (
                item
                for item in eligible
                if item.win_rate >= 55.0
                and item.average_return > 0
                and item.expectancy > 0
            ),
            key=lambda item: (item.expectancy, item.win_rate, item.sample_count),
            reverse=True,
        )[:safe_limit]
    )
    weak = tuple(
        _insight(item, "Weak historical bucket")
        for item in sorted(
            (
                item
                for item in eligible
                if item.win_rate <= 45.0
                or item.average_return < 0
                or item.expectancy < 0
            ),
            key=lambda item: (item.expectancy, item.win_rate, item.average_return),
        )[:safe_limit]
    )
    high_win_low_expectancy = tuple(
        _insight(item, "High win-rate but low expectancy")
        for item in sorted(
            (
                item
                for item in eligible
                if item.win_rate >= 60.0 and item.expectancy <= 1.0
            ),
            key=lambda item: (item.win_rate, -abs(item.expectancy), item.sample_count),
            reverse=True,
        )[:safe_limit]
    )
    high_expectancy_low_sample = tuple(
        _insight(item, "High expectancy but low sample")
        for item in sorted(
            (
                item
                for item in low_sample
                if item.expectancy >= 3.0 and item.average_return > 0
            ),
            key=lambda item: (item.expectancy, item.sample_count),
            reverse=True,
        )[:safe_limit]
    )

    return PatternStatisticsReport(
        min_sample_count=safe_min_sample_count,
        total_buckets=len(buckets),
        eligible_bucket_count=len(eligible),
        top_by_sample_count=_rank(eligible, "Ranked by sample count", lambda item: (item.sample_count, item.expectancy), safe_limit),
        top_by_win_rate=_rank(eligible, "Ranked by win rate", lambda item: (item.win_rate, item.sample_count), safe_limit),
        top_by_average_return_10d=_rank(eligible, "Ranked by average 10d return", lambda item: (item.average_return, item.sample_count), safe_limit),
        top_by_expectancy=_rank(eligible, "Ranked by expectancy", lambda item: (item.expectancy, item.sample_count), safe_limit),
        top_by_average_drawdown=_rank(eligible, "Ranked by average drawdown", lambda item: (item.average_drawdown, item.sample_count), safe_limit),
        strong_historical_buckets=strong,
        weak_historical_buckets=weak,
        high_win_rate_low_expectancy_buckets=high_win_low_expectancy,
        high_expectancy_low_sample_buckets=high_expectancy_low_sample,
        scope=statistics_report.scope,
    )


def _rank(
    buckets: Sequence[FeatureBucketStats],
    category: str,
    key: Callable[[FeatureBucketStats], tuple[float | int, float | int]],
    limit: int,
) -> tuple[PatternBucketInsight, ...]:
    return tuple(
        _insight(item, category)
        for item in sorted(
            buckets,
            key=key,
            reverse=True,
        )[:limit]
    )


def _insight(item: FeatureBucketStats, category: str) -> PatternBucketInsight:
    return PatternBucketInsight(
        category=category,
        feature_name=item.feature_name,
        bucket=item.bucket,
        sample_count=item.sample_count,
        win_rate=item.win_rate,
        average_return_10d=item.average_return,
        expectancy=item.expectancy,
        average_drawdown=item.average_drawdown,
        interpretation=_interpretation(item, category),
    )


def _interpretation(item: FeatureBucketStats, category: str) -> str:
    if category == "Strong historical bucket":
        return "Historically favorable bucket with positive return and expectancy."
    if category == "Weak historical bucket":
        return "Historically unfavorable bucket; inspect before trusting similar setups."
    if category == "High win-rate but low expectancy":
        return "Often wins, but payoff has been modest after losses and drawdown."
    if category == "High expectancy but low sample":
        return "Promising but under-sampled; treat as provisional research evidence."
    if category == "Ranked by average drawdown":
        return "Lower drawdown profile among buckets meeting sample threshold."
    if item.expectancy > 0 and item.average_return > 0:
        return "Positive historical bucket."
    return "Ranked historical bucket for developer inspection."
