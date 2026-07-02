from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any
from typing import Protocol

from src.daily_research_snapshot import (
    DailyResearchSnapshotRecord,
    SQLiteDailyResearchSnapshotRepository,
)
from src.outcome_tracking import OutcomeRecord, OutcomeStatus
from src.signal_ledger import SignalRecord, SignalType
from src.signal_ledger.sqlite_repository import SQLiteSignalLedgerRepository


DEFAULT_SIGNAL_HISTORY_DATABASE_PATH = Path("database") / "exos.db"
SIGNAL_HISTORY_COLUMNS = (
    "Snapshot Date",
    "Snapshot Type",
    "Confidence",
    "Snapshot",
    "Outcomes",
    "Latest Outcome",
)


class SignalHistoryRepository(Protocol):
    def list_signals(
        self,
        *,
        symbol: str | None = None,
    ) -> tuple[SignalRecord, ...]:
        """List saved signals."""

    def list_outcomes_for_signal(self, signal_id: str) -> tuple[OutcomeRecord, ...]:
        """List outcomes linked to a signal."""


def load_desktop_signal_history_view_model(
    database_path: Path | str | None = None,
    *,
    selected_symbol: str | None = None,
) -> dict[str, object]:
    symbol = _normalize_symbol(selected_symbol)
    if not symbol:
        return build_signal_history_view_model(selected_symbol=symbol)

    safe_database_path = Path(database_path or DEFAULT_SIGNAL_HISTORY_DATABASE_PATH)
    if not safe_database_path.exists():
        return build_signal_history_view_model(selected_symbol=symbol)

    uri = safe_database_path.resolve().as_uri() + "?mode=ro"
    connection = sqlite3.connect(uri, uri=True)
    try:
        if not _has_table(connection, "signal_ledger_signals"):
            return build_signal_history_view_model(selected_symbol=symbol)

        repository = SQLiteSignalLedgerRepository(connection)
        signals = repository.list_signals(symbol=symbol)
        outcomes_by_signal_id = (
            _outcomes_by_signal_id(repository, signals)
            if _has_table(connection, "signal_ledger_outcomes")
            else {}
        )
        return build_signal_history_view_model(
            selected_symbol=symbol,
            signals=signals,
            outcomes_by_signal_id=outcomes_by_signal_id,
        )
    finally:
        connection.close()


def load_desktop_snapshot_detail_view_model(
    database_path: Path | str | None = None,
    *,
    signal_id: str | None = None,
    snapshot_record_id: str | None = None,
    symbol: str | None = None,
    market_date: str | None = None,
    timeframe: str | None = None,
) -> dict[str, object]:
    safe_signal_id = str(signal_id or "").strip()
    safe_snapshot_record_id = str(snapshot_record_id or "").strip()
    safe_symbol = _normalize_symbol(symbol)
    safe_market_date = str(market_date or "").strip()
    safe_timeframe = str(timeframe or "").strip() or "1D"
    if not any((safe_signal_id, safe_snapshot_record_id, safe_symbol and safe_market_date)):
        return build_snapshot_detail_view_model()

    safe_database_path = Path(database_path or DEFAULT_SIGNAL_HISTORY_DATABASE_PATH)
    if not safe_database_path.exists():
        return build_snapshot_detail_view_model()

    uri = safe_database_path.resolve().as_uri() + "?mode=ro"
    connection = sqlite3.connect(uri, uri=True)
    try:
        signal_repository = (
            SQLiteSignalLedgerRepository(connection)
            if safe_signal_id and _has_table(connection, "signal_ledger_signals")
            else None
        )
        signal = signal_repository.load_signal(safe_signal_id) if signal_repository else None
        if _has_table(connection, "daily_research_snapshots"):
            snapshot_repository = SQLiteDailyResearchSnapshotRepository(connection)
            v2_snapshot = _load_preferred_v2_snapshot(
                snapshot_repository,
                snapshot_record_id=safe_snapshot_record_id,
                symbol=safe_symbol or (signal.symbol if signal is not None else ""),
                market_date=safe_market_date,
                timeframe=safe_timeframe,
                signal=signal,
            )
            if v2_snapshot is not None:
                outcomes = _detail_outcomes(
                    signal_repository,
                    signal_id=safe_signal_id or v2_snapshot.signal_id or "",
                )
                return build_v2_snapshot_detail_view_model(
                    snapshot=v2_snapshot,
                    outcomes=outcomes,
                )

        outcomes = _detail_outcomes(signal_repository, signal_id=safe_signal_id)
        return build_snapshot_detail_view_model(signal=signal, outcomes=outcomes)
    finally:
        connection.close()


