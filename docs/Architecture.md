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

### persistence

Persistence modules are owned by `src/backtest` and are described in the backtest ownership map. They form a boundary for storing and retrieving explicit Backtest v1 records.

Persistence modules should not implement strategy logic, trade simulation, portfolio logic, AI, broker execution, or live data access.

### data_source

`src/data_source` owns the preferred public read-only market-data boundary:

- Data-source contracts
- Deterministic memory source
- Read-only SQLite source

`MarketDataSource` implementations load OHLCV and future rows. They should return deterministic rows and avoid mutating source data.

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
- Future/experimental: walk-forward, portfolio, advanced report/query, or other additive layers only when added outside frozen contracts.

### src.data_source

- Frozen: none currently designated beyond stable public contract expectations.
- Canonical v1: `MarketDataSource` contract, request/result records, `MarketDataRow`, and deterministic read-only source implementations.
- Supporting: in-memory source for tests and deterministic orchestration.
- Legacy: older data/database paths outside `src.data_source`.
- Future/experimental: additive source adapters that preserve the read-only boundary and deterministic result contracts.

### src.analysis_pipeline

- Frozen: existing request/result/config/report contracts that callers already depend on.
- Canonical v1: orchestration that targets `src.analysis` Brain v1 engines for probability and prediction.
- Supporting: report building and adapters that translate data-source rows into deterministic analysis outputs.
- Legacy: orchestration paths that rely on older statistics probability/prediction helpers unless explicitly aligned with the canonical Brain v1 path.
- Future/experimental: additive pipeline versions that route through canonical Brain v1 engines without mutating frozen contracts.

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
