from __future__ import annotations

import json
import sqlite3
import unittest

from src.statistics_engine import (
    build_statistics_report,
    build_statistics_report_from_connection,
    calculate_forward_outcome,
    extract_feature_buckets,
)


class StatisticsEngineV1Test(unittest.TestCase):
    def test_extracts_feature_buckets_from_snapshot_payload_v2(self) -> None:
        payload = _payload(symbol="AAPL", close=100.0)

        buckets = dict(extract_feature_buckets(payload))

        self.assertEqual(buckets["poom_ew"], "positive:10_to_25")
        self.assertEqual(buckets["volume_pressure"], "negative:25_to_50")
        self.assertEqual(buckets["poom_trend_slope"], "positive:0_to_10")
        self.assertEqual(buckets["poom_squeeze"], "release_up")
        self.assertEqual(buckets["bos_choch"], "bos_up")
        self.assertEqual(buckets["ema_alignment"], "bullish")
        self.assertEqual(buckets["price_vs_ema20"], "above")
        self.assertEqual(buckets["price_vs_ema50"], "above")
        self.assertEqual(buckets["price_vs_ema200"], "below")
        self.assertEqual(buckets["trend_state"], "bullish")
        self.assertEqual(buckets["market_structure"], "higher_high")
        self.assertEqual(buckets["support_resistance_distance"], "support:2_to_5")

    def test_calculates_forward_outcomes_from_future_ohlcv(self) -> None:
        payload = _payload(symbol="AAPL", close=100.0)

        outcome = calculate_forward_outcome(
            payload,
            future_rows=_future_rows(final_5=105.0, final_10=110.0, final_20=120.0),
            snapshot_record_id="snapshot-1",
            symbol="AAPL",
            market_date="2026-01-01",
        )

        self.assertIsNotNone(outcome)
        assert outcome is not None
        self.assertEqual(outcome.forward_return_5d, 5.0)
        self.assertEqual(outcome.forward_return_10d, 10.0)
        self.assertEqual(outcome.forward_return_20d, 20.0)
        self.assertEqual(outcome.max_gain_10d, 12.0)
        self.assertEqual(outcome.max_drawdown_10d, -2.0)

    def test_aggregates_stats_by_feature_bucket(self) -> None:
        snapshots = (
            _snapshot_record("snapshot-1", "AAPL", _payload(symbol="AAPL", close=100.0)),
            _snapshot_record("snapshot-2", "MSFT", _payload(symbol="MSFT", close=100.0)),
        )
        rows = {
            "AAPL": _rows_for_snapshot(
                "2026-01-01",
                _future_rows(final_5=105.0, final_10=110.0, final_20=120.0),
            ),
            "MSFT": _rows_for_snapshot(
                "2026-01-01",
                _future_rows(final_5=99.0, final_10=95.0, final_20=90.0, high_10=103.0, low_10=90.0),
            ),
        }

        report = build_statistics_report(
            snapshots=snapshots,
            ohlcv_rows_by_symbol=rows,
        )

        self.assertEqual(report.snapshot_count, 2)
        self.assertEqual(report.outcome_count, 2)
        self.assertEqual(report.skipped_count, 0)
        stats = {
            (item.feature_name, item.bucket): item
            for item in report.feature_stats
        }
        poom_ew = stats[("poom_ew", "positive:10_to_25")]
        self.assertEqual(poom_ew.sample_count, 2)
        self.assertEqual(poom_ew.win_rate, 50.0)
        self.assertEqual(poom_ew.average_return, 2.5)
        self.assertEqual(poom_ew.median_return, 2.5)
        self.assertEqual(poom_ew.average_max_gain, 7.5)
        self.assertEqual(poom_ew.average_drawdown, -6.0)
        self.assertEqual(poom_ew.expectancy, 2.5)

    def test_current_symbol_scope_filters_snapshots_and_summarizes_symbols(self) -> None:
        snapshots = (
            _snapshot_record("snapshot-1", "AAPL", _payload(symbol="AAPL", close=100.0)),
            _snapshot_record("snapshot-2", "MSFT", _payload(symbol="MSFT", close=100.0)),
        )
        rows = {
            "AAPL": _rows_for_snapshot(
                "2026-01-01",
                _future_rows(final_5=105.0, final_10=110.0, final_20=120.0),
            ),
            "MSFT": _rows_for_snapshot(
                "2026-01-01",
                _future_rows(final_5=99.0, final_10=95.0, final_20=90.0),
            ),
        }

        report = build_statistics_report(
            snapshots=snapshots,
            ohlcv_rows_by_symbol=rows,
            scope_mode="current_symbol",
            current_symbol="AAPL",
        )

        self.assertEqual(report.snapshot_count, 1)
        self.assertEqual(report.outcome_count, 1)
        self.assertIsNotNone(report.scope)
        assert report.scope is not None
        self.assertEqual(report.scope.scope_mode, "current_symbol")
        self.assertEqual(report.scope.symbol_count, 1)
        self.assertEqual(report.scope.symbols_analyzed, ("AAPL",))
        self.assertEqual(report.scope.date_range, ("2026-01-01", "2026-01-01"))
        self.assertEqual(report.scope.snapshot_count_per_symbol, (("AAPL", 1),))

    def test_all_symbols_scope_summarizes_multiple_symbols(self) -> None:
        snapshots = (
            _snapshot_record("snapshot-1", "AAPL", _payload(symbol="AAPL", close=100.0)),
            _snapshot_record("snapshot-2", "MSFT", _payload(symbol="MSFT", close=100.0)),
        )
        rows = {
            "AAPL": _rows_for_snapshot(
                "2026-01-01",
                _future_rows(final_5=105.0, final_10=110.0, final_20=120.0),
            ),
            "MSFT": _rows_for_snapshot(
                "2026-01-01",
                _future_rows(final_5=99.0, final_10=95.0, final_20=90.0),
            ),
        }

        report = build_statistics_report(
            snapshots=snapshots,
            ohlcv_rows_by_symbol=rows,
            scope_mode="all_symbols",
            current_symbol="AAPL",
        )

        self.assertEqual(report.snapshot_count, 2)
        self.assertIsNotNone(report.scope)
        assert report.scope is not None
        self.assertEqual(report.scope.scope_mode, "all_symbols")
        self.assertEqual(report.scope.symbol_count, 2)
        self.assertEqual(report.scope.symbols_analyzed, ("AAPL", "MSFT"))
        self.assertEqual(
            report.scope.snapshot_count_per_symbol,
            (("AAPL", 1), ("MSFT", 1)),
        )

    def test_reads_snapshot_payload_v2_records_from_sqlite(self) -> None:
        connection = sqlite3.connect(":memory:")
        try:
            _create_daily_research_snapshots(connection)
            _create_ohlcv_daily(connection)
            _insert_snapshot(
                connection,
                "snapshot-1",
                "AAPL",
                "2026-01-01",
                _payload(symbol="AAPL", close=100.0),
            )
            _insert_ohlcv_rows(
                connection,
                "AAPL",
                _rows_for_snapshot(
                    "2026-01-01",
                    _future_rows(final_5=105.0, final_10=110.0, final_20=120.0),
                ),
            )

            report = build_statistics_report_from_connection(connection)
        finally:
            connection.close()

        self.assertEqual(report.snapshot_count, 1)
        self.assertEqual(report.outcome_count, 1)
        self.assertEqual(report.skipped_count, 0)
        self.assertIn(
            ("poom_squeeze", "release_up"),
            {(item.feature_name, item.bucket) for item in report.feature_stats},
        )