def build_signal_history_view_model(
    *,
    selected_symbol: str | None = None,
    signals: tuple[SignalRecord, ...] = (),
    outcomes_by_signal_id: dict[str, tuple[OutcomeRecord, ...]] | None = None,
) -> dict[str, object]:
    symbol = _normalize_symbol(selected_symbol)
    outcomes_by_signal_id = outcomes_by_signal_id or {}
    rows = tuple(
        _signal_row(signal, outcomes_by_signal_id.get(signal.signal_id, ()))
        for signal in signals
    )
    return {
        "selected_symbol": symbol or "No symbol selected",
        "columns": SIGNAL_HISTORY_COLUMNS,
        "rows": rows,
        "status": _status_text(symbol=symbol, row_count=len(rows)),
    }


def build_snapshot_detail_view_model(
    *,
    signal: SignalRecord | None = None,
    outcomes: tuple[OutcomeRecord, ...] = (),
) -> dict[str, object]:
    if signal is None:
        empty_raw = _json_pretty({})
        return {
            "title": "Snapshot Detail",
            "header": _detail_header(signal=None, outcomes=()),
            "groups": _empty_detail_groups(),
            "raw_json": empty_raw,
            "status": "Snapshot detail is not available.",
        }

    raw_payload = signal.to_dict()
    latest_outcome = outcomes[-1] if outcomes else None
    if latest_outcome is not None:
        raw_payload = {
            **raw_payload,
            "latest_outcome": latest_outcome.to_dict(),
            "linked_outcome_count": len(outcomes),
        }

    return {
        "title": f"Snapshot Detail - {signal.symbol or '-'}",
        "header": _detail_header(signal=signal, outcomes=outcomes),
        "groups": (
            _detail_group(
                "Market",
                (
                    ("Symbol", signal.symbol),
                    ("Market Date", _market_date(signal)),
                    ("Timeframe", signal.snapshot_reference.timeframe),
                    ("Snapshot Source", signal.snapshot_reference.source),
                ),
            ),
            _detail_group(
                "Indicators",
                _dict_items(_nested_dict(signal.context_summary, "indicators")),
            ),
            _detail_group(
                "Context",
                _dict_items(signal.context_summary),
            ),
            _detail_group(
                "Prediction",
                _dict_items(_prediction_summary(signal)),
            ),
            _detail_group(
                "Strategy",
                _dict_items(signal.strategy_summary),
            ),
        ),
        "raw_json": _json_pretty(raw_payload),
        "status": "Legacy Compatibility Projection",
    }


def build_v2_snapshot_detail_view_model(
    *,
    snapshot: DailyResearchSnapshotRecord | None = None,
    outcomes: tuple[OutcomeRecord, ...] = (),
) -> dict[str, object]:
    if snapshot is None:
        return build_snapshot_detail_view_model()

    canonical = snapshot.canonical_snapshot
    latest_outcome = outcomes[-1] if outcomes else None
    if _is_snapshot_payload_v2(canonical):
        return {
            "title": f"Snapshot Detail - {snapshot.symbol or '-'}",
            "header": _v2_detail_header(snapshot=snapshot, latest_outcome=latest_outcome),
            "tabs": _snapshot_payload_v2_tabs(canonical),
            "raw_json": _json_pretty(canonical),
            "status": "SnapshotPayloadV2",
        }

    return {
        "title": f"Snapshot Detail - {snapshot.symbol or '-'}",
        "header": _v2_detail_header(snapshot=snapshot, latest_outcome=latest_outcome),
        "groups": (
            _detail_group(
                "Market",
                (
                    ("Symbol", snapshot.symbol),
                    ("Market Date", snapshot.market_date),
                    ("Timeframe", snapshot.timeframe),
                    ("Snapshot Source", snapshot.source),
                    ("Canonical Schema", snapshot.canonical_schema_version),
                ),
            ),
            _detail_group("Indicators", _dict_items(_v2_indicators(canonical))),
            _detail_group("Context", _dict_items(_v2_section(canonical, "context"))),
            _detail_group("Prediction", _dict_items(_v2_prediction(canonical))),
            _detail_group("Strategy", _dict_items(_v2_section(canonical, "strategy"))),
        ),
        "raw_json": _json_pretty(canonical),
        "status": "Full Canonical Snapshot",
    }


