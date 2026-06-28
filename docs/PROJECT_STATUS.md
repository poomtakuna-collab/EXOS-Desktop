# PROJECT STATUS

Current
Milestone 4.28 - EXOS Similarity Engine v1 added

Done
- Dashboard
- State Manager
- SQLite Cache
- Developer Mode
- Candlestick Chart v1
- Real cached OHLC chart flow
- Chart metadata label and configurable visible rows
- Volume panel aligned to candlestick rows
- Market header from latest cached OHLCV row
- Compact two-line chart header/debug layout
- Current price line on candlestick chart
- Current price label in reserved price-axis area
- Price and volume axis labels moved to right side
- EMA20/50/200 overlays on price chart
- Mouse crosshair and OHLC/EMA hover tooltip
- Automatic cache-miss OHLCV loading for selected symbols
- NASDAQ-only scanner scope guard
- Timeframe Engine v1 with 1D, 1W, and 1M chart views
- 10-year daily OHLCV Yahoo Finance fetch depth
- Visible rows control for 60, 120, 240, and All
- Dark Theme v1 for standard PySide6 widgets
- Improved price and volume axis labels
- EXOS Indicator Snapshot v1 in Developer Panel
- TradingView-style EMA20/50/200 value labels on the right price axis
- EXOS Analysis Engine foundation with Indicator Engine v1
- EXOS EW Engine v1 in Developer Panel snapshot
- EXOS Volume Pressure Engine v1 in Developer Panel snapshot
- EXOS Trend Slope Engine v1 in Developer Panel snapshot
- EXOS Squeeze Engine v1 in Developer Panel snapshot
- EXOS Market Structure Engine v1 in Developer Panel snapshot
- EXOS Snapshot Builder v1 nested core_indicators_v1 contract
- EXOS Score Engine v1 weighted aggregate score
- EXOS Statistics Engine v1 foundation with schema helpers and snapshot insert support
- EXOS Snapshot Collector v1 for building and storing snapshot records from market rows
- EXOS Outcome Calculator v1 for calculating future return metrics from stored snapshots
- EXOS Pattern Discovery Engine v1 for simple SQL-based snapshot/outcome pattern statistics
- EXOS Pattern Library v1 for persisting discovered patterns as reusable knowledge
- EXOS Similarity Engine v1 for deterministic matching between new snapshots and stored patterns

Next
- Phase 2 - Market Learning Engine
- Implement Pattern Discovery reports or Factor Analysis UI integration later

Later
- Zoom / Pan
- Statistics
- Backtest
- AI

