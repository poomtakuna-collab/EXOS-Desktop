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

Analysis Pipeline opt-in canonical Brain v1 entry point is implemented.

Analysis Pipeline v2 foundation is implemented.

Analysis Pipeline v2 opt-in Persistence Adapter is implemented.

Data Source v1 public contracts, deterministic memory source, and read-only SQLite source are implemented.

Analysis Service v1 is implemented.

Near-term EXOS focus is Signal Ledger / Trade Journal, Outcome Tracking, statistical performance reporting, and validation of Context Engine outputs.

Context Engine v1 is complete.

Signal Ledger v1 foundation is implemented.

Portfolio / Risk Evaluation is postponed and parked until real EXOS usage proves it is needed.

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

Status: v1 legacy/supporting path, Canonical Brain Adapter v1 opt-in path, and Analysis Pipeline v2 foundation implemented.

Analysis Pipeline public contracts and deterministic execution include:

- `AnalysisRequest`
- `AnalysisResult`
- `PipelineConfig`
- `analyze_symbol`
- `analyze_symbol_with_canonical_brain`
- `CanonicalAnalysisResultV1`
- `AnalysisPipelineV2Request`
- `CanonicalAnalysisResultV2`
- `analyze_symbol_v2`
- `AnalysisReport`
- `build_analysis_report`

`analyze_symbol` remains the legacy/supporting Analysis Pipeline entry point.

It can build a snapshot from request-provided OHLCV rows using the existing Core Indicator / Snapshot Builder path.

It can then compute Probability and Prediction from request-provided similar-pattern fixtures using existing public Probability Engine and Prediction Engine APIs.

It can then compute Strategy using the existing public Strategy Engine API.

It can optionally run Backtest from request-provided deterministic future rows using existing public Backtest APIs:

- `BacktestInput`
- `run_backtest`
- `build_backtest_report`

`analyze_symbol_with_canonical_brain` is the opt-in canonical Brain v1 analysis path.

It uses Canonical Brain Adapter v1 to run:

Similar Pattern Resolver
-> Probability Engine
-> Price Projection
-> Target Zone
-> Risk Zone
-> Prediction Summary

It returns `CanonicalAnalysisResultV1` because canonical Prediction Summary is nested and does not map cleanly to the older flat `AnalysisResult.prediction` shape.

Canonical Brain Adapter v1 is implemented.

It provides the shared adapter used by `analyze_symbol_with_canonical_brain()` and `analyze_symbol_v2()`.

It runs:

Similar Pattern Resolver
-> Probability Engine
-> Price Projection
-> Target Zone
-> Risk Zone
-> Prediction Summary

Analysis Pipeline v2 is implemented as an additive canonical orchestration layer.

It accepts `AnalysisPipelineV2Request` and returns `CanonicalAnalysisResultV2`.

It supports:

- request-provided OHLCV rows
- optional `MarketDataSource` OHLCV loading
- request-provided deterministic future rows
- optional `MarketDataSource.load_future_rows`
- Canonical Brain Adapter v1
- local Strategy Engine v1 adaptation
- local Backtest Framework v1 adaptation
- local direct Backtest & Validation v1 adaptation
- opt-in Backtest Persistence v1 delegation

The v2 Opt-in Persistence Adapter is implemented.

It persists only when all are true:

- `persist_results=True`
- a SQLite `persistence_connection` is supplied
- v2 has produced a valid `BacktestRunV1`
- v2 has produced a valid `ValidationReportV1`

It delegates to existing `persist_backtest_run_v1()` and stores `BacktestPersistenceSummaryV1` in `CanonicalAnalysisResultV2.persistence`.

If persistence is not eligible, v2 leaves `persistence` as `None` and adds a deterministic skip note.

`analyze_symbol` remains legacy/supporting and unchanged. It continues to use the older statistics probability/prediction helper path for compatibility.

`analyze_symbol` still raises `NotImplementedError` when no OHLCV rows are supplied because latest snapshot loading is not implemented yet.

The legacy `analyze_symbol` path does not call AI, live data, broker paths, network paths, SQLite, DB-backed Backtest runners, or the database.

