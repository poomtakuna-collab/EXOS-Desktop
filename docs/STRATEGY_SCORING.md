# Strategy Scoring

Strategy Scoring v1 design notes.

This document defines the scoring philosophy only. It does not define formulas, weights, or implementation logic.

## 1. Purpose

Strategy Score represents the quality of a trading setup based on structured EXOS evidence.

It measures trade quality, not certainty.

A high Strategy Score means the available evidence is stronger, cleaner, and more favorable than a lower-scoring setup. It does not guarantee an outcome.

Strategy Score should help later systems compare setups consistently across symbols, timeframes, and historical decision points.

Strategy Score must not output BUY, SELL, or HOLD.

## 2. High-Level Philosophy

Strategy Engine v1 should combine evidence rather than predict the future.

It evaluates setup quality using existing EXOS outputs:

```text
Snapshot
-> Probability
-> Prediction
-> Strategy Score
```

Strategy Scoring should answer:

- How strong is the current setup evidence?
- How consistent are the probability and prediction outputs?
- How favorable is the reward/risk shape?
- How reliable is the available historical evidence?
- What factors improve or reduce the setup quality?

Strategy Scoring should not invent new market facts. It should consume structured outputs from the frozen pipeline and produce deterministic quality metrics.

## 3. Candidate Scoring Dimensions

The following dimensions are candidates for Strategy Scoring v1.

No weights are assigned yet.

### Trend Quality

Evaluates whether the snapshot shows a constructive trend state and trend slope.

Potential inputs:

- trend state
- trend score
- trend slope score
- EXOS score

### Probability Quality

Evaluates whether Probability Engine output shows favorable evidence-based expectations.

Potential inputs:

- expected 5D return
- expected 10D return
- expected 20D return
- probability of 5% upside within 10D
- probability of 10% upside within 10D
- approximate downside probability

### Prediction Quality

Evaluates whether Prediction Engine output produces useful and coherent price projections.

Potential inputs:

- expected 5D price
- expected 10D price
- expected 20D price
- target zone
- risk zone
- expected return
- prediction confidence

### Market Structure

Evaluates whether the market structure state supports or weakens the setup.

Potential inputs:

- market structure state
- market structure score
- break-of-structure context from the snapshot contract
- change-of-character context from the snapshot contract

### Risk Quality

Evaluates whether downside characteristics are acceptable relative to the setup evidence.

Potential inputs:

- expected drawdown
- probability of downside
- risk zone
- confidence
- evidence count

### Reward/Risk

Evaluates whether expected reward is reasonable compared with projected risk.

Potential inputs:

- expected 10D return
- expected max gain
- expected drawdown
- target zone
- risk zone

### Confidence

Evaluates how reliable the combined evidence appears.

Potential inputs:

- Probability Engine confidence
- Prediction Engine confidence
- best similarity
- consistency between expected return and projected price zones

### Evidence Strength

Evaluates whether enough historical evidence supports the current setup.

Potential inputs:

- evidence count
- sample count from matched patterns
- best pattern id
- best similarity

## 4. What Strategy Score Is Not

Strategy Score is not:

- win probability
- AI confidence
- BUY recommendation
- SELL recommendation
- HOLD recommendation
- guaranteed return
- portfolio allocation
- position size
- trade execution instruction

Strategy Score is a deterministic quality score derived from structured EXOS outputs.

## 5. Trade Grade

Trade Grade is a human-readable label derived from Strategy Score.

Planned grade labels:

- Excellent
- Good
- Neutral
- Weak
- Avoid

Illustrative interpretation:

- Excellent: very strong setup quality with favorable evidence and risk shape.
- Good: constructive setup quality with useful supporting evidence.
- Neutral: mixed or incomplete evidence.
- Weak: low-quality setup or unfavorable evidence.
- Avoid: poor setup quality, weak evidence, or unfavorable risk shape.

Grade ranges are illustrative only. Exact thresholds will be defined later.

Trade Grade must not be interpreted as BUY, SELL, or HOLD.

## 6. Future Extensibility

Strategy Scoring should be modular.

Future versions may add new scoring dimensions without breaking existing contracts by:

- preserving `StrategyInput`
- preserving `StrategyResult`
- adding optional detail fields later if needed
- keeping existing grade labels stable
- versioning new scoring methods
- documenting new dimensions before implementation

Examples of future dimensions:

- portfolio fit
- position sizing quality
- sector exposure
- volatility regime
- liquidity quality
- backtest performance profile

New dimensions should consume structured EXOS outputs or future structured risk/portfolio outputs. They should not modify frozen upstream engine contracts.

## 7. Versioning

Strategy Scoring v1 establishes philosophy only.

It defines:

- what Strategy Score represents
- candidate scoring dimensions
- what Strategy Score is not
- planned Trade Grade labels
- extensibility expectations

It does not define:

- formulas
- weights
- thresholds
- algorithms
- implementation logic

Weights and algorithms will be introduced in a later design or implementation sprint after the scoring philosophy is accepted.
