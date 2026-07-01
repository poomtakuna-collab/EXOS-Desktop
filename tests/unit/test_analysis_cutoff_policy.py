from __future__ import annotations

from datetime import date
import json
import unittest

from src.data_source.analysis_cutoff import (
    determine_analysis_cutoff_date,
    rows_through_analysis_cutoff,
)


class AnalysisCutoffPolicyTest(unittest.TestCase):
    def test_same_day_latest_row_uses_previous_completed_trading_day(self) -> None:
        result = determine_analysis_cutoff_date(
            [
                {"date": "2026-06-30", "close": 100.0},
                {"date": "2026-07-01", "close": 101.0},
            ],
            as_of_date=date(2026, 7, 1),
        )

        self.assertEqual(result.chart_latest_date, "2026-07-01")
        self.assertEqual(result.analysis_cutoff_date, "2026-06-30")
        self.assertEqual(
            result.to_dict(),
            {
                "chart_latest_date": "2026-07-01",
                "analysis_cutoff_date": "2026-06-30",
            },
        )
        json.dumps(result.to_dict(), sort_keys=True)

    def test_same_day_monday_latest_row_uses_previous_friday(self) -> None:
        result = determine_analysis_cutoff_date(
            [
                {"date": "2026-07-02", "close": 100.0},
                {"date": "2026-07-06", "close": 101.0},
            ],
            as_of_date="2026-07-06",
        )

        self.assertEqual(result.chart_latest_date, "2026-07-06")
        self.assertEqual(result.analysis_cutoff_date, "2026-07-03")

    def test_stale_latest_row_uses_latest_available_completed_row(self) -> None:
        result = determine_analysis_cutoff_date(
            [
                {"date": "2026-06-26", "close": 100.0},
                {"date": "2026-06-29", "close": 101.0},
            ],
            as_of_date="2026-07-01",
        )

        self.assertEqual(result.chart_latest_date, "2026-06-29")
        self.assertEqual(result.analysis_cutoff_date, "2026-06-29")

    def test_cutoff_selection_is_deterministic_for_unsorted_rows(self) -> None:
        rows = [
            {"date": "2026-06-29", "close": 101.0},
            {"date": "not-a-date", "close": 99.0},
            {"date": "2026-07-01", "close": 103.0},
            {"date": "2026-06-30", "close": 102.0},
        ]

        first = determine_analysis_cutoff_date(rows, as_of_date="2026-07-01")
        second = determine_analysis_cutoff_date(tuple(reversed(rows)), as_of_date="2026-07-01")

        self.assertEqual(first, second)
        self.assertEqual(first.chart_latest_date, "2026-07-01")
        self.assertEqual(first.analysis_cutoff_date, "2026-06-30")

    def test_rows_through_analysis_cutoff_preserves_source_order(self) -> None:
        rows = [
            {"date": "2026-06-29", "close": 101.0},
            {"date": "2026-06-30", "close": 102.0},
            {"date": "2026-07-01", "close": 103.0},
        ]

        filtered = rows_through_analysis_cutoff(rows, "2026-06-30")

        self.assertEqual([row["date"] for row in filtered], ["2026-06-29", "2026-06-30"])


if __name__ == "__main__":
    unittest.main()
