# EXOS Testing Plan

Testing plan for EXOS Desktop developer infrastructure.

This document describes the current test coverage, missing tests, proposed test structure, and long-term regression strategy before Strategy Engine implementation begins.

## Current Test Coverage

Current automated coverage is limited to one smoke test:

- `tests/smoke/test_market_learning_pipeline.py`

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

This verifies the happy path for Market Learning v1 using an in-memory SQLite database.

Current gaps:

- No dedicated unit tests for Core Indicators v1.
- No dedicated unit tests for Snapshot Builder v1.
- No dedicated unit tests for database persistence.
- No dedicated unit tests for Probability Engine v1.
- No dedicated unit tests for Prediction Engine v1.
- No regression fixtures for frozen engine contracts.
- No GUI tests.
- No integration tests using the on-disk SQLite database.
- No Strategy / Backtest tests yet.

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

### Future `src/strategy` and `src/backtest`

Missing:

- Strategy score formula tests.
- trade grade threshold tests.
- risk rating threshold tests.
- reward/risk estimate tests.
- no BUY / SELL / HOLD output tests.
- backtest execution tests.
- backtest persistence tests.

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
12. Strategy Engine v1 contract tests.
13. Backtest Engine integration tests.

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

Regression tests should not depend on live market data or network access.

## Smoke Tests

Smoke tests verify that major flows still work end to end.

Current smoke test:

- Market Learning Pipeline smoke test.

Future smoke tests:

- Probability / Prediction smoke test.
- Strategy Evaluation smoke test.
- Backtest Pipeline smoke test.

Smoke tests should be fast, deterministic, and based on fake or fixture data.

## Unit Tests

Unit tests should cover one module or function group at a time.

Unit tests should use:

- in-memory SQLite for statistics tests
- fake data providers for data manager tests
- fixed OHLCV fixtures for analysis tests
- no network calls
- no GUI event loop unless specifically testing GUI behavior

Unit tests should be added before implementing Strategy Engine v1.

## Future Integration Tests

Integration tests should verify cross-module behavior.

Planned integration coverage:

- OHLCV upsert and reload through `DatabaseManager`.
- `DataManager` cache miss to fake provider to SQLite cache.
- statistics database initialization on disk.
- snapshot collection to outcome calculation to pattern rebuild.
- probability and prediction from stored pattern library.
- Strategy Engine to Backtest Engine once Phase 4 begins.

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

The test suite should remain fast enough to run before every Strategy Engine change.
