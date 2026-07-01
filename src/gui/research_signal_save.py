from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import sqlite3
from typing import Protocol

from src.canonical_result import CanonicalResultV1
from src.signal_ledger import SignalRecord, build_signal_record_from_canonical_result
from src.signal_ledger.sqlite_repository import SQLiteSignalLedgerRepository


DEFAULT_SIGNAL_LEDGER_DATABASE_PATH = Path("database") / "exos.db"


class SignalRepository(Protocol):
    def save_signal(self, signal: SignalRecord) -> SignalRecord:
        pass

    def load_signal(self, signal_id: str) -> SignalRecord | None:
        pass


@dataclass(frozen=True)
class ManualSignalSaveResult:
    status: str
    message: str
    signal: SignalRecord | None = None

    @property
    def saved(self) -> bool:
        return self.status == "saved"

    @property
    def duplicate(self) -> bool:
        return self.status == "duplicate"


def save_manual_signal_candidate(
    canonical_result: CanonicalResultV1 | None,
    *,
    repository: SignalRepository | None = None,
    database_path: Path | str | None = None,
) -> ManualSignalSaveResult:
    if not isinstance(canonical_result, CanonicalResultV1):
        return ManualSignalSaveResult(
            status="unavailable",
            message="No research analysis is available to save.",
        )

    signal = _with_signal_id(build_signal_record_from_canonical_result(canonical_result))
    if repository is not None:
        return _save_with_repository(repository, signal)

    path = Path(database_path or DEFAULT_SIGNAL_LEDGER_DATABASE_PATH)
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        connection = sqlite3.connect(path)
    except sqlite3.Error as error:
        return ManualSignalSaveResult(
            status="error",
            message=f"Unable to save signal: {error}",
        )

    try:
        ledger_repository = SQLiteSignalLedgerRepository(connection)
        ledger_repository.initialize_schema()
        return _save_with_repository(ledger_repository, signal)
    except (sqlite3.Error, ValueError) as error:
        return ManualSignalSaveResult(
            status="error",
            message=f"Unable to save signal: {error}",
        )
    finally:
        connection.close()


def _save_with_repository(
    repository: SignalRepository,
    signal: SignalRecord,
) -> ManualSignalSaveResult:
    try:
        existing = repository.load_signal(signal.signal_id)
        if existing is not None:
            return ManualSignalSaveResult(
                status="duplicate",
                message=f"Signal already saved: {signal.signal_id}",
                signal=existing,
            )
        saved_signal = repository.save_signal(signal)
    except (RuntimeError, ValueError, sqlite3.Error) as error:
        return ManualSignalSaveResult(
            status="error",
            message=f"Unable to save signal: {error}",
        )

    return ManualSignalSaveResult(
        status="saved",
        message=f"Signal saved: {saved_signal.signal_id}",
        signal=saved_signal,
    )


def _with_signal_id(signal: SignalRecord) -> SignalRecord:
    if signal.signal_id:
        return signal
    signal_id = _signal_id(signal)
    return SignalRecord(
        signal_id=signal_id,
        symbol=signal.symbol,
        signal_date=signal.signal_date,
        snapshot_reference=signal.snapshot_reference,
        context_summary=signal.context_summary,
        strategy_summary=signal.strategy_summary,
        signal_type=signal.signal_type,
        confidence=signal.confidence,
        notes=signal.notes,
    )


def _signal_id(signal: SignalRecord) -> str:
    payload = signal.to_dict()
    payload["signal_id"] = ""
    digest = hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()[:16]
    symbol = _slug(signal.symbol or "unknown")
    signal_date = _slug(signal.signal_date or signal.snapshot_reference.snapshot_date or "undated")
    timeframe = _slug(signal.snapshot_reference.timeframe or "tf")
    return f"signal:{symbol}:{signal_date}:{timeframe}:{digest}"


def _slug(value: str) -> str:
    safe = "".join(
        character.lower()
        if character.isalnum()
        else "-"
        for character in str(value).strip()
    )
    collapsed = "-".join(part for part in safe.split("-") if part)
    return collapsed or "unknown"
