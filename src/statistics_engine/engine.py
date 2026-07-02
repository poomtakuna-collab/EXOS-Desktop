from __future__ import annotations

from collections import defaultdict
from dataclasses import asdict, dataclass
import json
import sqlite3
from statistics import median
from typing import Any, Mapping, Sequence


@dataclass(frozen=True)
class SnapshotFeatureOutcome:
    snapshot_record_id: str
    symbol: str
    market_date: str
    feature_buckets: tuple[tuple[str, str], ...]
    forward_return_5d: float
    forward_return_10d: float
    forward_return_20d: float
    max_gain_10d: float
    max_drawdown_10d: float

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class FeatureBucketStats:
    feature_name: str
    bucket: str
    sample_count: int
    win_rate: float
    average_return: float
    median_return: float
    average_max_gain: float
    average_drawdown: float
    expectancy: float

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class StatisticsScopeSummary:
    scope_mode: str
    symbol_count: int
    symbols_analyzed: tuple[str, ...]
    total_snapshots: int
    total_outcomes: int
    skipped_snapshots: int
    date_range: tuple[str, str] | None
    snapshot_count_per_symbol: tuple[tuple[str, int], ...]

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class StatisticsEngineReport:
    snapshot_count: int
    outcome_count: int
    skipped_count: int
    feature_stats: tuple[FeatureBucketStats, ...]
    outcomes: tuple[SnapshotFeatureOutcome, ...] = ()
    scope: StatisticsScopeSummary | None = None

    def to_dict(self) -> dict[str, object]:
        return {
            "snapshot_count": self.snapshot_count,
            "outcome_count": self.outcome_count,
            "skipped_count": self.skipped_count,
            "feature_stats": tuple(item.to_dict() for item in self.feature_stats),
            "outcomes": tuple(item.to_dict() for item in self.outcomes),
            "scope": self.scope.to_dict() if self.scope is not None else None,
        }


def build_statistics_report_from_connection(
    connection: sqlite3.Connection,
    *,
    min_sample_count: int = 1,
    scope_mode: str = "all_symbols",
    current_symbol: str | None = None,
) -> StatisticsEngineReport:
    snapshots = _filter_snapshots_for_scope(
        _load_snapshot_payloads(connection),
        scope_mode=scope_mode,
        current_symbol=current_symbol,
    )
    rows_by_symbol = {
        symbol: _load_ohlcv_rows(connection, symbol)
        for symbol in sorted({snapshot["symbol"] for snapshot in snapshots})
    }
    return build_statistics_report(
        snapshots=snapshots,
        ohlcv_rows_by_symbol=rows_by_symbol,
        min_sample_count=min_sample_count,
        scope_mode=scope_mode,
        current_symbol=current_symbol,
    )


def build_statistics_report(
    *,
    snapshots: Sequence[Mapping[str, Any]],
    ohlcv_rows_by_symbol: Mapping[str, Sequence[Mapping[str, Any]]],
    min_sample_count: int = 1,
    scope_mode: str = "all_symbols",
    current_symbol: str | None = None,
) -> StatisticsEngineReport:
    scoped_snapshots = _filter_snapshots_for_scope(
        snapshots,
        scope_mode=scope_mode,
        current_symbol=current_symbol,
    )
    outcomes: list[SnapshotFeatureOutcome] = []
    skipped = 0
    for snapshot in scoped_snapshots:
        payload = _snapshot_payload(snapshot)
        identity = _section(payload, "identity")
        symbol = _text(snapshot.get("symbol") or identity.get("symbol")).upper()
        market_date = _text(snapshot.get("market_date") or identity.get("market_date"))
        future_rows = _future_rows_for_date(
            ohlcv_rows_by_symbol.get(symbol, ()),
            market_date=market_date,
            horizon=20,
        )
        if len(future_rows) < 20:
            skipped += 1
            continue
        outcome = calculate_forward_outcome(
            payload,
            future_rows=future_rows,
            snapshot_record_id=_text(snapshot.get("snapshot_record_id")),
            symbol=symbol,
            market_date=market_date,
        )
        if outcome is None:
            skipped += 1
            continue
        outcomes.append(outcome)

    return StatisticsEngineReport(
        snapshot_count=len(scoped_snapshots),
        outcome_count=len(outcomes),
        skipped_count=skipped,
        feature_stats=_aggregate_feature_stats(
            outcomes,
            min_sample_count=max(int(min_sample_count), 1),
        ),
        outcomes=tuple(outcomes),
        scope=_scope_summary(
            scoped_snapshots,
            outcomes=outcomes,
            skipped_count=skipped,
            scope_mode=scope_mode,
            current_symbol=current_symbol,
        ),
    )


