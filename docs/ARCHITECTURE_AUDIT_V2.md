# EXOS Architecture Audit V2

Date: 2026-06-29

Scope: architecture review after Strategy Engine v1 initial implementation and expanded strategy tests.

This is a documentation-only audit. No production engine logic, frozen contracts, or Backtest code were changed.

## Current Architecture Summary

EXOS Desktop remains a local-first NASDAQ research platform built around the frozen EXOS Brain v1 pipeline:

```text
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
-> Strategy
```

Current repository shape:

- `src/analysis`: frozen Core Indicators v1 and Snapshot Builder v1.
- `src/statistics`: Market Learning v1, Probability Engine v1, Prediction Engine v1.
- `src/strategy`: Strategy Engine v1 contracts, enums, and initial deterministic engine.
- `src/backtest`: placeholder only.
- `src/database`: OHLCV SQLite cache manager.
- `src/data`: data provider abstraction and cache/fetch orchestration.
- `src/gui`: desktop UI, chart workspace, chart rendering, dashboard, and developer panel.
- `tests/smoke`: end-to-end market learning smoke test.
- `tests/unit`: Strategy Engine unit tests.
- `tests/regression`: Strategy contract regression tests.
- `tests/integration`: placeholder only.
- `docs`: roadmap, architecture decisions, strategy design, strategy scoring, testing plan, and architecture audits.

Strategy Engine v1 is now implemented as a new additive module:

```text
StrategyInput(snapshot, probability, prediction)
-> analyze_strategy
-> StrategyResult(strategy_score, trade_grade, entry_quality, risk_rating, reward_risk_estimate, notes)
```

The implementation is deterministic, pure, and independent from database access, AI, market loading, Probability Engine execution, and Prediction Engine execution.

## Match Against Current Docs

### `docs/ROADMAP.md`

Mostly aligned with the architectural direction:

- Strategy follows Probability and Prediction.
- Strategy remains deterministic and non-AI.
- Frozen upstream engines are not modified.

Mismatch:

- Roadmap still says Phase 4 Strategy / Backtest is "Not Started". Strategy Engine v1 has now started, while Backtest remains not started.

### `docs/PROJECT_STATUS.md`

Partially stale:

- It still lists Strategy Engine as not implemented.
- It still points the pipeline smoke test to `tests/test_market_learning_pipeline.py`, but the test now lives at `tests/smoke/test_market_learning_pipeline.py`.
- It does not mention the Strategy Engine v1 package or expanded strategy test coverage.

### `docs/ARCHITECTURE_DECISIONS.md`

Still aligned:

- SQLite remains the source of truth.
- Snapshot-first architecture is preserved.
- Strategy consumes existing evidence.
- AI is not part of strategy decisions.
- Frozen engine contracts remain unchanged.

### `docs/STRATEGY_ENGINE_DESIGN.md`

Mostly aligned:

- Strategy consumes snapshot, probability, and prediction structures.
- Strategy does not calculate indicators or discover patterns.
- Strategy does not call AI or execute trades.
- Output avoids BUY / SELL / HOLD.

Mismatch:

- The design doc says implementation should occur after exact scoring formula, thresholds, and output schema are defined. Initial placeholder scoring has now been implemented before those items were fully documented.

### `docs/STRATEGY_SCORING.md`

Partially stale:

- The philosophy still applies.
- The implementation now includes initial formula-like logic, score contributions, grade thresholds, risk thresholds, and boundary behavior.
- The doc says no formulas, weights, thresholds, or algorithms are defined yet. That was true at design time, but is no longer true after Strategy Engine v1 implementation.

### `docs/TESTING_PLAN.md`

Partially stale:

- The proposed test structure is now partially implemented.
- Strategy Engine tests now exist.
- Regression tests now include a strategy contract shape check.
- Several gaps remain: Core Indicators v1, Snapshot Builder v1, Probability Engine v1, Prediction Engine v1, DatabaseManager, DataManager, and integration tests.

## What Improved Since Previous Audit

- `src/strategy` now exists as a dedicated package.
- Strategy contracts are explicit through `StrategyInput` and `StrategyResult`.
- Strategy enums are centralized in `types.py`.
- `analyze_strategy` is pure and deterministic.
- Strategy Engine does not call AI, database, market data loading, Probability Engine, or Prediction Engine.
- Strategy outputs are structured and avoid BUY / SELL / HOLD.
- Strategy public API is exported from `src/strategy/__init__.py`.
- Tests are organized into `smoke`, `unit`, `regression`, and `integration` groups.
- Strategy unit tests cover empty inputs, missing optional fields, confidence scenarios, evidence scenarios, score bounds, reward/risk edge cases, and malformed numeric values.
- Regression tests protect StrategyResult public shape and no-recommendation language.
- The market-learning smoke test still passes after test-folder reorganization.

## Current Risks

### Documentation Drift

`ROADMAP.md`, `PROJECT_STATUS.md`, `STRATEGY_ENGINE_DESIGN.md`, `STRATEGY_SCORING.md`, and `TESTING_PLAN.md` now lag behind implementation.

Risk:

- Future work may follow stale status or stale scoring guidance.
- Backtest design may assume Strategy is still only conceptual.

### Strategy Scoring Contract Stability

`StrategyResult` is protected by regression tests, but `reward_risk_estimate` remains a generic dictionary.

Risk:

- Backtest Engine may depend on keys that are not represented as a typed contract.
- Optional nested keys may drift without compile-time visibility.

### Placeholder Rules Becoming Permanent

