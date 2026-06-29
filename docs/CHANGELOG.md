# CHANGELOG

## SQLiteDataSource v1

- Added `src/data_source/sqlite_source.py`.
- Added `SQLiteDataSource` as a read-only implementation of the existing `MarketDataSource` protocol.
- Implemented `load_ohlcv` for existing SQLite `ohlcv_daily` rows with deterministic symbol/date ordering, symbol filtering, date-range filtering, 1D timeframe validation, and optional limits.
- Implemented `load_future_rows` by reusing the existing Backtest Data Layer `SQLiteFutureRowsLoader` for standard future-row query behavior.
- Supported optional deterministic fixture role columns for separating current OHLCV rows from future rows in in-memory tests.
- Exported `SQLiteDataSource` from `src.data_source`.
- Added in-memory SQLite unit tests for deterministic ordering, filters, future rows, empty results, missing tables, read-only behavior, and no AI/network/broker imports.
- Added in-memory SQLite integration coverage for `SQLiteDataSource -> AnalysisService -> Analysis Pipeline -> Analysis Report`.
- Verified no table creation, schema initialization, database writes, live data, broker access, network access, AI calls, or frozen Analysis Pipeline contract changes.

## Analysis Service Smoke Coverage

- Added `tests/smoke/test_analysis_service.py`.
- Added deterministic application-layer smoke coverage for `AnalysisService.analyze_symbol_with_report`.
- Used `MemoryDataSource` with deterministic OHLCV rows, similar-pattern-shaped rows, and future rows.
- Verified `AnalysisServiceResult`, populated `AnalysisResult`, populated `AnalysisReport`, complete full-pipeline report statuses, deterministic fixed-input output, no BUY / SELL / HOLD output, and no AI/network/broker imports.
- No new service behavior, Analysis Pipeline contract changes, SQLite source implementation, live data, broker access, or AI calls were introduced.

## Analysis Service Report Generation

- Added immutable `AnalysisServiceResult` contract.
- Added `AnalysisService.analyze_symbol_with_report(symbol, timeframe="1D")`.
- Reused existing `AnalysisService.analyze_symbol` and existing `build_analysis_report`.
- Exported `AnalysisServiceResult` from `src.application`.
- Added unit tests for result/report return shape, report symbol/timeframe matching the result, populated full pipeline report statuses, deterministic output, no BUY / SELL / HOLD output, and no AI/network/broker imports.
- Analysis Pipeline v1 contracts, SQLite source implementation, live data, broker access, and AI calls remain unchanged and not implemented.

## Analysis Service v1

- Added `src/application/` package.
- Added `AnalysisService` for application-layer wiring from `MarketDataSource` to existing Analysis Pipeline v1.
- Added `analyze_symbol(symbol, timeframe="1D")`.
- Loaded OHLCV rows through `MarketDataSource.load_ohlcv`.
- Loaded future rows through `MarketDataSource.load_future_rows` when Backtest is enabled and current rows are available.
- Built existing `AnalysisRequest` values and called existing `analysis_pipeline.analyze_symbol`.
- Added unit tests using `MemoryDataSource` only.
- Verified `AnalysisResult` output, populated Snapshot / Probability / Prediction / Strategy, Backtest population from future rows, deterministic output, no BUY / SELL / HOLD output, and no AI/network/broker imports.
- SQLite source implementation, live data, broker access, AI calls, and Analysis Pipeline v1 contract changes remain not implemented.

## MemoryDataSource

- Added `src/data_source/memory_source.py`.
- Added `MemoryDataSource` for deterministic read-only in-memory market data loading.
- Exported `MemoryDataSource` from `src.data_source`.
- Implemented `load_ohlcv` with symbol, timeframe, start date, end date, and limit filtering.
- Implemented `load_future_rows` with symbol, timeframe, snapshot-date, and horizon filtering.
- Enforced deterministic ordering by symbol, timeframe, and date.
- Returned copied rows so callers cannot mutate stored source rows.
- Kept rows marked with `row_type`, `source_role`, or `data_role` of `future` out of normal OHLCV loads while allowing them in future-row loads for deterministic service fixtures.
- Added unit tests for matching loads, future rows after snapshot date, filters, ordering, empty results, read-only behavior, and no AI/network/broker imports.
- SQLite source implementation and direct Analysis Pipeline contract changes remain not implemented.

## Data Source v1 Contract Skeleton

- Added `src/data_source/` package.
- Added immutable public contracts: `MarketDataRequest`, `MarketDataResult`, `FutureRowsRequest`, `FutureRowsResult`, and `DataSourceConfig`.
- Added `MarketDataSource` public protocol with read-only `load_ohlcv` and `load_future_rows` methods.
- Added public exports for the Data Source contracts.
- Added unit tests for public imports, immutable dataclass shapes, default config values, request/result defaults, protocol shape, and no AI/network/broker imports.
- SQLite source implementation, Analysis Pipeline wiring, live data fetching, broker access, and AI calls remain not implemented.

