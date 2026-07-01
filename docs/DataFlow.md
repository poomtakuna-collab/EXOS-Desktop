# Data Flow

## Overview

EXOS Desktop uses a data-first workflow.

The application should not depend on AI to load, store, display, or analyze basic market data.

Core flow:

Dashboard
↓
StateManager
↓
DataManager
↓
DataProvider
↓
Local Storage
↓
ChartWorkspace
↓
Indicator / Statistics / Backtest
↓
AI Layer

## Data Sources

Initial data source:

- Yahoo Finance via yfinance

Future data sources may include:

- Polygon
- Alpha Vantage
- Twelve Data
- Finnhub
- Broker APIs

Data sources must be replaceable.

The rest of the application should not depend directly on a specific data provider.

## Data Loading

When a user selects a symbol:

1. Dashboard updates the selected symbol.
2. StateManager stores current_symbol.
3. ChartWorkspace receives the selected symbol.
4. DataManager requests historical data for current_symbol.
5. DataManager checks local storage first.
6. If local data has enough rows and the latest cached date is fresh, use local data.
7. If local data is missing, short, or stale by latest cached date, request data from DataProvider.
8. DataProvider returns normalized OHLCV data.
9. DataManager passes data to storage and chart layer.

Default historical range:

- 2500 trading days

## Local Storage

Early stage:

- JSON may be used for small app state such as Dashboard symbols.

Market data stage:

- SQLite should be used for OHLCV data.
- SQLite should become the source of truth for historical price data.

The application should avoid downloading the same data repeatedly.

Each symbol should track:

- symbol
- latest cached date
- last_updated
- available_start_date
- available_end_date

## Chart Flow

Chart flow:

Dashboard selection
↓
StateManager current_symbol
↓
DataManager historical data
↓
ChartWorkspace
↓
Candlestick chart
↓
EMA overlays
↓
Volume panel

ChartWorkspace must not read dashboard.json directly.

ChartWorkspace should only receive selected symbol and market data from approved managers.

## Indicator Flow

Indicator flow:

OHLCV data
↓
IndicatorEngine
↓
EMA / Volume / Trend / Momentum
↓
POOM+ Engine
↓
ChartWorkspace / Dashboard

Indicators must be calculated from structured OHLCV data, not screenshots.

## Statistics Flow

Statistics flow:

Trade records + historical data
↓
StatisticsEngine
↓
Win rate
Risk/reward
Expectancy
Drawdown
Performance

Statistics should read from stored structured data.

## Backtest Flow

Backtest flow:

Historical OHLCV data
↓
IndicatorEngine
↓
POOM+ rules
↓
BacktestEngine
↓
Backtest results
↓
StatisticsEngine
↓
Dashboard / Reports

Backtest must be reproducible from stored data.

## AI Flow

AI comes later.

AI must not be required for core application features.

AI flow:

SQLite / structured data
↓
JSON payload
↓
AI analysis
↓
Summary / score / suggestion
↓
Dashboard / Report

AI should read structured data only.

AI must not replace DataManager, DatabaseManager, IndicatorEngine, StatisticsEngine, or BacktestEngine.
