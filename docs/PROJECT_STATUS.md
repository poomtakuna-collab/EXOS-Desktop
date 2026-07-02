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

Canonical Result Model v1 contracts and adapter foundation are implemented.

Data Source v1 public contracts, deterministic memory source, and read-only SQLite source are implemented.

Analysis Service v1 is implemented.

Near-term EXOS focus is Signal Ledger / Trade Journal, Outcome Tracking, statistical performance reporting, and validation of Context Engine outputs.

Context Engine v1 is complete.

Signal Ledger v1 foundation is implemented.

Outcome Tracking v1 foundation is implemented.

Outcome Calculator v1 is implemented.

Signal Ledger Persistence v1 foundation and SQLite repository are implemented.

Daily Research Snapshot Persistence v2 foundation is implemented.

Daily Research Snapshot Persistence v2 is wired into explicit Manual Snapshot Save and Backfill flows.

Outcome SQLite Persistence v1 is implemented.

Outcome Evaluation Flow v1 foundation is implemented.

Performance Report v1 is implemented.

Performance Report Snapshot Health Summary is implemented.

EXOS Desktop Performance Surface v0 is implemented.

EXOS Desktop Symbol-scoped Performance v1 is implemented.

EXOS Desktop Research Surface v0 is implemented.

EXOS Desktop Research Surface v1 is implemented.

EXOS Desktop Signal History tab v0 is implemented.

EXOS Desktop Snapshot Detail Viewer is v2-aware and prefers full canonical Daily Research Snapshot payloads when available.

Manual Signal Backfill Service foundation is implemented.

Manual Evidence Loop Runner foundation is implemented.

EXOS Desktop Manual Evidence Loop action is implemented.

EXOS Desktop Manual Evidence Loop progress display is implemented.

Developer Reset Snapshot Tool is implemented and exposed through the EXOS Desktop Developer UI.

Snapshot Payload Inspection Report is complete.

SnapshotPayloadV2 contract and pure builder are implemented.

SnapshotPayloadV2 is wired into Daily Research Snapshot save JSON while preserving the existing table schema and SignalRecord compatibility projection.

Snapshot Detail UI displays SnapshotPayloadV2 sections in dedicated read-only tabs.

Chart -> Data Source v1 integration foundation is implemented.

Chart Data Source v1 integration coverage is implemented.

ChartWorkspace app integration coverage is implemented.

ChartWorkspace shared StateManager constructor wiring bug is fixed.

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

Architecture terminology decisions are maintained in `docs/ARCHITECTURE_DECISIONS.md`, including the accepted v1 decision that current `SignalRecord` rows are conceptually Daily Research Snapshots rather than trading decisions.

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

### Canonical Result Model v1

Status: Contracts and adapter foundation implemented.

Canonical Result Model v1 introduces `src/canonical_result` with immutable serializable result contracts for a stable future output boundary:

- `CanonicalIdentityV1`
- `CanonicalBrainResultV1`
- `CanonicalPredictionResultV1`
- `CanonicalContextResultV1`
- `CanonicalStrategyResultV1`
- `CanonicalBacktestResultV1`
- `CanonicalSignalSummaryV1`
- `CanonicalDiagnosticsV1`
- `CanonicalResultV1`

The model is additive and does not replace existing Brain v1, Strategy, Backtest, Context, Signal Ledger, or Outcome Tracking contracts.

Raw Brain sections remain dictionary-based inside `CanonicalBrainResultV1` so frozen Brain v1 outputs can be wrapped without mutation.

Canonical Result Model v1 includes a pure adapter foundation for mapping existing analysis result dictionaries or objects into the canonical identity, Brain, prediction, and diagnostics contracts.

Current adapter support is intentionally minimal:

- `build_canonical_result_v1`
- `build_canonical_identity_v1`
- `build_canonical_brain_result_v1`
- `build_canonical_prediction_result_v1`
- `build_canonical_diagnostics_v1`

Adapters are duck-typed and do not import Analysis Pipeline, Brain, Strategy, Backtest, Context, Signal Ledger, Outcome Tracking, database, network, broker, or AI modules.

