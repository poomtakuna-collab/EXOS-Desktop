# EXOS Testing Plan

Testing plan for EXOS Desktop developer infrastructure.

This document describes the current test coverage, missing tests, proposed test structure, and long-term regression strategy before database-backed Backtest and Portfolio implementation begins.

## Current Test Coverage

Current automated coverage includes:

- `tests/smoke/test_market_learning_pipeline.py`
- `tests/unit/test_strategy_engine.py`
- `tests/regression/test_strategy_contract.py`
- `tests/unit/test_backtest_engine.py`
- `tests/unit/test_backtest_metrics.py`
- `tests/unit/test_backtest_pipeline.py`
- `tests/unit/test_backtest_report.py`
- `tests/unit/test_backtest_data_skeleton.py`
- `tests/unit/test_backtest_db_schema.py`
- `tests/unit/test_sqlite_snapshot_loader.py`
- `tests/unit/test_sqlite_outcome_loader.py`
- `tests/unit/test_sqlite_future_rows_loader.py`
- `tests/unit/test_sqlite_backtest_dataset_builder.py`
- `tests/integration/test_strategy_backtest_pipeline.py`
- `tests/integration/test_sqlite_backtest_read_only_runner.py`

Covered flow:

```text
fake OHLCV rows
-> build_exos_snapshot
-> collect_snapshots_for_series
-> snapshots table
-> calculate_outcomes_for_series
-> outcomes table
-> discover_patterns
-> rebuild_pattern_library
-> find_similar_patterns
```

The smoke test verifies the happy path for Market Learning v1 using an in-memory SQLite database.

The Strategy Engine tests verify:

- valid StrategyInput returns StrategyResult
- score bounds
- empty probability input
- empty prediction input
- missing optional fields
- low confidence scenarios
- high confidence scenarios
- zero evidence
- high evidence
- score boundary behavior
- reward/risk edge cases
- malformed numeric values
- StrategyResult public shape
- no BUY / SELL / HOLD output

The Backtest Framework tests verify:

- target hit replay
- stop hit replay
- target and stop in the same candle
- timeout handling
- missing data handling
- invalid input handling
- deterministic replay
- stable SimulationResult shape
- metrics aggregation
- all-win, all-loss, mixed, breakeven, skipped, and empty-input metrics cases
- skipped / insufficient-data aggregation
- typed BacktestResult attempted/completed/skipped/breakeven counts
- expectancy and drawdown calculations
- Backtest Pipeline orchestration
- deterministic Backtest Report output
- typed BacktestReport attempted/completed/skipped/breakeven counts
- stable BacktestReport shape
- StrategyResult to BacktestInput to BacktestReport integration flow
- no BUY / SELL / HOLD output in Strategy-to-Backtest integration output
- no database, AI, network, or live data access in Strategy-to-Backtest integration coverage
- Backtest Data Layer public imports
- SnapshotQuery defaults
- BacktestDataset defaults
- loader and builder methods remain explicit skeletons
- DB-backed Backtest persistence and loading path design is documented
- Backtest DB schema skeleton table creation
- Backtest DB schema required columns
- Backtest DB schema initializer idempotency
- Backtest DB schema initialization does not modify existing source tables
- Backtest DB schema initialization does not import live data, AI, network, or broker modules
- SQLiteSnapshotLoader reads existing snapshots only
- SQLiteSnapshotLoader filters by symbol, timeframe, date range, and limit
- SQLiteSnapshotLoader returns deterministic ordering by symbol, timeframe, date, and snapshot_id
- SQLiteSnapshotLoader missing source table failure is clear and deterministic
- SQLiteSnapshotLoader does not write to the database
- SQLiteOutcomeLoader reads existing outcomes only
- SQLiteOutcomeLoader loads matching snapshot_id records and ignores non-matching rows
- SQLiteOutcomeLoader handles empty snapshot_id lists deterministically
- SQLiteOutcomeLoader returns deterministic ordering by snapshot_id and outcome_id
- SQLiteOutcomeLoader missing source table failure is clear and deterministic
- SQLiteOutcomeLoader does not write to the database
- SQLiteFutureRowsLoader reads existing OHLCV rows only
- SQLiteFutureRowsLoader loads rows after snapshot date only
- SQLiteFutureRowsLoader respects horizon limits
- SQLiteFutureRowsLoader groups rows by snapshot_id
- SQLiteFutureRowsLoader missing source table failure is clear and deterministic
- SQLiteFutureRowsLoader does not write to the database
- SQLiteBacktestDatasetBuilder composes SQLite loaders without executing replay
- SQLiteBacktestDatasetBuilder matches outcomes by snapshot_id
- SQLiteBacktestDatasetBuilder groups future rows by snapshot_id
- SQLiteBacktestDatasetBuilder represents missing outcomes and future rows deterministically
- SQLiteBacktestDatasetBuilder does not write to the database
- Read-only SQLite Backtest runner flows DB rows to dataset, BacktestResult, and BacktestReport
- Read-only SQLite Backtest runner preserves skipped records deterministically
- Read-only SQLite Backtest runner produces typed Backtest and report counts
- Read-only SQLite Backtest runner does not write to the database
- Read-only SQLite Backtest runner does not call AI, live data, network, or broker paths
- Read-only SQLite Backtest runner does not emit BUY / SELL / HOLD output

