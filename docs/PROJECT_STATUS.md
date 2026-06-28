# PROJECT STATUS

Current
Milestone 4.4.1 - EMA20/50/200 Overlays added

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

Next
- Timeframe

Later
- Statistics
- Backtest
- AI

Notes
- Candlestick Chart v1 renders OHLC rows loaded from SQLite Cache through DataManager.
- Dashboard selection updates StateManager, then ChartWorkspace refreshes the chart.
- Chart header uses a compact market line and a secondary source/cache/rendered row line.
- CHART_VISIBLE_ROWS controls the rendered row count and defaults to 120.
- Volume panel uses the same rendered rows as the candlestick chart.
- Green volume bars mean close >= open; red volume bars mean close < open.
- Market header shows symbol, last close, change, change percent, OHLC, volume, and latest date.
- Market header uses existing SQLite cached rows only; no live price API is called.
- Current price line uses the latest rendered OHLC close and is drawn only in the price panel.
- Current price label is placed beside the chart in the reserved price-axis area.
- Price and volume axis labels are drawn on the right-side axis area.
- EMA20, EMA50, and EMA200 are calculated from rendered close prices and drawn only in the price panel.
- Sample OHLC candles are isolated as developer fallback only and are disabled by default.
- If no cached rows exist for a symbol, the chart shows an empty OHLC message instead of fake candles.
- Timeframe, Statistics, Backtest, and AI are not implemented yet.

Last Commit
Improve developer panel layout

Run
py -m src.main
