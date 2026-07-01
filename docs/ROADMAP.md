# EXOS ROADMAP

Long-term development roadmap for EXOS Desktop.

Current implementation detail is tracked in `docs/PROJECT_STATUS.md`.

---

## Vision

Build EXOS into a local NASDAQ investment research platform.

EXOS is not intended to replace TradingView. Its purpose is to collect reproducible market data, calculate deterministic evidence, preserve research signals, evaluate outcomes, and explain what the evidence says.

The primary trading system is POOM+.

Market scope is limited to NASDAQ.

EXOS outputs evidence, probabilities, projected price zones, and research context. It does not output broker actions or automated buy/sell decisions.

---

## Current Phase

**Evidence Loop + Desktop Integration**

The current priority is to close the measurable loop:

```
Research Output
-> Signal
-> Outcome
-> Performance Report
-> Desktop Review
-> Backtest / Context Validation
```

This phase is about measuring whether deterministic EXOS outputs are useful before adding new engines.

---

## Implementation Status

### Brain v1

**Status:** Complete and frozen.

Implemented pipeline:

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

Frozen contracts should not be modified unless fixing a verified bug.

### Core Indicators

**Status:** Complete and frozen.

Implemented:

- Indicator Engine v1
- EW Engine v1
- Volume Pressure Engine v1
- Trend Slope Engine v1
- Squeeze Engine v1
- Market Structure Engine v1
- Snapshot Builder v1
- Score Engine v1

### Market Learning

**Status:** Complete.

Implemented:

- Statistics DB
- Snapshot Store
- Snapshot Collector
- Outcome Calculator foundation for market-learning outcomes
- Pattern Discovery
- Pattern Library
- Similarity Engine
- Pipeline smoke coverage

Design remains database-first. `snapshot_id` is the central reference, searchable values are stored as columns, and full EXOS snapshots are stored as JSON.

### Probability and Prediction

**Status:** Complete.

Implemented:

- Probability Engine v1
- Similar-pattern weighting
- Expected return estimation
- Expected risk estimation
- Safe defaults
- Prediction Engine v1
- Price Projection Engine v1
- Target Zone Engine
- Risk Zone Engine
- Prediction Summary Engine

Future work is calibration and scenario explanation, not a new prediction engine.

### Strategy and Backtest

**Status:** Core implementation complete.

Implemented:

- Strategy Engine
- Strategy contracts
- Strategy scoring
- Validation framework
- Replay Engine
- Metrics Aggregator
- Backtest Pipeline
- Backtest Report
- SQLite-backed Backtest
- Backtest Persistence
- Validation Report
- Trade Simulator
- Trade Outcome Model

Remaining work:

- Historical replay persistence from stored datasets
- Advanced Backtest reporting/query APIs
- Context validation/backtest comparison
- UI Backtest reports

Backtest should become the validation layer for future EXOS features.

### Context Engine v1

**Status:** Complete.

Context Engine v1 extends Brain v1 without modifying frozen Brain contracts.

Implemented:

- Context contracts
- Market Context
- Sector Context
- Relative Strength
- Volume Context
- Support / Resistance Context
- Deterministic context calculators and summaries
- Context-aware Research tab view-model support

Future work is validation, comparison, and better surfacing of real context outputs in Desktop.

### Data Source v1

**Status:** Implemented.

Implemented:

- Data Source contracts
- MemoryDataSource
- SQLiteDataSource
- AnalysisService read-only loading architecture
- ChartDataAdapter bridge for Desktop chart loading
- SQLite-backed chart adapter integration coverage
- Legacy desktop data-loader fallback
- Limited OHLCV reads return the latest N rows in chronological order
- Cache freshness checks use latest cached date, not row count alone

SQLite remains the source of truth for local structured market data.

The legacy chart loader remains available as fallback until Data Source v1 fully owns refresh and synchronization behavior.

### Signal Ledger

**Status:** Foundation and SQLite persistence implemented.

Implemented:

- Signal contracts
- SignalSnapshotReference
- SignalRecord
- In-memory Signal Ledger repository
- SQLite Signal Ledger repository
- Linked outcome storage through the Signal Ledger repository
- Deterministic JSON-safe serialization

Not yet implemented:

