from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import sqlite3
from typing import Protocol

from src.canonical_result import CanonicalResultV1
from src.daily_research_snapshot import SQLiteDailyResearchSnapshotRepository
from src.signal_ledger import SignalRecord, build_signal_record_from_canonical_result
from src.signal_ledger.sqlite_repository import SQLiteSignalLedgerRepository


DEFAULT_SIGNAL_LEDGER_DATABASE_PATH = Path("database") / "exos.db"


class SignalRepository(Protocol):
    def save_signal(self, signal: SignalRecord) -> SignalRecord:
        pass

    def load_signal(self, signal_id: str) -> SignalRecord | None:
        pass

    def list_signals(
        self,
        *,
        symbol: str | None = None,
    ) -> tuple[SignalRecord, ...]:
        pass


class DailyResearchSnapshotRepository(Protocol):
    def save_snapshot(
        self,
        canonical_result: CanonicalResultV1,
        *,
        signal_id: str | None = None,
        created_at: str = "",
    ) -> object:
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
    snapshot_repository: DailyResearchSnapshotRepository | None = None,
    database_path: Path | str | None = None,
) -> ManualSignalSaveResult:
    if not isinstance(canonical_result, CanonicalResultV1):
        return ManualSignalSaveResult(
            status="unavailable",
            message="No research analysis is available to save.",
        )

    signal = _with_signal_id(build_signal_record_from_canonical_result(canonical_result))
    if repository is not None:
        return _save_with_repository(
            repository,
            signal,
            canonical_result=canonical_result,
            snapshot_repository=snapshot_repository,
        )

    path = Path(database_path or DEFAULT_SIGNAL_LEDGER_DATABASE_PATH)
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        connection = sqlite3.connect(path)
    except sqlite3.Error as error:
        return ManualSignalSaveResult(
            status="error",
            message=f"Unable to save snapshot: {error}",
        )

    try:
        ledger_repository = SQLiteSignalLedgerRepository(connection)
        snapshot_repository = SQLiteDailyResearchSnapshotRepository(connection)
        ledger_repository.initialize_schema()
        snapshot_repository.initialize_schema()
        return _save_with_repository(
            ledger_repository,
            signal,
            canonical_result=canonical_result,
            snapshot_repository=snapshot_repository,
        )
    except (sqlite3.Error, ValueError) as error:
        return ManualSignalSaveResult(
            status="error",
            message=f"Unable to save snapshot: {error}",
        )
    finally:
        connection.close()


def _save_with_repository(
    repository: SignalRepository,
    signal: SignalRecord,
    *,
    canonical_result: CanonicalResultV1 | None = None,
    snapshot_repository: DailyResearchSnapshotRepository | None = None,
) -> ManualSignalSaveResult:
    try:
        existing_for_date = _existing_signal_for_candidate_market_date(repository, signal)
        if existing_for_date is not None:
            return ManualSignalSaveResult(
                status="duplicate",
                message=f"Snapshot already exists for {signal.symbol} on {_market_date(existing_for_date)}.",
                signal=existing_for_date,
            )
        existing = repository.load_signal(signal.signal_id)
        if existing is not None:
            return ManualSignalSaveResult(
                status="duplicate",
                message=f"Snapshot already saved: {signal.signal_id}",
                signal=existing,
            )
        if snapshot_repository is not None and canonical_result is not None:
            snapshot_repository.save_snapshot(
                canonical_result,
                signal_id=signal.signal_id,
                created_at=_market_date(signal),
            )
        saved_signal = repository.save_signal(signal)
    except (RuntimeError, ValueError, sqlite3.Error) as error:
        return ManualSignalSaveResult(
            status="error",
            message=f"Unable to save snapshot: {error}",
        )

    return ManualSignalSaveResult(
        status="saved",
        message=f"Snapshot saved: {saved_signal.signal_id}",
        signal=saved_signal,
    )


def signal_exists_for_market_date(
    repository: SignalRepository,
    *,
    symbol: str,
    market_date: str,
) -> SignalRecord | None:
    normalized_symbol = str(symbol or "").strip().upper()
    safe_market_date = str(market_date or "").strip()
    if not normalized_symbol or not safe_market_date:
        return None
    for existing in repository.list_signals(symbol=normalized_symbol):
        if _matches_market_date(existing, normalized_symbol, safe_market_date):
            return existing
    return None


def _existing_signal_for_candidate_market_date(
    repository: SignalRepository,
    signal: SignalRecord,
) -> SignalRecord | None:
    normalized_symbol = str(signal.symbol or "").strip().upper()
    if not normalized_symbol:
        return None
    candidate_dates = _market_dates(signal)
    if not candidate_dates:
        return None
    for existing in repository.list_signals(symbol=normalized_symbol):
        if str(existing.symbol or "").strip().upper() != normalized_symbol:
            continue
        if candidate_dates.intersection(_market_dates(existing)):
            return existing
    return None


def _matches_market_date(
    signal: SignalRecord,
    symbol: str,
    market_date: str,
) -> bool:
    if str(signal.symbol or "").strip().upper() != symbol:
        return False
    dates = {
        str(signal.signal_date or "").strip(),
        str(signal.snapshot_reference.snapshot_date or "").strip(),
    }
    return market_date in dates


def _market_dates(signal: SignalRecord) -> set[str]:
    return {
        value
        for value in (
            str(signal.signal_date or "").strip(),
            str(signal.snapshot_reference.snapshot_date or "").strip(),
        )
        if value
    }


def _market_date(signal: SignalRecord) -> str:
    return str(signal.signal_date or signal.snapshot_reference.snapshot_date or "").strip()


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
