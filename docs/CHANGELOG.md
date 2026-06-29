# CHANGELOG

## Read-only SQLite Backtest Runner

- Added read-only DB-backed Backtest orchestration.
- Added `run_sqlite_backtest_read_only` to build a dataset with `SQLiteBacktestDatasetBuilder`, run existing `run_backtest`, and build an existing `BacktestReport`.
- Added `SQLiteBacktestRun` result container with dataset, result, report, and skipped records.
- Preserved deterministic skipped records from dataset construction.
- Added in-memory SQLite integration tests for DB rows to dataset to BacktestResult to BacktestReport.
- Verified typed Backtest and report counts, deterministic ordering, no database writes, no AI/live data/network/broker imports, and no BUY / SELL / HOLD output.
- Backtest persistence remains not implemented yet.

## SQLite BacktestDatasetBuilder

- Added `SQLiteBacktestDatasetBuilder` for composing SQLite-backed snapshot, outcome, and future-row loaders.
- Added deterministic `BacktestDataset` construction from `SnapshotQuery`.
- Matched outcomes by `snapshot_id`.
- Grouped future rows by `snapshot_id`.
- Represented missing outcomes and insufficient future rows as deterministic skipped records.
- Added in-memory SQLite unit tests for loader composition, deterministic ordering, missing data representation, and no database writes.
- DB-backed Backtest execution remains not implemented yet.

## SQLite FutureRowsLoader

- Added `SQLiteFutureRowsLoader` for reading existing `ohlcv_daily` records.
- Added deterministic loading of 1D future rows after snapshot date.
- Added horizon-limited future-row loading for replay windows.
- Added grouped loading by `snapshot_id` for future dataset construction.
- Added in-memory SQLite unit tests for date filtering, horizon limits, grouping, missing table behavior, and no database writes.
- Verified the loader does not import live data, AI, network, or broker modules.
- DB-backed Backtest execution remains not implemented yet.

## SQLite OutcomeLoader

- Added `SQLiteOutcomeLoader` for reading existing `outcomes` records.
- Added deterministic loading by snapshot_id list.
- Enforced deterministic ordering by `snapshot_id` and `outcome_id`.
- Added in-memory SQLite unit tests for matching snapshot ids, ignoring non-matching rows, empty input, ordering, missing table behavior, and no database writes.
- Verified the loader does not import live data, AI, network, or broker modules.
- FutureRowsLoader and DB-backed Backtest execution remain not implemented yet.

## SQLite SnapshotLoader

- Added `SQLiteSnapshotLoader` for reading existing `snapshots` records.
- Added `SnapshotQuery.symbol` and `SnapshotQuery.limit` while preserving the existing `symbols` tuple.
- Supported deterministic filters for symbol, symbols, timeframe, start date, end date, and limit.
- Enforced deterministic ordering by symbol, timeframe, date, and `snapshot_id`.
- Added in-memory SQLite unit tests for filters, ordering, missing table behavior, and no database writes.
- Verified the loader does not import live data, AI, network, or broker modules.
- OutcomeLoader, FutureRowsLoader, and DB-backed Backtest execution remain not implemented yet.

## Backtest DB Schema Skeleton

- Added `src/backtest/db/` package.
- Added deterministic Backtest-owned SQLite schema initialization.
- Added schema definitions for `backtest_runs`, `backtest_assumptions`, `backtest_evaluations`, and `backtest_trade_results`.
- Added in-memory SQLite unit tests for table creation, required columns, initializer idempotency, and preserving existing source tables.
- Verified schema initialization does not import live data, AI, network, or broker modules.
- SnapshotLoader, OutcomeLoader, FutureRowsLoader, and DB-backed Backtest execution remain not implemented yet.

## Backtest DB Design

- Added `docs/BACKTEST_DB_DESIGN.md`.
- Defined DB-backed Backtest v1 persistence contracts: `BacktestRun`, `BacktestEvaluation`, `BacktestTradeResult`, and `BacktestAssumptions`.
- Defined Backtest-owned table direction for runs, assumptions, evaluations, and trade results.
- Defined SQLite loader direction for `SnapshotLoader`, `OutcomeLoader`, and `FutureRowsLoader`.
- Documented `snapshot_id` continuity, deterministic ordering, and skipped / insufficient-data persistence rules.
- Clarified that portfolio, fees/slippage, AI, broker execution, and live data are not implemented yet.
- DB-backed Backtest remains design-only at this step.

## Backtest Framework Integration Coverage

