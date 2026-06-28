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
- Backtest strategies
- Evaluate portfolio risk
- Estimate future probabilities
- Explain results using AI

The primary trading system is POOM+.

Market scope is limited to NASDAQ.

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

## Phase 3 - Strategy / Backtest

Status: Not Started.

Goal:

- Use snapshots, outcomes, patterns, and similarity results to evaluate strategy rules.

Planned:

- Strategy Engine
- Backtest Engine
- Portfolio / Risk Evaluation
- Entry / Exit Rules
- Position Management
- Performance Reports

## Phase 4 - Prediction

Status: Not Started.

Goal:

- Estimate future market probabilities using statistical evidence.

Planned:

- Probability Model
- Historical Similarity Search
- Scenario Generation
- Confidence Score

## Phase 5 - AI Analysis / Overlay

Status: Not Started.

Goal:

- Explain structured EXOS statistics to the user.

AI will not make decisions.

AI may:

- Explain current market condition
- Summarize statistics
- Compare historical situations
- Produce investment reports

## Later UI Work

- Pattern Discovery reports
- Market Learning dashboards
- Zoom / Pan improvements
- Better chart settings

## Design Principles

- SQLite is the source of truth.
- Historical data must be reproducible.
- Statistics come before strategy.
- Strategy and backtest come before prediction.
- Prediction comes before AI explanation.
- AI explains; it does not guess.
- Keep the architecture modular.
- Prioritize correctness over feature count.
