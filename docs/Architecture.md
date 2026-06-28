# Architecture

## Design Philosophy

EXOS Desktop is a data-first investment research platform.

AI is an optional analysis layer. The application must remain fully functional when AI is disabled.

Core order:

Market Data
-> Core Indicators
-> Snapshot
-> Statistics DB
-> Outcome
-> Pattern Discovery
-> Pattern Library
-> Similarity
-> Strategy
-> Prediction
-> AI

## Layered Architecture

EXOS Desktop is divided into three main layers.

### Presentation Layer

GUI, windows, panels, menus, tables, and charts.

### Business Layer

Core indicators, snapshot building, scoring, statistics, market learning, strategy, backtest, and trade analysis.

### Data Layer

Data loading, local storage, SQLite database, cache, and file access.

## Dependency Rule

- Presentation Layer may call Business Layer.
- Business Layer may call Data Layer.
- Presentation Layer must not access the database directly.
- AI must not control core logic.
- AI may only read structured data and generate analysis or summaries.

## Core Modules

### Main Window

The main desktop window of EXOS Desktop.

### Data Manager

Loads stock data from external sources and prepares it for storage or display.

### Database Manager

Handles local SQLite database access.

### Chart Engine

Displays candlestick charts, volume, and indicators.

### Core Indicators

Calculates the frozen Core Indicators v1 contract:

- Trend
- Trend Slope
- Squeeze
- Market Structure
- Score

Core Indicators v1 remains frozen unless a real bug appears.

### Snapshot Builder

Builds the nested `core_indicators_v1` EXOS snapshot contract.

### Market Learning Engine

Stores EXOS snapshots, attaches future outcomes, discovers repeatable market patterns, stores reusable pattern knowledge, and compares new snapshots to historical patterns.

Market Learning Engine v1 includes:

- Statistics DB
- Snapshot Store
- Snapshot Collector
- Outcome Calculator
- Pattern Discovery
- Pattern Library
- Similarity Engine
- Pipeline Smoke Test

Schema design:

- `docs/MARKET_LEARNING_SCHEMA.md`

Database rules:

- `snapshot_id` is the central reference.
- Important searchable fields are stored as columns.
- Full nested snapshots are stored as JSON.
- Queries must avoid loading all snapshots into memory.

### Strategy Engine

Planned Phase 3 module for evaluating rules against snapshots, outcomes, patterns, and similarity results.

### Backtest Engine

Planned Phase 3 module for historical strategy simulation.

### Portfolio / Risk Evaluation

Planned Phase 3 module for position sizing, drawdown, risk, and portfolio-level performance.

### Prediction Engine

Planned Phase 4 module for probability estimates based on statistical evidence.

### AI Layer

Planned Phase 5 overlay that explains structured EXOS outputs.

AI does not make decisions.

## Startup Flow

main.py
-> Application
-> Main Window
-> Managers
-> User Interaction

## Future Expansion

EXOS Desktop may later connect with the broader EXOS Agent system.
