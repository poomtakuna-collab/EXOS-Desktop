from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import sqlite3
from typing import Any, Mapping


REQUIRED_SNAPSHOT_PAYLOAD_V2_SECTIONS = (
    "identity",
    "provenance",
    "input",
    "analysis",
    "context",
    "strategy",
    "display_summary",
    "diagnostics",
    "compatibility",
)
REQUIRED_CONTEXT_SECTIONS = (
    "market",
    "sector",
    "relative_strength",
    "volume",
    "support_resistance",
)


@dataclass(frozen=True)
class SnapshotPayloadV2ValidationIssue:
    snapshot_record_id: str
    message: str

    def format(self) -> str:
        prefix = self.snapshot_record_id or "<payload>"
        return f"{prefix}: {self.message}"


@dataclass(frozen=True)
class SnapshotPayloadV2ValidationResult:
    checked_count: int
    issues: tuple[SnapshotPayloadV2ValidationIssue, ...] = ()

    @property
    def passed(self) -> bool:
        return not self.issues

    @property
    def status(self) -> str:
        return "PASS" if self.passed else "FAIL"

    @property
    def errors(self) -> tuple[str, ...]:
        return tuple(issue.format() for issue in self.issues)

    def report(self) -> str:
        if self.passed:
            return f"PASS: {self.checked_count} SnapshotPayloadV2 record(s) valid."
        return "\n".join(
            (
                f"FAIL: {self.checked_count} SnapshotPayloadV2 record(s) checked; "
                f"{len(self.issues)} issue(s) found.",
                *self.errors,
            )
        )


def validate_snapshot_payload_v2_payload(
    payload: Mapping[str, Any],
    *,
    snapshot_record_id: str = "",
) -> SnapshotPayloadV2ValidationResult:
    issues = _payload_issues(payload, snapshot_record_id=snapshot_record_id)
    return SnapshotPayloadV2ValidationResult(
        checked_count=1,
        issues=tuple(issues),
    )


def validate_snapshot_payload_v2_records(
    database_path: Path | str,
) -> SnapshotPayloadV2ValidationResult:
    path = Path(database_path)
    if not path.exists():
        return SnapshotPayloadV2ValidationResult(
            checked_count=0,
            issues=(
                SnapshotPayloadV2ValidationIssue(
                    snapshot_record_id="",
                    message=f"database not found: {path}",
                ),
            ),
        )

    connection = sqlite3.connect(path)
    try:
        if not _table_exists(connection, "daily_research_snapshots"):
            return SnapshotPayloadV2ValidationResult(
                checked_count=0,
                issues=(
                    SnapshotPayloadV2ValidationIssue(
                        snapshot_record_id="",
                        message="daily_research_snapshots table is missing",
                    ),
                ),
            )
        rows = connection.execute(
            """
            SELECT snapshot_record_id, canonical_snapshot_json
            FROM daily_research_snapshots
            ORDER BY snapshot_record_id ASC
            """
        ).fetchall()
    finally:
        connection.close()

    issues: list[SnapshotPayloadV2ValidationIssue] = []
    for snapshot_record_id, raw_json in rows:
        safe_snapshot_record_id = str(snapshot_record_id or "")
        try:
            payload = json.loads(str(raw_json or "{}"))
        except json.JSONDecodeError as error:
            issues.append(
                SnapshotPayloadV2ValidationIssue(
                    snapshot_record_id=safe_snapshot_record_id,
                    message=f"canonical_snapshot_json is not valid JSON: {error}",
                )
            )
            continue
        if not isinstance(payload, Mapping):
            issues.append(
                SnapshotPayloadV2ValidationIssue(
                    snapshot_record_id=safe_snapshot_record_id,
                    message="canonical_snapshot_json must decode to an object",
                )
            )
            continue
        issues.extend(
            _payload_issues(payload, snapshot_record_id=safe_snapshot_record_id)
        )

    return SnapshotPayloadV2ValidationResult(
        checked_count=len(rows),
        issues=tuple(issues),
    )


def _payload_issues(
    payload: Mapping[str, Any],
    *,
    snapshot_record_id: str,
) -> list[SnapshotPayloadV2ValidationIssue]:
    issues: list[SnapshotPayloadV2ValidationIssue] = []
    for section_name in REQUIRED_SNAPSHOT_PAYLOAD_V2_SECTIONS:
        section = payload.get(section_name)
        if not isinstance(section, Mapping):
            issues.append(
                _issue(snapshot_record_id, f"missing required section: {section_name}")
            )

    identity = _section(payload, "identity")
    if identity.get("payload_schema_version") != "snapshot_payload_v2":
        issues.append(
            _issue(
                snapshot_record_id,
                "identity.payload_schema_version must be snapshot_payload_v2",
            )
        )

    ohlcv_window = _section(_section(payload, "input"), "ohlcv_window")
    row_count = _positive_int(ohlcv_window.get("row_count"))
    if row_count is None:
        issues.append(
            _issue(
                snapshot_record_id,
                "input.ohlcv_window.row_count must be greater than 0",
            )
        )

    indicators = _section(_section(payload, "analysis"), "brain_snapshot").get(
        "indicators"
    )
    if not isinstance(indicators, Mapping) or not indicators:
        issues.append(
            _issue(
                snapshot_record_id,
                "analysis.brain_snapshot.indicators must be populated",
            )
        )

    context = _section(payload, "context")
    for section_name in REQUIRED_CONTEXT_SECTIONS:
        section = context.get(section_name)
        if not isinstance(section, Mapping) or not section:
            issues.append(
                _issue(
                    snapshot_record_id,
                    f"context.{section_name} must be populated",
                )
            )

    return issues


def _issue(
    snapshot_record_id: str,
    message: str,
) -> SnapshotPayloadV2ValidationIssue:
    return SnapshotPayloadV2ValidationIssue(
        snapshot_record_id=snapshot_record_id,
        message=message,
    )


def _section(source: Mapping[str, Any], name: str) -> Mapping[str, Any]:
    value = source.get(name)
    return value if isinstance(value, Mapping) else {}


def _positive_int(value: object) -> int | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        integer = int(value)
    except (TypeError, ValueError):
        return None
    return integer if integer > 0 else None


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