Current test count:

- 97 tests

Current gaps:

- No dedicated unit tests for Core Indicators v1.
- No dedicated unit tests for Snapshot Builder v1.
- No dedicated unit tests for database persistence.
- No dedicated unit tests for Probability Engine v1.
- No dedicated unit tests for Prediction Engine v1.
- No regression fixtures for frozen engine contracts.
- No GUI tests.
- No integration tests using the on-disk SQLite database.
- No database-backed Backtest persistence tests yet.
- No Backtest persistence write/read round-trip tests yet.

## Proposed Test Structure

Long-term test layout:

```text
tests/
  smoke/
    test_market_learning_pipeline.py
  unit/
    analysis/
    statistics/
    data/
    database/
    core/
  regression/
    fixtures/
    test_snapshot_contract.py
    test_probability_contract.py
    test_prediction_contract.py
  integration/
    test_database_pipeline.py
    test_data_manager_cache.py
    test_strategy_backtest_pipeline.py
```

Current implemented layout:

```text
tests/
  smoke/
  unit/
  regression/
  integration/
```

Empty folders are placeholders for future test work.

## Missing Tests by Module

### `src/analysis`

Missing:

- Indicator Engine v1 tests.
- EW Engine v1 tests.
- Volume Pressure Engine v1 tests.
- Trend Slope Engine v1 tests.
- Squeeze Engine v1 tests.
- Market Structure Engine v1 tests.
- Score Engine v1 tests.
- Snapshot Builder v1 contract tests.

Priority:

- High.

Reason:

- Core Indicators v1 are frozen and should be protected by regression tests before Strategy Engine consumes their outputs.

### `src/statistics`

Missing:

- Snapshot Store unit tests.
- Outcome Calculator edge-case tests.
- Pattern Discovery query tests.
- Pattern Library rebuild tests.
- Similarity scoring tests.
- Probability Engine no-evidence and weighted-evidence tests.
- Prediction Engine target/risk zone tests.

Priority:

- High.

Reason:

- Market Learning v1, Probability Engine v1, and Prediction Engine v1 are direct inputs to Strategy Engine v1.

### `src/database`

Missing:

- `DatabaseManager` initialization tests.
- OHLCV upsert tests.
- cache read order tests.
- duplicate row tests.
- on-disk SQLite integration tests.

Priority:

- Medium.

Reason:

- Backtest reproducibility depends on stable database behavior.

### `src/data`

Missing:

