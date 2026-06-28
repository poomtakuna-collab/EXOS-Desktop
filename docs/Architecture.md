# Architecture

## Design Philosophy

EXOS Desktop is a data-first investment research platform.

Priority:

Data
↓
Database
↓
Chart
↓
Statistics
↓
Backtest
↓
AI

AI is an optional analysis layer.

The application must remain fully functional even if AI is disabled.

## Layered Architecture

EXOS Desktop is divided into three main layers:

### Presentation Layer

GUI, windows, panels, menus, tables, and charts.

### Business Layer

POOM+, indicators, statistics, backtest logic, scoring, and trade analysis.

### Data Layer

Data loading, local storage, SQLite database, cache, and file access.

## Dependency Rule

Presentation Layer may call Business Layer.

Business Layer may call Data Layer.

Presentation Layer must not access Database directly.

AI must not control core logic.

AI may only read structured data and generate analysis or summaries.

## Core Modules

### Main Window

The main desktop window of EXOS Desktop.

### Data Manager

Loads stock data from external sources and prepares it for storage or display.

### Database Manager

Handles local SQLite database access.

### Chart Engine

Displays candlestick charts, volume, and indicators.

### Indicator Engine

Calculates technical indicators.

### POOM+ Engine

Applies the POOM+ trading logic and scoring system.

### Statistics Engine

Calculates win rate, risk/reward, expectancy, drawdown, and performance statistics.

### Backtest Engine

Runs historical strategy tests.

### Market Learning Engine

Stores EXOS snapshots, links future outcomes by snapshot_id, analyzes common factors before price movement, and groups repeatable market patterns.

The full nested snapshot is stored as JSON, while important searchable fields are stored as database columns.

Schema design:

- `docs/MARKET_LEARNING_SCHEMA.md`

Market Learning Engine v1 uses two core tables:

- `snapshots` for searchable EXOS snapshot records and full snapshot JSON.
- `outcomes` for future return, drawdown, hit-rate, and label data attached later by `snapshot_id`.

The engine must query snapshots by symbol, timeframe, date range, score, and state without loading all snapshots into memory.

### API Connector

Prepares structured JSON data for external APIs.

### AI Layer

Analyzes structured data and produces summaries, scores, and suggestions.

## Startup Flow

main.py
↓
Application
↓
Main Window
↓
Managers
↓
User Interaction

## Future Expansion

EXOS Desktop may later connect with the broader EXOS Agent system.
