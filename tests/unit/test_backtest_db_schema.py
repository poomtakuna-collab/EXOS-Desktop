from __future__ import annotations

from contextlib import closing
import sqlite3
import sys
import unittest

from src.backtest.db import initialize_backtest_schema


class BacktestDbSchemaTest(unittest.TestCase):
    def test_backtest_tables_are_created(self) -> None:
        with closing(sqlite3.connect(":memory:")) as connection:
            initialize_backtest_schema(connection)

            self.assertEqual(
                _table_names(connection),
                {
                    "backtest_assumptions",
                    "backtest_evaluations",
                    "backtest_runs",
                    "backtest_trade_results",
                },
            )

    def test_required_columns_exist(self) -> None:
        with closing(sqlite3.connect(":memory:")) as connection:
            initialize_backtest_schema(connection)

            self.assertTrue(
                _expected_run_columns().issubset(_column_names(connection, "backtest_runs"))
            )
            self.assertTrue(
                _expected_assumption_columns().issubset(
                    _column_names(connection, "backtest_assumptions")
                )
            )
            self.assertTrue(
                _expected_evaluation_columns().issubset(
                    _column_names(connection, "backtest_evaluations")
                )
            )
            self.assertTrue(
                _expected_trade_result_columns().issubset(
                    _column_names(connection, "backtest_trade_results")
                )
            )

    def test_initializer_is_idempotent(self) -> None:
        with closing(sqlite3.connect(":memory:")) as connection:
            initialize_backtest_schema(connection)
            first_schema = _schema_sql(connection)

            initialize_backtest_schema(connection)
            second_schema = _schema_sql(connection)

            self.assertEqual(first_schema, second_schema)

    def test_existing_market_and_statistics_tables_are_not_modified(self) -> None:
        with closing(sqlite3.connect(":memory:")) as connection:
            _create_existing_source_tables(connection)
            before_schema = _schema_sql(connection)

            initialize_backtest_schema(connection)

            after_schema = _schema_sql(connection)
            for table_name in ("ohlcv_daily", "outcomes", "patterns", "snapshots"):
                self.assertEqual(before_schema[table_name], after_schema[table_name])

    def test_initializer_does_not_import_live_data_ai_network_or_broker_modules(self) -> None:
        before_modules = set(sys.modules)
        with closing(sqlite3.connect(":memory:")) as connection:
            initialize_backtest_schema(connection)

        imported_modules = set(sys.modules) - before_modules
        forbidden_prefixes = (
            "src.ai",
            "src.data",
            "src.database",
            "urllib",
            "http",
            "socket",
            "yfinance",
            "broker",
        )
        self.assertFalse(
            {
                module_name
                for module_name in imported_modules
                if module_name.startswith(forbidden_prefixes)
            }
        )


def _table_names(connection: sqlite3.Connection) -> set[str]:
    rows = connection.execute(
        """
        SELECT name
        FROM sqlite_master
        WHERE type = 'table'
        ORDER BY name
        """
    ).fetchall()
    return {str(row[0]) for row in rows}


def _column_names(connection: sqlite3.Connection, table_name: str) -> set[str]:
    rows = connection.execute(f"PRAGMA table_info({table_name})").fetchall()
    return {str(row[1]) for row in rows}


def _schema_sql(connection: sqlite3.Connection) -> dict[str, str]:
    rows = connection.execute(
        """
        SELECT name, sql
        FROM sqlite_master
        WHERE type IN ('index', 'table')
          AND name NOT LIKE 'sqlite_autoindex_%'
        ORDER BY type, name
        """
    ).fetchall()
    return {str(name): str(sql) for name, sql in rows}


def _create_existing_source_tables(connection: sqlite3.Connection) -> None:
    connection.execute(
        """
        CREATE TABLE snapshots (
            snapshot_id TEXT PRIMARY KEY,
            snapshot_json TEXT NOT NULL
        )
        """
    )
    connection.execute(
        """
        CREATE TABLE outcomes (
            outcome_id TEXT PRIMARY KEY,
            snapshot_id TEXT NOT NULL
        )
        """
    )
    connection.execute(
        """
        CREATE TABLE patterns (
            pattern_id TEXT PRIMARY KEY,
            sample_count INTEGER NOT NULL
        )
        """
    )
    connection.execute(
        """
        CREATE TABLE ohlcv_daily (
            symbol TEXT NOT NULL,
            date TEXT NOT NULL,
            close REAL
        )
        """
    )
    connection.commit()


def _expected_run_columns() -> set[str]:
    return {
        "run_id",
        "run_name",
        "backtest_version",
        "strategy_version",
        "simulation_version",
        "source_database_id",
        "source_database_path",
        "symbols_json",
        "timeframe",
        "start_date",
        "end_date",
        "snapshot_query_json",
        "attempted_trades",
        "completed_trades",
        "total_trades",
        "winning_trades",
        "losing_trades",
        "skipped_trades",
        "breakeven_trades",
        "win_rate",
        "average_return",
        "average_drawdown",
        "expectancy",
        "max_drawdown",
        "notes_json",
        "created_at",
    }


def _expected_assumption_columns() -> set[str]:
    return {
        "run_id",
        "horizon_days",
        "entry_price_source",
        "conservative_same_window_rule",
        "target_source",
        "stop_source",
        "probability_source",
        "prediction_source",
        "strategy_source",
        "fees_enabled",
        "slippage_enabled",
        "portfolio_enabled",
        "ai_enabled",
        "live_data_enabled",
        "broker_execution_enabled",
        "assumptions_json",
        "created_at",
    }


def _expected_evaluation_columns() -> set[str]:
    return {
        "evaluation_id",
        "run_id",
        "sequence_number",
        "snapshot_id",
        "symbol",
        "timeframe",
        "snapshot_date",
        "outcome_id",
        "evaluation_status",
        "skip_reason",
        "has_outcome",
        "has_future_rows",
        "future_rows_count",
        "strategy_score",
        "trade_grade",
        "entry_quality",
        "risk_rating",
        "strategy_result_json",
        "probability_json",
        "prediction_json",
        "created_at",
    }


def _expected_trade_result_columns() -> set[str]:
    return {
        "trade_result_id",
        "run_id",
        "evaluation_id",
        "snapshot_id",
        "simulation_status",
        "trade_outcome",
        "exit_reason",
        "entry_price",
        "exit_price",
        "return_percent",
        "max_drawdown_percent",
        "notes_json",
        "created_at",
    }


if __name__ == "__main__":
    unittest.main()
