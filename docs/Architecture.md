# Architecture

## Design Philosophy

EXOS Desktop is a local-first investment research platform.

The core system is deterministic. AI is an optional explanation layer and must not control data loading, indicator calculation, statistics, strategy, backtest, persistence, or risk logic.

EXOS outputs structured evidence, probabilities, price zones, strategy context, backtest results, and reports. It does not output BUY, SELL, or HOLD recommendations.

Completed v1 contracts are frozen. New functionality should extend the system with additive modules unless a verified bug requires a targeted contract fix.

## Architectural Flow

The frozen EXOS Brain v1 flow is:

Market Data
-> Core Indicators
-> Snapshot
-> Statistics
-> Outcome
-> Pattern Discovery
-> Pattern Library
-> Similarity
-> Probability
-> Prediction

Within `src.analysis`, the canonical Brain v1 prediction path is:

Similar Pattern Resolver
-> Probability Engine
-> Price Projection
-> Target Zone
-> Risk Zone
-> Prediction Summary

The extended deterministic research flow is:

Market Data
-> Core Indicators
-> Snapshot
-> Statistics
-> Probability / Prediction
-> Strategy
-> Backtest
-> Validation
-> Persistence
-> Report / UI / optional AI explanation

Near-term roadmap focus after Foundation v1 is:

- Signal Ledger / Trade Journal
- Outcome Tracking
- Statistical performance reporting
- EXOS Context Engine v1

Portfolio / Risk Evaluation is postponed. EXOS is a NASDAQ investment research platform first, not a portfolio management system. Portfolio work should remain experimental / future / parked until real EXOS usage proves it is needed.

## Layered Architecture

### Presentation Layer

Owned by `src/gui` and launched through `src/app`.

Responsibilities:

- Windows, panels, charts, menus, and user interaction.
- Calling application/business services.
- Displaying structured outputs.

Rules:

- Presentation code should not query SQLite directly.
- Presentation code should not reimplement analysis, strategy, backtest, or persistence logic.

### Application Layer

Owned by `src/application` and `src/app`.

Responsibilities:

- Wire data sources to deterministic analysis pipelines.
- Own application-level orchestration for user workflows.
- Keep GUI code separated from business module details.

Rules:

- Application services may call data-source interfaces and business-layer APIs.
- Application services should not mutate frozen engine contracts.

### Business Layer

Owned by `src/analysis`, `src/statistics`, `src/strategy`, `src/backtest`, and `src/analysis_pipeline`.

Responsibilities:

- Build snapshots and deterministic indicators.
- Store and evaluate historical statistical evidence.
- Produce probability, prediction, strategy, backtest, validation, and report outputs.

Rules:

- Business modules should remain deterministic and testable with in-memory inputs.
- Business modules may depend on stable data contracts and read-only data-source boundaries.
- Business modules must not call live data, broker, or AI services directly.

### Data Layer

Owned by `src/data_source`, `src/data`, `src/database`, and SQLite-facing parts of `src/backtest`.

Responsibilities:

- Load market data.
- Provide read-only data-source boundaries for deterministic orchestration.
- Store and read local SQLite data.

Rules:

- `src/data_source` is the preferred read-only boundary for new orchestration.
- Older `src/data` and `src/database` paths may remain for legacy GUI/data-manager flows.
- New deterministic v1 paths should prefer additive adapters over changing older paths.

## Subsystem Ownership

### analysis

`src/analysis` owns deterministic snapshot and Brain v1 analysis engines:

- Core indicator calculations
- Snapshot building
- Similar Pattern Resolver
- Probability Engine
- Price Projection
- Target Zone
- Risk Zone
- Prediction Summary
- Strategy summary
- Trade plan
- Position sizing
- Strategy report

For probability and prediction, `src.analysis` is the canonical Brain v1 path. Future orchestration should target the sequence from Similar Pattern Resolver through Prediction Summary unless a versioned replacement is introduced.

This package is business logic. It should not depend on GUI, live data, broker execution, AI, or persistence writers.

### statistics

`src/statistics` owns market learning, stored historical evidence, and pattern support:

- Snapshot storage
- Outcome calculation
- Pattern discovery
- Pattern library
- Similarity