Canonical Result Model v1 is not wired into Analysis Pipeline v1, Analysis Pipeline v2, GUI, AI, persistence, or runtime Signal Ledger creation yet.

It does not call AI.

It does not call network services.

It does not call broker or live trading paths.

It does not read from or write to the database.

Current tests:

- `tests/unit/test_canonical_result_adapters.py`
- `tests/unit/test_canonical_result_contracts.py`

### Canonical Result -> Signal Adapter v1

Status: Implemented.

Canonical Result -> Signal Adapter v1 adds a pure adapter for creating deterministic `SignalRecord` candidates from `CanonicalResultV1`:

- `build_signal_record_from_canonical_result`

The adapter maps available canonical fields into the existing Signal Ledger contract:

- symbol
- signal date
- snapshot id
- snapshot date
- timeframe
- source
- signal type
- confidence
- context summary
- strategy summary
- prediction summary nested under `strategy_summary["prediction_summary"]`
- notes

`CanonicalSignalSummaryV1` fields take precedence where present.

Missing context, strategy, prediction, or malformed optional sections produce deterministic defaults without raising.

The adapter does not modify `SignalRecord`.

The adapter does not modify `CanonicalResultV1`.

It does not create signals automatically.

It does not call repositories.

It does not read from or write to the database.

It does not call AI.

It does not call network services.

It does not call broker or live trading paths.

It does not import GUI modules.

Current tests:

- `tests/unit/test_canonical_result_signal_adapter.py`

### EXOS Desktop Manual Signal Creation Flow v1

Status: Implemented.

EXOS Desktop Manual Signal Creation Flow v1 adds an explicit Research tab save action for turning the current deterministic research result into a durable Signal Ledger record.

The flow is:

- selected dashboard/watchlist symbol
- Research analysis
- `CanonicalResultV1`
- Canonical Result -> Signal adapter
- `SignalRecord`
- Signal Ledger SQLite repository

The Research tab now exposes a `Save Signal` button that is enabled only when a valid `CanonicalResultV1` is available.

Successful saves show a lightweight confirmation and refresh Signal History automatically.

Duplicate saves are handled idempotently by deterministic signal ID and by symbol plus market date, checking both `signal_date` and `snapshot_reference.snapshot_date`, so repeated or payload-varied saves do not create accidental duplicate research signal records for the same market date.

The manual save path persists:

- symbol
- signal date
- snapshot id
- snapshot date
- timeframe
- signal type
- confidence
- context summary
- strategy summary
- notes

The Qt widget remains thin and delegates candidate persistence to Qt-free helpers.

It does not create signals automatically.

It does not evaluate outcomes.

It does not trigger Performance recalculation beyond refreshing existing views.

It does not call AI.

It does not call network services.

It does not call broker or live trading paths.

Current tests:

- `tests/unit/test_research_signal_save.py`
- `tests/unit/test_research_surface.py`
- `tests/unit/test_main_window_wiring.py`

### Manual Signal Backfill Service Foundation

Status: Implemented.

Manual Signal Backfill Service adds an explicit application service for backfilling missing research signals for a symbol.

The service:

- loads OHLCV rows from Data Source v1
- excludes the latest/current unconfirmed row with Analysis Cutoff Policy
- identifies missing market dates from existing Signal Ledger records
- runs Analysis Pipeline v2 for each missing market date using rows through that date only
- stamps the canonical signal candidate with the backfilled market date
- saves through the duplicate-safe manual Signal save flow

It is not wired into Desktop.

It does not add a scheduler.

It does not modify Brain v1.

It does not modify Analysis Pipeline contracts.

It does not modify Signal Ledger contracts.

Current tests:

- `tests/unit/test_signal_backfill_service.py`

### Manual Evidence Loop Runner Foundation

Status: Implemented.

Manual Evidence Loop Runner adds an explicit application service for running the current evidence loop steps in order:

- `backfill_missing_research_signals`
- `evaluate_saved_signal_outcomes`

The runner returns a JSON-safe summary that includes signals created and outcomes evaluated/skipped.

