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

If at least 300 rows exist for a symbol, EXOS uses the local database.

If fewer than 300 rows exist, EXOS requests data from Yahoo Finance and upserts it into SQLite.

## Trade Journal

## Indicators

## Statistics

## Backtest Results

## Future Tables