Older probability and prediction helpers under `src.statistics` are legacy/supporting unless they are explicitly wired into the canonical Brain v1 path. `snapshot_id` is the continuity key for stored market states. Statistics modules should preserve stored identifiers and avoid loading unnecessary historical data when targeted queries can be used.

### analysis_pipeline

`src/analysis_pipeline` owns orchestration and reporting around deterministic analysis outputs.

Future orchestration updates should treat the `src.analysis` Brain v1 engines as the target canonical path for probability and prediction. The pipeline may consume statistics-backed evidence, but it should not treat older statistics probability/prediction helpers as the canonical Brain v1 prediction path unless that wiring is explicit.

`analyze_symbol_with_canonical_brain()` is the opt-in canonical Brain v1 analysis path. It uses the Canonical Brain Adapter v1 and returns `CanonicalAnalysisResultV1`.

`analyze_symbol()` remains unchanged as the legacy/supporting Analysis Pipeline entry point. It continues to use the older statistics probability/prediction helper path for compatibility.

### strategy

`src/strategy` owns the Strategy Engine v1 public contracts and deterministic strategy scoring.

Strategy consumes structured upstream outputs. It does not calculate indicators, discover patterns, call AI, fetch data, persist data, or make buy/sell/hold recommendations.

### backtest

`src/backtest` owns deterministic backtest, validation, and backtest-owned persistence boundaries.

Backtest v1 has four additive paths with separate ownership:

- Legacy / in-memory replay engine: `BacktestInput`, `SimulationResult`, `BacktestResult`, replay engine, metrics aggregator, pipeline, and report. This is the supporting compatibility path for existing in-memory replay behavior and request-row Analysis Pipeline backtests.
- Direct Backtest & Validation v1 path: `TradeOutcomeV1`, trade outcome generation, trade simulator, `BacktestResultV1`, direct runner, and validation report. This is the canonical path for new v1 direct validation work where inputs are trade setups and future OHLCV rows rather than stored snapshot datasets.
- Read-only DB-backed dataset runner: SQLite snapshot, outcome, and future-row loaders, dataset builder, and read-only runner. This is a supporting bridge from stored datasets into the legacy in-memory replay framework. It reads source data and builds datasets; it is not the canonical direct validation path.
- Backtest Persistence v1: persistence contracts, schema constants, writer, reader, and orchestrator. This is the additive persistence boundary for direct v1 run outputs. Reader v1 remains direct lookup/list only; report/query APIs belong in a separate additive layer.

New backtest work must name which path it extends. Direct validation features should extend the direct Backtest & Validation v1 path first. Historical replay from stored snapshots should extend the read-only dataset runner and persistence layers without changing frozen replay contracts. Persistence work should not run simulation or strategy logic.

Backtest must not depend on Portfolio Engine. Portfolio / Risk Evaluation is parked and must remain outside default backtest execution.

### persistence

Persistence modules are owned by `src/backtest` and are described in the backtest ownership map. They form a boundary for storing and retrieving explicit Backtest v1 records.

Persistence modules should not implement strategy logic, trade simulation, portfolio logic, AI, broker execution, or live data access.

### data_source

`src/data_source` owns the preferred public read-only market-data boundary:

- Data-source contracts
- Deterministic memory source
- Read-only SQLite source

`MarketDataSource` implementations load OHLCV and future rows. They should return deterministic rows and avoid mutating source data.

Data Source must not depend on Portfolio Engine. Portfolio-specific account or position loading should be introduced only through a future explicit adapter if the parked Portfolio/Risk milestone is resumed.

### context

`src/context` owns the Context Engine v1 Foundation contracts.

Context Engine v1 Foundation is additive and contracts-only. It defines immutable serializable context records for future market, sector, relative strength, volume, and support/resistance work.

Current Context Engine foundation contracts:

- `ContextRequest`
- `MarketContext`
- `SectorContext`
- `RelativeStrengthContext`
- `VolumeContext`
- `SupportResistanceContext`
- `ContextResult`

Context Engine is not wired into the default pipeline yet.

Strategy, Backtest, Analysis Pipeline, Data Source, and GUI should not depend on Context Engine until explicit context layers are implemented, tested, and proven through Backtest.