It does not add a scheduler.

It does not add a new engine.

It does not modify Brain v1.

It does not modify Analysis Pipeline contracts.

Current tests:

- `tests/unit/test_evidence_loop_runner.py`

### EXOS Desktop Manual Evidence Loop Action

Status: Implemented.

EXOS Desktop now provides an explicit `Run Evidence Loop` toolbar action for the selected dashboard/watchlist symbol.

The action starts a background Qt worker for `run_manual_evidence_loop`, disables the action while running, reports status-bar progress as backfilled snapshot dates are processed, refreshes Signal History and Performance after completion, and surfaces a lightweight status-bar summary or safe error status.

It does not run on startup.

It does not add a scheduler.

It does not add a new engine.

It does not modify Brain v1.

It does not modify Analysis Pipeline contracts.

Current tests:

- `tests/unit/test_main_window_wiring.py`

### Analysis Cutoff Policy v1 Foundation

Status: Implemented.

Analysis Cutoff Policy v1 adds a small deterministic helper for separating chart recency from analysis recency:

- `chart_latest_date`
- `analysis_cutoff_date`

Policy:

- if the latest OHLCV row is the current trading day, analysis uses the previous completed trading day
- otherwise analysis uses the latest available completed row

The helper is JSON-safe through `to_dict()`.

Desktop Research analysis now uses rows through `analysis_cutoff_date`.

Desktop Chart loading now filters rendered OHLCV rows through the same `analysis_cutoff_date`.

Research layout is unchanged.

Signal creation is unchanged.

Outcome tracking is unchanged.

It does not modify Brain v1.

It does not add Research Zone UI.

Current tests:

- `tests/unit/test_analysis_cutoff_policy.py`
- `tests/unit/test_research_surface.py`
- `tests/unit/test_chart_data_adapter.py`

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

Status: Foundation session complete.

Completed work:

- Context Engine v1 complete
- Signal Ledger v1 foundation
- Outcome Tracking v1 foundation
- Outcome Calculator v1
- Signal Ledger repository foundation
- Signal Ledger SQLite Persistence v1
- Canonical Result Model v1 contracts
- Canonical Result Model v1 adapter foundation

Context Engine v1 completed deterministic calculators:

- Market Context Calculator v1
- Sector Context Calculator v1
- Relative Strength Context Calculator v1
- Volume Context Calculator v1
- Support / Resistance Context Calculator v1

All Context Engine v1 calculators are pure, deterministic, modular under `src/context`, and exported through `src/context/__init__.py`.

Signal Ledger v1 introduced immutable storage-neutral signal contracts for recording EXOS-generated research signals.

Outcome Tracking v1 introduced immutable storage-neutral outcome contracts plus a pure deterministic calculator for deriving outcome records from signal metadata and future OHLCV rows.

Outcome SQLite Persistence v1 introduced an explicit opt-in SQLite repository for standalone `OutcomeRecord` storage and direct lookup/list reads.

Outcome Evaluation Flow v1 introduced deterministic evaluation from saved signals and future OHLCV rows into completed persisted outcomes.

Performance Report v1 introduced deterministic aggregate reporting from signal and outcome repositories, now including a read-only Snapshot Health Summary for Desktop.

EXOS Desktop Performance Surface v0 introduced a read-only Performance tab in the main desktop app.

EXOS Desktop Symbol-scoped Performance v1 added selected-symbol filtering to the Performance tab while keeping global performance visible.

EXOS Desktop Research Surface v0 introduced a read-only Research tab in the main desktop app.

EXOS Desktop Research Surface v1 refined the Research tab into compact grouped information cards.

EXOS Desktop Research real analysis/context loading foundation connects the Research tab to read-only Data Source v1 rows and Analysis Pipeline v2 canonical Brain output when available.

EXOS Desktop Signal History tab v0 introduced a read-only signal/outcome history tab for the selected dashboard symbol.

Chart -> Data Source v1 integration foundation introduced a thin chart data adapter that tries Data Source v1 before falling back to the legacy desktop data loader.

