# EXOS Architecture Audit V3

Date: 2026-06-29

Scope: architecture review after Backtest Framework v1 was added.

This is a documentation-only audit. No source code, production engine logic, Strategy logic, Backtest logic, or frozen contracts were changed.

## Current Architecture Summary

EXOS now has an in-memory deterministic Backtest Framework v1 layered after Strategy Engine v1.

Current high-level flow:

```text
Snapshot
-> Probability
-> Prediction
-> StrategyResult
-> Backtest Replay
-> Backtest Metrics
-> Backtest Pipeline
-> Backtest Report
```

Backtest package structure:

- `src/backtest/contracts.py`: public Backtest dataclasses.
- `src/backtest/types.py`: public Backtest enums.
- `src/backtest/engine.py`: single-trade deterministic replay.
- `src/backtest/metrics.py`: aggregation from `SimulationResult` records into `BacktestResult`.
- `src/backtest/pipeline.py`: orchestration from multiple `BacktestInput` records to `BacktestResult`.
- `src/backtest/report.py`: deterministic report object from `BacktestResult`.
- `src/backtest/__init__.py`: public exports.

The stack is clean:

```text
Replay
-> Metrics
-> Pipeline
-> Report
```

Current Backtest contracts:

- `BacktestInput`
- `SimulationConfig`
- `SimulationRule`
- `SimulationResult`
- `BacktestResult`
- `BacktestReport`

Current Backtest enums:

- `SimulationStatus`
- `TradeOutcome`
- `ExitReason`

Backtest Framework v1 remains local, deterministic, and pure. It does not access the database, load files, call AI, perform portfolio simulation, execute trades, or mutate Strategy / Probability / Prediction outputs.

## Match Against Current Docs

### `docs/ROADMAP.md`

Partially stale.

The roadmap says Backtest Engine is planned and not implemented. That is no longer fully accurate: a first in-memory Backtest Framework exists, including replay, metrics, pipeline, and report layers.

Backtest is still not DB-backed and not portfolio-aware.

### `docs/PROJECT_STATUS.md`

Stale.

It lists Backtest Engine as not implemented and does not mention:

- Backtest contracts.
- Backtest replay engine.
- Backtest metrics aggregator.
- Backtest pipeline.
- Backtest report layer.
- Backtest unit tests.

### `docs/ARCHITECTURE_DECISIONS.md`

Still aligned.

The Backtest additions are additive, deterministic, and do not modify frozen Brain v1 contracts.

### `docs/BACKTEST_ENGINE_DESIGN.md`

Mostly aligned but partially stale.

The design doc says Backtest Engine is not implemented yet. A first in-memory framework now exists.

The implementation follows the design boundaries:

- deterministic
- no AI
- no database access
- no historical data mutation
- no portfolio logic
- no trade execution

### `docs/BACKTEST_SIMULATION_RULES.md`

Mostly aligned.

The replay engine implements the core Simulation v1 rules:

- one simulated trade per input
- snapshot close entry by default
- optional StrategyResult entry override
- target from reward/risk target zone
- stop from reward/risk risk zone
- sequential OHLCV replay
- conservative same-candle target/stop handling
- timeout handling
- insufficient-data handling

Minor drift:

- The document says the simulation logic is not implemented yet. It should be updated.

### `docs/TESTING_PLAN.md`

Stale.

It still says no Backtest tests exist. Backtest now has unit tests for:

- replay engine
- metrics aggregator
- pipeline
- report layer

It still correctly identifies missing integration and DB-backed tests.

## What Improved Since V2

- Backtest package now exists beyond contracts.
- Replay, metrics, pipeline, and report responsibilities are separated cleanly.
- `replay_trade` is pure and deterministic.
- `analyze_backtest_results` is pure and deterministic.
- `run_backtest` is a thin orchestration layer.
- `build_backtest_report` creates a structured report without AI.
- Backtest contracts are explicit and frozen enough for in-memory tests.
- Backtest unit coverage is broad for v1 behavior.
- Test count increased to 50.
- No database, file loading, UI, AI, or portfolio logic leaked into the Backtest package.
- Strategy Engine remains unchanged by Backtest work.

