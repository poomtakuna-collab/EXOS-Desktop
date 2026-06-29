# Backtest DB Design

Design document for DB-backed Backtest v1 persistence and loading.

This is a design-only document. DB-backed Backtest is not implemented yet.

## Purpose

DB-backed Backtest v1 should replay stored EXOS decision points from SQLite, persist reproducible run metadata, and preserve every evaluated or skipped snapshot in a deterministic audit trail.

It should connect the existing Market Learning database to the in-memory Backtest Framework without changing frozen Brain v1, Probability, Prediction, or Strategy scoring logic.

## Source Tables

Existing SQLite tables remain the source inputs:

- `snapshots`
- `outcomes`
- `ohlcv_daily`
- `patterns`, when probability generation needs stored historical evidence in a later orchestration path

The existing Market Learning schema owns `snapshots`, `outcomes`, and `patterns`.

The market data cache owns `ohlcv_daily`.

Backtest must read these tables without mutating them.

## Backtest-Owned Tables

DB-backed Backtest v1 should introduce Backtest-owned tables under the `src/backtest` boundary:

- `backtest_runs`
- `backtest_assumptions`
- `backtest_evaluations`
- `backtest_trade_results`

These tables should be initialized by a future Backtest schema module, not by the frozen Brain v1 modules.

## Contract: BacktestRun

`BacktestRun` represents one reproducible backtest execution.

Purpose:

- Identify a complete run.
- Store query scope and versions.
- Store aggregate count and performance metrics.
- Link assumptions and per-snapshot evaluations.

Suggested fields:

- `run_id`
- `run_name`
- `backtest_version`
- `strategy_version`
- `simulation_version`
- `source_database_id` or `source_database_path`
- `symbols_json`
- `timeframe`
- `start_date`
- `end_date`
- `snapshot_query_json`
- `attempted_trades`
- `completed_trades`
- `total_trades`
- `winning_trades`
- `losing_trades`
- `skipped_trades`
- `breakeven_trades`
- `win_rate`
- `average_return`
- `average_drawdown`
- `expectancy`
- `max_drawdown`
- `notes_json`
- `created_at`

Rules:

- `run_id` is generated once for a run and never reused.
- `total_trades` remains a backward-compatible completed-trade count.
- Aggregate counts must match the persisted `backtest_evaluations` and `backtest_trade_results`.
- Run creation must not fetch live data or call AI.

## Contract: BacktestAssumptions

`BacktestAssumptions` stores the reproducibility settings for a run.

Purpose:

- Explain exactly how replay was configured.
- Keep simulation assumptions separate from performance outcomes.

Suggested fields:

- `run_id`
- `horizon_days`
- `entry_price_source`
- `conservative_same_window_rule`
- `target_source`
- `stop_source`
- `probability_source`
- `prediction_source`
- `strategy_source`
- `fees_enabled`
- `slippage_enabled`
- `portfolio_enabled`
- `ai_enabled`
- `live_data_enabled`
- `broker_execution_enabled`
- `created_at`
- `assumptions_json`

Rules:

- For DB-backed Backtest v1, `fees_enabled`, `slippage_enabled`, `portfolio_enabled`, `ai_enabled`, `live_data_enabled`, and `broker_execution_enabled` must be false.
- `assumptions_json` may preserve extra details, but indexed or commonly queried settings should be columns.
- Assumptions should be written once per run before or with the first evaluation result.

## Contract: BacktestEvaluation

`BacktestEvaluation` represents the per-snapshot evaluation attempt inside a run.

Purpose:

- Preserve the selected snapshot order.
- Persist whether the snapshot was evaluated, skipped, or insufficient.
- Link each attempt to source snapshot and optional outcome data.

Suggested fields:

- `evaluation_id`
- `run_id`
- `sequence_number`
- `snapshot_id`
- `symbol`
- `timeframe`
- `snapshot_date`
- `outcome_id`
- `evaluation_status`
- `skip_reason`
- `has_outcome`
- `has_future_rows`
- `future_rows_count`
- `strategy_score`
- `trade_grade`
- `entry_quality`
- `risk_rating`
- `strategy_result_json`
- `probability_json`
- `prediction_json`
- `created_at`