def calculate_forward_outcome(
    payload: Mapping[str, Any],
    *,
    future_rows: Sequence[Mapping[str, Any]],
    snapshot_record_id: str = "",
    symbol: str = "",
    market_date: str = "",
) -> SnapshotFeatureOutcome | None:
    if len(future_rows) < 20:
        return None
    entry = _entry_close(payload)
    if entry is None or entry == 0:
        return None
    first_10 = future_rows[:10]
    return SnapshotFeatureOutcome(
        snapshot_record_id=snapshot_record_id,
        symbol=symbol,
        market_date=market_date,
        feature_buckets=extract_feature_buckets(payload),
        forward_return_5d=_return_pct(entry, _number(future_rows[4].get("close"))),
        forward_return_10d=_return_pct(entry, _number(future_rows[9].get("close"))),
        forward_return_20d=_return_pct(entry, _number(future_rows[19].get("close"))),
        max_gain_10d=_return_pct(entry, max(_number(row.get("high")) for row in first_10)),
        max_drawdown_10d=_return_pct(entry, min(_number(row.get("low")) for row in first_10)),
    )


def extract_feature_buckets(payload: Mapping[str, Any]) -> tuple[tuple[str, str], ...]:
    analysis = _section(payload, "analysis")
    poom = _section(analysis, "poom_combo")
    brain = _section(analysis, "brain_snapshot")
    indicators = _section(brain, "indicators")
    context = _section(payload, "context")
    rows = _section(_section(payload, "input"), "ohlcv_window").get("rows")
    last_row = rows[-1] if isinstance(rows, list) and rows and isinstance(rows[-1], Mapping) else {}
    close = _number(last_row.get("close"))

    buckets = (
        ("poom_ew", _direction_value_bucket(poom.get("ew_norm"))),
        ("volume_pressure", _direction_value_bucket(poom.get("volume_pressure"))),
        ("poom_trend_slope", _direction_value_bucket(poom.get("trend_slope"))),
        ("poom_squeeze", _poom_squeeze_bucket(poom)),
        ("bos_choch", _poom_structure_bucket(poom)),
        ("ema_alignment", _text(indicators.get("ema_alignment")) or "unknown"),
        ("price_vs_ema20", _price_vs_level(close, indicators.get("ema20"))),
        ("price_vs_ema50", _price_vs_level(close, indicators.get("ema50"))),
        ("price_vs_ema200", _price_vs_level(close, indicators.get("ema200"))),
        ("trend_state", _state_bucket(_section(brain, "trend"))),
        ("market_structure", _state_bucket(_section(brain, "market_structure"))),
        (
            "support_resistance_distance",
            _support_resistance_distance_bucket(_section(context, "support_resistance")),
        ),
    )
    return tuple((feature, bucket) for feature, bucket in buckets if bucket)


def _aggregate_feature_stats(
    outcomes: Sequence[SnapshotFeatureOutcome],
    *,
    min_sample_count: int,
) -> tuple[FeatureBucketStats, ...]:
    grouped: dict[tuple[str, str], list[SnapshotFeatureOutcome]] = defaultdict(list)
    for outcome in outcomes:
        for feature_bucket in outcome.feature_buckets:
            grouped[feature_bucket].append(outcome)

    stats = [
        _stats_for_bucket(feature, bucket, values)
        for (feature, bucket), values in grouped.items()
        if len(values) >= min_sample_count
    ]
    return tuple(sorted(stats, key=lambda item: (item.feature_name, item.bucket)))


def _stats_for_bucket(
    feature_name: str,
    bucket: str,
    outcomes: Sequence[SnapshotFeatureOutcome],
) -> FeatureBucketStats:
    returns = [outcome.forward_return_10d for outcome in outcomes]
    gains = [outcome.max_gain_10d for outcome in outcomes]
    drawdowns = [outcome.max_drawdown_10d for outcome in outcomes]
    winning = [value for value in returns if value > 0]
    losing = [value for value in returns if value <= 0]
    return FeatureBucketStats(
        feature_name=feature_name,
        bucket=bucket,
        sample_count=len(outcomes),
        win_rate=round(len(winning) / len(outcomes) * 100, 4),
        average_return=round(sum(returns) / len(returns), 4),
        median_return=round(float(median(returns)), 4),
        average_max_gain=round(sum(gains) / len(gains), 4),
        average_drawdown=round(sum(drawdowns) / len(drawdowns), 4),
        expectancy=round(_expectancy(winning, losing, len(outcomes)), 4),
    )