Context Engine must not call AI, broker, live trading, or network services.

### portfolio

Portfolio / Risk Evaluation is parked as a future / experimental area.

Current roadmap direction:

- Do not wire Portfolio Engine into the default pipeline.
- Do not make Strategy, Backtest, Analysis Pipeline, Data Source, or Context Engine depend on Portfolio Engine.
- Do not treat portfolio allocation, diversification, or optimisation as near-term EXOS requirements.
- Keep any existing portfolio code isolated and deterministic if present.
- Keep any existing portfolio tests only while they pass and do not block the research-platform roadmap.

Portfolio work may be reconsidered later if real EXOS usage shows that portfolio-level allocation, exposure, or capital-management workflows are needed.

### application/gui

`src/application` owns application services. `src/gui` owns desktop presentation. `src/app` wires startup.

GUI code should depend on application services and display models, not database tables or engine internals. Application code may translate user workflows into calls to data-source and business-layer APIs.

## Public API Categories

Package-level `__init__` exports are convenience facades. An exported name is available for callers, but export presence alone does not mean every name is equally canonical for new work. Architectural ownership and the categories below decide which APIs should be preferred.

### src.analysis

- Frozen: Core Indicators v1 and snapshot-building contracts that feed the Brain v1 flow.
- Canonical v1: Similar Pattern Resolver, Probability Engine, Price Projection, Target Zone, Risk Zone, and Prediction Summary.
- Supporting: similarity helpers, strategy summary, trade plan, position sizing, and strategy report builders that consume structured Brain v1 outputs.
- Legacy: none currently designated as a primary legacy path in this package.
- Future/experimental: additive versioned analysis engines that may be introduced without changing frozen Brain v1 contracts.

### src.statistics

- Frozen: Market Learning Engine v1 storage and evidence contracts around snapshots, outcomes, discovered patterns, pattern library, and similarity.
- Canonical v1: stored market-learning support for the Brain v1 flow through snapshot/outcome persistence, pattern discovery, pattern library, and similarity evidence.
- Supporting: database schema helpers, snapshot collection, outcome calculation, and pattern statistics utilities.
- Legacy: older probability and prediction helpers unless explicitly wired into the canonical `src.analysis` Brain v1 probability/prediction path.
- Future/experimental: additive market-learning evidence APIs that preserve `snapshot_id` continuity and avoid replacing the canonical Brain v1 analysis path implicitly.

### src.backtest

`src.backtest.__init__` is a broad facade across several backtest-owned paths. Its exports include legacy replay contracts, direct Backtest & Validation v1 APIs, read-only DB-backed dataset runner APIs, and Persistence v1 APIs. These are convenience exports for callers, not a statement that all exports are equally canonical.

- Frozen: existing in-memory Backtest Framework contracts such as `BacktestInput`, `SimulationResult`, `BacktestResult`, replay engine, metrics, pipeline, and report.
- Canonical v1: direct Backtest & Validation v1 APIs such as trade outcome, trade simulator, `BacktestResultV1`, direct runner, and validation report for new direct validation work.
- Supporting: read-only DB-backed dataset runner and Backtest Persistence v1 contracts, schema, writer, reader, and orchestrator.
- Legacy: in-memory replay framework for compatibility and request-row Analysis Pipeline backtests.
- Future/experimental: walk-forward and advanced report/query layers only when added outside frozen contracts. Portfolio-related layers are parked until real usage proves they are needed.

### src.data_source

- Frozen: none currently designated beyond stable public contract expectations.
- Canonical v1: `MarketDataSource` contract, request/result records, `MarketDataRow`, and deterministic read-only source implementations.
- Supporting: in-memory source for tests and deterministic orchestration.
- Legacy: older data/database paths outside `src.data_source`.
- Future/experimental: additive source adapters that preserve the read-only boundary and deterministic result contracts. Portfolio/account sources are parked and should not be introduced as near-term dependencies.

### src.context

- Frozen: none currently designated.
- Canonical v1 foundation: immutable serializable context contracts in `src/context`.
- Supporting: future deterministic context calculators that consume explicit market data inputs.
- Legacy: none.
- Future/experimental: market, sector, industry, relative strength, volume, support/resistance, and optional macro context layers after validation.

