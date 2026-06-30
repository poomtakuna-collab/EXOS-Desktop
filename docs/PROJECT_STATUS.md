# PROJECT STATUS

## Current

EXOS Brain v1 is complete and frozen.

Prediction Engine v1 is implemented.

Strategy Engine v1 initial implementation is implemented.

Strategy validation tests are implemented.

In-memory Backtest Framework v1 is implemented.

Backtest unit tests are implemented.

Backtest & Validation v1 is implemented.

Backtest Persistence v1 direct persistence path is implemented.

Backtest Framework integration coverage is implemented.

Backtest Data Layer interface skeletons are implemented.

Backtest DB persistence and loading path design is documented.

Backtest DB schema skeleton is implemented.

SQLite-backed SnapshotLoader is implemented.

SQLite-backed OutcomeLoader is implemented.

SQLite-backed FutureRowsLoader is implemented.

SQLite-backed BacktestDatasetBuilder is implemented.

Read-only DB-backed Backtest orchestration is implemented.

Analysis Pipeline deterministic report layer is implemented.

Data Source v1 public contracts, deterministic memory source, and read-only SQLite source are implemented.

Analysis Service v1 is implemented.

Market Learning Engine v1 remains complete.

Similar Pattern Resolver v1 is implemented as an additive pure analysis engine.

Pipeline smoke test passed:

- `tests/smoke/test_market_learning_pipeline.py`
- `tests/smoke/test_analysis_pipeline.py`
- `tests/smoke/test_analysis_service.py`

Architecture Audit v2 completed:

- `docs/ARCHITECTURE_AUDIT_V2.md`

Architecture Audit v3 completed:

- `docs/ARCHITECTURE_AUDIT_V3.md`

## Architecture Summary

Architecture details are maintained in `docs/Architecture.md`.

## Completed

### Brain v1 Completed

Status: Complete and frozen.

EXOS Brain v1 freezes the completed analysis pipeline:

- Market Data
- Core Indicators
- Snapshot
- Statistics
- Outcome
- Pattern Discovery
- Pattern Library
- Similarity
- Probability
- Prediction

Future enhancements should extend this pipeline rather than modifying existing engine contracts unless fixing a verified bug.

### Core Indicators v1

Status: Complete and frozen.

Core Indicators v1 should remain unchanged unless a real bug appears.

Includes:

- Indicator Engine v1
- EW Engine v1
- Volume Pressure Engine v1
- Trend Slope Engine v1
- Squeeze Engine v1
- Market Structure Engine v1
- Snapshot Builder v1
- Score Engine v1

### Market Learning Engine v1

Status: Complete.

Market Learning Engine v1 includes:

- Statistics DB
- Snapshot Store
- Snapshot Collector
- Outcome Calculator
- Pattern Discovery
- Pattern Library
- Similarity Engine
- Pipeline Smoke Test

Key rules:

- `snapshot_id` is the central reference.
- Searchable snapshot fields are stored as database columns.
- Full nested EXOS snapshots are stored as JSON.
- Outcomes are calculated later when enough future OHLCV rows exist.
- Pattern Discovery is deterministic statistics only.
- Similarity is deterministic scoring only.

### Probability Engine v1

Status: Implemented.

Probability Engine v1 converts similar historical patterns into evidence-based probability outputs.

The additive Analysis Probability Engine v1 consumes Similar Pattern Resolver output directly and produces deterministic positive, negative, and neutral probability summaries from matched historical outcomes.

It outputs:

- Expected 5D / 10D / 20D returns
- Probability of 5% and 10% upside within 10D
- Approximate 5% downside probability within 10D
- Expected 10D max gain and drawdown
- Confidence
- Evidence count

It does not output BUY, SELL, or HOLD recommendations.

Current tests:

- `tests/unit/test_probability_engine.py`
- `tests/smoke/test_similarity_probability_bridge.py`

### Prediction Engine v1

Status: Implemented.

Prediction Engine v1 derives price projections only from Probability Engine outputs.

The additive Analysis Price Projection Engine v1 can also derive deterministic price projection ranges directly from resolver matches or probability-compatible historical match rows.

Prediction chain naming note:

- Similar Pattern Resolver output uses `similarity`.
- `similarity_score` is accepted only for legacy / probability-compatible match rows.

Flow:

Probability
-> Price Projection
-> Target Zone
-> Risk Zone

It outputs:

- Expected 5D / 10D / 20D prices
- 10D expected return
- Target zone
- Risk zone
- Confidence
- Best matching pattern metadata

It does not output BUY, SELL, or HOLD recommendations.

### Strategy Engine v1

Status: Initial implementation.

Strategy Engine v1 consumes existing structured EXOS outputs:

- Snapshot
- Probability Engine output
- Prediction Engine output

It outputs:

- Strategy score
- Trade grade
- Entry quality
- Risk rating
- Reward/risk estimate
- Notes

It does not calculate indicators.

It does not discover patterns.

It does not call AI.

It does not output BUY, SELL, or HOLD recommendations.

Current tests:

- `tests/unit/test_strategy_engine.py`
- `tests/regression/test_strategy_contract.py`

### Price Projection Engine v1

Status: Implemented.

Price Projection Engine v1 consumes resolver matches or probability-compatible historical match rows and calculates deterministic expected prices plus upside and downside ranges from historical outcome fields.

It does not call AI.

It does not output BUY, SELL, or HOLD recommendations.

It does not modify existing Prediction Engine contracts.

Current tests:

- `tests/unit/test_price_projection_engine.py`
- `tests/smoke/test_similarity_price_projection_bridge.py`

### Target Zone Engine v1

Status: Implemented.

Target Zone Engine v1 consumes Price Projection Engine output and derives deterministic conservative, base, and aggressive target levels from upside projection data.

It does not call AI.

It does not output BUY, SELL, or HOLD recommendations.

It does not modify existing Prediction Engine contracts.

Current tests:

- `tests/unit/test_target_zone_engine.py`
- `tests/smoke/test_price_projection_target_zone_bridge.py`

### Risk Zone Engine v1

Status: Implemented.

Risk Zone Engine v1 consumes Price Projection Engine output and derives deterministic conservative, base, and aggressive risk levels from downside projection data.

It does not call AI.

It does not output BUY, SELL, or HOLD recommendations.

It does not modify existing Prediction Engine contracts.

Current tests:

- `tests/unit/test_risk_zone_engine.py`
- `tests/smoke/test_price_projection_risk_zone_bridge.py`

### Prediction Summary Engine v1

Status: Implemented.

Prediction Summary Engine v1 consumes Probability Engine, Price Projection Engine, Target Zone Engine, and Risk Zone Engine outputs and returns one deterministic prediction summary object.

Prediction Summary metadata precedence:

- Probability metadata wins when present.
- If probability metadata is unavailable, projection / zone metadata is used.

It does not call AI.

It does not output BUY, SELL, or HOLD recommendations.

It does not implement Strategy Engine behavior.

Current tests:

- `tests/unit/test_prediction_summary_engine.py`
- `tests/smoke/test_full_prediction_summary_chain.py`
- `tests/smoke/test_pattern_library_prediction_summary_bridge.py`

### Strategy Summary Engine v1

Status: Implemented.

Strategy Summary Engine v1 consumes Prediction Summary output and returns deterministic non-decision strategy context.

`market_bias` is descriptive context only.

It is not a trade decision.

It outputs:

- Market bias
- Risk level
- Reward/risk ratio
- Notes

It does not call AI.

It does not output BUY, SELL, or HOLD recommendations.

Current tests:

- `tests/unit/test_strategy_summary_engine.py`
- `tests/smoke/test_prediction_strategy_summary_bridge.py`

### Trade Plan Engine v1

Status: Implemented.

Trade Plan Engine v1 consumes Prediction Summary and Strategy Summary outputs and returns deterministic non-decision planning context.

It outputs:

- Entry zone
- Stop zone
- Target zone
- Risk/reward
- Invalidation notes

It does not call AI.

It does not output BUY, SELL, or HOLD recommendations.

Current tests:

- `tests/unit/test_trade_plan_engine.py`
- `tests/smoke/test_strategy_summary_trade_plan_bridge.py`

### Position Sizing Engine v1

Status: Implemented.

Position Sizing Engine v1 consumes Trade Plan output and calculates deterministic position sizing from account size and account risk settings.

Position Sizing uses `entry_zone.high` and `stop_zone.aggressive` as conservative sizing anchors.

It outputs:

- Account risk percent
- Risk per share
- Position size shares
- Estimated capital required
- Max loss amount

