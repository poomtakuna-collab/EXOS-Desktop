from __future__ import annotations

from collections.abc import Iterable as IterableABC
from dataclasses import dataclass
from typing import Iterable, Mapping

from src.backtest.result_engine import BacktestResultV1, generate_backtest_result
from src.backtest.trade_outcome import TradeOutcomeV1
from src.backtest.trade_simulator import simulate_trade


@dataclass(frozen=True)
class BacktestRunV1:
    trades: list[TradeOutcomeV1]
    result: BacktestResultV1


def run_backtest_v1(
    trade_rows: Iterable[Mapping[str, object] | None] | object | None,
) -> BacktestRunV1:
    trades = [
        simulate_trade(_trade_setup(row), _future_rows(row))
        for row in _safe_iterable(trade_rows)
    ]
    result = generate_backtest_result(
        trade.gross_return_percent for trade in trades
    )
    return BacktestRunV1(trades=trades, result=result)


def _trade_setup(row: Mapping[str, object] | None) -> Mapping[str, object]:
    normalized_row = row if isinstance(row, Mapping) else {}
    nested_setup = normalized_row.get("trade_setup")
    if isinstance(nested_setup, Mapping):
        return nested_setup
    nested_setup = normalized_row.get("setup")
    if isinstance(nested_setup, Mapping):
        return nested_setup
    return normalized_row


def _future_rows(
    row: Mapping[str, object] | None,
) -> Iterable[Mapping[str, object] | None]:
    normalized_row = row if isinstance(row, Mapping) else {}
    future_rows = normalized_row.get("future_rows")
    if isinstance(future_rows, list):
        return future_rows
    return []


def _safe_iterable(value: object) -> IterableABC[object]:
    if isinstance(value, IterableABC):
        return value
    return []
