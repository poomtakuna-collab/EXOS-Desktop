# EXOS Architecture Audit

Date: 2026-06-29

Scope: repository architecture only. No engine contracts or implementation code were changed.

## 1. Current Architecture Summary

EXOS Desktop is currently organized as a local-first desktop research application with a frozen analysis/statistics pipeline and a simple Qt presentation shell.

Documented EXOS Brain v1 pipeline:

```text
Market Data
-> Core Indicators
-> Snapshot
-> Statistics
-> Outcome
-> Pattern Discovery
-> Pattern Library
-> Similarity
-> Probability
-> Prediction
```

The implementation broadly matches `docs/ROADMAP.md` and `docs/PROJECT_STATUS.md`:

- `src/app` starts the Qt application and wires the main window.
- `src/gui` owns the desktop UI, chart workspace, candlestick rendering, dashboard dock, and developer panel.
- `src/core` owns lightweight app state, dashboard symbol persistence, and NASDAQ market scope validation.
- `src/data` owns data provider abstraction and historical-data loading policy.
- `src/database` owns the OHLCV SQLite cache.
- `src/analysis` owns Core Indicators v1 and Snapshot Builder v1.
- `src/indicators` builds a UI-oriented indicator snapshot by combining the frozen analysis modules.
- `src/statistics` owns Market Learning v1, Probability Engine v1, and Prediction Engine v1.
- `src/backtest`, `src/ai`, `src/api`, `src/chart`, and `src/utils` are placeholders.
- `tests/test_market_learning_pipeline.py` provides a smoke test for the market-learning pipeline.

The main runtime flow is currently:

```text
src.main
-> Application
-> MainWindow
-> ChartWorkspace / DashboardManager / StateManager
-> DataManager
-> DatabaseManager or YahooFinanceDataProvider
-> build_indicator_snapshot
-> src.analysis engines
```

The market-learning flow is currently:

```text
OHLCV rows
-> build_exos_snapshot
-> collect_snapshots_for_series
-> snapshots table
-> calculate_outcomes_for_series
-> outcomes table
-> discover_patterns
-> patterns table
-> find_similar_patterns
-> calculate_probability_from_matches
-> build_prediction
```

## 2. What Is Clean / Working Well

- The frozen EXOS Brain v1 pipeline is clear in the docs and mostly clear in code.
- Core Indicators v1 are isolated in `src/analysis`, which helps protect the frozen contract.
- Market Learning v1 is database-first and centered on `snapshot_id`, matching `docs/MARKET_LEARNING_SCHEMA.md`.
- Snapshot storage duplicates searchable fields into columns while preserving the full nested snapshot JSON.
- Pattern discovery, similarity, probability, and prediction are deterministic and do not depend on AI.
- `DataProvider` is a protocol, so Yahoo Finance is replaceable later without forcing UI changes.
- SQLite is already the local source of truth for OHLCV and statistical learning tables.
- The UI does not read `dashboard.json` directly from `ChartWorkspace`; dashboard persistence stays in `DashboardManager`.
- The repository has a compact module layout, so Phase 4 can be added without a large migration first.

## 3. Risks or Technical Debt

- Statistics database ownership is separate from `DatabaseManager`. `src/database/database_manager.py` initializes only `ohlcv_daily`, while `src/statistics/schema.py` initializes `snapshots`, `outcomes`, and `patterns`. Phase 4 will need a single clear database access boundary or orchestration layer.
- The `docs/ROADMAP.md`, `docs/PROJECT_STATUS.md`, `docs/Architecture.md`, and `docs/DataFlow.md` files show mojibake for arrow characters. This is not a runtime issue, but it weakens documentation readability.
- `src/gui/chart_workspace.py` owns timeframe aggregation, visible-row slicing, data-refresh flow, status formatting, indicator snapshot creation, and sample fallback data. This mixes presentation, data shaping, and analysis orchestration.
- `src/indicators/indicator_snapshot.py` duplicates parts of the analysis pipeline already represented by `build_exos_snapshot`. This is useful for the current UI, but the responsibility boundary is unclear: it is partly adapter, partly aggregate contract.
- `src/statistics` contains multiple responsibilities: schema, snapshot persistence, outcome calculation, pattern discovery, pattern library, similarity, probability, and prediction. That is acceptable at current size, but Phase 4 may make the package too broad unless strategy/backtest are kept separate.
- Probability and prediction are implemented but not currently covered by direct unit tests.
- Core indicator modules are frozen but do not appear to have dedicated regression tests. That increases the risk of accidental contract drift later.
- The only test is a smoke test. It verifies the happy path but does not exercise edge cases such as empty data, duplicate snapshots, no evidence, malformed snapshots, or database persistence on disk.
- `src/backtest` is only a placeholder. There is no strategy/backtest contract, result schema, or report shape yet.
- Generated `__pycache__` directories are present under `src`. If they are tracked, they should be removed from version control later; if untracked, the current `.gitignore` should continue to keep them out.
- `DatabaseManager` currently uses `REQUIRED_ROW_COUNT = 2500` in `DataManager`, while `docs/DataFlow.md` and `docs/Database.md` still reference 300 rows as the default/historical threshold. The implementation may be ahead of the docs, but this mismatch should be resolved before Phase 4 depends on reproducible history windows.
- The docs still mention a future `StatisticsEngine` in places, while the implementation now uses `src/statistics` as the concrete market-learning/probability package. Naming should be clarified before backtest reporting is added.

