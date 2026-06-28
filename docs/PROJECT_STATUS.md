# PROJECT STATUS

## Current

EXOS Brain v1 is complete and frozen.

Prediction Engine v1 is implemented.

Market Learning Engine v1 remains complete.

Pipeline smoke test passed:

- `tests/test_market_learning_pipeline.py`

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

## Next

Phase 3:

- Strengthen Probability / Prediction validation
- Add probability and prediction report integration later
- Prepare Strategy Engine design

## Later

- Strategy Engine
- Backtest Engine
- Portfolio / Risk Evaluation
- Pattern Discovery reports / UI integration
- AI Analysis / Overlay
- Zoom / Pan improvements

## Not Implemented Yet

- Strategy Engine
- Backtest Engine
- Portfolio / Risk Evaluation
- AI Analysis / Overlay
- UI reports for Market Learning and Prediction output

## Run

Application:

- `py -m src.main`

Pipeline smoke test:

- `py -m unittest discover -s tests -p test_market_learning_pipeline.py`

## History

Detailed milestone history has moved to `docs/CHANGELOG.md`.
