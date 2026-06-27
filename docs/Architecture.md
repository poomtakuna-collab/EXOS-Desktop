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
