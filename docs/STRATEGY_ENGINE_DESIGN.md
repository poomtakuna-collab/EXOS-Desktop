# Strategy Engine v1 Design

Design document for EXOS Strategy Engine v1.

This document defines the intended architecture and contracts before implementation begins.

Strategy Engine v1 must follow `docs/ROADMAP.md`, `docs/PROJECT_STATUS.md`, and `docs/ARCHITECTURE_DECISIONS.md`.

## Purpose

Strategy Engine v1 evaluates trading quality from structured EXOS evidence.

It consumes completed EXOS outputs:

```text
Snapshot
-> Probability
-> Prediction
-> Strategy Evaluation
```

Strategy Engine does not calculate indicators.

Strategy Engine does not discover patterns.

Strategy Engine does not replace Probability Engine or Prediction Engine.

Its purpose is to combine existing evidence into deterministic strategy-quality outputs that can later be used by Backtest Engine, Portfolio Evaluation, Risk Evaluation, reports, and AI Overlay.

Strategy Engine v1 must not output BUY, SELL, or HOLD recommendations.

## Current Inputs

### Snapshot

The snapshot is the completed EXOS market-state contract for a symbol, timeframe, and candle date.

Expected snapshot data includes:

- `snapshot_id`
- symbol
- timeframe
- date
- close price
- EXOS score
- rating
- recommendation field from the frozen score contract
- trend state and score
- trend slope score
- squeeze state and score
- market structure state and score
- complete nested snapshot JSON when deeper context is needed

Strategy Engine should treat snapshots as read-only.

### Probability Engine Output

Probability Engine output provides evidence-based metrics from matched historical patterns.

Expected probability data includes:

- expected 5D return
- expected 10D return
- expected 20D return
- probability of 5% upside within 10D
- probability of 10% upside within 10D
- approximate probability of 5% downside within 10D
- expected 10D max gain
- expected 10D drawdown
- confidence
- evidence count
- best pattern id
- best similarity

Probability Engine output is evidence only. It is not a recommendation.

### Prediction Engine Output

Prediction Engine output provides deterministic price projections from probability outputs.

Expected prediction data includes:

- expected 5D price
- expected 10D price
- expected 20D price
- target zone low
- target zone high
- risk zone low
- risk zone high
- expected return
- confidence
- time horizon
- best pattern id
- best similarity

Prediction Engine output is projection data only. It is not a recommendation.

## Future Inputs

The following inputs are planned for later phases and are not required for Strategy Engine v1:

- Portfolio state
- Risk profile
- Position sizing assumptions
- Existing positions
- Cash balance
- Maximum drawdown limits
- Sector or exposure limits
- Fees and slippage assumptions

These inputs should be added later without changing frozen upstream engine contracts.

## Outputs

Strategy Engine v1 should produce structured strategy-quality outputs.

It must not output BUY, SELL, or HOLD.

### Strategy Score

Range:

- 0 to 100

Purpose:

- Summarize overall strategy quality from available evidence.
- Combine evidence strength, probability quality, prediction quality, reward/risk shape, and snapshot context.

### Trade Grade

Purpose:

- Provide a stable quality label derived from the strategy score.

Example labels:

- Excellent
- Good
- Neutral
- Weak
- Avoid

These labels describe quality only. They are not trade instructions.

### Entry Quality

Purpose:

- Evaluate whether the current snapshot and evidence form a favorable setup quality.

Example fields:

- entry_quality_score
- entry_quality_label
- supporting_factors
- limiting_factors

### Risk Rating

Purpose:

- Describe risk level using prediction risk zone, expected drawdown, downside probability, confidence, and evidence count.

Example labels:

- Low
- Medium
- High
- Unknown

### Reward/Risk Estimate

Purpose:

- Compare expected upside against projected downside.

Example fields:

- expected_reward_percent
- expected_risk_percent
- reward_risk_ratio
- target_zone
- risk_zone

### Notes

Purpose:

- Provide deterministic explanation strings for reports, Backtest Engine, and later AI Overlay.

Notes should explain which structured factors improved or reduced the strategy score.

## Responsibilities

Strategy Engine v1 is responsible for:

- Evaluating evidence quality.
- Combining snapshot, probability, and prediction outputs.
- Producing consistent strategy-quality scoring.
- Producing structured outputs for Backtest Engine.
- Preserving deterministic behavior.
- Explaining score components through structured notes.
- Keeping all inputs read-only.
- Remaining independent from AI.

## Non-Responsibilities

Strategy Engine v1 must not:

- Calculate indicators.
- Modify snapshots.
- Discover patterns.
- Modify Pattern Discovery.
- Modify Pattern Library.
- Modify Similarity Engine.
- Change Probability Engine.
- Change Prediction Engine.
- Call AI.
- Execute trades.
- Place orders.
- Manage brokerage connections.
- Output BUY, SELL, or HOLD.

## Future Integration

### Backtest Engine

Backtest Engine will consume Strategy Engine outputs as historical decision-quality records.

Expected flow:

```text
Snapshot
-> Probability
-> Prediction
-> Strategy Evaluation
-> Backtest Engine
-> Backtest Results
```

Backtest Engine should evaluate how Strategy Engine scores would have performed historically under defined entry, exit, sizing, fee, and slippage assumptions.

### Portfolio Evaluation

Portfolio Evaluation may later use Strategy Engine outputs to compare opportunities across symbols and timeframes.

It may consider:

- portfolio exposure
- available cash
- existing positions
- concentration
- diversification
- strategy quality distribution

### Risk Evaluation

Risk Evaluation may later consume Strategy Engine outputs and portfolio inputs to calculate:

- position-level risk
- portfolio-level drawdown risk
- exposure limits
- risk-adjusted performance
- scenario impact

### AI Overlay

AI Overlay may later summarize Strategy Engine outputs.

AI may:

- explain strategy score components
- summarize quality and risk factors
- generate reports from structured data
- compare current evidence to historical cases

AI must not:

- control Strategy Engine
- alter strategy scores
- output BUY, SELL, or HOLD
- make trading decisions

## Design Principles

Strategy Engine v1 must be:

- Deterministic.
- Testable.
- Explainable.
- Independent.
- Modular.
- Read-only against upstream contracts.
- Additive to the frozen EXOS Brain v1 pipeline.

Strategy Engine should consume structured data, produce structured results, and avoid hidden state.

## Contract Boundary

Strategy Engine v1 should be implemented later as a new module.

It should consume:

```text
snapshot
probability_output
prediction_output
```

It should return:

```text
strategy_evaluation
```

The output should be stable enough for Backtest Engine to store and replay.

No existing engine contract should change to support Strategy Engine v1 unless a verified bug is found.

## Open Design Items Before Implementation

Before implementation begins, define:

- exact strategy score formula
- trade grade thresholds
- entry quality scoring rules
- risk rating thresholds
- reward/risk calculation rule
- confidence and evidence-count minimums
- output schema
- unit test fixtures
- backtest persistence format

These decisions should be documented before source code is added.