Rules:

- Every selected snapshot should produce one `BacktestEvaluation`.
- Skipped and insufficient-data snapshots are persisted here instead of being silently dropped.
- `sequence_number` records deterministic replay order inside the run.
- `snapshot_id` must reference the existing `snapshots(snapshot_id)` value.
- `outcome_id` may be null when no outcome exists.

## Contract: BacktestTradeResult

`BacktestTradeResult` stores the deterministic replay result for an evaluation.

Purpose:

- Persist the output of `SimulationResult`.
- Keep completed, breakeven, open, skipped, and insufficient-data replay outcomes inspectable.

Suggested fields:

- `trade_result_id`
- `run_id`
- `evaluation_id`
- `snapshot_id`
- `simulation_status`
- `trade_outcome`
- `exit_reason`
- `entry_price`
- `exit_price`
- `return_percent`
- `max_drawdown_percent`
- `notes_json`
- `created_at`

Rules:

- Completed simulations have `simulation_status = SUCCESS`.
- Breakeven trades have `trade_outcome = BREAKEVEN` and count toward `completed_trades`, not wins or losses.
- Skipped and insufficient-data cases should be persisted either with a non-success `simulation_status` here, or as evaluation-only records if replay cannot produce a `SimulationResult`. The preferred v1 direction is to persist a `BacktestTradeResult` for every `BacktestEvaluation` so counts are auditable from one table.
- `evaluation_id` should be unique in `backtest_trade_results` for v1.

## Schema Direction

DDL direction:

```sql
CREATE TABLE IF NOT EXISTS backtest_runs (
    run_id TEXT PRIMARY KEY,
    run_name TEXT,
    backtest_version TEXT NOT NULL,
    strategy_version TEXT NOT NULL,
    simulation_version TEXT NOT NULL,
    source_database_id TEXT,
    source_database_path TEXT,
    symbols_json TEXT NOT NULL,
    timeframe TEXT,
    start_date TEXT,
    end_date TEXT,
    snapshot_query_json TEXT NOT NULL,
    attempted_trades INTEGER NOT NULL,
    completed_trades INTEGER NOT NULL,
    total_trades INTEGER NOT NULL,
    winning_trades INTEGER NOT NULL,
    losing_trades INTEGER NOT NULL,
    skipped_trades INTEGER NOT NULL,
    breakeven_trades INTEGER NOT NULL,
    win_rate REAL NOT NULL,
    average_return REAL NOT NULL,
    average_drawdown REAL NOT NULL,
    expectancy REAL NOT NULL,
    max_drawdown REAL NOT NULL,
    notes_json TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS backtest_assumptions (
    run_id TEXT PRIMARY KEY,
    horizon_days INTEGER NOT NULL,
    entry_price_source TEXT NOT NULL,
    conservative_same_window_rule INTEGER NOT NULL,
    target_source TEXT NOT NULL,
    stop_source TEXT NOT NULL,
    probability_source TEXT NOT NULL,
    prediction_source TEXT NOT NULL,
    strategy_source TEXT NOT NULL,
    fees_enabled INTEGER NOT NULL,
    slippage_enabled INTEGER NOT NULL,
    portfolio_enabled INTEGER NOT NULL,
    ai_enabled INTEGER NOT NULL,
    live_data_enabled INTEGER NOT NULL,
    broker_execution_enabled INTEGER NOT NULL,
    assumptions_json TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (run_id) REFERENCES backtest_runs(run_id)
);

CREATE TABLE IF NOT EXISTS backtest_evaluations (
    evaluation_id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL,
    sequence_number INTEGER NOT NULL,
    snapshot_id TEXT NOT NULL,
    symbol TEXT NOT NULL,
    timeframe TEXT NOT NULL,
    snapshot_date TEXT NOT NULL,
    outcome_id TEXT,
    evaluation_status TEXT NOT NULL,
    skip_reason TEXT,
    has_outcome INTEGER NOT NULL,
    has_future_rows INTEGER NOT NULL,
    future_rows_count INTEGER NOT NULL,
    strategy_score REAL,
    trade_grade TEXT,
    entry_quality TEXT,
    risk_rating TEXT,
    strategy_result_json TEXT,
    probability_json TEXT,
    prediction_json TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY (run_id) REFERENCES backtest_runs(run_id),
    FOREIGN KEY (snapshot_id) REFERENCES snapshots(snapshot_id),
    FOREIGN KEY (outcome_id) REFERENCES outcomes(outcome_id),
    UNIQUE (run_id, sequence_number),
    UNIQUE (run_id, snapshot_id)
);

CREATE TABLE IF NOT EXISTS backtest_trade_results (
    trade_result_id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL,
    evaluation_id TEXT NOT NULL,
    snapshot_id TEXT NOT NULL,
    simulation_status TEXT NOT NULL,
    trade_outcome TEXT NOT NULL,
    exit_reason TEXT NOT NULL,
    entry_price REAL,
    exit_price REAL,
    return_percent REAL,
    max_drawdown_percent REAL,
    notes_json TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (run_id) REFERENCES backtest_runs(run_id),
    FOREIGN KEY (evaluation_id) REFERENCES backtest_evaluations(evaluation_id),
    FOREIGN KEY (snapshot_id) REFERENCES snapshots(snapshot_id),
    UNIQUE (evaluation_id)
);
```

