# EXOS Market Learning Engine v1 Schema

## Purpose

Market Learning Engine v1 stores EXOS market snapshots and attaches future outcomes later when enough price data exists.

The database design is built around one central reference:

- `snapshot_id`

Every future Statistics, Outcome, Factor Analysis, Backtest, Prediction, and AI Analysis feature should reference snapshots through `snapshot_id`.

Core Indicators v1 remains frozen unless a real bug appears. Phase 2 stores and learns from the current snapshot contract; it does not redefine indicator logic.

## Design Principles

- SQLite remains the local source of truth.
- Do not load all snapshots into memory.
- Query snapshots by symbol, timeframe, date range, score, and state.
- Important searchable values are stored as columns.
- The full nested EXOS snapshot is stored as JSON in `snapshot_json`.
- Outcome rows are calculated later, after future price data exists.

## Table: snapshots

Stores one EXOS snapshot for one symbol, timeframe, and completed candle date.

Columns:

- `snapshot_id` TEXT PRIMARY KEY
- `symbol` TEXT NOT NULL
- `timeframe` TEXT NOT NULL
- `date` TEXT NOT NULL
- `close` REAL
- `exos_score` REAL
- `rating` TEXT
- `recommendation` TEXT
- `trend_score` REAL
- `trend_state` TEXT
- `trend_slope_score` REAL
- `squeeze_score` REAL
- `squeeze_state` TEXT
- `market_structure_score` REAL
- `market_structure_state` TEXT
- `snapshot_json` TEXT NOT NULL
- `created_at` TEXT NOT NULL

Suggested unique constraint:

- `symbol + timeframe + date`

Notes:

- `snapshot_id` should be stable and generated once when the snapshot is inserted.
- `date` is the completed candle date for the selected timeframe.
- `snapshot_json` stores the complete nested EXOS Snapshot Builder v1 output.
- Searchable fields are duplicated from JSON into columns so queries do not need to parse every snapshot.

## Table: outcomes

Stores future price outcome measurements for a snapshot.

Columns:

- `outcome_id` TEXT PRIMARY KEY
- `snapshot_id` TEXT NOT NULL
- `forward_5d_return` REAL
- `forward_10d_return` REAL
- `forward_20d_return` REAL
- `max_gain_10d` REAL
- `max_drawdown_10d` REAL
- `hit_5pct_10d` INTEGER
- `hit_10pct_10d` INTEGER
- `label_10d` TEXT
- `calculated_at` TEXT NOT NULL

Foreign key:

- `snapshot_id` references `snapshots(snapshot_id)`

Notes:

- `hit_5pct_10d` and `hit_10pct_10d` are boolean-style integer flags: `0` or `1`.
- A snapshot can be inserted before an outcome exists.
- Outcome calculation should skip snapshots that do not yet have enough future OHLCV rows.
- The first implementation can use one outcome row per snapshot.

## Indexes

Required indexes:

- `snapshots(snapshot_id)` through the primary key
- `snapshots(symbol, timeframe, date)`
- `snapshots(exos_score)`
- `snapshots(trend_state)`
- `snapshots(squeeze_state)`
- `snapshots(market_structure_state)`
- `outcomes(snapshot_id)`

Optional later indexes:

- `snapshots(symbol, timeframe, exos_score)`
- `snapshots(symbol, timeframe, trend_state)`
- `snapshots(symbol, timeframe, squeeze_state)`
- `snapshots(symbol, timeframe, market_structure_state)`
- `outcomes(label_10d)`

## Snapshot Insert Flow

1. Build the normal EXOS Snapshot Builder v1 payload for the selected symbol, timeframe, and latest completed candle.
2. Extract key searchable values from the nested snapshot into columns.
3. Store the complete nested snapshot payload in `snapshot_json`.
4. Insert or update one row by `symbol + timeframe + date`.
5. Return `snapshot_id` for later outcome, factor, backtest, prediction, and AI references.

The insert path should never require loading historical snapshots into memory. It only needs the current snapshot payload and a targeted upsert.

## SQLite DDL Draft

