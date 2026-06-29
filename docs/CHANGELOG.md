# CHANGELOG

## Backtest Data Layer Skeleton

- Added `src/backtest/data/` package skeleton.
- Added `SnapshotQuery`.
- Added `SnapshotLoader`, `OutcomeLoader`, and `FutureRowsLoader` public interfaces.
- Added `BacktestDataset` and `BacktestDatasetBuilder` public interfaces.
- Added Backtest data-layer skeleton unit tests.
- Data-layer implementations intentionally raise `NotImplementedError`.
- SQLite-backed loading, SQL queries, historical dataset construction, DB-backed Backtest execution, Portfolio Evaluation, and AI overlay are not implemented yet.

## Backtest Framework v1

- Added Backtest contracts.
- Added Backtest types.
- Added Backtest Simulation Rules documentation.
- Added deterministic single-trade Replay Engine.
- Added Metrics Aggregator.
- Added Backtest Pipeline.
- Added deterministic Backtest Report layer.
- Added Backtest unit tests.
- Backtest Framework v1 is in-memory only.
- Database-backed Backtest, Snapshot Loader, Outcome Loader, Dataset Builder, historical replay from stored datasets, Portfolio Evaluation, UI integration, and AI overlay are not implemented yet.

## Pre-Backtest Stabilization

- Added Architecture Audit v2.
- Added Backtest decision preparation notes.
- Clarified Strategy reward/risk estimate contract with typed fields.
- Updated project status and roadmap for Strategy Engine v1 initial implementation.
- Confirmed Backtest Engine remains not implemented.

## Strategy Engine v1 Initial Implementation

- Added `src/strategy` package.
- Added Strategy input/output contracts.
- Added Strategy grade, risk, and entry-quality enums.
- Added deterministic `analyze_strategy` implementation.
- Added Strategy Engine unit tests.
- Added Strategy contract regression tests.
- Strategy Engine v1 does not call AI, load market data, access the database, or output BUY / SELL / HOLD.

## Brain v1 Completed

- Frozen EXOS Brain v1 architecture.
- Completed analysis pipeline:
  Market Data → Core Indicators → Snapshot → Statistics → Outcome → Pattern Discovery → Pattern Library → Similarity → Probability → Prediction.
- Future enhancements should extend the pipeline rather than modifying existing engine contracts unless fixing a verified bug.

## Market Learning Engine v1

- Added Statistics DB schema helpers.
- Added Snapshot Store.
- Added Snapshot Collector.
- Added Outcome Calculator.
- Added Pattern Discovery Engine.
- Added Pattern Library.
- Added Similarity Engine.
- Added end-to-end Market Learning Pipeline smoke test.

## Core Indicators v1

- Added Indicator Engine v1.
- Added EW Engine v1.
- Added Volume Pressure Engine v1.
- Added Trend Slope Engine v1.
- Added Squeeze Engine v1.
- Added Market Structure Engine v1.
- Added Snapshot Builder v1.
- Added Score Engine v1.
- Core Indicators v1 is complete and frozen unless a real bug appears.

## Chart And Data Foundation

- Added Dashboard.
- Added State Manager.
- Added SQLite Cache.
- Added Developer Mode.
- Added Candlestick Chart v1.
- Added real cached OHLC chart flow.
- Added chart metadata label and configurable visible rows.
- Added volume panel aligned to candlestick rows.
- Added market header from latest cached OHLCV row.
- Added current price line and right-side price label.
- Moved price and volume axis labels to the right side.
- Added EMA20, EMA50, and EMA200 overlays.
- Added mouse crosshair and OHLC/EMA hover tooltip.
- Added automatic cache-miss OHLCV loading for selected symbols.
- Added NASDAQ-only scanner scope guard.
- Added Timeframe Engine v1 with 1D, 1W, and 1M chart views.
- Added 10-year daily OHLCV Yahoo Finance fetch depth.
- Added visible rows control for 60, 120, 240, and All.
- Added Dark Theme v1 for standard PySide6 widgets.