Chart Data Source v1 integration coverage now verifies realistic SQLite-backed adapter reads, fallback behavior, deterministic ordering, and read-only guarantees.

ChartWorkspace app integration coverage now verifies the desktop Chart tab uses injected chart data loaders/adapters for successful loads, fallback paths, symbol switching, and repeated refreshes.

ChartWorkspace now receives the main desktop shared `StateManager` through keyword-based construction, preserving dashboard symbol propagation into the Chart tab.

SQLiteDataSource limited OHLCV loading now selects the latest matching rows and returns them in chronological ascending order for chart consumers.

OHLCV cache freshness now checks the latest cached daily row date instead of treating row count alone as fresh. Full caches older than the freshness threshold fall through to the existing provider-backed refresh path.

Signal Ledger repository foundation introduced a storage-neutral repository protocol and deterministic in-memory repository for signals and associated outcomes.

Signal Ledger SQLite Persistence v1 introduced a SQLite-backed repository for durable `SignalRecord` and linked `OutcomeRecord` storage.

Canonical Result Model v1 introduced immutable serializable contracts and a pure duck-typed adapter foundation for mapping existing analysis result dictionaries or objects into canonical identity, Brain, prediction, and diagnostics sections.

Canonical Result Model v1 remains additive and is not wired into Analysis Pipeline v1, Analysis Pipeline v2, GUI, AI, persistence, or runtime Signal Ledger creation yet.

Canonical Result -> Signal Adapter v1 now provides a pure candidate adapter from `CanonicalResultV1` to `SignalRecord`.

EXOS Desktop Manual Signal Creation Flow v1 now lets the user explicitly save the current Research result as a Signal Ledger record through the existing canonical adapter and SQLite repository.

Manual Signal Backfill Service foundation now provides an explicit no-GUI, no-scheduler service for filling missing research signals by market date while excluding the current unconfirmed row.

Manual Evidence Loop Runner foundation now provides an explicit no-GUI, no-scheduler service that runs signal backfill before outcome evaluation and returns a combined summary.

EXOS Desktop Manual Evidence Loop action now exposes that runner as an explicit toolbar action backed by a background Qt worker, and refreshes Signal History plus Performance after completion.

Analysis Cutoff Policy v1 now exposes `chart_latest_date` and `analysis_cutoff_date`, and Desktop Research analysis plus Desktop Chart loading use the cutoff date.

Context Engine v1 does not modify frozen Brain v1 contracts.

The completed foundation modules do not modify frozen Brain v1 contracts.

The completed foundation modules do not write to the database.

The completed foundation modules do not call AI.

The completed foundation modules do not call network services.

The completed foundation modules do not call broker or live trading paths.

Verification:

- `py -m unittest discover -s tests`
- 619 tests passing

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

### Outcome Tracking v1 Foundation

Status: Implemented as a storage-neutral contracts foundation.

Outcome Tracking v1 Foundation introduces `src/outcome_tracking` with immutable serializable contracts for tracking outcomes after EXOS-generated signals:

- `OutcomeStatus`
- `OutcomeRecord`

The foundation captures:

- symbol
- signal date
- evaluation date
- horizon days
- entry price
- close price
- return percentage
- max runup percentage
- max drawdown percentage
- target hit flag
- stop hit flag
- outcome status / rating
- notes

It is deterministic and storage-neutral.

It does not implement outcome calculators yet.

The foundation contracts themselves remain storage-neutral.

It does not modify frozen Brain v1 contracts.

It does not write to the database.

It does not call AI.

It does not call network services.

It does not call broker or live trading paths.

Current tests:

- `tests/unit/test_outcome_tracking_contracts.py`

### Outcome Calculator v1

Status: Implemented.

Outcome Calculator v1 adds a deterministic pure calculator in `src/outcome_tracking` that derives `OutcomeRecord` from signal metadata and future OHLCV rows.

The calculator uses:

- symbol
- signal date
- entry price
- future OHLCV rows
- horizon days
- optional target price
- optional stop price
- notes

It calculates:

- close price at horizon
- return percentage
- max runup percentage
- max drawdown percentage
- target hit flag
- stop hit flag
- outcome status