## Contract Stability Review

### `BacktestInput`

Current status: usable for in-memory replay.

Strengths:

- References structured EXOS outputs.
- Includes `StrategyResult`.
- Includes `future_rows` for deterministic replay.

Risks:

- `snapshot`, `probability`, `prediction`, `outcome`, and `future_rows` are dictionary based.
- `future_rows` are embedded directly in input, which is useful for tests but may not be the final DB-backed shape.
- There is no `snapshot_id` field required at the contract level.
- There is no explicit symbol, timeframe, or date-range contract for DB-backed runs.

### `SimulationConfig`

Current status: stable enough for v1 replay.

Strengths:

- Minimal and deterministic.
- Captures horizon and same-window behavior.

Risks:

- `entry_price_source` is a free-form string.
- Future DB-backed or UI-driven configuration may need enums or a typed assumptions object.
- Fees, slippage, and position sizing are intentionally absent.

### `SimulationResult`

Current status: stable enough for v1 replay and metrics.

Strengths:

- Uses enums for status, outcome, and exit reason.
- Captures entry, exit, return, drawdown, and notes.

Risks:

- Does not include `snapshot_id`.
- Does not include simulated entry/exit dates.
- Does not include target/stop prices used.
- Does not include strategy version or simulation version.

### `BacktestResult`

Current status: stable enough for in-memory aggregation.

Strengths:

- Contains core metrics.
- Handles empty and skipped input safely.

Risks:

- Does not include run id, date range, symbol set, timeframe, assumptions, or version metadata.
- `total_trades` currently means completed successful simulations, not all attempted inputs. That should be documented before DB persistence.
- Skipped count is stored in notes, not a typed field.

### `BacktestReport`

Current status: stable enough for deterministic textual summaries.

Strengths:

- Structured report object.
- Rule-based comments.
- No AI.

Risks:

- Comments are intentionally simple.
- Report does not include skipped count as a typed field.
- No UI-ready sectioning yet.

## Test Coverage Review

Current Backtest tests:

- `tests/unit/test_backtest_engine.py`
- `tests/unit/test_backtest_metrics.py`
- `tests/unit/test_backtest_pipeline.py`
- `tests/unit/test_backtest_report.py`

Backtest v1 covered behavior:

- target hit
- stop hit
- target and stop same candle
- timeout
- missing data
- invalid inputs
- deterministic replay
- stable `SimulationResult`
- empty metrics
- all wins
- all losses
- mixed wins/losses
- breakeven
- skipped / insufficient-data aggregation
- max drawdown
- expectancy
- stable `BacktestResult`
- empty reports
- positive reports
- weak reports
- notes preservation
- stable `BacktestReport`

Coverage is sufficient for the current in-memory framework.

Remaining gaps before DB-backed Backtest:

- No integration test from Strategy -> Backtest Pipeline -> Report.
- No test using real stored snapshot/outcome rows.
- No test using `snapshot_id` continuity.
- No DB persistence tests.
- No test for assumptions/version metadata.
- No tests for weekly/monthly timeframe aggregation.
- No tests for Probability/Prediction regression as upstream Backtest inputs.

## Integration Risks

### DB Integration

Risk:

- Current Backtest inputs are test-fixture oriented and dictionary based.
- Database ownership is not yet decided.
- Backtest results do not include enough metadata for durable persistence.

Recommended mitigation:

- Define a DB-backed `BacktestRun` / `BacktestEvaluation` persistence design before writing DB integration.
- Add typed fields for attempted/skipped counts, date ranges, symbol, timeframe, strategy version, simulation version, and assumptions.

### Portfolio Engine

Risk:

