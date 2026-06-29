# EXOS ROADMAP

Long-term development roadmap for EXOS Desktop.

Current implementation progress is tracked separately in `PROJECT_STATUS.md`.

## Vision

Build EXOS into a local NASDAQ investment research platform.

EXOS is not intended to replace TradingView.

Its purpose is to:

- Collect historical market data
- Calculate indicators
- Build investment statistics
- Discover repeatable market patterns
- Estimate evidence-based probabilities
- Project probability-derived price zones
- Backtest strategies
- Evaluate portfolio risk
- Explain results using AI

The primary trading system is POOM+.

Market scope is limited to NASDAQ.

## EXOS Brain v1

Status: Complete and frozen.

Architecture:

Market Data
→ Core Indicators
→ Snapshot
→ Statistics
→ Outcome
→ Pattern Discovery
→ Pattern Library
→ Similarity
→ Probability
→ Prediction

Future enhancements should extend this pipeline rather than modifying existing engine contracts unless fixing a verified bug.

## Phase 1 - Core Indicators

Status: Complete and frozen.

Goal:

- Convert market rows into a stable EXOS snapshot contract.

Completed:

- Indicator Engine v1
- EW Engine v1
- Volume Pressure Engine v1
- Trend Slope Engine v1
- Squeeze Engine v1
- Market Structure Engine v1
- Snapshot Builder v1
- Score Engine v1

Rule:

- Core Indicators v1 remains frozen unless a real bug appears.

## Phase 2 - Market Learning Engine

Status: Complete.

Goal:

- Learn which market conditions tend to appear before future price movement.

Completed:

- Statistics DB
- Snapshot Store
- Snapshot Collector
- Outcome Calculator
- Pattern Discovery
- Pattern Library
- Similarity Engine
- Pipeline Smoke Test

Design:

- Database-first.
- `snapshot_id` is the central reference.
- Important searchable values are stored as columns.
- Full nested EXOS snapshots are stored as JSON.
- Outcomes are calculated when enough future OHLCV rows exist.
- Pattern Discovery and Similarity are deterministic statistics, not AI or ML.

Schema:

- `docs/MARKET_LEARNING_SCHEMA.md`

## Phase 3 - Probability Engine

Status: Started.

Goal:

- Convert matched historical patterns into probability-style outputs and probability-derived price projections.

Probability outputs are evidence-based metrics, not buy/sell recommendations.

Prediction outputs are price projections and zones, not buy/sell recommendations.

Implemented:

- Probability Engine v1
- Weighted probability calculation from similar patterns
- Expected return and risk metrics
- Safe defaults when no evidence exists
- Prediction Engine v1
- Probability-derived expected prices
- Target zone
- Risk zone

Planned:

- Probability / Prediction validation
- Probability and prediction report integration
- Scenario summaries

## Phase 4 - Strategy / Backtest

Status: Strategy Engine v1, in-memory Backtest Framework v1, Backtest integration coverage, SQLite-backed Backtest Data Layer, DB-backed Backtest design, and read-only DB-backed Backtest orchestration implemented. Backtest persistence is not implemented.

Goal:

- Use snapshots, outcomes, patterns, similarity, and probability outputs to evaluate strategy rules.

Implemented:

- Strategy Engine
- Strategy input/output contracts
- Initial deterministic strategy scoring
- Strategy validation tests
- Backtest contracts
- Backtest types
- Simulation rules
- Replay Engine
- Metrics Aggregator
- Backtest Pipeline
- Backtest Report
- Backtest unit tests
- Backtest data-layer package skeleton
- SnapshotQuery contract
- SnapshotLoader / OutcomeLoader / FutureRowsLoader interfaces
- BacktestDataset / BacktestDatasetBuilder interfaces
- Backtest data-layer skeleton tests
- Strategy-to-Backtest integration test
- DB-backed Backtest persistence and loading path design
- SQLite-backed SnapshotLoader
- SQLite-backed OutcomeLoader
- SQLite-backed FutureRowsLoader
- SQLite-backed BacktestDatasetBuilder
- Read-only DB-backed Backtest orchestration

Design docs:

- `docs/BACKTEST_DB_DESIGN.md`

Planned:

- Backtest persistence
- Backtest-owned persistence tables
- Persisted BacktestRun / BacktestEvaluation / BacktestTradeResult writes
- Historical replay result persistence from stored datasets
- Portfolio / Risk Evaluation
- Entry / Exit Rules
- Position Management
- Strategy performance reports

## Phase 5 - AI Analysis / Overlay

Status: Contract skeleton started.

Goal:

- Explain structured EXOS statistics and probability outputs to the user.

AI will not make decisions.

AI will not produce buy/sell/hold recommendations.

AI may:

- Explain current market condition
- Summarize statistics
- Compare historical situations
- Produce investment reports

Implemented:

- Analysis Pipeline package skeleton
- `AnalysisRequest`
- `AnalysisResult`
- `PipelineConfig`
- `analyze_symbol` public API placeholder
- Unit tests for imports, contract shapes, defaults, and placeholder behavior

Not implemented:

- Pipeline orchestration
- AI analysis
- Brain v1 / Probability / Prediction / Strategy / Backtest integration

## EXOS Brain v2 - Context Engine

Status: Not Implemented.

Goal:

- Add deterministic market context around stock-level EXOS analysis.

Context Engine should help EXOS understand the environment around a stock:

- Market Context
- Sector Context
- Industry Context
- Relative Strength
- Optional Macro Context

Example future flow:

Market
-> Sector
-> Industry
-> Stock
-> Snapshot
-> Probability
-> Prediction
-> Strategy
-> Backtest

Design:

- Context Engine is not AI.
- Context Engine is structured market data analysis.
- Context outputs should be deterministic.
- Context layers should be optional and independently testable.
- Context Engine should extend Brain v1 rather than modifying frozen Brain v1 contracts.
- Context Engine should come after Brain v1, Backtest, and Portfolio / Risk foundations are stable.

Future Backtest should compare:

- Brain v1 only
- Brain v1 + Sector Context
- Brain v1 + Market Context
- Brain v1 + Sector + Industry Context

Purpose:

- Prove whether each context layer improves results before making it part of default strategy evaluation.

## Later Research

Planned:

- Deeper scenario modeling
- More advanced probability calibration
- Context Engine calibration after Backtest can measure context-layer value

## Later UI Work

- Pattern Discovery reports
- Market Learning dashboards
- Zoom / Pan improvements
- Better chart settings

## Design Principles

- SQLite is the source of truth.
- Historical data must be reproducible.
- Statistics come before strategy.
- Probability comes before strategy.
- Strategy and backtest come before AI explanation.
- AI explains; it does not guess.
- Context Engine is deterministic structured analysis, not AI.
- EXOS outputs probability, evidence, and price zones, not buy/sell recommendations.
- Keep the architecture modular.
- Prioritize correctness over feature count.