It gracefully handles missing or malformed data and marks incomplete horizons as `open`.

It does not implement persistence.

It does not modify frozen Brain v1 contracts.

It does not write to the database.

It does not call AI.

It does not call network services.

It does not call broker or live trading paths.

Current tests:

- `tests/unit/test_outcome_calculator.py`

### Outcome SQLite Persistence v1

Status: Implemented.

Outcome SQLite Persistence v1 introduces a standalone repository boundary for durable `OutcomeRecord` storage:

- `OutcomeRepository`
- `InMemoryOutcomeRepository`
- `SQLiteOutcomeRepository`
- `initialize_outcome_schema`

The repository interface includes:

- `save_outcome`
- `load_outcome`
- `list_outcomes`
- `list_outcomes_for_signal`

The SQLite implementation stores outcomes in `outcome_records`.

It supports direct outcome lookup by repository-owned `outcome_id`, deterministic listing by insertion order, deterministic listing per signal, optional symbol filtering, and persistence across repository instances that share the same SQLite database.

`save_outcome(signal_id, outcome)` remains compatible with existing outcome-save call shape, with optional `outcome_id` support for direct lookup.

The SQLite implementation stores notes as deterministic JSON strings and round-trips known `OutcomeStatus` values or custom status strings without validation side effects.

It is not wired into Analysis Pipeline, GUI, Signal Ledger, Canonical Result Model, Brain v1, or runtime creation flows.

It does not modify frozen Brain v1 contracts.

It writes only through explicit repository calls supplied with a SQLite connection.

It does not call AI.

It does not call network services.

It does not call broker or live trading paths.

Current tests:

- `tests/unit/test_outcome_repository.py`
- `tests/unit/test_outcome_sqlite_repository.py`

### Outcome Evaluation Flow v1 Foundation

Status: Implemented.

Outcome Evaluation Flow v1 adds a deterministic service for evaluating saved `SignalRecord` entries against supplied future OHLCV rows and persisting completed `OutcomeRecord` results through the existing Outcome repository boundary.

The flow is:

- saved signals from Signal Ledger repository
- future OHLCV rows after signal date
- Outcome Calculator v1
- Outcome SQLite repository

Signals with existing persisted outcomes are skipped without overwrite.

Signals without enough future rows for their horizon are skipped safely without persisting partial/open outcomes.

It does not modify `SignalRecord`.

It does not modify `OutcomeRecord`.

It does not modify Brain v1.

It does not wire Desktop runtime behavior.

Current tests:

- `tests/unit/test_outcome_evaluation.py`

### Performance Report v1

Status: Implemented.

Performance Report v1 introduces `src/performance_report` with deterministic aggregate reporting over existing signal and outcome repositories:

- `PerformanceReport`
- `build_performance_report`

The report includes:

- total signals
- total outcomes
- completed outcomes
- pending outcomes
- outcome coverage
- duplicate snapshots
- last snapshot date
- last outcome evaluation date
- win rate
- average return
- average max drawdown
- outcome status distribution
- signal type breakdown
- confidence bucket breakdown

The report supports JSON-safe `to_dict()` output.

It gracefully handles empty repositories with zero totals, zero averages, empty observed distributions, and stable zero-filled confidence buckets.

Win rate is calculated over stored outcomes. Numeric positive returns are treated as wins; if return percentage is missing, positive or target-hit outcome status is used as a fallback.

Average return and average max drawdown are calculated only from outcomes that provide those numeric values.

Distributions are deterministic and stable.

It is not wired into Analysis Pipeline, GUI, Signal Ledger, Outcome Tracking persistence, Canonical Result Model, Brain v1, or runtime creation flows.

It does not introduce a new engine.

It does not modify frozen Brain v1 contracts.

It does not write to the database.

It does not call AI.

It does not call network services.

It does not call broker or live trading paths.

It does not implement portfolio analysis.

Current tests:

- `tests/unit/test_performance_report.py`

### EXOS Desktop Performance Surface v0

Status: Implemented.

