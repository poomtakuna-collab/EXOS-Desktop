# Backtest Simulation Rules

Simulation rules for Backtest Engine v1.

This document defines deterministic replay assumptions for Backtest Engine v1.

In-memory Backtest simulation logic is implemented.

Database-backed simulation is not implemented yet.

## Purpose

Backtest Simulation v1 defines a simple, reproducible way to evaluate historical StrategyResult performance.

The rules are intentionally limited:

- one simulated trade per snapshot
- deterministic entry
- deterministic target
- deterministic stop/risk handling
- fixed horizon
- no portfolio logic
- no position sizing
- no AI

Simulation v1 is a foundation for measuring whether Strategy Engine outputs have historical value. It is not a complete trading system.

## Deterministic Replay Principle

For the same inputs, Backtest Simulation v1 must always produce the same result.

The simulation must not:

- fetch live data
- call AI
- mutate historical data
- modify snapshots
- recalculate indicators
- discover patterns
- change StrategyResult
- use random behavior

Every skipped or insufficient-data record should include a deterministic reason.

## Simulation Scope

Simulation v1 assumptions:

- One simulated trade per snapshot.
- Entry uses snapshot close or an explicitly provided current price.
- Target is derived from StrategyResult reward/risk target zone when available.
- Stop/risk is derived from StrategyResult reward/risk risk zone when available.
- The default horizon is 10 trading days.
- If both target and stop are hit in the same window, use the conservative outcome.
- If neither target nor stop is hit within the horizon, classify by final return.
- Missing required future OHLCV data results in `SKIPPED` / `INSUFFICIENT_DATA`.

Simulation v1 does not include:

- position sizing
- portfolio logic
- partial exits
- trailing stops
- pyramiding
- fees
- slippage
- AI
- broker execution

## Entry Rule

Default entry:

- Use snapshot close as the simulated entry price.

Alternative future input:

- Use provided current price if BacktestInput later includes an explicit entry/current price field.

Required data:

- `snapshot.close` or equivalent structured snapshot close field.

If entry price is missing, zero, or invalid:

- status: `INSUFFICIENT_DATA`
- exit reason: `INSUFFICIENT_DATA`

## Exit Rule

Simulation v1 exits by the first applicable condition:

1. Target hit.
2. Stop/risk-zone hit.
3. Timeout at the configured horizon.
4. Open if the horizon has not completed.
5. Skipped if required data is missing.

If target and stop are both hit in the same evaluation window, Simulation v1 uses the conservative result:

- stop/risk-zone hit takes priority over target hit.

This rule avoids overstating historical performance when intraday order is unknown.

## Target Handling

Target source:

- StrategyResult `reward_risk_estimate.target_zone`.

Default target:

- Use the lower target-zone bound for conservative evaluation when both low and high are available.

If only one target-zone bound is available:

- Use the available bound.

If no target is available:

- Simulation may still evaluate timeout and final return.
- Target-based win classification should not be used.

Target hit condition:

- Future high is greater than or equal to the target price within the horizon.

## Stop / Risk-Zone Handling

Stop source:

- StrategyResult `reward_risk_estimate.risk_zone`.

Default stop:

- Use the lower risk-zone bound when both low and high are available.

If only one risk-zone bound is available:

- Use the available bound.

If no stop is available:

- Simulation may still evaluate target and timeout.
- Risk-zone stop classification should not be used.

Stop hit condition:

- Future low is less than or equal to the stop price within the horizon.

## Timeout Handling

Timeout occurs when neither target nor stop is hit within the configured horizon.

Default horizon:

- 10 trading days.

Timeout exit price:

- Use the close price of the final available row in the horizon.

Timeout classification:

- Positive final return: `WIN`
- Negative final return: `LOSS`
- Zero final return: `BREAKEVEN`

## Open Trade Handling

A simulated trade is `OPEN` when:

- the snapshot is valid
- entry data is valid
- future rows exist
- the configured horizon has not completed
- target and stop have not been hit

Open trades should not be counted as wins or losses.

Open trades should be reported separately from skipped records.

## Breakeven Handling

A trade is `BREAKEVEN` when:

- timeout occurs and final return is exactly zero
- or a future explicit breakeven rule exits at entry price

Simulation v1 does not implement a separate breakeven stop.

Breakeven trades should not be counted as wins or losses unless a later reporting rule explicitly chooses to include them.

Breakeven trades are included in `completed_trades` / `total_trades` and exposed separately as `breakeven_trades`.

## Missing Data Handling

Missing required data results in:

- status: `INSUFFICIENT_DATA`
- trade outcome: `OPEN` or another non-win/loss placeholder
- exit reason: `INSUFFICIENT_DATA`

Missing required data includes:

- missing entry price
- invalid entry price
- no future OHLCV rows
- not enough rows to evaluate the configured horizon
- missing high/low/close fields required for target, stop, or timeout checks

Backtest records skipped counts as `skipped_trades` and preserves deterministic notes.

The metrics aggregator also exposes:

- `attempted_trades`
- `completed_trades`
- `breakeven_trades`

`total_trades` remains a backward-compatible completed-trade count.

## Simulation Contracts

Backtest Simulation v1 uses these public contract concepts:

- `SimulationConfig`
- `SimulationRule`
- `SimulationResult`
- `SimulationStatus`
- `TradeOutcome`
- `ExitReason`

These contracts define the vocabulary for replay logic.

The current in-memory Replay Engine and Metrics Aggregator implement these contracts without database access.

## Conservative Same-Window Rule

When target and stop are both hit in the same evaluation window, Simulation v1 assumes the worse outcome.

For a long-only simulation:

- stop hit wins priority over target hit.

Reason:

- Daily OHLCV data does not prove whether target or stop happened first inside the same candle.
- Conservative handling reduces optimistic backtest bias.

## Versioning

Simulation v1 is intentionally simple.

Future versions may add:

- fees
- slippage
- position sizing
- partial exits
- trailing stops
- portfolio constraints
- context-layer toggles

New behavior should be versioned and compared against Simulation v1 before becoming default.

## Implementation Guardrails

When Backtest replay logic is implemented later, it must:

- remain deterministic
- use structured EXOS inputs
- avoid AI
- avoid database writes unless explicitly part of a persistence step
- avoid modifying historical records
- avoid changing Strategy Engine logic
- preserve frozen Brain v1 contracts