### src.analysis_pipeline

- Frozen: existing request/result/config/report contracts that callers already depend on.
- Canonical v1: `analyze_symbol_with_canonical_brain()`, backed by Canonical Brain Adapter v1 and `src.analysis` Brain v1 engines for probability and prediction.
- Canonical v2: `analyze_symbol_v2()`, backed by Canonical Brain Adapter v1, v2-local Strategy / Backtest / Validation adapters, and opt-in Backtest Persistence v1 delegation.
- Supporting: report building and adapters that translate data-source rows into deterministic analysis outputs.
- Legacy: `analyze_symbol()` and other orchestration paths that rely on older statistics probability/prediction helpers unless explicitly aligned with the canonical Brain v1 path.
- Future/experimental: additive pipeline versions that route through canonical Brain v1 engines without mutating frozen contracts. Portfolio orchestration is parked and should not be part of default analysis pipelines.

## Canonical Analysis Pipeline Alignment

`src.analysis_pipeline` now has two explicit deterministic entry points.

`analyze_symbol()` builds snapshots through `src.analysis`, then computes probability and prediction through older `src.statistics` helpers. That path remains legacy/supporting and unchanged for compatibility.

`analyze_symbol_with_canonical_brain()` is the opt-in canonical Brain v1 path. It uses Canonical Brain Adapter v1 to run the canonical `src.analysis` sequence:

Similar Pattern Resolver
-> Probability Engine
-> Price Projection
-> Target Zone
-> Risk Zone
-> Prediction Summary

The opt-in canonical path returns `CanonicalAnalysisResultV1`, not `AnalysisResult`. This is intentional: canonical `Prediction Summary` is nested and carries probability, projection, target zone, and risk zone sections, so it does not map cleanly to the older flat `AnalysisResult.prediction` shape.

The legacy statistics probability/prediction helpers remain available for compatibility. New orchestration should prefer `analyze_symbol_with_canonical_brain()` when canonical Brain v1 probability/prediction output is required. Any future config switch should be introduced only after both paths remain explicitly named, tested, and documented.

## Analysis Pipeline v2 Foundation

Analysis Pipeline v2 is implemented as an additive canonical orchestration layer, not a replacement for `analyze_symbol()`.

Public entry point:

- `analyze_symbol_v2()`

Result contract:

- `CanonicalAnalysisResultV2`

The v2 pipeline keeps the canonical Brain output as a first-class nested result and adds downstream Strategy, Backtest / Validation, optional Persistence, metadata, and notes around it. It does not force canonical Prediction Summary into the older flat `AnalysisResult.prediction` field.

Implemented v2 flow:

MarketDataSource / request-provided rows
-> AnalysisRequest-compatible normalized rows
-> Canonical Brain Adapter v1
-> Strategy Engine v1
-> Backtest / Validation v1
-> optional Backtest Persistence v1
-> CanonicalAnalysisResultV2

### Inputs

The v2 entry point accepts an explicit request object rather than overloading the existing `AnalysisRequest` contract.

Request contract:

- `AnalysisPipelineV2Request`

Required fields:

- `symbol`
- `config`

Optional fields:

- `ohlcv_rows`
- `future_rows`
- `similar_patterns`
- `data_source`
- `start_date`
- `end_date`
- `limit`
- `persist_results`
- `persistence_connection`
- `run_id`
- `run_name`

Data loading rule:

- If `ohlcv_rows` are supplied, v2 uses those rows directly.
- If `ohlcv_rows` are absent and `data_source` is supplied, v2 calls `MarketDataSource.load_ohlcv()` with `MarketDataRequest`.
- If Backtest is enabled and `future_rows` are supplied, v2 uses those rows directly.
- If Backtest is enabled, `future_rows` are absent, `data_source` is supplied, and a snapshot date can be derived from the loaded OHLCV rows, v2 calls `MarketDataSource.load_future_rows()` with `FutureRowsRequest`.
- If no rows can be loaded, v2 returns a safe result with notes rather than calling legacy snapshot-loading paths implicitly.

### Canonical Brain Adapter

v2 calls `build_canonical_brain_analysis()` and preserves the full `CanonicalBrainAdapterResult`.

The adapter remains responsible for:

- Snapshot construction from OHLCV rows.
- Similar Pattern Resolver.
- Probability Engine.
- Price Projection.
- Target Zone.
- Risk Zone.
- Prediction Summary.

v2 does not reimplement those steps. It normalizes loaded rows into an `AnalysisRequest` only so the existing adapter can be reused.

### Strategy Layer

If Strategy is enabled and the canonical Brain output includes usable snapshot, probability, and prediction data, v2 calls `analyze_strategy()` with `StrategyInput`.

The Strategy input is derived from canonical Brain output:

- `snapshot`: `canonical_brain.snapshot`
- `probability`: `canonical_brain.probability`
- `prediction`: a Strategy-compatible projection dictionary derived from canonical Brain projection / target zone / risk zone / prediction summary

The derivation is an explicit v2-local adapter step because Strategy Engine v1 currently expects flat keys such as expected return and zone fields, while Canonical Brain Adapter v1 preserves nested prediction summary sections.

### Backtest / Validation

Backtest remains optional and deterministic.

v2 uses the existing request-row Backtest Framework compatibility path only when deterministic future rows are available:

- Build one `BacktestInput` from canonical snapshot, canonical probability, Strategy result, and future rows.
- Call existing `run_backtest()`.
- Call existing `build_backtest_report()`.

v2 also builds a direct Backtest & Validation v1 run through an explicit adapter from v2 strategy/backtest setup data to trade setup rows:

- `run_backtest_v1()`
- `build_validation_report()`

v2 does not call DB-backed Backtest orchestration by default. DB-backed replay remains a separate explicit workflow until its result and persistence semantics are intentionally aligned with v2.

### Optional Persistence

The opt-in Persistence Adapter is implemented as a v2-local adapter. `analyze_symbol_v2()` does not write persistence records directly.

v2 persists only when all are true:

- Persistence is enabled by `persist_results=True`.
- A SQLite connection is supplied on the v2 request.
- `CanonicalAnalysisResultV2.backtest_run` is a valid `BacktestRunV1`.
- `CanonicalAnalysisResultV2.validation_report` is a valid `ValidationReportV1`.
- The run has already been produced by v2 Backtest / Validation flow from deterministic future rows.

The v2 persistence adapter maps only this valid direct validation pair:

BacktestRunV1
+ ValidationReportV1
+ v2 request metadata
-> `persist_backtest_run_v1()`
-> `BacktestPersistenceSummaryV1`

The adapter passes through:

- `connection`: the explicit SQLite connection supplied by the request
- `backtest_run`: `CanonicalAnalysisResultV2.backtest_run`
- `validation_report`: `CanonicalAnalysisResultV2.validation_report`
- `run_id`: explicit request `run_id`, or deterministic v2 fallback `analysis-pipeline-v2:{symbol}:{timeframe}`
- `run_name`: explicit request `run_name`
- `symbols_json`: JSON list containing the v2 request symbol
- `timeframe`: v2 request timeframe
- `start_date`: v2 request start date or first loaded OHLCV row date
- `end_date`: v2 request end date or latest loaded OHLCV row date
- `snapshot_query_json`: JSON metadata describing v2 source mode, row counts, future row counts, and canonical adapter name
- `created_at`: left empty to preserve deterministic tests

The adapter does not inspect or mutate Backtest Persistence v1 records directly. It calls `persist_backtest_run_v1()` and returns its `BacktestPersistenceSummaryV1` as the v2 `persistence` field.

Persistence must not run strategy, simulation, data loading, AI, broker behavior, or live-data behavior.

Persistence ineligibility is explicit and non-fatal. If the opt-in flag is false, no persistence is attempted. If the flag is true but the connection is missing, the run or validation report is missing, future rows were unavailable, or Backtest / Validation was skipped, v2 returns a result with `persistence` as `None` and a deterministic note explaining why persistence was skipped.

Implemented persistence request flag:

- `persist_results: bool = False`

`persistence_connection` alone should not trigger writes. The connection and `persist_results=True` should both be required.

### Outputs

`CanonicalAnalysisResultV2` should include:

- request metadata
- normalized config
- symbol
- timeframe
- data source metadata
- loaded row counts
- canonical Brain adapter result
- Strategy result or `None`
- Backtest result/report or `None`
- Validation report or `None`
- Persistence summary or `None`
- metadata
- notes

The result should keep dataclass objects intact where practical. Serialization for UI, reports, or API display should be a separate adapter/reporting concern.

### Legacy And Supporting Boundaries

The following should remain legacy/supporting:

- `analyze_symbol()` and `AnalysisResult`
- older `src.statistics` probability/prediction helper wiring inside `analyze_symbol()`
- request-row in-memory Backtest Framework compatibility path
- DB-backed Backtest dataset runner until explicitly selected by a separate workflow
- older `src.data` / `src.database` paths outside the `MarketDataSource` boundary

The following should remain canonical/supporting for v2:

- `MarketDataSource` as the preferred read-only data-loading boundary
- `build_canonical_brain_analysis()` as the canonical Brain adapter call
- `analyze_strategy()` as the Strategy Engine v1 call
- existing Backtest APIs only through explicit adapter steps
- Backtest Persistence v1 only as an opt-in persistence boundary

## Dependency Direction

Allowed direction:

GUI
-> Application
-> Data Source / Business APIs
-> Data Layer where required

Business modules may depend on lower-level contracts and data-source abstractions, but lower-level data modules should not depend on GUI or application services.

Forbidden direction:

- Frozen core engines depending on GUI.
- Frozen core engines depending on AI, broker, or live network modules.
- Persistence modules depending on strategy/backtest internals beyond explicit record-building inputs.
- GUI querying SQLite directly.
- AI controlling deterministic core logic.

## Frozen Layers

The following are treated as frozen v1 foundations:

- EXOS Brain v1 flow
- Core Indicators v1
- Market Learning Engine v1
- Probability / Prediction v1 contracts
- Strategy Engine v1 contracts
- Existing Backtest v1 contracts
- Backtest & Validation v1 contracts once frozen
- Backtest Persistence v1 contracts once frozen

Frozen means downstream behavior should rely on the contract remaining stable. Fix verified bugs narrowly; add new behavior through adjacent modules or versioned contracts.

## Legacy And Additive Paths

Older paths may exist because EXOS is evolving by additive phases.

Examples:

- `src/data` / `src/database` coexist with newer `src/data_source`.
- `src.analysis` owns the canonical Brain v1 probability and prediction path; older `src.statistics` probability/prediction helpers are supporting unless explicitly wired into that path.
- Existing in-memory Backtest Framework contracts support compatibility and request-row replay.
- Direct Backtest & Validation v1 is canonical for new direct validation work.
- Read-only DB-backed dataset runner is a supporting bridge from stored datasets into legacy replay.
- Backtest Persistence v1 is additive storage and retrieval for direct v1 outputs, not a report/query layer.
- Existing Backtest DB schema skeleton coexists with direct Persistence v1 schema constants.

This is acceptable when the ownership boundary is explicit. New v1 work should avoid modifying older paths unless the task is specifically to migrate, deprecate, or fix them.

## Startup Flow

Runtime startup remains:

`src.main`
-> `src.app.Application`
-> `src.gui.MainWindow`
-> application services / managers
-> user interaction

## AI Boundary

AI is outside the deterministic core.

AI may read structured outputs and generate explanations or summaries. AI must not:

- Fetch or mutate source data.
- Generate core indicators, probabilities, strategy scores, backtest results, or persistence records.
- Make trading decisions.
- Output BUY, SELL, or HOLD recommendations.

## Persistence Boundary

SQLite is the local source of truth for reproducible historical research data.

Persistence code should:

- Use explicit contracts and schema fields.
- Preserve identifiers such as `snapshot_id` when replaying stored historical data.
- Keep direct reads/writes deterministic.
- Keep advanced report/query APIs separate from direct persistence primitives.

Persistence code should not:

- Recalculate indicators.
- Run strategy or trade simulation.
- Fetch live data.
- Call AI or broker services.

## Documentation Boundaries

- `docs/ROADMAP.md` contains long-term milestones.
- `docs/PROJECT_STATUS.md` contains current implementation status.
- `docs/Architecture.md` contains system architecture and dependency rules.

Avoid duplicating status inventories or roadmap planning in this document.