def _load_snapshot_payloads(connection: sqlite3.Connection) -> tuple[dict[str, Any], ...]:
    if not _table_exists(connection, "daily_research_snapshots"):
        return ()
    rows = connection.execute(
        """
        SELECT snapshot_record_id, symbol, market_date, timeframe, canonical_snapshot_json
        FROM daily_research_snapshots
        ORDER BY symbol ASC, market_date ASC, timeframe ASC
        """
    ).fetchall()
    output: list[dict[str, Any]] = []
    for row in rows:
        payload = json.loads(row[4])
        if not isinstance(payload, dict):
            continue
        if _section(payload, "identity").get("payload_schema_version") != "snapshot_payload_v2":
            continue
        output.append(
            {
                "snapshot_record_id": row[0],
                "symbol": row[1],
                "market_date": row[2],
                "timeframe": row[3],
                "payload": payload,
            }
        )
    return tuple(output)


def _load_ohlcv_rows(
    connection: sqlite3.Connection,
    symbol: str,
) -> tuple[dict[str, Any], ...]:
    if not _table_exists(connection, "ohlcv_daily"):
        return ()
    cursor = connection.execute(
        """
        SELECT date, open, high, low, close, volume
        FROM ohlcv_daily
        WHERE symbol = ?
        ORDER BY date ASC
        """,
        (symbol,),
    )
    return tuple(
        {
            "date": row[0],
            "open": row[1],
            "high": row[2],
            "low": row[3],
            "close": row[4],
            "volume": row[5],
        }
        for row in cursor.fetchall()
    )


def _filter_snapshots_for_scope(
    snapshots: Sequence[Mapping[str, Any]],
    *,
    scope_mode: str,
    current_symbol: str | None,
) -> tuple[Mapping[str, Any], ...]:
    safe_snapshots = tuple(snapshots)
    safe_mode = _scope_mode(scope_mode, current_symbol)
    if safe_mode != "current_symbol":
        return safe_snapshots
    symbol = _text(current_symbol).upper()
    if not symbol:
        return ()
    return tuple(
        snapshot
        for snapshot in safe_snapshots
        if _snapshot_symbol(snapshot) == symbol
    )


def _scope_summary(
    snapshots: Sequence[Mapping[str, Any]],
    *,
    outcomes: Sequence[SnapshotFeatureOutcome],
    skipped_count: int,
    scope_mode: str,
    current_symbol: str | None,
) -> StatisticsScopeSummary:
    symbols = tuple(sorted({_snapshot_symbol(snapshot) for snapshot in snapshots if _snapshot_symbol(snapshot)}))
    dates = tuple(
        sorted(
            date
            for date in (_snapshot_market_date(snapshot) for snapshot in snapshots)
            if date
        )
    )
    counts: dict[str, int] = defaultdict(int)
    for snapshot in snapshots:
        symbol = _snapshot_symbol(snapshot)
        if symbol:
            counts[symbol] += 1
    return StatisticsScopeSummary(
        scope_mode=_scope_mode(scope_mode, current_symbol),
        symbol_count=len(symbols),
        symbols_analyzed=symbols,
        total_snapshots=len(snapshots),
        total_outcomes=len(outcomes),
        skipped_snapshots=skipped_count,
        date_range=(dates[0], dates[-1]) if dates else None,
        snapshot_count_per_symbol=tuple(sorted(counts.items())),
    )


def _scope_mode(scope_mode: str, current_symbol: str | None) -> str:
    if str(scope_mode or "").strip() == "current_symbol" and _text(current_symbol):
        return "current_symbol"
    return "all_symbols"


def _snapshot_symbol(snapshot: Mapping[str, Any]) -> str:
    payload = _snapshot_payload(snapshot)
    identity = _section(payload, "identity")
    return _text(snapshot.get("symbol") or identity.get("symbol")).upper()


def _snapshot_market_date(snapshot: Mapping[str, Any]) -> str:
    payload = _snapshot_payload(snapshot)
    identity = _section(payload, "identity")
    return _text(snapshot.get("market_date") or identity.get("market_date"))