## 4. Files / Modules That May Need Refactor Later

- `src/gui/chart_workspace.py`: consider extracting timeframe aggregation and market-data display preparation into a non-UI service before Strategy/Backtest needs the same transformations.
- `src/indicators/indicator_snapshot.py`: clarify whether this is a UI adapter, a public snapshot facade, or a compatibility layer over `src.analysis`.
- `src/database/database_manager.py` and `src/statistics/schema.py`: consider a unified database initialization/access boundary so OHLCV, snapshots, outcomes, patterns, and future backtest tables are managed consistently.
- `src/statistics/pattern_discovery.py`: SQL is centralized and deterministic, but factor definitions are hard-coded. Phase 4 may need a more explicit factor registry or query builder if strategy rules expand.
- `src/statistics/similarity.py`: loads the full pattern library into memory. This is acceptable for current scale, but large libraries may need SQL-side filtering or indexed preselection.
- `src/statistics/probability.py` and `src/statistics/prediction.py`: add direct tests and document output contracts before strategies consume their outputs.
- `src/core/state_manager.py`: currently holds UI state and latest indicator snapshot only. If strategy preview or backtest UI arrives, avoid turning this into a broad application store.
- `docs/Database.md`: update to include statistics tables and future backtest table ownership, or link clearly to `MARKET_LEARNING_SCHEMA.md`.
- `docs/DataFlow.md`: update the implemented Brain v1/statistics/probability/prediction flow and align row-count expectations.

## 5. Readiness for Strategy Engine

EXOS is partially ready for Phase 4.

Ready foundations:

- Historical OHLCV data exists in SQLite.
- Snapshots have stable `snapshot_id` values.
- Outcomes are joined to snapshots through `snapshot_id`.
- Pattern discovery and pattern library are deterministic.
- Similarity, probability, and prediction outputs exist and avoid recommendation language.
- Backtest support is anticipated in `docs/MARKET_LEARNING_SCHEMA.md`.
- Frozen engine boundaries are clear enough that Strategy Engine can consume outputs instead of changing upstream contracts.

Not ready yet:

- There is no Strategy Engine interface or rule contract.
- There is no Backtest Engine interface, execution model, result schema, or persistence table.
- There is no explicit strategy-safe read model for snapshots, outcomes, probability, and prediction.
- There is no documented position model for entries, exits, sizing, cash, fees, slippage, or portfolio risk.
- There is no validation suite for probability/prediction outputs that strategies would depend on.
- Timeframe aggregation currently lives in the GUI, so backtests could accidentally diverge from chart behavior unless this logic is moved or shared.
- Documentation does not yet define whether Phase 4 consumes stored snapshots only, freshly computed snapshots, or both.

Recommended Phase 4 boundary:

```text
Strategy Engine
    input: snapshot record, optional outcome/probability/prediction context, strategy rules
    output: deterministic signal/event objects, not buy/sell recommendations

Backtest Engine
    input: ordered historical decision points and strategy signal/events
    output: trades, equity curve, drawdown, expectancy, hit rate, and reproducible metadata

Risk / Portfolio Layer
    input: backtest trades and portfolio assumptions
    output: risk metrics and portfolio-level performance
```

Strategy Engine should be added as a consumer after Prediction Engine, not as a modification to Core Indicators v1, Market Learning v1, Probability Engine v1, or Prediction Engine v1.

## 6. Recommended Next Steps

1. Define the Phase 4 contracts before implementation:
   - strategy rule input shape
   - strategy signal/event output shape
   - backtest result shape
   - assumptions for fees, slippage, sizing, and entry/exit timing

2. Add direct tests for Probability Engine v1 and Prediction Engine v1:
   - no matches
   - zero confidence
   - weighted matches
   - negative expected return
   - target/risk zone ordering

3. Add regression tests around frozen snapshot contracts:
   - `build_exos_snapshot`
   - `prepare_snapshot_record`
   - `calculate_outcome_for_snapshot`
   - duplicate snapshot upsert behavior

4. Move or duplicate timeframe aggregation into a non-UI module before any backtest uses weekly or monthly data.

5. Decide whether statistics tables should be initialized by `DatabaseManager`, a new database bootstrap module, or a dedicated repository layer.

6. Update docs before Phase 4 starts:
   - fix corrupted arrow characters
   - reconcile 300-row docs with the current 2500-row implementation
   - document current statistics/probability/prediction modules
   - add a Phase 4 architecture sketch

7. Keep Phase 4 additive:
   - create new modules under `src/backtest` and/or `src/strategy`
   - consume existing snapshots, outcomes, patterns, probabilities, and predictions
   - avoid changing frozen upstream contracts unless a verified bug is found

## Audit Conclusion

The repository is in a reasonable state for a Phase 4 design pass. The main pipeline matches the roadmap and project status docs, and the frozen engines appear well separated from planned strategy/backtest work.

The biggest architectural risk is not the current engine code; it is boundary drift as Phase 4 begins. Before implementing Strategy Engine, EXOS should define stable strategy/backtest contracts, share timeframe/data preparation outside the GUI, and add targeted tests around the probability/prediction outputs that strategies will consume.