EXOS Desktop Performance Surface v0 adds a read-only Performance tab to the main `MainWindow` central workspace.

The central desktop workspace now includes:

- Chart tab
- Performance tab

The Performance tab displays Performance Report v1 output:

- total signals
- total outcomes
- Snapshot Health Summary:
  - total snapshots
  - completed outcomes
  - pending outcomes
  - outcome coverage
  - duplicate snapshots
  - last snapshot date
  - last outcome evaluation date
- win rate
- average return
- average max drawdown
- outcome status distribution
- signal type breakdown
- confidence bucket breakdown

The UI uses a thin Qt panel and a Qt-free view-model/helper module:

- `PerformancePanel`
- `load_desktop_performance_report`
- `build_performance_view_model`

The data loader opens `database/exos.db` read-only when it exists and uses existing SQLite repository implementations only when their tables are present.

Missing database files or missing repository tables render an empty report without creating or modifying storage.

The UI provides a manual Refresh action.

Business logic remains in `src/performance_report`.

It does not create standalone demo scripts.

It does not introduce a new engine.

It does not modify frozen Brain v1 contracts.

It does not add AI, network, broker, portfolio, or trading actions.

Current tests:

- `tests/unit/test_performance_surface.py`

### EXOS Desktop Symbol-scoped Performance v1

Status: Implemented.

EXOS Desktop Symbol-scoped Performance v1 improves the existing Performance tab so it can display performance for the currently selected dashboard/watchlist symbol.

The Performance tab now shows:

- selected symbol scope when a dashboard symbol is active
- symbol-filtered total signals
- symbol-filtered total outcomes
- symbol-filtered win rate
- symbol-filtered average return
- symbol-filtered average max drawdown
- symbol-filtered outcome status distribution
- symbol-filtered signal type breakdown
- symbol-filtered confidence bucket breakdown
- a compact global performance reference summary

Filtering is handled through the existing `PerformanceReport` builder and repository filtering paths.

Missing or empty selected-symbol records render a clear empty state.

The UI wiring remains thin and consumes Qt-free view-model helpers.

It does not introduce a new engine.

It does not modify frozen Brain v1 contracts.

It does not add AI, broker, portfolio, trading actions, or runtime auto-persistence.

Current tests:

- `tests/unit/test_performance_report.py`
- `tests/unit/test_performance_surface.py`

### EXOS Desktop Research Surface v0

Status: Implemented.

EXOS Desktop Research Surface v0 adds a read-only Research tab to the main `MainWindow` central workspace.

The central desktop workspace now includes:

- Chart tab
- Research tab
- Performance tab

When a dashboard symbol is selected, the Research tab displays the selected symbol and available deterministic research sections:

- Symbol
- Market Context
- Sector Context
- Relative Strength
- Volume Context
- Support / Resistance
- Prediction Summary
- Strategy Summary
- Signal Summary placeholder

The Research tab uses current `StateManager` selection and indicator snapshot data populated by the existing chart/data-loading path.

Available context sections are derived through existing context calculators.

Prediction and Strategy sections use existing deterministic summary builders with empty-safe inputs.

Signal Summary is explicitly shown as a v0 placeholder.

The UI uses a thin Qt panel and a Qt-free view-model/helper module:

- `ResearchPanel`
- `build_research_view_model`

Graceful empty states are shown when no symbol is selected or no deterministic snapshot data is loaded.

It does not create standalone demo scripts.

It does not introduce a new engine.

It does not modify frozen Brain v1 contracts.

It does not add AI, broker, portfolio, trading actions, or runtime auto-persistence.

Current tests:

- `tests/unit/test_research_surface.py`

### EXOS Desktop Research Surface v1

Status: Implemented.

EXOS Desktop Research Surface v1 refines the existing Research tab into grouped card-style panels.

Cards include:

- Symbol
- Market Context
- Sector Context
- Relative Strength
- Volume
- Support / Resistance
- Prediction
- Strategy
- Signal Summary placeholder

Each card uses compact label/value rows and consistent spacing.

Unknown or missing values are rendered as muted placeholders instead of repeated `unknown` text.

The Research Qt widget consumes only the card view model.