`analyze_strategy` uses initial deterministic rules, thresholds, and score contributions.

Risk:

- Placeholder scoring may become treated as final business logic without a dedicated scoring calibration pass.
- `STRATEGY_SCORING.md` does not yet document the implemented thresholds.

### Snapshot Underuse in Strategy Engine

`StrategyInput` includes `snapshot`, but the current engine does not use snapshot fields.

Risk:

- Strategy scoring currently leans on probability and prediction outputs only.
- Candidate dimensions such as Trend Quality and Market Structure are not yet represented.

### Test Coverage Imbalance

Strategy Engine now has solid first-pass tests, but frozen upstream engines still have limited direct test coverage.

Risk:

- Backtest Engine will depend on snapshots, outcomes, probabilities, predictions, and strategy results.
- If upstream contracts drift, Backtest may fail in ways that look like strategy/backtest defects.

### Test Structure Still Shallow

`tests/unit` and `tests/regression` currently store tests directly at the folder root.

Risk:

- This is fine now, but as analysis/statistics/data/database/backtest tests grow, subfolders may be needed to avoid a flat and noisy test namespace.

### Generated Cache Files Present

`__pycache__` files are present in `src` and `tests`.

Risk:

- If not ignored by git, generated files can create review noise.

### Naming Consistency

Current naming is mostly clear, but a few names need alignment:

- `PROJECT_STATUS.md` references the old smoke-test location.
- `StrategyResult.reward_risk_estimate` is a dictionary while `StrategyInput` and enum fields are typed.
- `docs/Architecture.md` and other docs still show corrupted arrow characters.
- The old docs mention "Strategy / Backtest" as not started, while Strategy is now implemented and Backtest is not.

## Module Boundary Issues

- `src/strategy` correctly depends only on strategy contracts/types and plain dictionaries.
- `src/strategy` does not modify frozen engines.
- `src/statistics` still combines schema, storage, outcome, pattern, probability, and prediction responsibilities. This is acceptable now but will matter when Backtest needs data access.
- `src/database` manages OHLCV only, while `src/statistics/schema.py` manages statistics tables. Backtest persistence will need a clear database ownership decision.
- `src/gui/chart_workspace.py` still owns timeframe aggregation and display-data preparation. Backtest should not duplicate or depend on GUI-owned aggregation logic.

## Contract Stability Risks

Backtest will need stable replayable contracts. Current contract risks:

- Strategy output is partly typed and partly dictionary-based.
- Strategy scoring thresholds are implemented but not documented as accepted rules.
- Probability and prediction output dictionaries are not represented by typed contracts.
- Snapshot contract is frozen by convention but not protected by direct regression tests.
- `StrategyInput` accepts any dictionary shape, which keeps the engine decoupled but pushes validation responsibility to callers and tests.

## Test Structure Issues

Current tests pass and are organized better than before.

Remaining issues:

- No dedicated tests for Probability Engine v1.
- No dedicated tests for Prediction Engine v1.
- No direct regression tests for Core Indicators v1 or Snapshot Builder v1.
- No integration test that runs snapshot -> probability -> prediction -> strategy.
- No database integration tests for backtest-ready persistence.
- `docs/TESTING_PLAN.md` should be updated to reflect the implemented strategy test coverage.

## Recommended Fixes Before Backtest Engine

1. Update project documentation:
   - `PROJECT_STATUS.md`
   - `ROADMAP.md`
   - `STRATEGY_SCORING.md`
   - `TESTING_PLAN.md`

2. Document Strategy Engine v1 implemented scoring:
   - score dimensions currently used
   - thresholds
   - risk rating behavior
   - boundary behavior
   - known placeholder status

3. Add typed result detail contracts before Backtest depends on nested dictionaries:
   - reward/risk estimate structure
   - target zone structure
   - risk zone structure

4. Add upstream regression tests:
   - Snapshot Builder v1 shape
   - Snapshot Store stable `snapshot_id`
   - Probability Engine empty and weighted evidence
   - Prediction Engine empty and normal projections

5. Add an integration test for:

```text
snapshot
-> probability
-> prediction
-> strategy
```

6. Decide database ownership before Backtest:
   - whether Backtest tables live under `src/database`
   - whether statistics/backtest schemas get a shared bootstrap layer
   - how backtest runs reference `snapshot_id`

7. Move timeframe aggregation out of GUI before Backtest supports weekly/monthly replay.

8. Keep Backtest additive:
   - do not alter frozen engines
   - consume `StrategyResult`
   - persist replayable assumptions
   - keep AI outside the execution path

## Readiness Score for Backtest Phase

Readiness score: 72 / 100.

Rationale:

- Strategy Engine v1 is now isolated, deterministic, and tested.
- The package boundary is good enough for early Backtest design.
- The test suite has meaningful strategy validation and regression coverage.
- Frozen upstream engines and probability/prediction contracts still need stronger tests before Backtest relies on them heavily.
- Documentation drift should be fixed before Backtest implementation begins.
- Backtest persistence and database ownership are not yet designed.

Recommended interpretation:

- Ready for Backtest design.
- Not yet ready for durable Backtest implementation.

## Audit Conclusion

EXOS architecture has improved since the previous audit. The new Strategy package is additive, deterministic, and separated from frozen upstream engines. The testing structure is also meaningfully stronger.

The main risk is now coordination rather than code shape: docs, scoring assumptions, typed result details, and upstream regression tests should be synchronized before Backtest Engine begins. Once those are handled, the repository will be in a much better position to implement Backtest without destabilizing the frozen EXOS Brain v1 pipeline.
