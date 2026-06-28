# PROJECT STATUS

## Current

Market Learning Engine v1 is complete.

Pipeline smoke test passed:

- `tests/test_market_learning_pipeline.py`

## Architecture Summary

Market Data
-> Core Indicators
-> Snapshot
-> Statistics DB
-> Outcome
-> Pattern Discovery
-> Pattern Library
-> Similarity
-> Strategy
-> Prediction
-> AI

## Completed

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

## Next

Phase 3:

- Strategy Engine
- Backtest Engine
- Portfolio / Risk Evaluation

## Later

- Pattern Discovery reports / UI integration
- Prediction Engine
- AI Analysis / Overlay
- Zoom / Pan improvements

## Not Implemented Yet

- Strategy Engine
- Backtest Engine
- Portfolio / Risk Evaluation
- Prediction Engine
- AI Analysis / Overlay
- UI reports for Market Learning output

## Run

Application:

- `py -m src.main`

Pipeline smoke test:

- `py -m unittest discover -s tests -p test_market_learning_pipeline.py`

## History

Detailed milestone history has moved to `docs/CHANGELOG.md`.