def _payload(*, symbol: str, close: float) -> dict[str, object]:
    return {
        "identity": {
            "payload_schema_version": "snapshot_payload_v2",
            "symbol": symbol,
            "market_date": "2026-01-01",
            "timeframe": "1D",
        },
        "input": {
            "ohlcv_window": {
                "row_count": 1,
                "first_date": "2026-01-01",
                "last_date": "2026-01-01",
                "rows": [
                    {
                        "date": "2026-01-01",
                        "open": 99.0,
                        "high": 101.0,
                        "low": 98.0,
                        "close": close,
                        "volume": 1000.0,
                    }
                ],
            }
        },
        "analysis": {
            "poom_combo": {
                "ew_norm": 12.0,
                "volume_pressure": -35.0,
                "trend_slope": 6.0,
                "in_squeeze": False,
                "squeeze_up": True,
                "squeeze_down": False,
                "bos_up": True,
                "bos_down": False,
                "choch_up": False,
                "choch_down": False,
                "msb_dir": 1,
            },
            "brain_snapshot": {
                "indicators": {
                    "ema20": 95.0,
                    "ema50": 90.0,
                    "ema200": 105.0,
                    "ema_alignment": "bullish",
                },
                "trend": {"state": "bullish"},
                "market_structure": {"state": "higher_high"},
            },
        },
        "context": {
            "support_resistance": {
                "support_distance_pct": 3.0,
                "resistance_distance_pct": 8.0,
            }
        },
    }