It does not call AI.

It does not output BUY, SELL, or HOLD recommendations.

Current tests:

- `tests/unit/test_position_sizing_engine.py`
- `tests/smoke/test_trade_plan_position_sizing_bridge.py`

### Strategy Report Engine v1

Status: Implemented.

Strategy Report Engine v1 consumes Prediction Summary, Strategy Summary, Trade Plan, and Position Sizing outputs and returns one deterministic strategy report object.

It includes:

- Prediction summary
- Strategy summary
- Trade plan
- Position sizing

It does not call AI.

It does not output BUY, SELL, or HOLD recommendations.

Current tests:

- `tests/unit/test_strategy_report_engine.py`
- `tests/smoke/test_full_strategy_report_chain.py`

### Backtest Framework v1

Status: Backtest Framework v1, Backtest & Validation v1, and Backtest Persistence v1 direct path implemented.

Backtest Framework v1 includes:

- Backtest contracts
- Backtest types
- Simulation rules
- Replay Engine
- Metrics Aggregator
- Backtest Pipeline
- Backtest Report
- Unit Tests
- Integration Test
- Backtest Result Engine v1
- Trade Outcome Model v1
- Trade Simulator v1
- Backtest Runner v1
- Validation Report Engine v1
- Backtest Persistence v1 contracts
- Backtest Persistence v1 schema constants
- SQLite Backtest Persistence Writer v1
- SQLite Backtest Persistence Reader v1 direct lookup/list reads
- Backtest Persistence Orchestrator v1

BacktestResult count semantics are explicit:

- `attempted_trades` counts all simulation results supplied to metrics.
- `completed_trades` counts successful completed simulations.
- `total_trades` remains a backward-compatible alias for completed trades.
- `skipped_trades` counts skipped or insufficient-data simulations.
- `breakeven_trades` counts completed breakeven simulations separately from wins and losses.

Backtest & Validation v1 contract notes:

- Same-candle simulator rule: when target and stop are both hit in one OHLCV row, stop wins.
- Frozen `profit_factor` behavior: `profit_factor` may be `float("inf")` for all-winning runs.

Backtest Persistence v1 direct path is implemented:

- `BacktestRunRecord`
- `BacktestEvaluationRecord`
- `BacktestTradeResultRecord`
- Persistence schema constants for `backtest_runs`, `backtest_evaluations`, and `backtest_trade_results`
- SQLite writer functions
- SQLite reader functions for direct lookup/list reads
- Persistence orchestrator from `BacktestRunV1` and `ValidationReportV1`

Persistence Reader v1 is intentionally limited to direct lookup/list reads.

Advanced Backtest Persistence report/query APIs are not implemented.

Backtest Data Layer skeleton includes:

- `src/backtest/data/`
- `SnapshotQuery`
- `SnapshotLoader`
- `SQLiteSnapshotLoader`
- `OutcomeLoader`
- `SQLiteOutcomeLoader`
- `FutureRowsLoader`
- `SQLiteFutureRowsLoader`
- `BacktestDataset`
- `BacktestDatasetBuilder`
- `SQLiteBacktestDatasetBuilder`

Backtest DB design is documented in:

- `docs/BACKTEST_DB_DESIGN.md`

The design defines:

- `BacktestRun`
- `BacktestEvaluation`
- `BacktestTradeResult`
- `BacktestAssumptions`
- Backtest-owned persistence tables
- SQLite loader direction for snapshots, outcomes, and future rows
- snapshot_id continuity rules
- deterministic ordering rules
- skipped and insufficient-data persistence rules

Backtest DB schema skeleton includes:

- `src/backtest/db/`
- `initialize_backtest_schema`
- `backtest_runs`
- `backtest_assumptions`
- `backtest_evaluations`
- `backtest_trade_results`
- in-memory SQLite schema tests

Current flow:

BacktestInput
-> Replay Engine
-> SimulationResult
-> Metrics Aggregator
-> BacktestResult
-> Backtest Report

The core Backtest Framework flow remains in-memory.

Read-only SQLite orchestration can now load stored snapshots, outcomes, and future rows into `BacktestDataset`.

The read-only SQLite orchestration path is:

SnapshotQuery
-> SQLiteBacktestDatasetBuilder
-> BacktestDataset
-> run_backtest
-> BacktestResult
-> BacktestReport