The Qt-free view model exposes future-ready rows for values such as confidence, probability-compatible evidence, score, similarity, and notes.

Business logic remains in existing context and analysis summary modules.

It does not introduce a new engine.

It does not modify frozen Brain v1 or Context Engine contracts.

It does not add AI, broker, portfolio, trading actions, or runtime auto-persistence.

Current tests:

- `tests/unit/test_research_surface.py`

### EXOS Desktop Research Real Analysis Loading Foundation

Status: Implemented.

The Research tab now attempts to load real deterministic research context for the selected dashboard symbol from existing local data.

The read-only loading path is:

Research tab
-> `load_desktop_research_view_model`
-> Data Source v1 `MarketDataSource.load_ohlcv`
-> default read-only `SQLiteDataSource` over `database/exos.db`
-> Analysis Pipeline v2 canonical Brain adapter
-> existing Context calculators
-> existing Prediction and Strategy summary helpers
-> grouped Research card view model

When local OHLCV rows are available, the Research cards can now show real deterministic values for:

- Market Context
- Volume
- Support / Resistance
- Prediction Summary safe defaults from canonical Brain output
- Strategy Summary derived from deterministic prediction output where available

Sector Context and Relative Strength remain placeholder-capable when no sector or benchmark rows are available.

Signal Summary remains a placeholder until explicit Signal creation is implemented.

Missing databases, missing rows, and analysis failures render graceful empty or error states without writing to storage.

Normal Research loading remains read-only and does not call providers.

It does not introduce a new engine.

It does not modify frozen Brain v1 or Context Engine contracts.

It does not add AI, broker, portfolio, trading actions, or auto-persistence.

Current tests:

- `tests/unit/test_research_surface.py`

### EXOS Desktop Signal History tab v0

Status: Implemented.

EXOS Desktop Signal History tab v0 adds a read-only Signal History tab to the main `MainWindow` central workspace.

The central desktop workspace now includes:

- Chart tab
- Research tab
- Performance tab
- Signal History tab

When a dashboard/watchlist symbol is selected, the tab loads saved signals for that symbol from `database/exos.db` using the existing Signal Ledger SQLite repository in read-only mode.

The table displays:

- signal date
- signal type
- confidence
- snapshot date/id
- linked outcome count
- latest linked outcome status / return

Missing database files, missing Signal Ledger tables, no selected symbol, and no matching records render graceful empty states.

The UI uses a thin Qt panel and a Qt-free view-model/data-loading helper:

- `SignalHistoryPanel`
- `load_desktop_signal_history_view_model`
- `build_signal_history_view_model`

It does not create standalone demo scripts.

It does not introduce a new engine.

It does not modify frozen Brain v1 contracts.

It does not add AI, broker, portfolio, trading actions, or runtime auto-persistence.

Current tests:

- `tests/unit/test_signal_history_surface.py`

### Chart -> Data Source v1 Integration Foundation

Status: Implemented.

Chart -> Data Source v1 Integration Foundation introduces a thin deterministic chart data adapter between the desktop Chart surface and data loading:

- `ChartDataAdapter`
- `LegacyChartDataLoader`

The current legacy chart path remains available and unchanged as a fallback:

Chart tab
-> `ChartWorkspace`
-> `DataManager.get_cached_historical_data`
-> SQLite cache through `DatabaseManager`
-> if insufficient rows, `DataManager.get_historical_data`
-> legacy provider fetch / SQLite upsert path
-> existing chart rendering

The foundation path is:

Chart tab
-> `ChartWorkspace`
-> `ChartDataAdapter`
-> Data Source v1 `MarketDataSource.load_ohlcv`
-> existing Data Source v1 implementations such as `SQLiteDataSource`
-> existing chart rendering

If Data Source v1 has no rows, has insufficient rows for the refresh path, is unavailable, or raises a supported load error, the adapter falls back to the existing legacy `DataManager` path.

The chart widget still receives the existing `HistoricalDataResult` shape.

Chart appearance and rendering behavior are preserved.

The default desktop adapter opens `database/exos.db` read-only for SQLite Data Source v1 reads.

