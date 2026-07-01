# EXOS Architecture Decisions

Key architecture decisions for EXOS Desktop.

These decisions preserve the frozen roadmap and project principles in `docs/ROADMAP.md` and `docs/PROJECT_STATUS.md`.

## ADR-001: SQLite as Source of Truth

Status: Accepted.

Decision:

EXOS uses SQLite as the local source of truth for historical market data, market-learning statistics, snapshots, outcomes, and reusable pattern evidence.

Reason:

- EXOS is local-first and must remain useful without a remote service dependency.
- Historical research and backtest inputs must be reproducible.
- SQLite provides durable structured storage for local datasets.
- SQLite supports targeted queries by symbol, timeframe, date, score, state, and `snapshot_id`.
- Historical statistics should be queryable without loading every stored snapshot into memory.

Consequence:

Future statistics, strategy, backtest, prediction, and AI analysis features should read from structured SQLite data where possible. JSON files may still be used for small app state, but historical research data belongs in SQLite.

## ADR-002: Snapshot-First Architecture

Status: Accepted.

Decision:

EXOS uses snapshots as the central market-state contract.

Reason:

- A snapshot captures the completed Core Indicators v1 output for a symbol, timeframe, and candle date.
- Snapshots create stable historical decision points.
- `snapshot_id` is the main reference connecting statistics, outcomes, patterns, similarity, probability, and prediction.
- Searchable snapshot fields can be stored as columns while the complete nested snapshot remains available as JSON.

Consequence:

Future systems should reference historical market state through `snapshot_id` instead of recalculating or redefining upstream engine outputs. Strategy, backtest, risk, reports, and AI analysis should consume snapshots as stable inputs.

## ADR-003: Statistics Before Strategy

Status: Accepted.

Decision:

EXOS collects outcomes and pattern evidence before adding Strategy Engine rules.

Reason:

- Strategy logic should be based on measured historical outcomes, not intuition.
- Pattern discovery depends on completed snapshots joined to future outcomes.
- Evidence needs to exist before entry, exit, and risk rules can be evaluated responsibly.
- Backtest results should be reproducible from stored data and deterministic rules.

Consequence:

Strategy Engine work should begin only after the market-learning pipeline has produced usable snapshots, outcomes, patterns, similarity results, probability metrics, and prediction outputs.

## ADR-004: Probability Before Strategy

Status: Accepted.

Decision:

EXOS produces evidence-based probability metrics before Strategy Engine decisions.

Reason:

- Probability Engine outputs are not BUY, SELL, or HOLD recommendations.
- Probability Engine v1 converts matched historical patterns into expected returns, upside probabilities, downside risk approximation, confidence, and evidence count.
- Prediction Engine v1 converts probability outputs into price projections and zones.
- Strategy Engine will consume probability outputs later as structured evidence.

Consequence:

Probability and prediction outputs must remain descriptive metrics. Recommendation, entry, exit, and position logic belongs in later Strategy / Backtest / Risk systems.

## ADR-005: AI Explains, AI Does Not Decide

Status: Accepted.

Decision:

AI is an explanation and reporting layer only.

Reason:

- EXOS must remain functional without AI.
- AI must not replace deterministic data, indicator, statistics, probability, strategy, backtest, or risk systems.
- AI must not output BUY, SELL, or HOLD recommendations.
- AI may summarize structured EXOS outputs, explain market context, compare historical situations, and generate reports.

Consequence:

Final trading logic must come from Strategy / Backtest / Risk systems. AI may read structured outputs and explain them, but it must not control core logic or make trading decisions.

## ADR-006: Frozen Engine Contracts

Status: Accepted.

Decision:

Completed v1 engines are frozen and should not be changed unless fixing verified bugs.

Reason:

- EXOS Brain v1 is complete and frozen.
- Core Indicators v1, Market Learning v1, Probability Engine v1, and Prediction Engine v1 form the stable foundation for future phases.
- Stable contracts protect reproducibility and reduce downstream drift.
- Future development should extend the pipeline instead of modifying completed engine behavior.

Consequence:

Phase 4 Strategy / Backtest work should be additive. New modules should consume existing snapshots, outcomes, patterns, similarity results, probability outputs, and prediction outputs without changing frozen upstream contracts unless a verified bug is found.

## ADR-007: Context Engine as Future Brain v2 Layer

Status: Accepted.

Decision:

Sector, market, industry, relative strength, and optional macro context should be implemented later as a separate deterministic Context Engine / Market Context Layer.

Context should not be hardcoded into Strategy Engine v1.

Reason:

- A stock may pass stock-level EXOS conditions while its sector ETF or broader market context is weak.
- Context is important, but it should not modify frozen Brain v1 contracts.
- Context Engine should remain deterministic structured market data analysis, not AI.
- Context should be independently testable and toggleable.
- Backtest should prove whether each context layer improves results before it becomes part of default evaluation.

Consequence:

Future Context Engine outputs may be consumed by Probability, Strategy, Backtest, statistical performance reports, or AI reports after the Backtest foundation exists.

Backtest should eventually compare:

- Brain v1 only
- Brain v1 + Sector Context
- Brain v1 + Market Context
- Brain v1 + Sector + Industry Context

Context layers must extend the pipeline rather than modifying completed v1 engine contracts.

## ADR-008: Portfolio / Risk Evaluation Parked

Status: Accepted.

Decision:

Portfolio / Risk Evaluation is postponed and parked as a future / experimental area.

EXOS is a NASDAQ investment research platform first, not a portfolio management system.

Reason:

- Near-term EXOS value comes from signal logging, trade journaling, outcome tracking, statistical performance reporting, and deterministic market context.
- Portfolio allocation, diversification, correlation analysis, and capital optimisation require real usage patterns before the correct product shape is clear.
- Adding portfolio dependencies too early would pull EXOS toward account management instead of evidence-driven research.
- Strategy, Backtest, Analysis Pipeline, Data Source, and Context Engine should remain independent of portfolio state.

Consequence:

Portfolio Engine code, if present, should remain experimental / future / parked.

Portfolio Engine must not be wired into the default pipeline.

Portfolio Engine must not become a dependency of Strategy, Backtest, Analysis Pipeline, Data Source, or Context Engine.

Portfolio / Risk Evaluation may be reconsidered only after real EXOS usage proves that portfolio-level workflows are needed.
