# CHANGELOG

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