def _outcomes_by_signal_id(
    repository: SignalHistoryRepository,
    signals: tuple[SignalRecord, ...],
) -> dict[str, tuple[OutcomeRecord, ...]]:
    return {
        signal.signal_id: repository.list_outcomes_for_signal(signal.signal_id)
        for signal in signals
        if signal.signal_id
    }


def _signal_row(
    signal: SignalRecord,
    outcomes: tuple[OutcomeRecord, ...],
) -> dict[str, str]:
    latest_outcome = outcomes[-1] if outcomes else None
    return {
        "signal_id": signal.signal_id,
        "snapshot_record_id": "",
        "symbol": signal.symbol,
        "market_date": _market_date(signal),
        "timeframe": signal.snapshot_reference.timeframe or "1D",
        "signal_date": signal.signal_date or "-",
        "signal_type": _format_label(_signal_type_value(signal.signal_type)),
        "confidence": _format_percent(signal.confidence),
        "snapshot": _format_snapshot(signal),
        "linked_outcome_count": str(len(outcomes)),
        "latest_outcome": _format_latest_outcome(latest_outcome),
    }


def _format_snapshot(signal: SignalRecord) -> str:
    snapshot = signal.snapshot_reference
    snapshot_id = snapshot.snapshot_id.strip()
    snapshot_date = snapshot.snapshot_date.strip()
    if snapshot_date and snapshot_id:
        return f"{snapshot_date} / {snapshot_id}"
    return snapshot_date or snapshot_id or "-"


def _format_latest_outcome(outcome: OutcomeRecord | None) -> str:
    if outcome is None:
        return "-"
    status = _format_label(_outcome_status_value(outcome.outcome_status))
    return_value = _format_percent(outcome.return_pct)
    if return_value == "-":
        return status
    return f"{status} / {return_value}"


def _status_text(*, symbol: str, row_count: int) -> str:
    if not symbol:
        return "Select a dashboard symbol to view saved snapshot history."
    if row_count == 0:
        return f"No saved snapshots found for {symbol}."
    return f"Read-only snapshot history for {symbol}."



def _detail_outcomes(
    repository: SQLiteSignalLedgerRepository | None,
    *,
    signal_id: str,
) -> tuple[OutcomeRecord, ...]:
    safe_signal_id = str(signal_id or "").strip()
    if repository is None or not safe_signal_id:
        return ()
    try:
        return repository.list_outcomes_for_signal(safe_signal_id)
    except sqlite3.Error:
        return ()


def _load_preferred_v2_snapshot(
    repository: SQLiteDailyResearchSnapshotRepository,
    *,
    snapshot_record_id: str = "",
    symbol: str = "",
    market_date: str = "",
    timeframe: str = "1D",
    signal: SignalRecord | None = None,
) -> DailyResearchSnapshotRecord | None:
    if snapshot_record_id:
        try:
            linked = repository.load_snapshot_by_record_id(snapshot_record_id)
        except (sqlite3.Error, ValueError):
            linked = None
        if linked is not None:
            return linked

    safe_symbol = str(symbol or "").strip()
    safe_market_date = str(market_date or "").strip()
    safe_timeframe = str(timeframe or "").strip() or "1D"
    if safe_symbol and safe_market_date:
        try:
            snapshot = repository.load_snapshot(
                symbol=safe_symbol,
                market_date=safe_market_date,
                timeframe=safe_timeframe,
            )
        except (sqlite3.Error, ValueError):
            snapshot = None
        if snapshot is not None:
            return snapshot

    if signal is not None and signal.signal_id:
        try:
            linked = repository.load_snapshot_for_signal_id(signal.signal_id)
        except (sqlite3.Error, ValueError):
            linked = None
        if linked is not None:
            return linked

    if signal is None:
        return None
    fallback_symbol = str(signal.symbol or "").strip()
    fallback_timeframe = str(signal.snapshot_reference.timeframe or "1D").strip()
    if not fallback_symbol:
        return None
    for candidate_market_date in _candidate_market_dates(signal):
        try:
            snapshot = repository.load_snapshot(
                symbol=fallback_symbol,
                market_date=candidate_market_date,
                timeframe=fallback_timeframe or "1D",
            )
        except (sqlite3.Error, ValueError):
            snapshot = None
        if snapshot is not None:
            return snapshot
    return None