`SQLiteSnapshotLoader` reads existing `snapshots` rows only.

It supports deterministic filters for symbol, timeframe, date range, and limit.

`SQLiteOutcomeLoader` reads existing `outcomes` rows only.

It loads outcomes by snapshot_id list and orders deterministically by snapshot_id and outcome_id.

`SQLiteFutureRowsLoader` reads existing `ohlcv_daily` rows only.

It loads 1D future rows after snapshot date, respects horizon, and groups rows by snapshot_id.

`SQLiteBacktestDatasetBuilder` composes the SQLite loaders and builds `BacktestDataset`.

It does not execute replay or aggregate backtest results.

Read-only DB-backed Backtest orchestration:

- builds a dataset with `SQLiteBacktestDatasetBuilder`
- runs existing `run_backtest`
- builds existing `BacktestReport`
- preserves dataset skipped records
- does not persist results
- does not initialize schema

The older DB schema skeleton creates Backtest-owned tables only.

The Backtest Persistence v1 direct path writes and reads the v1 persistence records through SQLite.

It does not implement portfolio evaluation.

It does not call AI.

Current tests:

- `tests/unit/test_backtest_engine.py`
- `tests/unit/test_backtest_metrics.py`
- `tests/unit/test_backtest_pipeline.py`
- `tests/unit/test_backtest_report.py`
- `tests/unit/test_backtest_result_engine.py`
- `tests/unit/test_trade_outcome.py`
- `tests/unit/test_trade_simulator.py`
- `tests/unit/test_backtest_runner.py`
- `tests/unit/test_validation_report.py`
- `tests/unit/test_backtest_persistence_contracts.py`
- `tests/unit/test_backtest_persistence_schema.py`
- `tests/unit/test_backtest_persistence_writer.py`
- `tests/unit/test_backtest_persistence_reader.py`
- `tests/unit/test_backtest_persistence_orchestrator.py`
- `tests/unit/test_backtest_data_skeleton.py`
- `tests/unit/test_backtest_db_schema.py`
- `tests/unit/test_sqlite_snapshot_loader.py`
- `tests/unit/test_sqlite_outcome_loader.py`
- `tests/unit/test_sqlite_future_rows_loader.py`
- `tests/unit/test_sqlite_backtest_dataset_builder.py`
- `tests/integration/test_strategy_backtest_pipeline.py`
- `tests/integration/test_sqlite_backtest_read_only_runner.py`
- `tests/smoke/test_backtest_result_generation.py`
- `tests/smoke/test_trade_outcome_backtest_result_bridge.py`
- `tests/smoke/test_trade_simulator_backtest_result_bridge.py`
- `tests/smoke/test_backtest_runner_full_path.py`
- `tests/smoke/test_backtest_runner_validation_report_bridge.py`
- `tests/smoke/test_backtest_persistence_writer.py`
- `tests/smoke/test_backtest_persistence_reader_writer.py`
- `tests/smoke/test_backtest_persistence_orchestrator_full_path.py`

### Analysis Pipeline

Status: Snapshot + Probability + Prediction + Strategy + request-row Backtest + deterministic report implementation.

Analysis Pipeline Phase 5 has started with public contracts and deterministic execution through:

- `AnalysisRequest`
- `AnalysisResult`
- `PipelineConfig`
- `analyze_symbol`
- `AnalysisReport`
- `build_analysis_report`

`analyze_symbol` can build a snapshot from request-provided OHLCV rows using the existing Core Indicator / Snapshot Builder path.

It can then compute Probability and Prediction from request-provided similar-pattern fixtures using existing public Probability Engine and Prediction Engine APIs.

It can then compute Strategy using the existing public Strategy Engine API.

It can optionally run Backtest from request-provided deterministic future rows using existing public Backtest APIs:

- `BacktestInput`
- `run_backtest`
- `build_backtest_report`

`analyze_symbol` still raises `NotImplementedError` when no OHLCV rows are supplied because latest snapshot loading is not implemented yet.

The Analysis Pipeline does not yet call AI, live data, broker paths, network paths, SQLite, DB-backed Backtest runners, or the database.

Backtest remains empty/default unless deterministic future rows are supplied on the request.

Backtest output includes:

- Backtest result
- Backtest report

Analysis Report summarizes:

