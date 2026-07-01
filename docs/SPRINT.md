# EXOS Sprint

## Current Sprint

Evidence Loop Sprint v1

## Sprint Goal

Close the first measurable EXOS loop:

Snapshot
-> Outcome
-> Performance Report
-> Desktop report surface

The sprint should make EXOS able to preserve generated Daily Research Snapshots, track their outcomes, and report whether current deterministic outputs are useful before adding new engines.

## Current Baseline

- EXOS Brain v1 is complete and frozen.
- Context Engine v1 is complete.
- Signal Ledger v1 foundation is implemented.
- Outcome Tracking v1 foundation and Outcome Calculator v1 are implemented.
- Signal Ledger repository foundation is implemented.
- Signal Ledger SQLite Persistence v1 is implemented.
- Daily Research Snapshot Persistence v2 foundation is implemented.
- Daily Research Snapshot Persistence v2 is wired into explicit Manual Snapshot Save and Backfill flows.
- Outcome SQLite Persistence v1 is implemented.
- Outcome Evaluation Flow v1 foundation is implemented.
- Performance Report v1 is implemented.
- Performance Report Snapshot Health Summary is implemented.
- EXOS Desktop Performance Surface v0 is implemented.
- EXOS Desktop Symbol-scoped Performance v1 is implemented.
- EXOS Desktop Research Surface v1 is implemented.
- EXOS Desktop Research real analysis/context loading foundation is implemented.
- EXOS Desktop Snapshot History tab v0 is implemented.
- EXOS Desktop Snapshot Detail Viewer prefers full v2 canonical snapshot payloads when available.
- Chart -> Data Source v1 integration foundation is implemented.
- Chart Data Source v1 integration coverage is implemented.
- ChartWorkspace app integration coverage is implemented.
- Canonical Result Model v1 contracts and adapter foundation are implemented.
- Canonical Result -> Signal Adapter v1 is implemented.
- EXOS Desktop Manual Snapshot Save Flow v1 is implemented through the existing Signal Ledger compatibility contract.
- Manual Snapshot Backfill Service foundation is implemented.
- Manual Evidence Loop Runner foundation is implemented.
- EXOS Desktop Manual Evidence Loop action is implemented.
- EXOS Desktop Evidence Loop background worker and crash guard are implemented.
- Desktop Snapshot terminology is implemented for user-facing save/history/performance surfaces.
- Analysis Cutoff Policy v1 foundation is implemented.
- Current full test baseline: 639 tests passing with `py -m unittest discover -s tests`.

## Completed Foundation Work

- Deterministic Brain v1 analysis path.
- Analysis Pipeline v2 foundation.
- Backtest, validation, and Backtest Persistence v1 foundations.
- Data Source v1 public read-only boundary.
- Context calculators for market, sector, relative strength, volume, and support/resistance.
- Signal Ledger contracts remain the v1 compatibility storage contract for Daily Research Snapshots.
- Outcome contracts and pure outcome calculation from future OHLCV rows.
- Standalone Outcome SQLite repository for durable `OutcomeRecord` reads/writes.
- Deterministic Outcome Evaluation Flow v1 from saved snapshots to persisted completed outcomes.
- In-memory Signal Ledger repository.
- SQLite-backed Signal Ledger repository for snapshot-compatible records and linked outcomes.
- Additive immutable Daily Research Snapshot v2 repository for full lossless `CanonicalResultV1.to_dict()` JSON by symbol, market date, timeframe, canonical schema version, and persistence version.
- Explicit snapshot creation flows now persist both the full v2 canonical snapshot row and the existing Signal Ledger compatibility row.
- Deterministic Performance Report v1 from snapshot/outcome repositories, including Snapshot Health Summary fields for coverage, pending outcomes, duplicates, and latest dates.
- Main EXOS Desktop Performance tab.
- Selected-symbol scoped Performance tab metrics with global reference summary.
- Main EXOS Desktop Research tab with grouped read-only context cards.
- Read-only Research tab loading from Data Source v1 rows and Analysis Pipeline v2 canonical Brain output where available.
- Main EXOS Desktop Snapshot History tab for saved snapshots and linked outcomes.
- Snapshot Detail opens full v2 canonical Daily Research Snapshot JSON when present and falls back to legacy reduced SignalRecord detail when absent.
- Chart Data Source v1 adapter foundation with legacy desktop loader fallback.
- SQLite-backed Chart Data Source v1 integration coverage for adapter reads, fallback behavior, ordering, values, and read-only guarantees.
- ChartWorkspace app-level coverage for adapter injection, successful loads, fallback paths, symbol switching, and repeated refreshes.
- Canonical Result Model v1 typed output contracts.
- Canonical Result adapter foundation for identity, Brain, prediction, and diagnostics sections.
- Pure Canonical Result -> Signal adapter for deterministic `SignalRecord` candidates.
- Explicit Research tab `Save Snapshot` action through the Canonical Result -> Signal adapter and SQLite Signal Ledger repository.
- Duplicate-safe manual snapshot save by symbol and market date.
- Explicit Manual Snapshot Backfill Service for missing symbol/date research snapshots.
- Deterministic Outcome Evaluation Flow v1 for saved snapshots.
- Explicit Manual Evidence Loop Runner for backfill followed by outcome evaluation.
- Main EXOS Desktop `Run Evidence Loop` toolbar action with Snapshot History and Performance refresh.
- Background Qt worker, retained thread/worker references, and defensive crash guard for Evidence Loop completion/error paths.
- User-facing Snapshot terminology across Research save, History, Performance, and Evidence Loop status surfaces.
- Deterministic Analysis Cutoff Policy v1 for separating chart latest date from Research analysis cutoff date.

## Next Prioritized Tasks

1. Performance report with real accumulated snapshot data
   - Feed Performance Report v1 from saved snapshots and evaluated outcomes.
   - Keep global and selected-symbol views useful.

2. Context validation/backtest comparison
   - Compare Brain v1 against Brain v1 plus context layers.
   - Adopt only context layers that demonstrate measurable improvement.

## Definition of Done

- Changes are additive and do not modify frozen Brain v1 contracts.
- Existing runtime pipeline outputs remain unchanged unless explicitly requested.
- New persistence or reporting code is deterministic and unit-tested.
- SQLite writes happen only through explicit repository/persistence calls.
- Public contracts have stable `to_dict()` or JSON-safe output where appropriate.
- `py -m unittest discover -s tests` passes before session close.
- `docs/PROJECT_STATUS.md` is updated when foundation status or test count changes.

## Risks / Guardrails

- Do not add new engines before measurable performance reporting exists.
- Do not add new engines until current engines are measurable.
- Do not start Portfolio Engine.
- Do not add an AI decision layer.
- AI, when added later, must explain structured EXOS outputs only and must not decide.
- Do not wire new persistence into runtime paths until contracts and reports are tested.
- Do not mutate frozen Brain v1, Strategy, Backtest, Context, Signal Ledger, or Outcome contracts unless fixing a verified bug.
- Prefer small, explicit adapters over expanding Analysis Pipeline v2 into a large translation hub.
- Prefer growing EXOS Desktop as the main program instead of creating many demo scripts.

## Workflow

Use a Morning Review + End Session Review workflow to reduce usage.

Morning Review:

- Read this file first.
- Read `docs/PROJECT_STATUS.md` second.
- Confirm the next task and constraints before coding.
- Avoid broad repo exploration unless the task requires it.

End Session Review:

- Run the required tests.
- Update `docs/PROJECT_STATUS.md` if status or test count changed.
- Summarize files changed, tests run, and next recommended task.
- Leave the repo in a ready-to-commit state.
