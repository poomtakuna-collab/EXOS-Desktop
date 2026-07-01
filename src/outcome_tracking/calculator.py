from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from src.outcome_tracking.contracts import OutcomeRecord, OutcomeStatus


def calculate_outcome_record(
    *,
    symbol: str = "",
    signal_date: str = "",
    entry_price: Any = None,
    future_rows: Sequence[Mapping[str, Any]] | None = None,
    horizon_days: Any = None,
    target_price: Any = None,
    stop_price: Any = None,
    notes: Sequence[str] | None = None,
) -> OutcomeRecord:
    """Calculate a deterministic outcome record from future OHLCV rows."""
    safe_notes = _notes(notes)
    entry = _positive_number(entry_price)
    horizon = _positive_int(horizon_days)
    rows = _valid_rows(future_rows)

    if entry is None:
        return OutcomeRecord(
            symbol=symbol,
            signal_date=signal_date,
            horizon_days=horizon,
            entry_price=None,
            outcome_status=OutcomeStatus.UNKNOWN,
            notes=safe_notes + ("entry price unavailable",),
        )
    if horizon is None:
        return OutcomeRecord(
            symbol=symbol,
            signal_date=signal_date,
            horizon_days=None,
            entry_price=entry,
            outcome_status=OutcomeStatus.UNKNOWN,
            notes=safe_notes + ("horizon unavailable",),
        )
    if len(rows) < horizon:
        return OutcomeRecord(
            symbol=symbol,
            signal_date=signal_date,
            horizon_days=horizon,
            entry_price=entry,
            hit_target=_hit_target(entry, rows, target_price),
            hit_stop=_hit_stop(entry, rows, stop_price),
            outcome_status=OutcomeStatus.OPEN,
            notes=safe_notes + ("not enough future rows for horizon",),
        )

    evaluation_rows = rows[:horizon]
    horizon_row = evaluation_rows[-1]
    close = _positive_number(horizon_row.get("close"))
    if close is None:
        return OutcomeRecord(
            symbol=symbol,
            signal_date=signal_date,
            evaluation_date=_row_date(horizon_row),
            horizon_days=horizon,
            entry_price=entry,
            hit_target=_hit_target(entry, evaluation_rows, target_price),
            hit_stop=_hit_stop(entry, evaluation_rows, stop_price),
            outcome_status=OutcomeStatus.UNKNOWN,
            notes=safe_notes + ("horizon close unavailable",),
        )

    hit_target = _hit_target(entry, evaluation_rows, target_price)
    hit_stop = _hit_stop(entry, evaluation_rows, stop_price)
    return_pct = _pct_change(close, entry)

    return OutcomeRecord(
        symbol=symbol,
        signal_date=signal_date,
        evaluation_date=_row_date(horizon_row),
        horizon_days=horizon,
        entry_price=entry,
        close_price=close,
        return_pct=return_pct,
        max_runup_pct=_max_runup_pct(entry, evaluation_rows),
        max_drawdown_pct=_max_drawdown_pct(entry, evaluation_rows),
        hit_target=hit_target,
        hit_stop=hit_stop,
        outcome_status=_outcome_status(
            return_pct=return_pct,
            hit_target=hit_target,
            hit_stop=hit_stop,
        ),
        notes=safe_notes,
    )


def _outcome_status(
    *,
    return_pct: float,
    hit_target: bool | None,
    hit_stop: bool | None,
) -> OutcomeStatus:
    if hit_target and not hit_stop:
        return OutcomeStatus.TARGET_HIT
    if hit_stop and not hit_target:
        return OutcomeStatus.STOP_HIT
    if hit_target and hit_stop:
        return OutcomeStatus.TARGET_HIT if return_pct >= 0 else OutcomeStatus.STOP_HIT
    if return_pct > 0:
        return OutcomeStatus.POSITIVE
    if return_pct < 0:
        return OutcomeStatus.NEGATIVE
    return OutcomeStatus.NEUTRAL


def _hit_target(
    entry: float,
    rows: Sequence[Mapping[str, Any]],
    target_price: Any,
) -> bool | None:
    target = _positive_number(target_price)
    if target is None:
        return None
    if target >= entry:
        return any((_number(row.get("high")) or float("-inf")) >= target for row in rows)
    return any((_number(row.get("low")) or float("inf")) <= target for row in rows)


def _hit_stop(
    entry: float,
    rows: Sequence[Mapping[str, Any]],
    stop_price: Any,
) -> bool | None:
    stop = _positive_number(stop_price)
    if stop is None:
        return None
    if stop <= entry:
        return any((_number(row.get("low")) or float("inf")) <= stop for row in rows)
    return any((_number(row.get("high")) or float("-inf")) >= stop for row in rows)


def _max_runup_pct(entry: float, rows: Sequence[Mapping[str, Any]]) -> float | None:
    highs = [_positive_number(row.get("high")) for row in rows]
    valid_highs = [high for high in highs if high is not None]
    if not valid_highs:
        return None
    return round(max(_pct_change(max(valid_highs), entry), 0.0), 4)


def _max_drawdown_pct(entry: float, rows: Sequence[Mapping[str, Any]]) -> float | None:
    lows = [_positive_number(row.get("low")) for row in rows]
    valid_lows = [low for low in lows if low is not None]
    if not valid_lows:
        return None
    return round(min(_pct_change(min(valid_lows), entry), 0.0), 4)


def _pct_change(value: float, entry: float) -> float:
    return round((value - entry) / entry * 100, 4)


def _valid_rows(
    rows: Sequence[Mapping[str, Any]] | None,
) -> tuple[Mapping[str, Any], ...]:
    if not isinstance(rows, Sequence) or isinstance(rows, (str, bytes)):
        return ()
    return tuple(row for row in rows if isinstance(row, Mapping))


def _row_date(row: Mapping[str, Any]) -> str:
    value = row.get("date")
    return str(value or "")


def _positive_int(value: Any) -> int | None:
    number = _number(value)
    if number is None or number <= 0:
        return None
    return int(number)


def _positive_number(value: Any) -> float | None:
    number = _number(value)
    if number is None or number <= 0:
        return None
    return number


def _number(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _notes(notes: Sequence[str] | None) -> tuple[str, ...]:
    if not isinstance(notes, Sequence) or isinstance(notes, (str, bytes)):
        return ()
    return tuple(str(note) for note in notes if note is not None)