## Analysis Pipeline Smoke Coverage

- Added `tests/smoke/test_analysis_pipeline.py`.
- Added deterministic full in-memory smoke coverage for `analyze_symbol` and `build_analysis_report`.
- Used fake OHLCV rows, similar-pattern fixtures, and future rows.
- Verified populated Snapshot, Probability, Prediction, Strategy, Backtest, and Analysis Report output.
- Verified no BUY / SELL / HOLD output, no AI/network/broker imports, and deterministic fixed-input behavior.
- No new Analysis Pipeline behavior or existing engine contract changes were introduced.

## Analysis Pipeline Deterministic Report Layer

- Added `src/analysis_pipeline/report.py`.
- Added immutable `AnalysisReport` contract.
- Added `build_analysis_report` for deterministic, rule-based summaries of Analysis Pipeline results.
- Report output summarizes symbol, timeframe, snapshot status, probability status, prediction status, strategy status, backtest status, and notes.
- Added public exports for `AnalysisReport` and `build_analysis_report`.
- Added tests for snapshot-only reports, full pipeline reports, missing Backtest handling, no BUY / SELL / HOLD output, deterministic fixed-output behavior, and no AI/network/broker imports.
- Report generation does not call AI, live data, network access, broker access, SQLite, or DB-backed Backtest runners.

## Analysis Pipeline Request-Row Backtest Step

- Updated `analyze_symbol` to optionally run Backtest after Strategy.
- Used existing public Backtest APIs: `BacktestInput`, `run_backtest`, and `build_backtest_report`.
- Added deterministic request-provided future rows to `AnalysisRequest`.
- Populated `AnalysisResult.backtest` with Backtest result and report dictionaries when future rows are supplied.
- Kept Backtest empty/default when future rows are not supplied.
- Added tests for the full Snapshot -> Probability -> Prediction -> Strategy -> Backtest flow.
- Added tests for Backtest population, empty/default Backtest behavior, no BUY / SELL / HOLD output, no AI/network/broker imports, deterministic fixed-input output, and optional Backtest skipping.
- SQLite, DB-backed Backtest runners, AI analysis, live data, network access, broker access, and database access remain not implemented in Analysis Pipeline.

## Analysis Pipeline Strategy Step

- Updated `analyze_symbol` to compute Strategy after Snapshot, Probability, and Prediction.
- Used the existing public Strategy Engine API.
- Populated `AnalysisResult.strategy` when Strategy is enabled and upstream outputs are present.
- Kept Backtest empty/default.
- Added tests for populated snapshot, probability, prediction, and strategy outputs.
- Added tests for Backtest remaining empty/default, no BUY / SELL / HOLD output, no AI/network/broker imports, deterministic fixed-input output, and optional Strategy skipping.
- Latest snapshot loading, Backtest execution, AI analysis, live data, network access, broker access, and database access remain not implemented in Analysis Pipeline.

## Analysis Pipeline Probability + Prediction Step

- Updated `analyze_symbol` to compute Probability and Prediction after building the snapshot.
- Used existing public Probability Engine and Prediction Engine APIs.
- Added optional deterministic similar-pattern fixtures to `AnalysisRequest`.
- Added `PipelineConfig` switches for Probability and Prediction.
- Kept Strategy and Backtest fields empty/default.
- Added deterministic tests for populated snapshot, populated probability, populated prediction, Strategy and Backtest defaults, no BUY / SELL / HOLD output, no AI/network/broker imports, and stable fixed-input output.
- Latest snapshot loading, Strategy orchestration, Backtest execution, AI analysis, live data, network access, broker access, and database access remain not implemented in Analysis Pipeline.

## Analysis Pipeline Snapshot-Only Step

- Updated `analyze_symbol` to build snapshot-only `AnalysisResult` values from request-provided OHLCV rows.
- Reused the existing Core Indicator / Snapshot Builder path without changing frozen Brain v1 engine contracts.
- Added request, config, and metadata fields to `AnalysisResult`.
- Added optional request OHLCV rows to `AnalysisRequest`.
- Kept Probability, Prediction, Strategy, and Backtest fields empty/default.
- Added deterministic fake-OHLCV unit tests for snapshot output, downstream defaults, no BUY / SELL / HOLD output, and no AI/network/broker imports.
- Latest snapshot loading, Probability, Prediction, Strategy, Backtest, AI analysis, live data, network access, broker access, and database access remain not implemented in Analysis Pipeline.

## Analysis Pipeline Contract Skeleton

- Added `src/analysis_pipeline/` package.
- Added immutable public contracts: `AnalysisRequest`, `AnalysisResult`, and `PipelineConfig`.
- Added `analyze_symbol` public API placeholder.
- Added unit tests for public imports, contract shapes, default config, result defaults, request defaults, and explicit placeholder behavior.
- `analyze_symbol` intentionally raises `NotImplementedError`.
- Pipeline orchestration, AI analysis, Brain v1 integration, Probability integration, Prediction integration, Strategy integration, and Backtest integration are not implemented yet.

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