def _detail_header(
    *,
    signal: SignalRecord | None,
    outcomes: tuple[OutcomeRecord, ...],
) -> tuple[dict[str, str], ...]:
    latest_outcome = outcomes[-1] if outcomes else None
    return (
        {"label": "Symbol", "value": signal.symbol if signal else "-"},
        {"label": "Market Date", "value": _market_date(signal) if signal else "-"},
        {"label": "Snapshot ID", "value": _snapshot_id(signal)},
        {"label": "Brain Version", "value": _brain_version(signal) if signal else "-"},
        {"label": "Outcome Status", "value": _format_latest_outcome(latest_outcome)},
    )

def _v2_detail_header(
    *,
    snapshot: DailyResearchSnapshotRecord,
    latest_outcome: OutcomeRecord | None,
) -> tuple[dict[str, str], ...]:
    canonical = snapshot.canonical_snapshot
    return (
        {"label": "Symbol", "value": snapshot.symbol or "-"},
        {"label": "Market Date", "value": snapshot.market_date or "-"},
        {"label": "Snapshot ID", "value": _v2_snapshot_id(snapshot)},
        {"label": "Brain Version", "value": _v2_brain_version(canonical)},
        {"label": "Outcome Status", "value": _format_latest_outcome(latest_outcome)},
    )

def _empty_detail_groups() -> tuple[dict[str, object], ...]:
    return (
        _detail_group("Market", ()),
        _detail_group("Indicators", ()),
        _detail_group("Context", ()),
        _detail_group("Prediction", ()),
        _detail_group("Strategy", ()),
    )


def _detail_group(
    title: str,
    items: tuple[tuple[str, object], ...],
) -> dict[str, object]:
    return {
        "title": title,
        "items": tuple(
            {"label": label, "value": _format_detail_value(value)}
            for label, value in items
        )
        or ({"label": "Status", "value": "-"},),
    }


def _snapshot_payload_v2_tabs(canonical: dict[str, Any]) -> tuple[dict[str, object], ...]:
    return (
        _payload_section_tab(canonical, "Identity", "identity"),
        _payload_section_tab(canonical, "Provenance", "provenance"),
        _payload_section_tab(canonical, "Input", "input"),
        _payload_section_tab(canonical, "Analysis", "analysis"),
        _payload_section_tab(canonical, "Context", "context"),
        _payload_section_tab(canonical, "Strategy", "strategy"),
        _payload_section_tab(canonical, "Diagnostics", "diagnostics"),
        _payload_section_tab(canonical, "Compatibility", "compatibility"),
    )


def _payload_section_tab(
    canonical: dict[str, Any],
    title: str,
    section_name: str,
) -> dict[str, object]:
    return _detail_group(title, _dict_items(_v2_section(canonical, section_name)))


def _dict_items(value: dict[str, Any]) -> tuple[tuple[str, object], ...]:
    return tuple(
        (_format_label(str(key)), value[key])
        for key in sorted(value)
        if key not in {"indicators", "prediction", "prediction_summary"}
    )


def _nested_dict(value: dict[str, Any], key: str) -> dict[str, Any]:
    candidate = value.get(key)
    return candidate if isinstance(candidate, dict) else {}

def _v2_snapshot_id(snapshot: DailyResearchSnapshotRecord) -> str:
    canonical = snapshot.canonical_snapshot
    identity = canonical.get("identity")
    if isinstance(identity, dict):
        value = str(
            identity.get("snapshot_id")
            or identity.get("legacy_snapshot_id")
            or ""
        ).strip()
        if value:
            return value
    compatibility = canonical.get("compatibility")
    if isinstance(compatibility, dict):
        value = str(compatibility.get("legacy_snapshot_id") or "").strip()
        if value:
            return value
    return snapshot.snapshot_record_id or "-"


def _is_snapshot_payload_v2(canonical: dict[str, Any]) -> bool:
    identity = canonical.get("identity")
    return bool(
        isinstance(identity, dict)
        and identity.get("payload_schema_version") == "snapshot_payload_v2"
    )


