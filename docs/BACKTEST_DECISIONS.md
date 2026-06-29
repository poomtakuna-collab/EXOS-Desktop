# Backtest Decisions

Decision preparation notes for Backtest Engine.

This document records decisions that must be made before Backtest implementation begins.

Backtest Engine is not implemented yet.

## 1. Source of Historical Truth

Decision needed:

- Backtest should use SQLite as the historical source of truth.

Open questions:

- Should Backtest read only stored snapshots, or can it build missing snapshots on demand?
- Should Backtest use `ohlcv_daily`, `snapshots`, `outcomes`, `patterns`, probability outputs, StrategyResult outputs, or all of them?
- Should backtest runs be reproducible from stored records only?

Recommended direction:

- Use SQLite-backed OHLCV and snapshot records.
- Reference historical decision points by `snapshot_id`.
- Avoid live data fetches during backtest execution.

## 2. Timeframe Handling

Decision needed:

- Define where daily, weekly, and monthly timeframe aggregation lives.

Open questions:

- Should timeframe aggregation move out of `src/gui/chart_workspace.py` before Backtest uses it?
- Should aggregated timeframe data be persisted or generated deterministically at runtime?
- How should incomplete weekly/monthly candles be handled?

Recommended direction:

- Move reusable timeframe aggregation into a non-GUI module before Backtest supports 1W or 1M.
- Keep aggregation deterministic and fixture-tested.

## 3. Snapshot Selection

Decision needed:

- Define how Backtest chooses historical decision snapshots.

Open questions:

- Should Backtest select snapshots by symbol, timeframe, date range, score, state, or strategy eligibility?
- Should Backtest require every decision point to already have a stored snapshot?
- How should missing snapshots be reported?

Recommended direction:

- Query stored snapshots by symbol, timeframe, and date range.
- Treat `snapshot_id` as the central reference for every decision point.
- Do not modify snapshot contents during Backtest.

## 4. Outcome Availability

Decision needed:

- Define how Backtest handles future outcome data.

Open questions:

- Should Backtest require existing outcome rows?
- Should Backtest calculate trade outcomes independently from `outcomes`?
- Should outcome rows be used only for validation and reports?

Recommended direction:

- Use `outcomes` for evidence and validation where appropriate.
- Let Backtest execution calculate trade-specific exits from historical OHLCV according to explicit rules.
- Skip or report snapshots without enough future data.

## 5. StrategyResult Storage

Decision needed:

- Decide whether StrategyResult outputs are stored for replay.

Open questions:

- Should StrategyResult be persisted per `snapshot_id` and strategy version?
- Should reward/risk estimate be stored as structured columns, JSON, or both?
- How should strategy scoring version be recorded?

Recommended direction:

- Store StrategyResult with `snapshot_id`, strategy version, score, grade, risk rating, entry quality, reward/risk fields, notes JSON, and created timestamp.
- Keep enough metadata to reproduce historical reports.

## 6. Database Schema Impact

Decision needed:

- Define Backtest database ownership and schema boundaries.

Open questions:

- Should Backtest schema live in `src/backtest`, `src/database`, or a shared schema module?
- Should Backtest create tables for runs, trades, equity curves, assumptions, and strategy evaluations?
- Should statistics and backtest schemas share initialization?

Recommended direction:

- Keep Backtest schema additive.
- Do not alter frozen snapshot/outcome/pattern table contracts unless a verified bug is found.
- Add a clear bootstrap path before implementation.

## 7. Reproducibility Rules

Decision needed:

- Define what makes a backtest reproducible.

Open questions:

- Which assumptions must be stored?
- How should fees, slippage, sizing, entry timing, exit timing, and date ranges be captured?
- How should strategy version and code assumptions be recorded?

Recommended direction:

- Store all run assumptions.
- Store strategy version.
- Store symbol, timeframe, date range, data source, and generated timestamp.
- Avoid network calls and AI calls during Backtest execution.
- Keep Backtest deterministic for fixed inputs.

## 8. Future Context Layer Comparisons

Decision needed later:

- Backtest should eventually support comparing runs with optional context layers enabled or disabled.

Context layers are not implemented yet.

Future examples:

- Strategy only
- Strategy + Sector Context
- Strategy + Market Context
- Strategy + Sector + Industry Context

Purpose:

- Measure whether each Context Engine layer improves results before making it part of default evaluation.
- Keep Context Engine deterministic, optional, and testable.
- Avoid hardcoding sector or market context into Strategy Engine v1.

Open questions:

- How should context layer versions be recorded in backtest assumptions?
- Should context outputs be persisted by `snapshot_id`, symbol/date, or a separate context id?
- Should context be consumed by Probability, Strategy, Backtest, or all of them?
- What fixtures are required to prove context-layer behavior?

## 9. Decisions Required Before Implementation

Before Backtest Engine code is added, decide:

- Historical input source.
- Timeframe aggregation ownership.
- Snapshot selection rules.
- Outcome usage rules.
- StrategyResult persistence shape.
- Backtest table ownership.
- Required run assumptions.
- Reproducibility metadata.
- Minimum test fixtures.
- Whether v1 explicitly records context layers as disabled.

Backtest should remain additive and should consume existing EXOS outputs without modifying frozen upstream contracts.