def _snapshot_record(
    snapshot_record_id: str,
    symbol: str,
    payload: dict[str, object],
) -> dict[str, object]:
    return {
        "snapshot_record_id": snapshot_record_id,
        "symbol": symbol,
        "market_date": "2026-01-01",
        "payload": payload,
    }


def _future_rows(
    *,
    final_5: float,
    final_10: float,
    final_20: float,
    high_10: float = 112.0,
    low_10: float = 98.0,
) -> tuple[dict[str, object], ...]:
    rows: list[dict[str, object]] = []
    for index in range(1, 21):
        close = 100.0
        if index == 5:
            close = final_5
        elif index == 10:
            close = final_10
        elif index == 20:
            close = final_20
        rows.append(
            {
                "date": f"2026-01-{index + 1:02d}",
                "open": close,
                "high": high_10 if index == 3 else close,
                "low": low_10 if index == 4 else close,
                "close": close,
                "volume": 1000.0,
            }
        )
    return tuple(rows)


def _rows_for_snapshot(
    market_date: str,
    future_rows: tuple[dict[str, object], ...],
) -> tuple[dict[str, object], ...]:
    return (
        {
            "date": market_date,
            "open": 99.0,
            "high": 101.0,
            "low": 98.0,
            "close": 100.0,
            "volume": 1000.0,
        },
        *future_rows,
    )


def _create_daily_research_snapshots(connection: sqlite3.Connection) -> None:
    connection.execute(
        """
        CREATE TABLE daily_research_snapshots (
            snapshot_record_id TEXT PRIMARY KEY,
            symbol TEXT NOT NULL,
            market_date TEXT NOT NULL,
            timeframe TEXT NOT NULL,
            canonical_schema_version TEXT NOT NULL,
            persistence_version TEXT NOT NULL,
            canonical_snapshot_json TEXT NOT NULL,
            signal_id TEXT,
            payload_hash TEXT NOT NULL,
            source TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )


def _create_ohlcv_daily(connection: sqlite3.Connection) -> None:
    connection.execute(
        """
        CREATE TABLE ohlcv_daily (
            symbol TEXT NOT NULL,
            date TEXT NOT NULL,
            open REAL NOT NULL,
            high REAL NOT NULL,
            low REAL NOT NULL,
            close REAL NOT NULL,
            volume REAL NOT NULL
        )
        """
    )


def _insert_snapshot(
    connection: sqlite3.Connection,
    snapshot_record_id: str,
    symbol: str,
    market_date: str,
    payload: dict[str, object],
) -> None:
    connection.execute(
        """
        INSERT INTO daily_research_snapshots (
            snapshot_record_id,
            symbol,
            market_date,
            timeframe,
            canonical_schema_version,
            persistence_version,
            canonical_snapshot_json,
            signal_id,
            payload_hash,
            source,
            created_at
        )
        VALUES (?, ?, ?, '1D', 'canonical_result_v1', 'daily_research_snapshot_v2', ?, NULL, 'hash', 'test', '2026-01-01')
        """,
        (snapshot_record_id, symbol, market_date, json.dumps(payload)),
    )


def _insert_ohlcv_rows(
    connection: sqlite3.Connection,
    symbol: str,
    rows: tuple[dict[str, object], ...],
) -> None:
    connection.executemany(
        """
        INSERT INTO ohlcv_daily (symbol, date, open, high, low, close, volume)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            (
                symbol,
                row["date"],
                row["open"],
                row["high"],
                row["low"],
                row["close"],
                row["volume"],
            )
            for row in rows
        ),
    )


if __name__ == "__main__":
    unittest.main()
