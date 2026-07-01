# Database

## Overview

EXOS Desktop uses a local SQLite database for structured market data cache.

## Database Choice

SQLite is used for local-first storage.

Database file:

- database/exos.db

## Tables

### ohlcv_daily

Stores daily OHLCV market data by symbol and date.

Columns:

- symbol TEXT
- date TEXT
- open REAL
- high REAL
- low REAL
- close REAL
- volume INTEGER
- source TEXT
- created_at TEXT
- updated_at TEXT

Unique key:

- symbol + date

## Stock Data

DataManager checks SQLite before requesting data from an external provider.

If at least 2500 rows exist for a symbol and the latest cached date is fresh, EXOS uses the local database.

If fewer than 2500 rows exist, or the latest cached date is stale, EXOS requests data from Yahoo Finance and upserts it into SQLite.

The current daily OHLCV freshness threshold is three calendar days. This keeps a Friday close fresh over a weekend while allowing the app to refresh by midweek if new trading days were not cached.

## Trade Journal

## Indicators

## Statistics

## Backtest Results

## Future Tables
