from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import sqlite3
from typing import Any, Mapping

from src.canonical_result import CANONICAL_RESULT_SCHEMA_VERSION_V1, CanonicalResultV1
from src.snapshot_payload_v2 import build_snapshot_payload_v2


DAILY_RESEARCH_SNAPSHOT_PERSISTENCE_VERSION_V2 = "daily_research_snapshot_v2"


CREATE_DAILY_RESEARCH_SNAPSHOTS_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS daily_research_snapshots (
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


CREATE_DAILY_RESEARCH_SNAPSHOTS_UNIQUE_INDEX_SQL = """
CREATE UNIQUE INDEX IF NOT EXISTS idx_daily_research_snapshot_identity
ON daily_research_snapshots (
    symbol,
    market_date,
    timeframe,
    canonical_schema_version,
    persistence_version
)
"""


DAILY_RESEARCH_SNAPSHOT_SCHEMA_SQL = (
    CREATE_DAILY_RESEARCH_SNAPSHOTS_TABLE_SQL,
    CREATE_DAILY_RESEARCH_SNAPSHOTS_UNIQUE_INDEX_SQL,
)


@dataclass(frozen=True)
class DailyResearchSnapshotRecord:
    snapshot_record_id: str
    symbol: str
    market_date: str
    timeframe: str
    canonical_schema_version: str
    persistence_version: str
    canonical_snapshot_json: str
    signal_id: str | None
    payload_hash: str
    source: str
    created_at: str

    def to_dict(self) -> dict[str, object]:
        return {
            "snapshot_record_id": self.snapshot_record_id,
            "symbol": self.symbol,
            "market_date": self.market_date,
            "timeframe": self.timeframe,
            "canonical_schema_version": self.canonical_schema_version,
            "persistence_version": self.persistence_version,
            "canonical_snapshot": self.canonical_snapshot,
            "signal_id": self.signal_id,
            "payload_hash": self.payload_hash,
            "source": self.source,
            "created_at": self.created_at,
        }

    @property
    def canonical_snapshot(self) -> dict[str, Any]:
        loaded = json.loads(self.canonical_snapshot_json)
        return loaded if isinstance(loaded, dict) else {}


class DailyResearchSnapshotConflictError(ValueError):
    pass


class SQLiteDailyResearchSnapshotRepository:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self.connection = connection

    def initialize_schema(self) -> None:
        initialize_daily_research_snapshot_schema(self.connection)

    def save_snapshot(
        self,
        canonical_result: CanonicalResultV1,
        *,
        signal_id: str | None = None,
        created_at: str = "",
        compatibility: Mapping[str, Any] | None = None,
    ) -> DailyResearchSnapshotRecord:
        record = build_daily_research_snapshot_record(
            canonical_result,
            signal_id=signal_id,
            created_at=created_at,
            compatibility=compatibility,
        )
        existing = self.load_snapshot(
            symbol=record.symbol,
            market_date=record.market_date,
            timeframe=record.timeframe,
            canonical_schema_version=record.canonical_schema_version,
            persistence_version=record.persistence_version,
        )
        if existing is not None:
            if _same_payload_ignoring_created_at(
                existing.canonical_snapshot,
                record.canonical_snapshot,
            ):
                return existing
            raise DailyResearchSnapshotConflictError(
                "daily research snapshot identity already exists with different payload"
            )

        self.connection.execute(
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
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            _record_values(record),
        )
        self.connection.commit()
        return record

    def load_snapshot(
        self,
        *,
        symbol: str,
        market_date: str,
        timeframe: str = "1D",
        canonical_schema_version: str = CANONICAL_RESULT_SCHEMA_VERSION_V1,
        persistence_version: str = DAILY_RESEARCH_SNAPSHOT_PERSISTENCE_VERSION_V2,
    ) -> DailyResearchSnapshotRecord | None:
        safe_symbol = _normalize_symbol(symbol)
        safe_market_date = _required_text(market_date, "market_date")
        safe_timeframe = _required_text(timeframe, "timeframe")
        safe_schema = _required_text(canonical_schema_version, "canonical_schema_version")
        row = self.connection.execute(
            """
            SELECT
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
            FROM daily_research_snapshots
            WHERE symbol = ?
              AND market_date = ?
              AND timeframe = ?
              AND canonical_schema_version = ?
              AND persistence_version = ?
            """,
            (
                safe_symbol,
                safe_market_date,
                safe_timeframe,
                safe_schema,
                _required_text(persistence_version, "persistence_version"),
            ),
        ).fetchone()
        if row is None:
            return None
        return _record_from_row(row)

    def load_snapshot_for_signal_id(
        self,
        signal_id: str,
    ) -> DailyResearchSnapshotRecord | None:
        safe_signal_id = _required_text(signal_id, "signal_id")
        row = self.connection.execute(
            """
            SELECT
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
            FROM daily_research_snapshots
            WHERE signal_id = ?
            ORDER BY symbol ASC, market_date ASC, timeframe ASC, canonical_schema_version ASC, persistence_version ASC
            LIMIT 1
            """,
            (safe_signal_id,),
        ).fetchone()
        if row is None:
            return None
        return _record_from_row(row)

    def list_snapshots(
        self,
        *,
        symbol: str | None = None,
        market_date: str | None = None,
        timeframe: str | None = None,
    ) -> tuple[DailyResearchSnapshotRecord, ...]:
        clauses: list[str] = []
        values: list[str] = []
        if symbol is not None:
            clauses.append("symbol = ?")
            values.append(_normalize_symbol(symbol))
        if market_date is not None:
            clauses.append("market_date = ?")
            values.append(_required_text(market_date, "market_date"))
        if timeframe is not None:
            clauses.append("timeframe = ?")
            values.append(_required_text(timeframe, "timeframe"))

        where_sql = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        cursor = self.connection.execute(
            f"""
            SELECT
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
            FROM daily_research_snapshots
            {where_sql}
            ORDER BY symbol ASC, market_date ASC, timeframe ASC, canonical_schema_version ASC, persistence_version ASC
            """,
            tuple(values),
        )
        return tuple(_record_from_row(row) for row in cursor.fetchall())


def initialize_daily_research_snapshot_schema(connection: sqlite3.Connection) -> None:
    for statement in DAILY_RESEARCH_SNAPSHOT_SCHEMA_SQL:
        connection.execute(statement)
    connection.commit()


def build_daily_research_snapshot_record(
    canonical_result: CanonicalResultV1,
    *,
    signal_id: str | None = None,
    created_at: str = "",
    compatibility: Mapping[str, Any] | None = None,
) -> DailyResearchSnapshotRecord:
    if not isinstance(canonical_result, CanonicalResultV1):
        raise TypeError("canonical_result must be CanonicalResultV1")

    payload = canonical_result.to_dict()
    snapshot_payload = build_snapshot_payload_v2(
        canonical_result=canonical_result,
        compatibility={
            **dict(compatibility or {}),
            "signal_id": _optional_text(signal_id) or str((compatibility or {}).get("signal_id") or ""),
        },
    ).to_dict()
    canonical_json = _canonical_json(snapshot_payload)
    payload_hash = _sha256(canonical_json)
    symbol = _normalize_symbol(_identity_value(payload, "symbol"))
    market_date = _required_text(
        _identity_value(payload, "analysis_date")
        or _identity_value(payload, "snapshot_date")
        or _signal_summary_value(payload, "signal_date")
        or _signal_summary_value(payload, "snapshot_date"),
        "market_date",
    )
    timeframe = _required_text(
        _identity_value(payload, "timeframe")
        or _signal_summary_value(payload, "timeframe")
        or "1D",
        "timeframe",
    )
    schema_version = _required_text(payload.get("schema_version"), "canonical_schema_version")
    persistence_version = DAILY_RESEARCH_SNAPSHOT_PERSISTENCE_VERSION_V2
    source = _source(payload)
    snapshot_record_id = _snapshot_record_id(
        symbol=symbol,
        market_date=market_date,
        timeframe=timeframe,
        canonical_schema_version=schema_version,
        persistence_version=persistence_version,
    )
    return DailyResearchSnapshotRecord(
        snapshot_record_id=snapshot_record_id,
        symbol=symbol,
        market_date=market_date,
        timeframe=timeframe,
        canonical_schema_version=schema_version,
        persistence_version=persistence_version,
        canonical_snapshot_json=canonical_json,
        signal_id=_optional_text(signal_id),
        payload_hash=payload_hash,
        source=source,
        created_at=_required_text(created_at or market_date, "created_at"),
    )


def _record_values(record: DailyResearchSnapshotRecord) -> tuple[object, ...]:
    return (
        record.snapshot_record_id,
        record.symbol,
        record.market_date,
        record.timeframe,
        record.canonical_schema_version,
        record.persistence_version,
        record.canonical_snapshot_json,
        record.signal_id,
        record.payload_hash,
        record.source,
        record.created_at,
    )


def _record_from_row(row: sqlite3.Row | tuple[Any, ...]) -> DailyResearchSnapshotRecord:
    values = tuple(row)
    return DailyResearchSnapshotRecord(
        snapshot_record_id=str(values[0] or ""),
        symbol=str(values[1] or ""),
        market_date=str(values[2] or ""),
        timeframe=str(values[3] or ""),
        canonical_schema_version=str(values[4] or ""),
        persistence_version=str(values[5] or ""),
        canonical_snapshot_json=str(values[6] or "{}"),
        signal_id=str(values[7]) if values[7] is not None else None,
        payload_hash=str(values[8] or ""),
        source=str(values[9] or ""),
        created_at=str(values[10] or ""),
    )


def _canonical_json(value: object) -> str:
    return json.dumps(value, indent=2, sort_keys=True, default=str)


def _sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _snapshot_record_id(
    *,
    symbol: str,
    market_date: str,
    timeframe: str,
    canonical_schema_version: str,
    persistence_version: str,
) -> str:
    identity = "|".join(
        (
            symbol,
            market_date,
            timeframe,
            canonical_schema_version,
            persistence_version,
        )
    )
    digest = _sha256(identity)[:16]
    return f"snapshot-v2:{symbol.lower()}:{market_date}:{timeframe.lower()}:{digest}"


def _identity_value(payload: dict[str, Any], key: str) -> str:
    identity = payload.get("identity")
    if not isinstance(identity, dict):
        return ""
    return str(identity.get(key) or "").strip()


def _signal_summary_value(payload: dict[str, Any], key: str) -> str:
    signal_summary = payload.get("signal_summary")
    if not isinstance(signal_summary, dict):
        return ""
    return str(signal_summary.get(key) or "").strip()


def _source(payload: dict[str, Any]) -> str:
    for section_name, key in (
        ("identity", "source"),
        ("identity", "pipeline_name"),
        ("diagnostics", "source_pipeline"),
    ):
        section = payload.get(section_name)
        if isinstance(section, dict):
            value = str(section.get(key) or "").strip()
            if value:
                return value
    return "unknown"


def _normalize_symbol(value: object) -> str:
    return _required_text(value, "symbol").upper()


def _required_text(value: object, name: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise ValueError(f"{name} is required")
    return text


def _optional_text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def _same_payload_ignoring_created_at(
    first: dict[str, Any],
    second: dict[str, Any],
) -> bool:
    return _without_created_at(first) == _without_created_at(second)


def _without_created_at(payload: dict[str, Any]) -> dict[str, Any]:
    copied = json.loads(json.dumps(payload, sort_keys=True, default=str))
    provenance = copied.get("provenance")
    if isinstance(provenance, dict):
        provenance.pop("created_at", None)
    return copied