Required indexes:

- `backtest_runs(created_at)`
- `backtest_runs(timeframe, start_date, end_date)`
- `backtest_evaluations(run_id, sequence_number)`
- `backtest_evaluations(run_id, snapshot_id)`
- `backtest_evaluations(snapshot_id)`
- `backtest_trade_results(run_id, evaluation_id)`
- `backtest_trade_results(run_id, simulation_status, trade_outcome)`

## Loader Path

The DB-backed loading path should be:

```text
SnapshotQuery
-> SnapshotLoader.load_snapshots
-> OutcomeLoader.load_outcomes
-> FutureRowsLoader.load_future_rows
-> BacktestDatasetBuilder
-> BacktestInput records
-> run_backtest
-> build_backtest_report
-> persist BacktestRun / BacktestAssumptions / BacktestEvaluation / BacktestTradeResult
```

This path is not implemented yet.

## SnapshotLoader Read Rules

`SnapshotLoader` should read from `snapshots`.

Input:

- `SnapshotQuery`

Filters:

- `symbols`
- `timeframe`
- `start_date`
- `end_date`
- `minimum_exos_score`
- `trend_state`
- `squeeze_state`
- `market_structure_state`

Returned fields should include:

- `snapshot_id`
- `symbol`
- `timeframe`
- `date`
- `close`
- searchable score/state columns needed by reporting
- parsed or raw `snapshot_json`

Rules:

- Do not recalculate indicators.
- Do not update snapshots.
- Do not parse all snapshots when SQL filters can narrow the query.
- Preserve `snapshot_id` exactly as stored.

## OutcomeLoader Read Rules

`OutcomeLoader` should read from `outcomes`.

Input:

- one `snapshot_id`, or a deterministic list of `snapshot_id` values

Returned fields should include:

- `outcome_id`
- `snapshot_id`
- forward return fields
- max gain / max drawdown fields
- hit flags
- label

Rules:

- Outcomes are looked up by `snapshot_id`.
- Missing outcomes should be represented as missing data, not as a failed test or exception.
- Outcome loading must not calculate new outcomes.
- Outcome loading must not update existing outcomes.

## FutureRowsLoader Read Rules

`FutureRowsLoader` should read from the cached OHLCV table.

Initial direction:

- Use `ohlcv_daily` for `1D` backtests.
- Load rows for the same `symbol`.
- Select rows with `date > snapshot_date`.
- Order rows by `date ASC`.
- Limit to `horizon_days`.

Required returned fields:

- `date`
- `open`
- `high`
- `low`
- `close`
- `volume`

Rules:

- If fewer than `horizon_days` rows exist, the evaluation is insufficient data.
- If required high/low/close fields are missing, the evaluation is insufficient data.
- No live data fetch is allowed.
- Weekly and monthly backtests require a future non-GUI timeframe aggregation design before implementation.

