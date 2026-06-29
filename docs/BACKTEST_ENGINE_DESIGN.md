# Backtest Engine v1 Design

Design document for EXOS Backtest Engine v1.

This document defines architecture and contracts for Backtest Engine v1.

In-memory Backtest Framework v1 is implemented.

Database-backed Backtest is not implemented yet.

## 1. Purpose

Backtest Engine v1 evaluates historical StrategyResult performance using reproducible historical data.

It replays historical EXOS decision points and compares Strategy Engine outputs against later market outcomes.

Backtest Engine should answer:

- How did historical high-scoring setups perform?
- How did StrategyResult grades compare with actual future outcomes?
- How did expected reward/risk compare with realized reward/risk?
- What drawdowns appeared during historical replay?
- Which evidence levels were associated with better or worse results?

Backtest Engine must be deterministic.

Backtest Engine must not output BUY, SELL, or HOLD.

Implemented in-memory components:

- Backtest contracts
- Backtest types
- Simulation rules
- Replay Engine
- Metrics Aggregator
- Backtest Pipeline
- Backtest Report
- Unit Tests

Not implemented yet:

- Database-backed Backtest
- Snapshot Loader
- Outcome Loader
- Dataset Builder
- Historical replay from stored datasets
- Portfolio Evaluation
- UI integration
- AI overlay

## 2. Inputs

Backtest Engine v1 should consume structured historical records and completed EXOS outputs.

### Historical OHLCV Rows

Purpose:

- Provide reproducible historical prices for simulation, drawdown, and actual outcome measurement.

Expected fields:

- symbol
- date
- open
- high
- low
- close
- volume
- source

### Snapshot Records

Purpose:

- Provide historical decision points.

Expected fields:

- `snapshot_id`
- symbol
- timeframe
- date
- close
- EXOS score
- rating
- trend state and score
- trend slope score
- squeeze state and score
- market structure state and score
- snapshot JSON

Snapshots are read-only.

### Outcome Records

Purpose:

- Provide measured future outcomes for validation and comparison.

Expected fields:

- `outcome_id`
- `snapshot_id`
- forward 5D return
- forward 10D return
- forward 20D return
- max gain 10D
- max drawdown 10D
- hit 5% within 10D
- hit 10% within 10D
- label 10D

### Probability Output

Purpose:

- Provide evidence-based probability metrics for each historical decision point.

Expected fields:

- expected 5D return
- expected 10D return
- expected 20D return
- upside probability
- downside probability
- expected max gain
- expected drawdown
- confidence
- evidence count
- best pattern id
- best similarity

### Prediction Output

Purpose:

- Provide deterministic price projections and zones for each historical decision point.

Expected fields:

- expected 5D price
- expected 10D price
- expected 20D price
- target zone
- risk zone
- expected return
- confidence
- time horizon
- best pattern id
- best similarity

### StrategyResult

Purpose:

- Provide the Strategy Engine evaluation being tested.

Expected fields:

- strategy score
- trade grade
- entry quality
- risk rating
- reward/risk estimate
- notes

StrategyResult must be produced deterministically from `StrategyInput`.

## 3. Outputs

Backtest Engine v1 produces structured performance outputs in memory.

### BacktestResult

Purpose:

- Summarize one reproducible backtest run.

Planned fields:

- run id
- strategy version
- symbol set
- timeframe
- date range
- snapshot count
- evaluated setup count
- skipped setup count
- assumptions
- created timestamp
- metrics summary

Current in-memory `BacktestResult` fields:

- total trades
- attempted trades
- completed trades
- winning trades
- losing trades
- skipped trades
- breakeven trades
- win rate
- average return
- average drawdown
- expectancy
- max drawdown
- notes

Count semantics:

- `attempted_trades` counts every `SimulationResult` supplied to the metrics aggregator.
- `completed_trades` counts `SimulationStatus.SUCCESS` records.
- `total_trades` is retained as a backward-compatible alias for completed trades.
- `skipped_trades` counts non-success simulations, including insufficient-data records.
- `breakeven_trades` counts completed breakeven simulations and is not included in win or loss counts.

### Trade Simulation Summary

Purpose:

- Summarize replayed historical strategy decisions.

Planned fields:

- total simulated trades or evaluated setups
- eligible setups
- skipped setups
- breakeven setups
- average strategy score
- average evidence count
- average expected reward
- average actual return

### Win/Loss Statistics

Purpose:

- Compare simulated setups against outcome labels or trade rules.

Planned fields:

- wins
- losses
- win rate
- loss rate
- average win
- average loss
- expectancy

### Expected vs Actual Comparison

Purpose:

- Compare StrategyResult and Prediction output against realized historical outcomes.

Planned fields:

- expected return
- actual forward return
- expected max gain
- actual max gain
- expected drawdown
- actual max drawdown
- prediction error

### Drawdown Statistics

Purpose:

- Measure downside behavior during replay.

Planned fields:

- max drawdown
- average drawdown
- worst 10D drawdown
- drawdown by grade
- drawdown by risk rating

### Strategy Score Distribution

Purpose:

- Analyze performance by score bucket and trade grade.

Planned fields:

- count by score range
- count by trade grade
- average return by score range
- average drawdown by score range
- win rate by score range

