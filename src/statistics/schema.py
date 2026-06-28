from __future__ import annotations

import sqlite3
from pathlib import Path


CREATE_SNAPSHOTS_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS snapshots (
    snapshot_id TEXT PRIMARY KEY,
    symbol TEXT NOT NULL,
    timeframe TEXT NOT NULL,
    date TEXT NOT NULL,
    close REAL,
    exos_score REAL,
    rating TEXT,
    recommendation TEXT,
    trend_score REAL,
    trend_state TEXT,
    trend_slope_score REAL,
    squeeze_score REAL,
    squeeze_state TEXT,
    market_structure_score REAL,
    market_structure_state TEXT,
    snapshot_json TEXT NOT NULL,
    created_at TEXT NOT NULL,
    UNIQUE(symbol, timeframe, date)
)
"""

CREATE_OUTCOMES_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS outcomes (
    outcome_id TEXT PRIMARY KEY,
    snapshot_id TEXT NOT NULL,
    forward_5d_return REAL,
    forward_10d_return REAL,
    forward_20d_return REAL,
    max_gain_10d REAL,
    max_drawdown_10d REAL,
    hit_5pct_10d INTEGER,
    hit_10pct_10d INTEGER,
    label_10d TEXT,
    calculated_at TEXT NOT NULL,
    FOREIGN KEY(snapshot_id) REFERENCES snapshots(snapshot_id)
)
"""

CREATE_PATTERNS_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS patterns (
    pattern_id TEXT PRIMARY KEY,
    trend_state TEXT,
    squeeze_state TEXT,
    market_structure_state TEXT,
    rating TEXT,
    recommendation TEXT,
    sample_count INTEGER NOT NULL,
    average_5d_return REAL,
    average_10d_return REAL,
    average_20d_return REAL,
    hit_5pct_rate REAL,
    hit_10pct_rate REAL,
    average_max_gain REAL,
    average_drawdown REAL,
    dominant_label TEXT,
    confidence REAL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
)
"""

REQUIRED_INDEX_SQL = (
    """
    CREATE INDEX IF NOT EXISTS idx_snapshots_symbol_timeframe_date
    ON snapshots(symbol, timeframe, date)
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_snapshots_exos_score
    ON snapshots(exos_score)
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_snapshots_trend_state
    ON snapshots(trend_state)
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_snapshots_squeeze_state
    ON snapshots(squeeze_state)
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_snapshots_market_structure_state
    ON snapshots(market_structure_state)
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_outcomes_snapshot_id
    ON outcomes(snapshot_id)
    """,
)


def initialize_statistics_db(db_path: str | Path) -> None:
    database_path = Path(db_path)
    database_path.parent.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(database_path)
    try:
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute(CREATE_SNAPSHOTS_TABLE_SQL)
        connection.execute(CREATE_OUTCOMES_TABLE_SQL)
        connection.execute(CREATE_PATTERNS_TABLE_SQL)
        for index_sql in REQUIRED_INDEX_SQL:
            connection.execute(index_sql)
        connection.commit()
    finally:
        connection.close()