```sql
CREATE TABLE IF NOT EXISTS snapshots (
    snapshot_id TEXT PRIMARY KEY,
    symbol TEXT NOT NULL,
    timeframe TEXT NOT NULL,
    date TEXT NOT NULL,
    close REAL,
    exos_score REAL,
    rating TEXT,
    recommendation TEXT,
    trend_score REAL,
    trend_state TEXT,
    trend_slope_score REAL,
    squeeze_score REAL,
    squeeze_state TEXT,
    market_structure_score REAL,
    market_structure_state TEXT,
    snapshot_json TEXT NOT NULL,
    created_at TEXT NOT NULL,
    UNIQUE (symbol, timeframe, date)
);

CREATE TABLE IF NOT EXISTS outcomes (
    outcome_id TEXT PRIMARY KEY,
    snapshot_id TEXT NOT NULL,
    forward_5d_return REAL,
    forward_10d_return REAL,
    forward_20d_return REAL,
    max_gain_10d REAL,
    max_drawdown_10d REAL,
    hit_5pct_10d INTEGER,
    hit_10pct_10d INTEGER,
    label_10d TEXT,
    calculated_at TEXT NOT NULL,
    FOREIGN KEY (snapshot_id) REFERENCES snapshots(snapshot_id)
);

CREATE INDEX IF NOT EXISTS idx_snapshots_symbol_timeframe_date
    ON snapshots(symbol, timeframe, date);

CREATE INDEX IF NOT EXISTS idx_snapshots_exos_score
    ON snapshots(exos_score);

CREATE INDEX IF NOT EXISTS idx_snapshots_trend_state
    ON snapshots(trend_state);

CREATE INDEX IF NOT EXISTS idx_snapshots_squeeze_state
    ON snapshots(squeeze_state);

CREATE INDEX IF NOT EXISTS idx_snapshots_market_structure_state
    ON snapshots(market_structure_state);

CREATE INDEX IF NOT EXISTS idx_outcomes_snapshot_id
    ON outcomes(snapshot_id);
```

## Outcome Calculation Flow

Outcomes are calculated after future price data exists.

1. Find snapshots without outcomes, limited by a batch size.
2. For each snapshot, load only the required future OHLCV rows for the same symbol and timeframe.
3. Skip snapshots that do not yet have enough future rows for 20D measurement.
4. Calculate 5D, 10D, and 20D forward returns from the snapshot close.
5. Calculate 10D maximum gain and maximum drawdown from future high/low or close data, depending on the final implementation rule.
6. Set `hit_5pct_10d` and `hit_10pct_10d`.
7. Assign `label_10d`.
8. Insert or update the outcome row by `snapshot_id`.

Outcome calculation should run incrementally in batches and avoid scanning the entire snapshot table into memory.

## Label 10D Draft

`label_10d` can start with a simple return-based rule:

- `Strong Bull`: forward 10D return >= 10%
- `Crash`: forward 10D return <= -10%
- `Bull`: forward 10D return >= 5%
- `Bear`: forward 10D return <= -5%
- `Sideway`: forward 10D return > -5% and < 5%

Evaluate the strongest positive and negative labels first. The exact thresholds may be tuned later, but labels should remain derived from stored outcome measurements.

## Factor Analysis Support

Factor Analysis can query snapshots joined to outcomes without parsing all JSON.

Example questions:

- Which `trend_state` values commonly appear before `Strong Bull` outcomes?
- Which `squeeze_state` values have better 10D returns?
- What `exos_score` ranges are associated with high hit rates?
- How does `market_structure_state` change the distribution of future returns?

The indexed searchable columns make these queries efficient. `snapshot_json` remains available when deeper nested factor inspection is needed.

## Backtest Support

Backtest can use `snapshot_id` as the historical decision point.

The backtest engine can:

- Query snapshots by symbol, timeframe, date range, score, and state.
- Apply entry rules against snapshot columns.
- Join outcomes for measured forward performance.
- Retrieve `snapshot_json` only for detailed analysis or report generation.

This keeps historical simulation database-first and avoids loading every snapshot into memory.