- Symbol
- Timeframe
- Snapshot status
- Probability status
- Prediction status
- Strategy status
- Backtest status
- Notes

The Analysis Report is deterministic and rule-based only.

Current tests:

- `tests/unit/test_analysis_pipeline_contracts.py`
- `tests/smoke/test_analysis_pipeline.py`

### Similar Pattern Resolver v1

Status: Implemented.

Similar Pattern Resolver v1 compares a current snapshot with supplied pattern library entries using deterministic weighted scoring only.

Weights:

- trend: 25
- trend_slope: 20
- adx: 15
- rsi: 10
- atr: 10
- squeeze: 10
- market_structure: 10

It outputs top similar historical patterns with:

- pattern_id
- similarity
- outcome
- pattern

It does not call AI.

It does not calculate probabilities.

It does not output BUY, SELL, or HOLD recommendations.

It does not modify Pattern Library contracts.

Current tests:

- `tests/unit/test_similar_pattern_resolver.py`
- `tests/smoke/test_market_learning_pipeline.py`

### Data Source v1

Status: Public contracts, deterministic memory source, and read-only SQLite source implemented.

Data Source v1 starts Phase 6 with immutable contracts and a read-only public protocol:

- `DataSourceConfig`
- `MarketDataRequest`
- `MarketDataResult`
- `FutureRowsRequest`
- `FutureRowsResult`
- `MarketDataSource`

`MarketDataSource` describes read-only loading methods only:

- `load_ohlcv`
- `load_future_rows`

`SQLiteDataSource` is implemented as a read-only adapter over existing `ohlcv_daily` rows.

Data Source is connected to Analysis Pipeline through Analysis Service v1 only.

It does not call AI, live data, network paths, broker paths, or legacy data providers.

`MemoryDataSource` is available for deterministic testing and future application-layer wiring.

It is initialized with in-memory rows, filters by symbol, timeframe, and date range, respects request limits and future-row horizons, returns deterministic ordering by symbol, timeframe, and date, and returns copied rows without mutating stored rows.

`SQLiteDataSource` loads deterministic OHLCV rows from existing SQLite `ohlcv_daily` records, reuses the Backtest Data Layer `SQLiteFutureRowsLoader` for standard future-row loading, supports optional deterministic fixture role columns for separating current and future rows in tests, and never creates tables, initializes schema, or writes database contents.

Current tests:

- `tests/unit/test_data_source_contracts.py`
- `tests/unit/test_memory_data_source.py`
- `tests/unit/test_sqlite_data_source.py`
- `tests/integration/test_sqlite_data_source_analysis_service.py`

### Analysis Service v1

Status: Implemented.

Analysis Service v1 provides an application-layer boundary from `MarketDataSource` to the existing Analysis Pipeline v1.

It accepts:

- `MarketDataSource`
- optional default `PipelineConfig`

It exposes:

- `analyze_symbol(symbol: str, timeframe: str = "1D")`
- `analyze_symbol_with_report(symbol: str, timeframe: str = "1D")`

The service loads OHLCV rows from `MarketDataSource.load_ohlcv`, optionally loads future rows from `MarketDataSource.load_future_rows` when Backtest is enabled and rows are available, builds an existing `AnalysisRequest`, calls existing `analysis_pipeline.analyze_symbol`, and returns `AnalysisResult`.

`analyze_symbol_with_report` uses the existing service `analyze_symbol` method and existing `build_analysis_report` function, returning immutable `AnalysisServiceResult` with:

- `analysis_result`
- `analysis_report`

It does not modify Analysis Pipeline v1 contracts.

It does not implement SQLite source access.

It does not call AI, live data, network paths, or broker paths.

Current tests:

- `tests/unit/test_analysis_service.py`
- `tests/smoke/test_analysis_service.py`

## Not Implemented Yet

- Analysis Pipeline latest snapshot loading
- Analysis Pipeline DB-backed Backtest orchestration
- Historical replay persistence from stored datasets
- Portfolio / Risk Evaluation
- Advanced Backtest Persistence report/query APIs
- UI Backtest reports
- AI Analysis / Overlay
- UI reports for Market Learning and Prediction output

## Run

Application:

- `py -m src.main`

Pipeline smoke test:

- `py -m unittest discover -s tests`

Current test count:

- 317 tests

## History

Detailed milestone history has moved to `docs/CHANGELOG.md`.