- Current Backtest intentionally has no sizing, cash, exposure, fees, slippage, or position state.
- Portfolio Engine cannot safely consume `BacktestResult` alone for portfolio-level decisions.

Recommended mitigation:

- Keep Portfolio Engine separate.
- Add portfolio contracts after DB-backed backtest run metadata is stable.

### UI Reports

Risk:

- `BacktestReport` is useful but not yet sectioned for UI display.
- Report comments are simple strings.
- Skipped and breakeven counts are notes, not typed fields.

Recommended mitigation:

- Add typed report sections before UI work.
- Keep UI read-only against structured report data.

### AI Overlay

Risk:

- AI could be tempted to interpret raw notes or generate recommendations.

Recommended mitigation:

- AI should consume `BacktestReport` only after the report schema is stable.
- AI must remain explanatory and must not produce BUY / SELL / HOLD.

## Technical Debt

- Documentation drift: roadmap, project status, testing plan, and backtest design docs need updating for Backtest Framework v1.
- `BacktestInput` uses dictionaries for several important records.
- `SimulationConfig.entry_price_source` is a string instead of an enum.
- `BacktestResult` lacks typed skipped/attempted/breakeven counts.
- `SimulationResult` lacks `snapshot_id`, dates, target price, stop price, and version metadata.
- `BacktestReport` does not expose skipped count, breakeven count, or loss count directly.
- Backtest tests are unit-heavy but not integration-backed.
- Existing `__pycache__` files are present in source/test folders and should stay ignored by git.
- Docs still contain mojibake arrow characters in older files.

## Recommended Fixes

1. Update documentation:
   - `PROJECT_STATUS.md`
   - `ROADMAP.md`
   - `BACKTEST_ENGINE_DESIGN.md`
   - `BACKTEST_SIMULATION_RULES.md`
   - `TESTING_PLAN.md`
   - `CHANGELOG.md`

2. Clarify Backtest terminology:
   - attempted simulations
   - completed simulations
   - skipped simulations
   - breakeven simulations
   - total trades

3. Add typed fields to `BacktestResult` before DB persistence:
   - attempted_trades
   - skipped_trades
   - breakeven_trades

4. Add metadata fields before DB-backed runs:
   - run id
   - strategy version
   - simulation version
   - symbol
   - timeframe
   - date range
   - assumptions

5. Add integration tests:
   - StrategyResult -> replay -> metrics -> report
   - snapshot id continuity
   - insufficient-data handling across pipeline

6. Define DB ownership:
   - schema location
   - initialization path
   - persistence tables
   - migration rules

7. Keep Portfolio Engine separate from Backtest:
   - no cash/exposure logic inside current replay engine
   - portfolio consumes backtest outputs later

8. Keep AI overlay downstream:
   - AI reads reports
   - AI does not run or alter backtests
   - AI does not generate recommendations

## Readiness Score for DB-Backed Backtest / Portfolio Phase

Readiness score: 74 / 100.

Rationale:

- In-memory Backtest Framework v1 is well layered and well tested.
- Core replay, metrics, pipeline, and report behavior is deterministic.
- The public contracts are usable for current unit-tested behavior.
- DB-backed persistence requires additional metadata and clearer count semantics.
- Portfolio readiness is lower because no position/cash/exposure contracts exist yet.
- Documentation needs to catch up before the next milestone.

Recommended interpretation:

- Ready for DB-backed Backtest design.
- Nearly ready for DB-backed Backtest implementation after metadata/count contract cleanup.
- Not ready for Portfolio Engine implementation yet.

## Audit Conclusion

Backtest Framework v1 is architecturally clean. The current stack separates replay, metrics, orchestration, and reporting in a way that should scale into DB-backed Backtest work.

The next milestone should not be a feature jump into Portfolio or UI. It should first stabilize Backtest result semantics, run metadata, DB ownership, and integration tests. Once those are in place, EXOS can move into durable Backtest storage without disturbing Strategy Engine v1 or the frozen EXOS Brain v1 pipeline.
