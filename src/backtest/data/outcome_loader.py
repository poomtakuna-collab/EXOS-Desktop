from __future__ import annotations

import sqlite3
from typing import Any


class OutcomeLoader:
    """Public interface for loading stored outcome records for Backtest."""

    def load_outcome(self, snapshot_id: str) -> dict[str, Any] | None:
        """Load one outcome record associated with `snapshot_id`.

        Implementations must not calculate new outcomes or modify stored records.
        Missing outcomes should be represented deterministically.
        """
        raise NotImplementedError("OutcomeLoader.load_outcome is not implemented yet")

    def load_outcomes(
        self,
        snapshot_ids: list[str],
    ) -> dict[str, dict[str, Any]]:
        """Load outcome records for the provided snapshot ids.

        Implementations must preserve the `snapshot_id` relationship and should
        report missing outcomes without raising for normal absence.
        """
        raise NotImplementedError("OutcomeLoader.load_outcomes is not implemented yet")


class SQLiteOutcomeLoader(OutcomeLoader):
    """SQLite-backed reader for existing Backtest outcome records."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        self.connection = connection

    def load_outcome(self, snapshot_id: str) -> dict[str, Any] | None:
        return self.load_outcomes([snapshot_id]).get(snapshot_id)

    def load_outcomes(
        self,
        snapshot_ids: list[str],
    ) -> dict[str, dict[str, Any]]:
        if not snapshot_ids:
            return {}
        self._ensure_outcomes_table()

        unique_snapshot_ids = tuple(dict.fromkeys(snapshot_ids))
        placeholders = ", ".join("?" for _ in unique_snapshot_ids)
        cursor = self.connection.execute(
            f"""
            SELECT *
            FROM outcomes
            WHERE snapshot_id IN ({placeholders})
            ORDER BY snapshot_id ASC, outcome_id ASC
            """,
            unique_snapshot_ids,
        )

        outcomes: dict[str, dict[str, Any]] = {}
        for row in cursor.fetchall():
            outcome = _row_to_dict(cursor, row)
            snapshot_id = str(outcome["snapshot_id"])
            outcomes.setdefault(snapshot_id, outcome)
        return outcomes

    def _ensure_outcomes_table(self) -> None:
        row = self.connection.execute(
            """
            SELECT 1
            FROM sqlite_master
            WHERE type = 'table'
              AND name = 'outcomes'
            """
        ).fetchone()
        if row is None:
            raise RuntimeError("SQLite outcomes table is required for SQLiteOutcomeLoader")


def _row_to_dict(cursor: sqlite3.Cursor, row: sqlite3.Row | tuple[object, ...]) -> dict[str, Any]:
    columns = [description[0] for description in cursor.description]
    return dict(zip(columns, row, strict=True))