- `DataManager` cache-hit tests.
- cache-miss provider fallback tests.
- provider error wrapping tests.
- empty symbol tests.

Priority:

- Medium.

Reason:

- Data loading should remain replaceable and predictable.

### `src/core`

Missing:

- State Manager tests.
- Dashboard Manager load/add/remove tests.
- Market scope validation tests.

Priority:

- Medium.

Reason:

- These modules are small but support predictable application state and NASDAQ scope enforcement.

### `src/gui`

Missing:

- Chart workspace data-state tests.
- timeframe aggregation tests.
- visible-row slicing tests.
- developer panel rendering-state tests.

Priority:

- Low to Medium.

Reason:

- GUI tests are useful, but Strategy Engine readiness depends first on deterministic engine and data tests.

### `src/strategy` and `src/backtest`

Missing:

- More granular Strategy score component tests.
- Snapshot-aware Strategy scoring tests when snapshot dimensions are added.
- Strategy integration tests with Probability and Prediction outputs.
- SQLite-backed Backtest Data Layer tests.
- Additional SnapshotLoader edge-case tests.
- Additional OutcomeLoader edge-case tests.
- Additional FutureRowsLoader edge-case tests.
- Additional BacktestDatasetBuilder edge-case tests.
- Additional read-only DB-backed Backtest runner edge-case tests.
- Backtest persistence write/read tests.

Priority:

- High when Phase 4 starts.

Reason:

- Strategy Engine and Backtest Engine should be implemented test-first from their documented contracts.

## Priority Order

1. Snapshot contract regression tests.
2. Probability Engine v1 unit tests.
3. Prediction Engine v1 unit tests.
4. Outcome Calculator unit tests.
5. Snapshot Store unit tests.
6. Pattern Discovery / Pattern Library tests.
7. Similarity Engine tests.
8. Core Indicators v1 regression tests.
9. DatabaseManager integration tests.
10. DataManager cache/provider tests.
11. Timeframe aggregation tests.
12. Strategy Engine v1 integration tests.
13. Expand Backtest Framework integration tests.
14. SQLite-backed Backtest Data Layer unit tests.
15. Database-backed Backtest integration tests.
16. Backtest persistence schema and round-trip tests.

## Regression Testing Strategy

Regression tests should protect frozen contracts.

Frozen outputs should be tested with stable fixtures:

- input OHLCV rows
- expected snapshot shape
- expected score fields
- expected stored snapshot columns
- expected probability fields
- expected prediction fields

Regression tests should verify:

- required keys exist
- value types are stable
- deterministic outputs remain stable for fixed inputs
- no recommendation output is introduced by Probability or Prediction
- `snapshot_id` remains stable for the same symbol, timeframe, and date
- StrategyResult shape remains stable before Backtest consumes it
- StrategyResult does not emit BUY / SELL / HOLD

Regression tests should not depend on live market data or network access.

## Smoke Tests

Smoke tests verify that major flows still work end to end.

Current smoke test:

- Market Learning Pipeline smoke test.

Future smoke tests:

- Probability / Prediction smoke test.
- Strategy Evaluation smoke test from Probability / Prediction outputs.
- Backtest Pipeline smoke test from stored-like fixtures.
- Database-backed Backtest smoke test.

Smoke tests should be fast, deterministic, and based on fake or fixture data.

## Unit Tests

Unit tests should cover one module or function group at a time.

Unit tests should use:

- in-memory SQLite for statistics tests
- fake data providers for data manager tests
- fixed OHLCV fixtures for analysis tests
- no network calls
- no GUI event loop unless specifically testing GUI behavior

Unit tests should be added before implementing database-backed Backtest or Portfolio Engine.

## Pre-DB-Backtest Regression Checklist

Before database-backed Backtest implementation begins, add or verify regression coverage for the following areas.

### Probability Engine

