# Backtest Data Layer

Design document for connecting the existing EXOS Market Learning database to the Backtest Framework.

This document defines the data-layer direction and records the current interface skeleton.

Database-backed replay is not implemented yet.

The `src/backtest/data/` package now exists as an interface skeleton only. Loader and builder methods intentionally raise `NotImplementedError` until SQLite-backed loading is designed and implemented.

## Purpose

Backtest Data Layer should construct deterministic `BacktestInput` records from stored EXOS data.

It connects the existing Market Learning pipeline to Backtest replay without adding trading logic, probability calculation, prediction calculation, strategy scoring, or AI.

Intended flow:

```text
Market Data
-> Indicators
-> Snapshot
-> Statistics DB
-> Outcome
-> Pattern Library

-> Backtest Data Layer
-> BacktestInput
-> Replay Engine
-> Metrics
-> Report
```

## Source Architecture

The current Market Learning schema already supports Backtest through `snapshot_id`.

Relevant tables:

- `snapshots`
- `outcomes`
- `patterns`
- `ohlcv_daily` from the market data cache

Important rules from `docs/MARKET_LEARNING_SCHEMA.md`:

- `snapshot_id` is the central reference.
- Snapshots are queryable by symbol, timeframe, date range, score, and state.
- Searchable snapshot values are stored as columns.
- Full nested snapshot payloads are stored in `snapshot_json`.
- Outcomes are linked to snapshots by `snapshot_id`.
- Backtest should avoid loading every snapshot into memory.

## Data Layer Responsibilities

Backtest Data Layer should:

- Load stored snapshots.
- Load associated outcomes.
- Load future OHLCV rows needed for replay.
- Construct `BacktestInput` objects.
- Preserve deterministic ordering.
- Preserve `snapshot_id` continuity.
- Report missing snapshots, outcomes, or future rows deterministically.
- Keep all loaded source records read-only.

Backtest Data Layer must not:

- Perform trading logic.
- Calculate indicators.
- Build new snapshots unless a future explicit design allows it.
- Discover patterns.
- Calculate probability.
- Build predictions.
- Run Strategy Engine scoring unless a future explicit orchestration layer owns that step.
- Call AI.
- Fetch live market data.
- Modify stored market data.
- Modify snapshots.
- Modify outcomes.

## Current Skeleton Status

Implemented interface skeletons:

- `src/backtest/data/`
- `SnapshotQuery`
- `SnapshotLoader`
- `OutcomeLoader`
- `FutureRowsLoader`
- `BacktestDataset`
- `BacktestDatasetBuilder`

Current skeleton behavior:

- Public imports are available.
- Query and dataset containers exist for future DB-backed construction.
- Loader and builder methods raise `NotImplementedError`.
- No SQLite connection is opened.
- No SQL is executed.
- No historical dataset is constructed.
- No DB-backed Backtest execution exists.
- No Portfolio Evaluation or AI overlay exists.

## Deterministic Ordering

Backtest datasets should be ordered deterministically.

Default ordering:

```text
symbol ASC
timeframe ASC
date ASC
snapshot_id ASC
```

If a caller requests a single symbol and timeframe, ordering should still use:

```text
date ASC
snapshot_id ASC
```

This avoids nondeterministic replay when multiple rows match the same filter.

## BacktestInput Construction

Each `BacktestInput` should contain:

- snapshot record or nested snapshot payload
- probability output
- prediction output
- strategy result
- outcome record
- future OHLCV rows

Current contract:

```text
BacktestInput(
    snapshot,
    probability,
    prediction,
    strategy_result,
    outcome,
    future_rows
)
```

The Data Layer should construct these objects from stored records or from deterministic upstream outputs produced earlier in the pipeline.

Open design issue:

- Probability, prediction, and strategy outputs are not currently persisted in the existing Market Learning schema.
- Until they are persisted, the Data Layer must either receive them from an upstream deterministic builder or a later persistence design must add tables for them.

## Data Layer Interfaces

The following interfaces now exist as public skeletons. Their database-backed behavior is not implemented yet.

### SnapshotLoader

Responsibility:

- Query stored snapshots from SQLite.
- Filter by symbol, timeframe, date range, score, and state.
- Return rows in deterministic order.
- Preserve `snapshot_id`.
- Parse `snapshot_json` only when required for BacktestInput construction or reporting.

Must not:

- Recalculate snapshots.
- Modify snapshot rows.
- Load all snapshots if a targeted query is possible.

### OutcomeLoader

Responsibility:

- Load outcome rows associated with selected `snapshot_id` values.
- Report missing outcomes deterministically.
- Preserve one-to-one outcome linkage where available.

Must not:

- Calculate new outcomes during Backtest Data Layer loading.
- Modify outcome rows.

