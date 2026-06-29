# PROJECT STATUS

## Current

EXOS Brain v1 is complete and frozen.

Prediction Engine v1 is implemented.

Strategy Engine v1 initial implementation is implemented.

Strategy validation tests are implemented.

In-memory Backtest Framework v1 is implemented.

Backtest unit tests are implemented.

Backtest Data Layer interface skeletons are implemented.

Market Learning Engine v1 remains complete.

Pipeline smoke test passed:

- `tests/smoke/test_market_learning_pipeline.py`

Architecture Audit v2 completed:

- `docs/ARCHITECTURE_AUDIT_V2.md`

Architecture Audit v3 completed:

- `docs/ARCHITECTURE_AUDIT_V3.md`

## Architecture Summary

EXOS Brain v1:

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

This architecture is frozen.

Future enhancements should extend the pipeline rather than modifying existing engine contracts unless fixing a verified bug.

Detailed flow:

Market Data
-> Core Indicators
-> Snapshot
-> Statistics DB
-> Outcome
-> Pattern Discovery
-> Pattern Library
-> Similarity
-> Probability
-> Price Projection
-> Target Zone
-> Risk Zone
-> Strategy
-> Backtest
-> AI

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

It outputs:

- Expected 5D / 10D / 20D returns
- Probability of 5% and 10% upside within 10D
- Approximate 5% downside probability within 10D
- Expected 10D max gain and drawdown
- Confidence
- Evidence count

It does not output BUY, SELL, or HOLD recommendations.

### Prediction Engine v1

Status: Implemented.

Prediction Engine v1 derives price projections only from Probability Engine outputs.

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

### Backtest Framework v1

Status: In-memory framework implemented.

Backtest Framework v1 includes:

- Backtest contracts
- Backtest types
- Simulation rules
- Replay Engine
- Metrics Aggregator
- Backtest Pipeline
- Backtest Report
- Unit Tests

Backtest Data Layer skeleton includes:

- `src/backtest/data/`
- `SnapshotQuery`
- `SnapshotLoader`
- `OutcomeLoader`
- `FutureRowsLoader`
- `BacktestDataset`
- `BacktestDatasetBuilder`

Current flow:

BacktestInput
-> Replay Engine
-> SimulationResult
-> Metrics Aggregator
-> BacktestResult
-> Backtest Report

It does not access the database.

It does not load stored datasets.

The data-layer skeleton does not execute SQL or construct historical datasets yet.

It does not implement portfolio evaluation.

It does not call AI.

Current tests:

- `tests/unit/test_backtest_engine.py`
- `tests/unit/test_backtest_metrics.py`
- `tests/unit/test_backtest_pipeline.py`
- `tests/unit/test_backtest_report.py`
- `tests/unit/test_backtest_data_skeleton.py`

## Next

DB-backed Backtest preparation:

- Strengthen Probability / Prediction validation
- Add upstream regression tests before database-backed Backtest
- Implement SQLite-backed Backtest Data Layer loaders
- Keep Strategy and Backtest v1 deterministic and additive

## Later

- Database-backed Backtest
- SQLite-backed Snapshot Loader implementation
- SQLite-backed Outcome Loader implementation
- Future OHLCV rows loader implementation
- Historical Dataset Builder implementation
- Historical replay from stored datasets
- Portfolio / Risk Evaluation
- Pattern Discovery reports / UI integration
- AI Analysis / Overlay
- Zoom / Pan improvements

## Not Implemented Yet

- Database-backed Backtest
- SQLite-backed loading
- SQL queries
- Historical dataset construction
- DB-backed Backtest execution
- Historical replay from stored datasets
- Portfolio / Risk Evaluation
- UI Backtest reports
- AI Analysis / Overlay
- UI reports for Market Learning and Prediction output

## Run

Application:

- `py -m src.main`

Pipeline smoke test:

- `py -m unittest discover -s tests`

Current test count:

- 55 tests

## History

Detailed milestone history has moved to `docs/CHANGELOG.md`.
