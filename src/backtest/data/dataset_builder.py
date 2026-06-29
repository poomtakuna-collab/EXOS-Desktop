from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass, field
from typing import Any

from src.backtest.contracts import BacktestInput, SimulationConfig
from src.backtest.data.future_rows_loader import FutureRowsLoader, SQLiteFutureRowsLoader
from src.backtest.data.outcome_loader import OutcomeLoader, SQLiteOutcomeLoader
from src.backtest.data.snapshot_loader import (
    SQLiteSnapshotLoader,
    SnapshotLoader,
    SnapshotQuery,
)
from src.strategy import EntryQuality, RiskRating, StrategyResult, TradeGrade


@dataclass(frozen=True)
class BacktestDataset:
    inputs: list[BacktestInput]
    metadata: dict[str, Any] = field(default_factory=dict)
    skipped_records: list[dict[str, Any]] = field(default_factory=list)


class BacktestDatasetBuilder:
    """Public interface for constructing Backtest datasets from stored records."""

    def __init__(
        self,
        snapshot_loader: SnapshotLoader,
        outcome_loader: OutcomeLoader,
        future_rows_loader: FutureRowsLoader,
    ) -> None:
        self.snapshot_loader = snapshot_loader
        self.outcome_loader = outcome_loader
        self.future_rows_loader = future_rows_loader

    def build_dataset(
        self,
        query: SnapshotQuery,
        config: SimulationConfig,
    ) -> BacktestDataset:
        """Build a deterministic `BacktestDataset` for the supplied query/config.

        Implementations should coordinate snapshot, outcome, and future-row loaders
        to create `BacktestInput` records. They must not run replay, aggregate
        metrics, execute trades, call AI, or mutate source data.
        """
        raise NotImplementedError("BacktestDatasetBuilder.build_dataset is not implemented yet")


class SQLiteBacktestDatasetBuilder(BacktestDatasetBuilder):
    """SQLite-backed dataset builder composed from read-only Backtest loaders."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        super().__init__(
            snapshot_loader=SQLiteSnapshotLoader(connection),
            outcome_loader=SQLiteOutcomeLoader(connection),
            future_rows_loader=SQLiteFutureRowsLoader(connection),
        )

    def build_dataset(
        self,
        query: SnapshotQuery,
        config: SimulationConfig,
    ) -> BacktestDataset:
        snapshots = self.snapshot_loader.load_snapshots(query)
        snapshot_ids = [str(snapshot["snapshot_id"]) for snapshot in snapshots]
        outcomes = self.outcome_loader.load_outcomes(snapshot_ids)
        future_rows_by_snapshot = self.future_rows_loader.load_future_rows_for_snapshots(
            snapshots,
            config.horizon_days,
        )

        inputs: list[BacktestInput] = []
        skipped_records: list[dict[str, Any]] = []

        for sequence_number, snapshot in enumerate(snapshots, start=1):
            snapshot_id = str(snapshot["snapshot_id"])
            outcome = outcomes.get(snapshot_id, {})
            future_rows = future_rows_by_snapshot.get(snapshot_id, [])

            if not outcome:
                skipped_records.append(
                    _skipped_record(
                        sequence_number=sequence_number,
                        snapshot=snapshot,
                        reason="Missing outcome",
                    )
                )
            if len(future_rows) < config.horizon_days:
                skipped_records.append(
                    _skipped_record(
                        sequence_number=sequence_number,
                        snapshot=snapshot,
                        reason="Insufficient future rows",
                    )
                )

            inputs.append(
                BacktestInput(
                    snapshot=snapshot,
                    probability=_json_dict(snapshot.get("probability_json")),
                    prediction=_json_dict(snapshot.get("prediction_json")),
                    strategy_result=_strategy_result(snapshot.get("strategy_result_json")),
                    outcome=outcome,
                    future_rows=future_rows,
                )
            )

        return BacktestDataset(
            inputs=inputs,
            metadata={
                "snapshot_count": len(snapshots),
                "outcome_count": len(outcomes),
                "missing_outcome_count": sum(
                    1 for snapshot_id in snapshot_ids if snapshot_id not in outcomes
                ),
                "missing_future_rows_count": sum(
                    1
                    for snapshot_id in snapshot_ids
                    if len(future_rows_by_snapshot.get(snapshot_id, [])) < config.horizon_days
                ),
                "horizon_days": config.horizon_days,
            },
            skipped_records=skipped_records,
        )


def _json_dict(value: object) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    if not isinstance(value, str) or not value:
        return {}
    try:
        decoded = json.loads(value)
    except json.JSONDecodeError:
        return {}
    return decoded if isinstance(decoded, dict) else {}


def _strategy_result(value: object) -> StrategyResult:
    data = _json_dict(value)
    if not data:
        return _placeholder_strategy_result()

    return StrategyResult(
        strategy_score=_float_value(data.get("strategy_score")),
        trade_grade=_enum_value(TradeGrade, data.get("trade_grade"), TradeGrade.NEUTRAL),
        entry_quality=_enum_value(
            EntryQuality,
            data.get("entry_quality"),
            EntryQuality.ACCEPTABLE,
        ),
        risk_rating=_enum_value(RiskRating, data.get("risk_rating"), RiskRating.MEDIUM),
        reward_risk_estimate={
            "expected_reward_percent": _float_value(
                _json_dict(data.get("reward_risk_estimate")).get("expected_reward_percent")
            ),
            "expected_risk_percent": _float_value(
                _json_dict(data.get("reward_risk_estimate")).get("expected_risk_percent")
            ),
            "reward_risk_ratio": _optional_float(
                _json_dict(data.get("reward_risk_estimate")).get("reward_risk_ratio")
            ),
            "target_zone": _zone(
                _json_dict(data.get("reward_risk_estimate")).get("target_zone")
            ),
            "risk_zone": _zone(
                _json_dict(data.get("reward_risk_estimate")).get("risk_zone")
            ),
        },
        notes=[
            str(note)
            for note in data.get("notes", [])
            if isinstance(data.get("notes"), list)
        ],
    )


def _placeholder_strategy_result() -> StrategyResult:
    return StrategyResult(
        strategy_score=0.0,
        trade_grade=TradeGrade.NEUTRAL,
        entry_quality=EntryQuality.ACCEPTABLE,
        risk_rating=RiskRating.MEDIUM,
        reward_risk_estimate={
            "expected_reward_percent": 0.0,
            "expected_risk_percent": 0.0,
            "reward_risk_ratio": None,
            "target_zone": {"low": None, "high": None},
            "risk_zone": {"low": None, "high": None},
        },
        notes=["StrategyResult not persisted; deterministic placeholder used"],
    )


def _zone(value: object) -> dict[str, float | None]:
    data = _json_dict(value)
    return {
        "low": _optional_float(data.get("low")),
        "high": _optional_float(data.get("high")),
    }


def _enum_value(enum_type: Any, value: object, default: Any) -> Any:
    try:
        return enum_type(str(value))
    except ValueError:
        return default


def _float_value(value: object) -> float:
    return _optional_float(value) or 0.0


def _optional_float(value: object) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _skipped_record(
    sequence_number: int,
    snapshot: dict[str, Any],
    reason: str,
) -> dict[str, Any]:
    return {
        "sequence_number": sequence_number,
        "snapshot_id": snapshot.get("snapshot_id"),
        "symbol": snapshot.get("symbol"),
        "timeframe": snapshot.get("timeframe"),
        "date": snapshot.get("date"),
        "reason": reason,
    }