### Evidence Count

Purpose:

- Track how much historical evidence supported evaluated setups.

Planned fields:

- average evidence count
- minimum evidence count
- maximum evidence count
- performance by evidence bucket

## 4. Responsibilities

Backtest Engine v1 currently:

- Replays one StrategyResult against one future OHLCV sequence.
- Aggregates multiple replay results.
- Runs a pure in-memory pipeline.
- Builds a deterministic report object.

Database-backed Backtest later should:

- Replay historical snapshots.
- Apply Strategy Engine deterministically.
- Compare StrategyResult against future outcomes.
- Compare expected outputs against actual historical results.
- Produce reproducible performance metrics.
- Track skipped records and explain why they were skipped.
- Store or return enough metadata to reproduce a run later.
- Keep all historical inputs read-only.

## 5. Non-Responsibilities

Backtest Engine v1 must not:

- Modify historical data.
- Change snapshots.
- Discover new patterns.
- Recalculate indicators.
- Modify Probability Engine.
- Modify Prediction Engine.
- Modify Strategy Engine scoring.
- Call AI.
- Execute trades.
- Place orders.
- Connect to broker APIs.
- Fetch live market data.
- Output BUY, SELL, or HOLD recommendations.

## 6. Design Decisions

Backtest Engine v1 should follow `docs/BACKTEST_DECISIONS.md`.

### Historical Source of Truth

Decision direction:

- SQLite-backed historical data should be the source of truth.
- Backtest should avoid network calls during execution.
- Historical decision points should reference `snapshot_id`.

Open:

- Whether database-backed Backtest requires all snapshots to be precomputed or can report missing snapshots.

### Timeframe Handling

Decision direction:

- Timeframe aggregation should not live in GUI code.
- Backtest should use deterministic timeframe handling.

Open:

- Whether aggregated timeframe data is stored or generated at runtime.
- How incomplete weekly/monthly candles are handled.

### Snapshot Selection

Decision direction:

- Select snapshots by symbol, timeframe, and date range.
- Treat snapshots as read-only.
- Use `snapshot_id` as the historical decision reference.

Open:

- Additional selection filters such as score, state, or strategy eligibility.

### Outcome Availability

Decision direction:

- Outcome records may be used for validation and comparison.
- Backtest may calculate trade-specific results from OHLCV according to explicit rules later.

Open:

- Whether outcome rows are mandatory for v1.
- How skipped snapshots are represented when future data is unavailable.

### StrategyResult Storage

Decision direction:

- StrategyResult should be persistable by `snapshot_id` and strategy version.
- Reward/risk fields should remain structured.
- Notes may be stored as JSON.

Open:

- Whether database-backed Backtest stores StrategyResult outputs immediately or returns them in memory first.

Current:

- In-memory Backtest Framework receives StrategyResult inside `BacktestInput`.

### Database Schema Impact

Decision direction:

- Backtest schema should be additive.
- Frozen snapshot/outcome/pattern contracts should not change unless fixing verified bugs.

Open:

- Final table ownership and bootstrap path.
- Required tables for runs, evaluations, trades, equity curves, and assumptions.

### Reproducibility Rules

Decision direction:

- Store run assumptions.
- Store strategy version.
- Store symbol, timeframe, date range, data source, and generated timestamp.
- Avoid network and AI calls during Backtest execution.

Open:

- Exact assumption schema.
- Versioning format for strategy and backtest logic.

## 7. Future Integration

### Portfolio / Risk Evaluation

Backtest results will later provide inputs for portfolio-level analysis.

Future consumers may use:

- drawdown statistics
- position-level performance
- exposure by symbol
- risk by strategy grade
- performance by evidence bucket

### Strategy Tuning

Backtest outputs may later help compare strategy score thresholds, risk filters, or evidence minimums.

Strategy tuning must remain deterministic and should not alter frozen upstream engine contracts.

### AI Reports

AI Overlay may later summarize BacktestResult outputs.

AI may:

- explain performance summaries
- compare expected and actual outcomes
- summarize drawdown behavior
- generate reports from structured backtest outputs

AI must not:

- run backtests
- alter results
- make trading decisions
- output BUY, SELL, or HOLD

### UI Reports

UI reports may later display:

- backtest summary
- performance by grade
- drawdown chart
- expected vs actual comparison
- strategy score distribution
- skipped record summary

UI should read structured BacktestResult data instead of recalculating backtest logic.

## 8. Open Questions

Before implementation begins, answer:

- What exact DB-backed BacktestInput construction path should be used?
- What additional metadata should be added to BacktestResult before persistence?
- Which outcome horizon is the default comparison target?
- Are outcome rows required, or can OHLCV rows alone drive actual results?
- How are entry and exit timing rules represented?
- How are fees and slippage represented?
- How is strategy version recorded?
- How is backtest version recorded?
- Where does Backtest schema live?
- Are StrategyResult outputs persisted in database-backed Backtest?
- Should weekly/monthly timeframe support wait until aggregation is moved out of GUI?
- What minimum fixtures are required before implementation?

## Implementation Rule

Backtest Engine v1 must be additive.

It should consume existing EXOS outputs and should not modify frozen upstream contracts.
