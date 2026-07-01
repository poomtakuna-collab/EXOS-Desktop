# EXOS ROADMAP

Long-term development roadmap for EXOS Desktop.

Current implementation progress is tracked separately in `PROJECT_STATUS.md`.

---

# Vision

Build EXOS into a local NASDAQ investment research platform.

EXOS is not intended to replace TradingView.

Its purpose is to:

* Collect historical market data
* Calculate indicators
* Build investment statistics
* Discover repeatable market patterns
* Estimate evidence-based probabilities
* Project probability-derived price zones
* Backtest strategies
* Measure strategy performance
* Build statistical market context
* Explain results using AI

The primary trading system is POOM+.

Market scope is limited to NASDAQ.

---

# EXOS Brain v1

**Status:** Complete and frozen.

Architecture:

```
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
```

Future enhancements should extend this pipeline rather than modifying existing engine contracts unless fixing a verified bug.

---

# Phase 1 - Core Indicators

**Status:** Complete and frozen.

## Goal

Convert market rows into a stable EXOS Snapshot contract.

### Completed

* Indicator Engine v1
* EW Engine v1
* Volume Pressure Engine v1
* Trend Slope Engine v1
* Squeeze Engine v1
* Market Structure Engine v1
* Snapshot Builder v1
* Score Engine v1

### Rule

Core Indicators v1 remains frozen unless a verified bug exists.

---

# Phase 2 - Market Learning Engine

**Status:** Complete.

## Goal

Learn which market conditions tend to appear before future price movement.

### Completed

* Statistics DB
* Snapshot Store
* Snapshot Collector
* Outcome Calculator
* Pattern Discovery
* Pattern Library
* Similarity Engine
* Pipeline Smoke Test

### Design

* Database-first.
* `snapshot_id` is the central reference.
* Important searchable values are stored as columns.
* Full EXOS snapshots are stored as JSON.
* Outcomes are calculated once sufficient future OHLCV rows exist.
* Pattern Discovery and Similarity are deterministic statistical systems, not AI or machine learning.

### Schema

`docs/MARKET_LEARNING_SCHEMA.md`

---

# Phase 3 - Probability Engine

**Status:** Complete.

## Goal

Convert historical evidence into probability-based outputs and projected price zones.

Probability outputs are evidence-based metrics.

Prediction outputs are price projections, not recommendations.

### Implemented

* Probability Engine v1
* Similar Pattern weighting
* Expected return estimation
* Expected risk estimation
* Safe defaults
* Prediction Engine v1
* Price Projection Engine v1
* Target Zone Engine
* Risk Zone Engine
* Prediction Summary Engine

### Planned

* Scenario summaries
* Probability calibration improvements

---

# Phase 4 - Strategy & Backtest

**Status:** Core implementation complete.

## Goal

Evaluate deterministic trading strategies using historical evidence.

### Implemented

* Strategy Engine
* Strategy contracts
* Strategy scoring
* Validation framework
* Replay Engine
* Metrics Aggregator
* Backtest Pipeline
* Backtest Report
* SQLite-backed Backtest
* Backtest Persistence
* Validation Report
* Trade Simulator
* Trade Outcome Model

### Planned

* Historical replay persistence
* Entry rule evaluation
* Exit rule evaluation
* Holding rule evaluation
* Signal Ledger
* Trade Journal
* Outcome Tracking
* Strategy performance reports
* Advanced Backtest reporting APIs

### Design

Backtest should become the primary validation layer for every future EXOS feature.

Every new analysis component should prove measurable improvement through historical testing before becoming part of the default pipeline.

---

# EXOS Brain v2 - Context Engine

**Status:** Context Engine v1 Foundation implemented.

## Goal

Provide deterministic market context around every stock analysis.

Context Engine extends Brain v1 without modifying frozen contracts.

### Planned Context Layers

* Context contracts foundation
* Market Context
* Sector Context
* Industry Context
* Relative Strength
* Relative Volume
* Support / Resistance Context
* Optional Macro Context

### Example Flow

```
Market
-> Sector
-> Industry
-> Stock
-> Snapshot
-> Probability
-> Prediction
-> Strategy
-> Backtest
```

### Design Principles

* Deterministic only
* No AI
* Independently testable
* Optional layers
* Database-driven
* Backtest every context layer independently
* Not wired into the default pipeline until each layer proves measurable value

### Future Validation

Compare:

* Brain v1
* Brain v1 + Market Context
* Brain v1 + Sector Context
* Brain v1 + Relative Strength
* Brain v1 + Support / Resistance
* Combined Context

Purpose:

Only adopt context layers that demonstrate measurable statistical improvement.

---

# Phase 5 - AI Analysis / Overlay

**Status:** Deterministic pipeline complete.

AI overlay not implemented.

## Goal

Explain structured EXOS outputs.

AI does **not** make investment decisions.

AI does **not** generate buy/sell recommendations.

AI may:

* Explain market conditions
* Summarize statistics
* Compare historical situations
* Generate research reports
* Explain probability outputs
* Explain strategy evaluation

### Implemented

* Analysis Pipeline
* Analysis Request / Result
* Pipeline configuration
* Deterministic orchestration
* Snapshot integration
* Probability integration
* Prediction integration
* Strategy integration
* Backtest integration
* Analysis Report

### Not Implemented

* AI explanation layer
* Latest snapshot loading
* DB-backed analysis orchestration

---

# Phase 6 - Data Source

**Status:** Core implementation complete.

## Goal

Provide a stable read-only interface for all future orchestration.

### Implemented

* DataSource contracts
* MemoryDataSource
* SQLiteDataSource
* AnalysisService
* Read-only loading architecture

### Future

* Live market providers
* Multi-source loading
* Data synchronization
* Historical import pipeline

---

# Later Research

Planned:

* Signal Ledger / Trade Journal
* Outcome Tracking
* Statistical performance reporting
* Scenario modelling
* Probability calibration
* Pattern confidence calibration
* Context Engine validation
* Statistical feature evaluation
* Advanced market behaviour research

---

# Later UI Work

* Pattern Discovery reports
* Statistical dashboards
* Context visualisation
* Support / Resistance overlays
* Relative Strength panels
* Zoom / Pan improvements
* Better chart settings

---

# Parked / Future (Long-Term)

These features become valuable only after sufficient historical evidence exists.

* Portfolio / Risk Evaluation
* Position sizing
* Portfolio diversification analysis
* Correlation analysis
* Capital allocation
* Portfolio optimisation

These are intentionally postponed because EXOS is currently focused on becoming an evidence-driven research platform rather than a portfolio management system.

Portfolio Engine work should remain experimental / future / parked until real EXOS usage proves portfolio-level workflows are needed.

---

# Design Principles

* SQLite is the source of truth.
* Historical data must be reproducible.
* Statistics come before strategy.
* Probability comes before strategy.
* Strategy must be validated through Backtesting.
* Every new analysis layer should prove measurable value.
* Context Engine extends Brain v1 without modifying frozen contracts.
* AI explains evidence; it does not guess.
* AI never replaces deterministic analysis.
* EXOS outputs evidence, probabilities, and projected price zones - not buy/sell recommendations.
* Keep the architecture modular.
* Prioritize correctness over feature count.
* Build statistical confidence before adding automation.
