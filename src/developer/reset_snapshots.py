from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import sqlite3


SNAPSHOT_RESET_TABLES = (
    "daily_research_snapshots",
    "signal_ledger_signals",
    "snapshots",
)


@dataclass(frozen=True)
class SnapshotResetResult:
    database_path: Path
    deleted_by_table: dict[str, int]

    @property
    def total_deleted(self) -> int:
        return sum(self.deleted_by_table.values())


def reset_snapshots(
    database_path: Path | str,
    *,
    confirm: bool = False,
) -> SnapshotResetResult:
    if not confirm:
        raise ValueError("snapshot reset requires explicit confirm=True")

    path = Path(database_path)
    deleted_by_table = {table_name: 0 for table_name in SNAPSHOT_RESET_TABLES}
    if not path.exists():
        return SnapshotResetResult(database_path=path, deleted_by_table=deleted_by_table)

    connection = sqlite3.connect(path)
    try:
        for table_name in SNAPSHOT_RESET_TABLES:
            if not _table_exists(connection, table_name):
                continue
            deleted_by_table[table_name] = _row_count(connection, table_name)
            connection.execute(f"DELETE FROM {table_name}")
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()

    return SnapshotResetResult(database_path=path, deleted_by_table=deleted_by_table)


def _table_exists(connection: sqlite3.Connection, table_name: str) -> bool:
    row = connection.execute(
        """
        SELECT 1
        FROM sqlite_master
        WHERE type = 'table'
          AND name = ?
        """,
        (table_name,),
    ).fetchone()
    return row is not None


def _row_count(connection: sqlite3.Connection, table_name: str) -> int:
    row = connection.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()
    return int(row[0] or 0) if row else 0