## Snapshot ID Continuity Rules

`snapshot_id` is the central continuity key.

Rules:

- Backtest must never generate a replacement `snapshot_id` for a stored snapshot.
- Every `BacktestEvaluation` must persist the source `snapshot_id`.
- Every `BacktestTradeResult` must persist the same `snapshot_id` as its evaluation.
- If a snapshot row is updated by `symbol + timeframe + date`, its `snapshot_id` must remain stable.
- Missing outcomes or missing future rows do not break `snapshot_id` continuity; they produce skipped or insufficient-data records tied to the same `snapshot_id`.
- Backtest reports should reference `run_id` for the run and `snapshot_id` for source decision points.

## Deterministic Ordering Rules

Snapshot selection order:

```text
symbol ASC
timeframe ASC
date ASC
snapshot_id ASC
```

When symbol and timeframe are fixed:

```text
date ASC
snapshot_id ASC
```

Evaluation order:

- Assign `sequence_number` from the selected snapshot order, starting at 1.
- Persist `sequence_number` in `backtest_evaluations`.
- Replay results must be aggregated in `sequence_number ASC` order.

Tie-breakers:

- `snapshot_id` is the final tie-breaker.
- SQL queries must include explicit `ORDER BY`.
- Python aggregation should not depend on dictionary iteration order for replay order.

## Skipped and Insufficient-Data Persistence

Skipped records are part of the run result, not discarded records.

Persist skipped or insufficient cases when:

- snapshot is missing required close/entry data
- strategy inputs cannot be constructed
- outcome is missing and the selected evaluation mode requires it
- future OHLCV rows are missing
- future OHLCV rows are fewer than `horizon_days`
- future OHLCV rows are missing required high/low/close fields

Rules:

- Create a `BacktestEvaluation` for each selected snapshot.
- Set `evaluation_status` to `EVALUATED`, `SKIPPED`, or `INSUFFICIENT_DATA`.
- Store a deterministic `skip_reason` for skipped and insufficient cases.
- Prefer creating a `BacktestTradeResult` for every evaluation so run counts can be audited from trade results.
- Count skipped and insufficient cases in `skipped_trades`.
- Do not include skipped cases in win rate, average return, expectancy, or drawdown calculations.
- Breakeven completed trades count in `completed_trades` / `total_trades`, not wins or losses.

## Persistence Flow

Preferred future implementation flow:

1. Create a `BacktestRun` draft with query scope and zeroed metrics, or hold the run in memory until aggregation is complete.
2. Persist `BacktestAssumptions`.
3. Load snapshots in deterministic order.
4. For each snapshot, create a `BacktestEvaluation`.
5. Load outcome and future rows.
6. Build `BacktestInput` only when required source data exists.
7. Run deterministic replay.
8. Persist `BacktestTradeResult`.
9. Aggregate persisted or in-memory `SimulationResult` records into `BacktestResult`.
10. Update or insert final `BacktestRun` aggregate metrics.
11. Build deterministic `BacktestReport` from `BacktestResult`.

Open implementation decision:

- Whether to persist a draft `BacktestRun` before replay or persist the run only after all evaluations succeed. If draft runs are allowed, add a run status field such as `RUNNING`, `COMPLETE`, or `FAILED`.

## Not Implemented Yet

The following are not part of DB-backed Backtest v1 implementation yet:

- portfolio logic
- fees
- slippage
- AI
- broker execution
- live data
- order management
- position sizing
- partial exits
- trailing stops
- weekly/monthly DB replay without shared non-GUI aggregation
- persistence of probability, prediction, or strategy result source tables

## Implementation Guardrails

DB-backed Backtest must:

- remain additive
- use SQLite as the local source of truth
- preserve existing `snapshot_id` values
- avoid live data and network access
- avoid AI calls
- avoid changing frozen Brain v1 behavior
- avoid changing Probability, Prediction, or Strategy scoring logic
- expose skipped and insufficient-data records explicitly
- keep replay deterministic for the same database state, query, assumptions, and code versions