- Canonical Result -> Signal adapter
- Explicit/manual Signal creation flow
- Runtime Signal persistence from Desktop actions

### Outcome Tracking

**Status:** Foundation, calculator, and SQLite persistence implemented.

Implemented:

- Outcome contracts
- OutcomeRecord
- Outcome status model
- Pure outcome calculation from future OHLCV rows
- Standalone Outcome SQLite repository
- Outcome persistence tests with temporary SQLite databases

Not yet implemented:

- End-to-end Outcome evaluation flow for accumulated saved signals
- Desktop action/workflow for evaluating outcomes

### Performance Reporting

**Status:** Performance Report v1 implemented.

Implemented:

- Total signals
- Total outcomes
- Win rate
- Average return
- Average max drawdown
- Outcome status distribution
- Signal type breakdown
- Confidence bucket breakdown
- JSON-safe `to_dict()`
- Empty-data handling
- Symbol-scoped Desktop Performance surface

Next work is to feed the report with real accumulated signal and outcome data from the explicit evidence loop.

### EXOS Desktop

**Status:** Main app is the single growing Desktop surface.

Implemented tabs:

- Chart
- Research
- Performance
- Signal History

Current Desktop behavior:

- Chart loads through Data Source v1 where possible.
- Chart falls back to the legacy DataManager/provider path when data is missing, insufficient, stale, or unavailable.
- Normal cached chart reads remain read-only.
- Research tab shows grouped deterministic context/research cards.
- Performance tab shows global and selected-symbol report data.
- Signal History tab reads saved signals and linked outcomes from SQLite when available.

No standalone demo scripts should be added for new Desktop surfaces.

---

## Next Priorities

1. Research tab loads real analysis/context output
   - Connect the Research tab to actual deterministic analysis/context results for the selected symbol.
   - Keep business logic in existing modules and view-model helpers.

2. Canonical Result -> Signal adapter
   - Add pure adapter helpers that derive `SignalRecord` candidates from `CanonicalResultV1`.
   - Do not wire automatic persistence.

3. Explicit/manual Signal creation flow
   - Let the user intentionally save deterministic research output as a signal.
   - No auto-trading, no broker action, no runtime surprise persistence.

4. Outcome evaluation flow
   - Evaluate saved signals against future OHLCV rows.
   - Persist outcomes through existing repositories.

5. Performance report with real accumulated signal data
   - Feed Performance Report v1 from saved signals and evaluated outcomes.
   - Keep global and symbol-scoped views.

6. Context validation/backtest comparison
   - Compare Brain v1 against Brain v1 plus context layers.
   - Adopt only context signals that demonstrate measurable improvement.

---

## Later Work

### AI Overlay

**Status:** Later, explanation-only.

AI may eventually:

- Explain market conditions
- Summarize deterministic statistics
- Compare historical situations
- Generate research reports
- Explain probability outputs
- Explain strategy evaluation

AI must not:

- Make investment decisions
- Generate broker actions
- Replace deterministic analysis
- Invent evidence outside structured EXOS outputs

### Advanced Research

Later research areas:

- Scenario modelling
- Probability calibration
- Pattern confidence calibration
- Statistical feature evaluation
- Support / Resistance overlays
- Relative Strength panels
- Pattern Discovery reports
- Statistical dashboards

### Portfolio Engine

**Status:** Parked.

Portfolio/Risk work remains intentionally postponed:

- Portfolio / Risk Evaluation
- Position sizing
- Diversification analysis
- Correlation analysis
- Capital allocation
- Portfolio optimisation

These workflows become useful only after EXOS has enough measured signal/outcome evidence to justify portfolio-level decisions.

---

## Design Principles

- SQLite is the source of truth.
- Historical data must be reproducible.
- Statistics come before strategy.
- Probability comes before strategy.
- Strategy must be validated through backtesting.
- Every new analysis layer should prove measurable value.
- Do not add new engines until current engines are measurable.
- Context Engine extends Brain v1 without modifying frozen contracts.
- Signal and outcome persistence must be explicit and deterministic.
- AI explains evidence; it does not guess.
- AI never replaces deterministic analysis.
- EXOS outputs evidence, probabilities, and projected price zones, not buy/sell recommendations.
- Keep the architecture modular.
- Prioritize correctness over feature count.
- Build statistical confidence before adding automation.