- Empty match list returns safe default probability output.
- Zero-weight matches return safe default probability output.
- Weighted evidence produces deterministic expected returns.
- Confidence remains within expected bounds.
- Evidence count is stable for fixed matches.
- Output does not contain BUY, SELL, or HOLD.

### Prediction Engine

- Empty or zero-confidence probability output returns safe price defaults.
- Positive expected return produces ordered target and risk zones.
- Negative expected return remains deterministic and bounded.
- Best pattern metadata passes through.
- Output does not contain BUY, SELL, or HOLD.

### Market Learning Pipeline

- Snapshot insert keeps stable `snapshot_id`.
- Duplicate snapshot upsert preserves the central snapshot reference.
- Outcome calculation skips rows without enough future data.
- Pattern discovery remains deterministic for fixed fixtures.
- Similarity results are ordered deterministically.

### Strategy Engine

- StrategyInput accepts snapshot, probability, and prediction structures without invoking upstream engines.
- StrategyResult shape remains stable.
- Reward/risk estimate keys remain stable.
- Score remains within 0 to 100.
- Trade grade, entry quality, and risk rating always use valid enum values.
- Output does not contain BUY, SELL, or HOLD.

### Backtest Framework

- `SimulationResult` shape remains stable.
- `BacktestResult` shape remains stable.
- `BacktestReport` shape remains stable.
- `BacktestResult` count semantics remain stable: attempted, completed, skipped, breakeven, and backward-compatible total trades.
- `BacktestReport` exposes count semantics as typed fields instead of notes only.
- Replay remains deterministic for fixed future rows.
- Metrics aggregation remains deterministic for fixed simulation results.
- Pipeline remains deterministic for fixed BacktestInput records.
- Backtest report comments remain rule-based and deterministic.

### Backtest Data Layer

- `SnapshotQuery` shape remains stable.
- `SnapshotLoader`, `OutcomeLoader`, and `FutureRowsLoader` public methods remain importable.
- `BacktestDataset` and `BacktestDatasetBuilder` shapes remain stable.
- Skeleton methods remain explicit until SQLite-backed behavior is implemented.
- Future SQLite-backed tests verify deterministic ordering and no live data access.

### Backtest DB Persistence

- `backtest_runs`, `backtest_assumptions`, `backtest_evaluations`, and `backtest_trade_results` schemas initialize deterministically.
- Backtest persistence preserves `snapshot_id` continuity from `snapshots`.
- Backtest evaluation rows are ordered by explicit `sequence_number`.
- Skipped and insufficient-data records are persisted with deterministic reasons.
- Backtest aggregate counts match persisted evaluation and trade-result rows.
- DB-backed Backtest tests do not call AI, network, broker, or live data paths.

## Future Integration Tests

Integration tests should verify cross-module behavior.

Planned integration coverage:

- OHLCV upsert and reload through `DatabaseManager`.
- `DataManager` cache miss to fake provider to SQLite cache.
- statistics database initialization on disk.
- snapshot collection to outcome calculation to pattern rebuild.
- probability and prediction from stored pattern library.
- Strategy Engine to Backtest Framework. Initial deterministic coverage exists in `tests/integration/test_strategy_backtest_pipeline.py`.
- Backtest Data Layer from stored snapshots/outcomes to BacktestInput.
- Database-backed Backtest from stored dataset to report.
- Backtest persistence round trip from run assumptions to evaluations, trade results, aggregate run metrics, and report.

Integration tests should use temporary directories or in-memory databases and should not require external services.

## Test Data Policy

Tests should prefer deterministic fixtures.

Allowed:

- generated fake OHLCV rows
- small JSON fixtures
- in-memory SQLite databases
- temporary on-disk SQLite databases

Avoid:

- live Yahoo Finance requests
- local user database state
- timestamps in expected values unless normalized
- external services

## Developer Command

Run all tests:

```powershell
py -m unittest discover -s tests
```

The test suite should remain fast enough to run before every Strategy or Backtest change.