- Added deterministic integration coverage for `StrategyResult -> BacktestInput -> run_backtest -> build_backtest_report`.
- Verified Backtest typed counts through the integration flow: attempted, completed, skipped, and breakeven trades.
- Verified Backtest Report exposes attempted, completed, skipped, and breakeven counts as structured fields.
- Verified integration output does not contain BUY, SELL, or HOLD.
- Guarded the integration test against database, network, HTTP, and live-data access.
- Database-backed Backtest remains not implemented yet.

## Backtest Framework v1 Contract Stabilization

- Added typed BacktestResult count semantics for attempted, completed, skipped, and breakeven trades.
- Kept `total_trades` as a backward-compatible completed-trade count.
- Updated metrics aggregation to populate typed count fields.
- Updated Backtest Report output to expose attempted, completed, skipped, and breakeven counts as structured fields.
- Expanded Backtest unit tests for all-win, all-loss, breakeven, skipped / insufficient-data, mixed, and empty-input scenarios.
- Database-backed Backtest remains not implemented yet.

## Backtest Data Layer Skeleton

- Added `src/backtest/data/` package skeleton.
- Added `SnapshotQuery`.
- Added `SnapshotLoader`, `OutcomeLoader`, and `FutureRowsLoader` public interfaces.
- Added `BacktestDataset` and `BacktestDatasetBuilder` public interfaces.
- Added Backtest data-layer skeleton unit tests.
- Data-layer implementations intentionally raise `NotImplementedError`.
- SQLite-backed loading, SQL queries, historical dataset construction, DB-backed Backtest execution, Portfolio Evaluation, and AI overlay are not implemented yet.

## Backtest Framework v1

- Added Backtest contracts.
- Added Backtest types.
- Added Backtest Simulation Rules documentation.
- Added deterministic single-trade Replay Engine.
- Added Metrics Aggregator.
- Added Backtest Pipeline.
- Added deterministic Backtest Report layer.
- Added Backtest unit tests.
- Backtest Framework v1 is in-memory only.
- Database-backed Backtest, Snapshot Loader, Outcome Loader, Dataset Builder, historical replay from stored datasets, Portfolio Evaluation, UI integration, and AI overlay are not implemented yet.

## Pre-Backtest Stabilization

- Added Architecture Audit v2.
- Added Backtest decision preparation notes.
- Clarified Strategy reward/risk estimate contract with typed fields.
- Updated project status and roadmap for Strategy Engine v1 initial implementation.
- Confirmed Backtest Engine remains not implemented.

## Strategy Engine v1 Initial Implementation

- Added `src/strategy` package.
- Added Strategy input/output contracts.
- Added Strategy grade, risk, and entry-quality enums.
- Added deterministic `analyze_strategy` implementation.
- Added Strategy Engine unit tests.
- Added Strategy contract regression tests.
- Strategy Engine v1 does not call AI, load market data, access the database, or output BUY / SELL / HOLD.

## Brain v1 Completed

- Frozen EXOS Brain v1 architecture.
- Completed analysis pipeline:
  Market Data → Core Indicators → Snapshot → Statistics → Outcome → Pattern Discovery → Pattern Library → Similarity → Probability → Prediction.
- Future enhancements should extend the pipeline rather than modifying existing engine contracts unless fixing a verified bug.

## Market Learning Engine v1

- Added Statistics DB schema helpers.
- Added Snapshot Store.
- Added Snapshot Collector.
- Added Outcome Calculator.
- Added Pattern Discovery Engine.
- Added Pattern Library.
- Added Similarity Engine.
- Added end-to-end Market Learning Pipeline smoke test.

## Core Indicators v1

- Added Indicator Engine v1.
- Added EW Engine v1.
- Added Volume Pressure Engine v1.
- Added Trend Slope Engine v1.
- Added Squeeze Engine v1.
- Added Market Structure Engine v1.
- Added Snapshot Builder v1.
- Added Score Engine v1.
- Core Indicators v1 is complete and frozen unless a real bug appears.

## Chart And Data Foundation

- Added Dashboard.
- Added State Manager.
- Added SQLite Cache.
- Added Developer Mode.
- Added Candlestick Chart v1.
- Added real cached OHLC chart flow.
- Added chart metadata label and configurable visible rows.
- Added volume panel aligned to candlestick rows.
- Added market header from latest cached OHLCV row.
- Added current price line and right-side price label.
- Moved price and volume axis labels to the right side.
- Added EMA20, EMA50, and EMA200 overlays.
- Added mouse crosshair and OHLC/EMA hover tooltip.
- Added automatic cache-miss OHLCV loading for selected symbols.
- Added NASDAQ-only scanner scope guard.
- Added Timeframe Engine v1 with 1D, 1W, and 1M chart views.
- Added 10-year daily OHLCV Yahoo Finance fetch depth.
- Added visible rows control for 60, 120, 240, and All.
- Added Dark Theme v1 for standard PySide6 widgets.