def _future_rows_for_date(
    rows: Sequence[Mapping[str, Any]] | None,
    *,
    market_date: str,
    horizon: int,
) -> tuple[Mapping[str, Any], ...]:
    safe_rows = tuple(rows or ())
    for index, row in enumerate(safe_rows):
        if _text(row.get("date")) == market_date:
            return safe_rows[index + 1 : index + 1 + horizon]
    return ()


def _snapshot_payload(snapshot: Mapping[str, Any]) -> Mapping[str, Any]:
    payload = snapshot.get("payload")
    if isinstance(payload, Mapping):
        return payload
    return snapshot


def _entry_close(payload: Mapping[str, Any]) -> float | None:
    window = _section(_section(payload, "input"), "ohlcv_window")
    rows = window.get("rows")
    if isinstance(rows, list) and rows and isinstance(rows[-1], Mapping):
        close = _number(rows[-1].get("close"))
        if close is not None:
            return close
    return None


def _direction_value_bucket(value: object) -> str:
    number = _number(value)
    if number is None:
        return "unknown"
    direction = "positive" if number > 0 else "negative" if number < 0 else "neutral"
    magnitude = abs(number)
    if magnitude < 10:
        value_bucket = "0_to_10"
    elif magnitude < 25:
        value_bucket = "10_to_25"
    elif magnitude < 50:
        value_bucket = "25_to_50"
    else:
        value_bucket = "50_plus"
    return f"{direction}:{value_bucket}"


def _poom_squeeze_bucket(poom: Mapping[str, Any]) -> str:
    if poom.get("squeeze_up"):
        return "release_up"
    if poom.get("squeeze_down"):
        return "release_down"
    if poom.get("in_squeeze"):
        return "in_squeeze"
    return "none"


def _poom_structure_bucket(poom: Mapping[str, Any]) -> str:
    if poom.get("choch_up"):
        return "choch_up"
    if poom.get("choch_down"):
        return "choch_down"
    if poom.get("bos_up"):
        return "bos_up"
    if poom.get("bos_down"):
        return "bos_down"
    direction = _number(poom.get("msb_dir"))
    if direction is not None and direction > 0:
        return "bullish"
    if direction is not None and direction < 0:
        return "bearish"
    return "neutral"


def _price_vs_level(price: float | None, level: object) -> str:
    value = _number(level)
    if price is None or value is None or value == 0:
        return "unknown"
    if price > value:
        return "above"
    if price < value:
        return "below"
    return "at"


def _state_bucket(value: Mapping[str, Any]) -> str:
    for key in ("state", "structure_state", "trend", "direction", "status"):
        text = _text(value.get(key))
        if text:
            return text
    return "unknown"


def _support_resistance_distance_bucket(value: Mapping[str, Any]) -> str:
    support = _number(value.get("support_distance_pct"))
    resistance = _number(value.get("resistance_distance_pct"))
    candidates = [
        ("support", abs(support)) for support in [support] if support is not None
    ] + [
        ("resistance", abs(resistance))
        for resistance in [resistance]
        if resistance is not None
    ]
    if not candidates:
        return "unknown"
    side, distance = min(candidates, key=lambda item: item[1])
    return f"{side}:{_distance_bucket(distance)}"


def _distance_bucket(value: float) -> str:
    if value < 2:
        return "0_to_2"
    if value < 5:
        return "2_to_5"
    if value < 10:
        return "5_to_10"
    return "10_plus"


def _return_pct(entry: float, exit_price: float | None) -> float:
    if exit_price is None or entry == 0:
        return 0.0
    return round(((exit_price - entry) / entry) * 100, 4)


def _expectancy(winning: Sequence[float], losing: Sequence[float], total: int) -> float:
    if total <= 0:
        return 0.0
    win_rate = len(winning) / total
    loss_rate = len(losing) / total
    average_win = sum(winning) / len(winning) if winning else 0.0
    average_loss = abs(sum(losing) / len(losing)) if losing else 0.0
    return (average_win * win_rate) - (average_loss * loss_rate)


def _section(value: Mapping[str, Any], key: str) -> Mapping[str, Any]:
    candidate = value.get(key)
    return candidate if isinstance(candidate, Mapping) else {}


def _number(value: object) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _text(value: object) -> str:
    return str(value or "").strip()


def _table_exists(connection: sqlite3.Connection, table_name: str) -> bool:
    row = connection.execute(
        """
        SELECT 1
        FROM sqlite_master
        WHERE type = 'table'
          AND name = ?
        LIMIT 1
        """,
        (table_name,),
    ).fetchone()
    return row is not None