Analysis Pipeline v2 does not call AI, live data, broker paths, network paths, or DB-backed Backtest runners. Its optional SQLite interaction is limited to explicit opt-in delegation to Backtest Persistence v1.

Backtest remains empty/default unless deterministic future rows are supplied on the request or loaded by v2 through `MarketDataSource.load_future_rows`.

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
- `tests/unit/test_canonical_brain_adapter.py`
- `tests/unit/test_canonical_pipeline.py`
- `tests/unit/test_analysis_pipeline_v2.py`
- `tests/smoke/test_analysis_pipeline.py`
- `tests/smoke/test_canonical_brain_adapter.py`
- `tests/smoke/test_canonical_pipeline_entry_point.py`
- `tests/smoke/test_analysis_pipeline_v2.py`

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

### Context Engine v1

Status: Complete.

Context Engine v1 introduces `src/context` with immutable serializable context contracts and pure deterministic calculators:

- `ContextRequest`
- `MarketContext`
- `SectorContext`
- `RelativeStrengthContext`
- `VolumeContext`
- `SupportResistanceContext`
- `ContextResult`

The engine is deterministic and has no runtime dependency on frozen Brain v1 internals.

It is not wired into the default Analysis Pipeline, Strategy Engine, Backtest, Data Source, or GUI.

It does not call AI.

It does not call network services.

It does not call broker or live trading paths.

Current tests:

- `tests/unit/test_context_contracts.py`
- `tests/unit/test_market_context_calculator.py`
- `tests/unit/test_sector_context_calculator.py`
- `tests/unit/test_relative_strength_calculator.py`
- `tests/unit/test_volume_context_calculator.py`
- `tests/unit/test_support_resistance_calculator.py`

### Market Context Calculator v1

Status: Implemented.

Market Context Calculator v1 adds a deterministic pure calculator in `src/context` that derives `MarketContext` from available analysis outputs:

- snapshot
- probability
- prediction
- strategy

The calculator handles missing or malformed inputs gracefully and returns the existing immutable `MarketContext` contract.

It is exported through the context package as:

- `calculate_market_context`
- `calculate_market_context_from_analysis`

It does not modify frozen Brain v1 contracts.

It does not write to the database.

It does not call AI.

It does not call network services.

It does not call broker or live trading paths.

Current tests:

- `tests/unit/test_market_context_calculator.py`

### Support / Resistance Context Calculator v1

Status: Implemented.

Support / Resistance Context Calculator v1 adds a deterministic pure calculator in `src/context` that derives `SupportResistanceContext` from available local analysis inputs:

- snapshot market-structure levels
- indicator levels such as EMA/SMA/VWAP values
- supplied OHLCV price rows
- explicit or inferred current price

The calculator identifies nearest support and resistance when enough local data exists and returns support/resistance distance percentages as the existing contract's level-quality fields.

It is exported through the context package as:

- `calculate_support_resistance_context`
- `calculate_support_resistance_context_from_analysis`

It does not modify frozen Brain v1 contracts.

It does not write to the database.

It does not call AI.

It does not call network services.

It does not call broker or live trading paths.

Current tests:

- `tests/unit/test_support_resistance_calculator.py`

### Volume Context Calculator v1

Status: Implemented.

Volume Context Calculator v1 adds a deterministic pure calculator in `src/context` that derives `VolumeContext` from available local analysis inputs:

- snapshot volume fields
- indicator volume fields
- supplied OHLCV volume rows
- explicit current, average, or relative volume values

The calculator estimates relative volume when enough local data exists and classifies volume regime as:

- `low`
- `normal`
- `high`
- `spike`
- `unknown`

It returns `relative_volume` as the existing contract's numeric volume-quality field and `volume_state` as the regime label.

It is exported through the context package as:

- `calculate_volume_context`
- `calculate_volume_context_from_analysis`

It does not modify frozen Brain v1 contracts.

It does not write to the database.

It does not call AI.

It does not call network services.

It does not call broker or live trading paths.

Current tests:

- `tests/unit/test_volume_context_calculator.py`

### Relative Strength Context Calculator v1

Status: Implemented.