Notes
- Candlestick Chart v1 renders OHLC rows loaded from SQLite Cache through DataManager.
- Dashboard selection updates StateManager, then ChartWorkspace refreshes the chart.
- Chart header uses a compact market line and a secondary source/cache/rendered row line.
- Visible rows default to 120 and can be changed to 60, 240, or All.
- Visible row selection is applied after timeframe resampling.
- Volume panel uses the same rendered rows as the candlestick chart.
- Green volume bars mean close >= open; red volume bars mean close < open.
- Market header shows symbol, last close, change, change percent, OHLC, volume, and latest date.
- Market header uses existing SQLite cached rows only; no live price API is called.
- Current price line uses the latest rendered OHLC close and is drawn only in the price panel.
- Current price label is placed beside the chart in the reserved price-axis area.
- Price and volume axis labels are drawn on the right-side axis area.
- EMA20, EMA50, and EMA200 are calculated from rendered close prices and drawn only in the price panel.
- Interaction Layer v1 adds mouse crosshair and nearest-candle tooltip using rendered rows.
- When selected symbol has no cached rows, ChartWorkspace fetches through DataManager, saves to SQLite, then refreshes from SQLite.
- MARKET_SCOPE is NASDAQ. Current symbol validation accepts plain 1-5 letter ticker symbols only.
- SET, NYSE, AMEX, crypto, forex, and suffix-style symbols are not supported yet.
- 1D uses cached daily rows directly.
- 1W and 1M are resampled in memory from cached daily rows using OHLCV aggregation rules.
- EMA20, EMA50, and EMA200 recalculate from the selected timeframe close prices.
- Header, volume panel, current price line, crosshair, and tooltip use the selected timeframe rows.
- Yahoo Finance daily downloads request 10 years of history.
- SQLite remains the source of truth for chart display.
- Symbols with the old 300-row cache are refreshed when selected because the cache target is now 2500 daily rows.
- Candles, volume, EMA overlays, current price line, crosshair, tooltip, and header use the selected visible rows.
- Dark Theme v1 is centralized in src/gui/theme.py and applied once from Application startup.
- Candlestick chart drawing colors are unchanged for now.
- Price axis labels use multiple right-side scale marks aligned to horizontal grid lines.
- Price axis labels prefer rounded values and avoid the current price label area.
- Volume axis labels show max, mid, and 0 on the right side.
- Indicator Snapshot v1 uses selected symbol, NASDAQ market scope, selected timeframe, and the latest completed timeframe candle.
- Indicator Snapshot v1 includes OHLCV, EMA20/50/200, price-vs-EMA status, and EMA alignment.
- Indicator Snapshot v1 is displayed in the Developer Panel for now.
- EMA20, EMA50, and EMA200 display latest value labels on the right price axis.
- EMA value labels match EMA line colors and adjust vertically to reduce overlap.
- Analysis Engine foundation lives in src/analysis.
- Indicator Engine v1 calculates EMA20/50/200, price-vs-EMA state, and EMA alignment from selected timeframe rows.
- Developer Panel indicator snapshot now uses the Analysis Indicator Engine.
- EXOS EW Engine v1 calculates normalized EW from SMA5, SMA35, and EMA35.
- Developer Panel indicator snapshot includes ew, ew_fast, ew_slow, and ew_state.
- EXOS Volume Pressure Engine v1 calculates volume_pressure and vp_state using buy/sell volume EMA smoothing.
- Developer Panel indicator snapshot includes volume_pressure and vp_state.
- EXOS Trend Slope Engine v1 calculates trend_slope and trend_slope_state from EMA20 slope over a 10-candle lookback.
- Developer Panel indicator snapshot includes trend_slope and trend_slope_state.
- EXOS Squeeze Engine v1 calculates compression_ratio, compression_score, state, release_probability, and confidence.
- Developer Panel indicator snapshot includes Squeeze Engine v1 fields.
- EXOS Market Structure Engine v1 detects simple pivots, HH/HL, LH/LL, range, BOS, and CHOCH states.
- Developer Panel indicator snapshot includes Market Structure Engine v1 fields.
- Developer Panel uses market_structure_confidence to avoid colliding with Squeeze confidence.
- EXOS Snapshot Builder v1 creates the nested core_indicators_v1 contract for future Statistics, Backtest, Prediction, and AI inputs.
- Developer Panel indicator snapshot includes exos_snapshot while preserving existing flat debug fields.
- EXOS Score Engine v1 aggregates trend, trend_slope, squeeze, and market_structure scores with 30/20/20/30 weights.
- EXOS Snapshot Builder v1 now injects score into the nested snapshot.
- Core Indicators v1 is complete through Snapshot Builder and Score Engine.
- Phase 2 is Market Learning Engine: store snapshots, attach future outcomes, analyze factors, and group repeatable market patterns.
- EXOS Phase 2 is not just win-rate tracking. It is designed to learn what market conditions tend to appear before future price movement.
- Snapshot is the central data unit. Use snapshot_id as the shared reference for Statistics, Outcome, Factor Analysis, Backtest, Prediction, and AI Analysis.
- Phase 2 is database-first: store searchable fields as columns and store the full nested snapshot as JSON.
- Market Learning Engine v1 schema is documented in docs/MARKET_LEARNING_SCHEMA.md.
- Required Phase 2 tables are snapshots and outcomes.
- snapshots stores snapshot_id, symbol, timeframe, date, close, EXOS score fields, state fields, full snapshot_json, and created_at.
- outcomes stores future 5D/10D/20D returns, 10D max gain/drawdown, hit flags, label_10d, and calculated_at by snapshot_id.
- Required indexes cover symbol/timeframe/date, exos_score, trend_state, squeeze_state, market_structure_state, and outcome snapshot_id.
- Snapshot inserts should upsert by symbol + timeframe + date and return snapshot_id.
- Outcome calculation should run later in batches after enough future OHLCV data exists.
- Statistics Engine v1 foundation lives in src/statistics.
- initialize_statistics_db creates snapshots, outcomes, and required indexes using sqlite3.
- prepare_snapshot_record extracts searchable fields from nested EXOS snapshots and stores the full JSON snapshot.
- insert_snapshot writes one snapshot row at a time and returns snapshot_id.
- Snapshot Collector v1 lives in src/statistics/collector.py.
- collect_snapshot builds one EXOS snapshot from market rows, prepares the statistics record, inserts it, and returns snapshot_id.
- collect_snapshots_for_series walks historical rows with a rolling window and inserts one snapshot per valid completed date.
- Snapshot Collector v1 enriches the collected snapshot copy with latest date and close metadata for database storage.
- Outcome Calculator v1 lives in src/statistics/outcome_calculator.py.
- calculate_outcome_for_snapshot calculates forward 5D/10D/20D returns, 10D max gain, 10D max drawdown, 10D hit flags, and label_10d.
- insert_or_update_outcome writes one outcome row by snapshot_id using stable outcome_id upsert behavior.
- calculate_outcomes_for_series matches stored snapshot dates to future OHLCV rows and skips snapshots without enough future data.
- Outcome Calculator v1 does not run factor analysis, backtest, prediction, AI, or UI logic.
- Pattern Discovery Engine v1 lives in src/statistics/pattern_discovery.py.
- discover_patterns groups stored snapshots joined to outcomes by trend_state, squeeze_state, market_structure_state, rating, and recommendation.
- Pattern metrics include sample count, average 5D/10D/20D returns, hit rates, average max gain, average drawdown, dominant label, and sample-size confidence.
- discover_best_patterns filters for patterns with sample_count >= 50, average_10d_return > 5, and hit_5pct_rate > 60 by default.
- summarize_pattern_statistics reports total patterns, largest pattern, average pattern size, best pattern return, and best hit rate.
- discover_strong_bull_patterns remains available as a convenience filter for Strong Bull style patterns.
- summarize_factor_distribution counts factor values across all outcomes or a supported label_10d outcome filter.
- Pattern Discovery Engine v1 is SQL/statistics only. It is not AI, ML, backtest, prediction, or UI logic.
- Pattern Library v1 lives in src/statistics/pattern_library.py.
- patterns table stores discovered factor combinations, returns, hit rates, dominant label, confidence, and timestamps.
- rebuild_pattern_library clears stored patterns, runs discover_patterns, inserts every discovered pattern, and returns rebuild counts.
- load_pattern_library returns stored patterns sorted by confidence.
- get_pattern returns one stored pattern by pattern_id.
- Pattern Library v1 is reusable statistical knowledge only. It is not AI, prediction, backtest, API, or UI logic.
- Similarity Engine v1 lives in src/statistics/similarity.py.
- calculate_similarity compares snapshot states, rating, recommendation, and available numeric score fields against a pattern.
- find_similar_patterns loads the Pattern Library read-only and returns the top deterministic matches.
- find_best_match returns the highest similarity pattern.
- Similarity Engine v1 is deterministic scoring only. It is not AI, ML, prediction, backtest, API, or UI logic.
- Core Indicators v1 should remain frozen unless a real bug appears.
- Statistics, Backtest, Prediction, and AI are not implemented yet.
- Sample OHLC candles are isolated as developer fallback only and are disabled by default.
- If no cached rows exist for a symbol, the chart shows an empty OHLC message instead of fake candles.
- Zoom, Pan, Statistics, Backtest, and AI are not implemented yet.

Last Commit
Improve developer panel layout

Run
py -m src.main