def _v2_brain_version(canonical: dict[str, Any]) -> str:
    identity = canonical.get("identity")
    if isinstance(identity, dict):
        for key in ("pipeline_version", "pipeline_name", "source"):
            value = str(identity.get(key) or "").strip()
            if value:
                return value
    brain = canonical.get("brain")
    if isinstance(brain, dict):
        metadata = brain.get("metadata")
        if isinstance(metadata, dict):
            for key in ("brain_version", "version"):
                value = str(metadata.get(key) or "").strip()
                if value:
                    return value
    provenance = canonical.get("provenance")
    if isinstance(provenance, dict):
        adapter_versions = provenance.get("adapter_versions")
        if isinstance(adapter_versions, dict):
            for key in ("canonical_result", "canonical_brain", "builder"):
                value = str(adapter_versions.get(key) or "").strip()
                if value:
                    return value
    return "-"


def _v2_section(canonical: dict[str, Any], name: str) -> dict[str, Any]:
    section = canonical.get(name)
    return section if isinstance(section, dict) else {}


def _v2_indicators(canonical: dict[str, Any]) -> dict[str, Any]:
    brain = _v2_section(canonical, "brain")
    if not brain:
        brain = _v2_section(canonical, "analysis")
    snapshot = brain.get("snapshot")
    if not isinstance(snapshot, dict):
        snapshot = brain.get("brain_snapshot")
    if not isinstance(snapshot, dict):
        return {}
    indicators = snapshot.get("indicators")
    return indicators if isinstance(indicators, dict) else snapshot


def _v2_prediction(canonical: dict[str, Any]) -> dict[str, Any]:
    prediction = _v2_section(canonical, "prediction")
    if prediction:
        return prediction
    brain = _v2_section(canonical, "brain")
    if not brain:
        brain = _v2_section(canonical, "analysis")
    summary = brain.get("prediction_summary")
    if isinstance(summary, dict):
        return summary
    display = _v2_section(canonical, "display_summary")
    compact = display.get("compact_prediction")
    return compact if isinstance(compact, dict) else {}

def _prediction_summary(signal: SignalRecord) -> dict[str, Any]:
    for source in (signal.context_summary, signal.strategy_summary):
        for key in ("prediction_summary", "prediction"):
            candidate = source.get(key)
            if isinstance(candidate, dict):
                return candidate
    return {}


def _market_date(signal: SignalRecord | None) -> str:
    if signal is None:
        return "-"
    return (
        signal.snapshot_reference.snapshot_date
        or signal.signal_date
        or "-"
    )


def _candidate_market_dates(signal: SignalRecord) -> tuple[str, ...]:
    return tuple(
        dict.fromkeys(
            value
            for value in (
                str(signal.signal_date or "").strip(),
                str(signal.snapshot_reference.snapshot_date or "").strip(),
            )
            if value
        )
    )


def _snapshot_id(signal: SignalRecord | None) -> str:
    if signal is None:
        return "-"
    return signal.snapshot_reference.snapshot_id or signal.signal_id or "-"


def _brain_version(signal: SignalRecord | None) -> str:
    if signal is None:
        return "-"
    for source in (signal.context_summary, signal.strategy_summary):
        for key in ("brain_version", "brainVersion", "version"):
            value = source.get(key)
            if value:
                return str(value)
    return "-"


def _format_detail_value(value: object) -> str:
    if value is None or value == "":
        return "-"
    if isinstance(value, float):
        return f"{value:.4f}".rstrip("0").rstrip(".")
    if isinstance(value, (dict, list, tuple)):
        return _json_pretty(value)
    return str(value)


def _json_pretty(value: object) -> str:
    return json.dumps(value, indent=2, sort_keys=True, default=str)


def _has_table(connection: sqlite3.Connection, table_name: str) -> bool:
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


def _normalize_symbol(symbol: str | None) -> str:
    return str(symbol or "").strip().upper()


def _format_percent(value: float | None) -> str:
    if value is None:
        return "-"
    return f"{float(value):.2f}%"


def _format_label(value: str) -> str:
    safe_value = str(value or "").strip()
    if not safe_value:
        return "-"
    return safe_value.replace("_", " ").replace("-", " ").title()


def _signal_type_value(signal_type: SignalType | str) -> str:
    if isinstance(signal_type, SignalType):
        return signal_type.value
    return str(signal_type or SignalType.UNKNOWN.value)


def _outcome_status_value(outcome_status: OutcomeStatus | str) -> str:
    if isinstance(outcome_status, OutcomeStatus):
        return outcome_status.value
    return str(outcome_status or OutcomeStatus.UNKNOWN.value)