Limited SQLite OHLCV reads select the newest matching rows first, then return the chart-facing row set in date-ascending order.

Normal cached chart loads remain read-only. When a full cached set is stale, the explicit historical refresh path can fall back to `DataManager`, provider fetch, and SQLite upsert.

It does not retire the legacy chart loader yet.

It does not introduce a new engine.

It does not modify frozen Brain v1 contracts.

It does not add AI, broker, portfolio, trading actions, or runtime auto-persistence.

Current tests:

- `tests/unit/test_data_manager.py`
- `tests/unit/test_chart_data_adapter.py`
- `tests/integration/test_chart_data_adapter_sqlite_integration.py`
- `tests/integration/test_chart_workspace_adapter_integration.py`

### Signal Ledger Persistence v1 Foundation

Status: Storage-neutral repository foundation and SQLite repository implemented.

Signal Ledger Persistence v1 Foundation introduces repository contracts, an in-memory implementation, and a SQLite implementation for saving and loading `SignalRecord` and associated `OutcomeRecord` values:

- `SignalLedgerRepository`
- `InMemorySignalLedgerRepository`
- `SQLiteSignalLedgerRepository`
- `initialize_signal_ledger_schema`

The repository interface includes:

- `save_signal`
- `load_signal`
- `list_signals`
- `save_outcome`
- `list_outcomes_for_signal`

The in-memory implementation is deterministic, JSON-serializable through `to_dict()`, and intended for tests and foundation use only.

The SQLite implementation stores signals in `signal_ledger_signals` and linked outcomes in `signal_ledger_outcomes`.

The SQLite implementation stores nested signal context, strategy summaries, and notes as deterministic JSON strings.

The SQLite implementation stores outcome notes as deterministic JSON strings and preserves outcome insertion order per signal.

The SQLite implementation supports persistence across repository instances that share the same SQLite database.

It is not wired into the runtime Analysis Pipeline, GUI, Canonical Result Model, or Signal Ledger creation flow yet.

It does not modify frozen Brain v1 contracts.

It writes only through explicit repository calls supplied with a SQLite connection.

It does not call AI.

It does not call network services.

It does not call broker or live trading paths.

Current tests:

- `tests/unit/test_signal_ledger_repository.py`
- `tests/unit/test_signal_ledger_sqlite_repository.py`

### Daily Research Snapshot Persistence v2 Foundation

Status: Implemented.

Daily Research Snapshot Persistence v2 adds an additive immutable SQLite persistence layer for full canonical daily research snapshots:

- `DailyResearchSnapshotRecord`
- `SQLiteDailyResearchSnapshotRepository`
- `initialize_daily_research_snapshot_schema`

The v2 table is `daily_research_snapshots`, separate from `signal_ledger_signals`.

It stores the full lossless `CanonicalResultV1.to_dict()` payload as deterministic pretty/sorted JSON.

It preserves existing `SignalRecord` and Signal Ledger compatibility contracts unchanged.

The unique immutable identity is:

- symbol
- market date
- timeframe
- canonical schema version
- persistence version

Save behavior is insert-only:

- same identity plus same payload hash returns the existing record idempotently
- same identity plus different payload hash raises an immutable conflict
- different schema/version records may coexist

The stable `snapshot_record_id` is generated from the v2 identity and does not depend on legacy or empty `snapshot_id` values.

It is wired into explicit Manual Snapshot Save and Manual Snapshot Backfill flows, where v2 canonical rows are saved alongside existing Signal Ledger compatibility records.

Snapshot History detail now prefers the v2 canonical payload when available and falls back to the legacy reduced `SignalRecord` detail when v2 is missing.

It is not wired into Outcome Evaluation or Performance reporting yet.

It does not modify frozen Brain v1 contracts.

It does not modify `SignalRecord`.

It does not modify existing Signal Ledger repository behavior.

Current tests:

- `tests/unit/test_daily_research_snapshot_sqlite_repository.py`

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

- 639 tests

## History

Detailed milestone history has moved to `docs/CHANGELOG.md`.
