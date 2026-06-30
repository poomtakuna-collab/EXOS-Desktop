from __future__ import annotations

import sqlite3
import unittest

from src.backtest import (
    BACKTEST_PERSISTENCE_SCHEMA_SQL,
    CREATE_BACKTEST_EVALUATIONS_PERSISTENCE_TABLE_SQL,
    CREATE_BACKTEST_RUNS_PERSISTENCE_TABLE_SQL,
    CREATE_BACKTEST_TRADE_RESULTS_PERSISTENCE_TABLE_SQL,
    BacktestEvaluationRecord,
    BacktestRunRecord,
    BacktestTradeResultRecord,
)


class BacktestPersistenceSchemaTest(unittest.TestCase):
    def test_schema_contains_only_backtest_owned_persistence_tables(self) -> None:
        with sqlite3.connect(":memory:") as connection:
            _execute_schema(connection)

            self.assertEqual(
                _table_names(connection),
                {
                    "backtest_runs",
                    "backtest_evaluations",
                    "backtest_trade_results",
                },
            )

    def test_run_table_columns_match_contract_fields(self) -> None:
        with sqlite3.connect(":memory:") as connection:
            _execute_schema(connection)

            self.assertEqual(
                _column_names(connection, "backtest_runs"),
                set(BacktestRunRecord().__dict__),
            )

    def test_evaluation_table_columns_match_contract_fields(self) -> None:
        with sqlite3.connect(":memory:") as connection:
            _execute_schema(connection)

            self.assertEqual(
                _column_names(connection, "backtest_evaluations"),
                set(BacktestEvaluationRecord().__dict__),
            )

    def test_trade_result_table_columns_match_contract_fields(self) -> None:
        with sqlite3.connect(":memory:") as connection:
            _execute_schema(connection)

            self.assertEqual(
                _column_names(connection, "backtest_trade_results"),
                set(BacktestTradeResultRecord().__dict__),
            )

    def test_schema_constants_are_ordered_deterministically(self) -> None:
        self.assertEqual(
            BACKTEST_PERSISTENCE_SCHEMA_SQL,
            (
                CREATE_BACKTEST_RUNS_PERSISTENCE_TABLE_SQL,
                CREATE_BACKTEST_EVALUATIONS_PERSISTENCE_TABLE_SQL,
                CREATE_BACKTEST_TRADE_RESULTS_PERSISTENCE_TABLE_SQL,
            ),
        )

    def test_schema_constants_do_not_include_write_or_read_functions(self) -> None:
        sql_text = "\n".join(BACKTEST_PERSISTENCE_SCHEMA_SQL).upper()

        self.assertIn("CREATE TABLE IF NOT EXISTS BACKTEST_RUNS", sql_text)
        self.assertNotIn("INSERT INTO", sql_text)
        self.assertNotIn("UPDATE ", sql_text)
        self.assertNotIn("DELETE FROM", sql_text)
        self.assertNotIn("SELECT ", sql_text)

    def test_schema_is_idempotent_when_executed_directly(self) -> None:
        with sqlite3.connect(":memory:") as connection:
            _execute_schema(connection)
            first_schema = _schema_sql(connection)

            _execute_schema(connection)
            second_schema = _schema_sql(connection)

            self.assertEqual(first_schema, second_schema)


def _execute_schema(connection: sqlite3.Connection) -> None:
    for statement in BACKTEST_PERSISTENCE_SCHEMA_SQL:
        connection.execute(statement)
    connection.commit()


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
        WHERE type = 'table'
        ORDER BY name
        """
    ).fetchall()
    return {str(name): str(sql) for name, sql in rows}


if __name__ == "__main__":
    unittest.main()