Relative Strength Context Calculator v1 adds a deterministic pure calculator in `src/context` that derives `RelativeStrengthContext` from local performance inputs:

- symbol OHLCV rows
- optional market benchmark OHLCV rows
- optional sector benchmark OHLCV rows
- explicit symbol, benchmark, or sector performance values

The calculator compares symbol performance against available benchmark data and classifies relative strength as:

- `outperform`
- `neutral`
- `underperform`
- `unknown`

It returns `stock_vs_market` and `stock_vs_sector` as the existing contract's numeric relative-strength quality fields.

It is exported through the context package as:

- `calculate_relative_strength_context`
- `calculate_relative_strength_context_from_analysis`

It does not modify frozen Brain v1 contracts.

It does not write to the database.

It does not call AI.

It does not call network services.

It does not call broker or live trading paths.

Current tests:

- `tests/unit/test_relative_strength_calculator.py`

### Sector Context Calculator v1

Status: Implemented.

Sector Context Calculator v1 adds a deterministic pure calculator in `src/context` that derives `SectorContext` from local performance inputs:

- symbol OHLCV rows
- sector benchmark OHLCV rows
- optional industry benchmark OHLCV rows
- explicit symbol, sector, or industry performance values

The calculator classifies sector trend as:

- `up`
- `sideways`
- `down`
- `unknown`

It classifies sector strength in the existing `relative_to_market` contract field as:

- `strong`
- `neutral`
- `weak`
- `unknown`

It returns `trend` and `relative_to_market` as the existing contract's sector quality fields.

It is exported through the context package as:

- `calculate_sector_context`
- `calculate_sector_context_from_analysis`

It does not modify frozen Brain v1 contracts.

It does not write to the database.

It does not call AI.

It does not call network services.

It does not call broker or live trading paths.

Current tests:

- `tests/unit/test_sector_context_calculator.py`

### Session Report - 2026-07-01

Status: Context Engine v1 complete.

Completed calculators:

- Market Context Calculator v1
- Sector Context Calculator v1
- Relative Strength Context Calculator v1
- Volume Context Calculator v1
- Support / Resistance Context Calculator v1

All Context Engine v1 calculators are pure, deterministic, modular under `src/context`, and exported through `src/context/__init__.py`.

Context Engine v1 does not modify frozen Brain v1 contracts.

Context Engine v1 does not write to the database.

Context Engine v1 does not call AI.

Context Engine v1 does not call network services.

Context Engine v1 does not call broker or live trading paths.

### Signal Ledger v1 Foundation

Status: Implemented as a storage-neutral contracts foundation.

Signal Ledger v1 Foundation introduces `src/signal_ledger` with immutable serializable contracts for recording EXOS-generated signals:

- `SignalType`
- `SignalSnapshotReference`
- `SignalRecord`

The foundation captures:

- symbol
- signal date
- snapshot reference
- context summary
- strategy summary
- signal type
- confidence
- notes

It is deterministic and storage-neutral.

It does not modify frozen Brain v1 contracts.

It does not write to the database.

It does not call AI.

It does not call network services.

It does not call broker or live trading paths.

Current tests:

- `tests/unit/test_signal_ledger_contracts.py`

## Not Implemented Yet

- Analysis Pipeline latest snapshot loading
- Analysis Pipeline DB-backed Backtest orchestration
- Historical replay persistence from stored datasets
- Advanced Backtest Persistence report/query APIs
- UI Backtest reports
- AI Analysis / Overlay
- UI reports for Market Learning and Prediction output

## Parked / Future

- Portfolio / Risk Evaluation
- Portfolio allocation
- Portfolio diversification analysis
- Correlation analysis
- Capital allocation
- Portfolio optimisation

These are intentionally postponed. EXOS is currently focused on NASDAQ investment research, signal/outcome tracking, statistical performance reporting, and deterministic Context Engine work rather than portfolio management.

## Run

Application:

- `py -m src.main`

Pipeline smoke test:

- `py -m unittest discover -s tests`

Current test count:

- 425 tests

## History

Detailed milestone history has moved to `docs/CHANGELOG.md`.
