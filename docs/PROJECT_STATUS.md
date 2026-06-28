# PROJECT STATUS

Current
Milestone 4.22 - EXOS Score Engine v1 added

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

Next
- Zoom / Pan

Later
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
- Statistics, Backtest, Prediction, and AI are not implemented yet.
- Sample OHLC candles are isolated as developer fallback only and are disabled by default.
- If no cached rows exist for a symbol, the chart shows an empty OHLC message instead of fake candles.
- Zoom, Pan, Statistics, Backtest, and AI are not implemented yet.

Last Commit
Improve developer panel layout

Run
py -m src.main