### FutureRowsLoader

Responsibility:

- Load future OHLCV rows for each snapshot.
- Use symbol, timeframe, snapshot date, and simulation horizon.
- Return only the rows required for replay.
- Report insufficient data deterministically.

Must not:

- Fetch live data.
- Mutate OHLCV rows.
- Perform replay logic.

### BacktestDataset

Responsibility:

- Hold a deterministic collection of `BacktestInput` records.
- Hold dataset metadata.

Possible metadata:

- symbol list
- timeframe
- date range
- snapshot count
- skipped count
- missing outcome count
- missing future rows count
- source database path or identifier
- created timestamp

Must not:

- Run replay logic.
- Aggregate metrics.
- Generate AI summaries.

### BacktestDatasetBuilder

Responsibility:

- Coordinate `SnapshotLoader`, `OutcomeLoader`, and `FutureRowsLoader`.
- Construct `BacktestInput` records.
- Preserve deterministic ordering.
- Produce a `BacktestDataset`.
- Record skipped records and reasons.

Must not:

- Decide trade outcomes.
- Run portfolio logic.
- Run AI.
- Modify source records.

Still not implemented:

- SQLite-backed loading.
- SQL query construction.
- Historical dataset construction.
- DB-backed Backtest execution.
- Portfolio Evaluation.
- AI overlay.

## Snapshot Selection

Initial selection should follow existing schema support:

- symbol
- timeframe
- date range
- EXOS score
- trend state
- squeeze state
- market structure state

Every selected snapshot should retain:

- `snapshot_id`
- symbol
- timeframe
- date
- close

Snapshots without enough required downstream data should be skipped or marked as insufficient data, not silently dropped.

## Outcome Handling

Outcome rows should be loaded by `snapshot_id`.

Backtest Data Layer should support:

- snapshot with outcome
- snapshot without outcome
- snapshot with insufficient future data

Outcome rows are useful for validation and expected-vs-actual comparison.

Trade replay may still use future OHLCV rows directly according to `docs/BACKTEST_SIMULATION_RULES.md`.

## Future OHLCV Handling

Replay requires future OHLCV rows after the snapshot date.

Data Layer should load:

- high
- low
- close
- date
- open and volume when available

Rows should be ordered ascending by date.

Missing or incomplete rows should produce deterministic skipped/insufficient-data records.

## Probability / Prediction / Strategy Inputs

Current issue:

- The existing Market Learning schema persists snapshots, outcomes, and patterns.
- It does not yet define persisted probability, prediction, or strategy result tables.

Allowed future approaches:

1. Build probability, prediction, and strategy outputs during dataset construction using deterministic functions.
2. Persist probability, prediction, and strategy outputs before Backtest.
3. Support both, with persisted outputs preferred for reproducibility.

Decision needed before DB-backed Backtest:

- Which approach is the source of truth for probability, prediction, and strategy outputs during replay?

## Reproducibility Rules

Backtest Data Layer should record:

- database source
- symbol filters
- timeframe filters
- date range
- snapshot query filters
- simulation horizon
- strategy version
- backtest version
- context layer state if future context is disabled or enabled

Backtest Data Layer should avoid:

- network calls
- AI calls
- random ordering
- hidden mutable state

## Documentation Review Notes

Reviewed:

- `docs/BACKTEST_ENGINE_DESIGN.md`
- `docs/BACKTEST_DECISIONS.md`
- `docs/MARKET_LEARNING_SCHEMA.md`

Compatibility findings:

- The proposed Backtest Data Layer is compatible with the snapshot-first architecture.
- The existing schema already identifies `snapshot_id` as the central Backtest reference.
- The existing schema supports snapshot selection by symbol, timeframe, date, score, and state.
- Outcomes are already linked to snapshots through `snapshot_id`.
- Backtest decision notes already require SQLite-backed historical truth and deterministic replay.

Documentation drift found:

- Historical notes in older design documents may describe the data layer as future-only. The current state is interface skeletons implemented, with SQLite-backed behavior still pending.

No architecture conflict found.

## Open Decisions

Before implementing DB-backed Backtest Data Layer, decide:

- Whether probability outputs are built on demand or persisted.
- Whether prediction outputs are built on demand or persisted.
- Whether StrategyResult outputs are built on demand or persisted.
- Where Backtest run and evaluation schemas live.
- Whether `BacktestInput` should gain typed `snapshot_id`, symbol, timeframe, and date fields.
- Whether skipped dataset records are stored separately from replay results.
- Whether timeframe aggregation must move out of GUI before DB-backed Backtest supports 1W or 1M.

## Implementation Rule

Backtest Data Layer must be additive.

It should consume existing EXOS data and construct Backtest inputs without modifying frozen Brain v1 contracts or Strategy Engine behavior.
