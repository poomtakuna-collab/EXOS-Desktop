# EXOS Sprint

## Current Sprint

Evidence Loop Sprint v1

## Sprint Goal

Close the first measurable EXOS loop:

Signal
-> Outcome
-> Performance Report
-> Desktop report surface

The sprint should make EXOS able to preserve generated research signals, track their outcomes, and report whether current deterministic outputs are useful before adding new engines.

## Current Baseline

- EXOS Brain v1 is complete and frozen.
- Context Engine v1 is complete.
- Signal Ledger v1 foundation is implemented.
- Outcome Tracking v1 foundation and Outcome Calculator v1 are implemented.
- Signal Ledger repository foundation is implemented.
- Signal Ledger SQLite Persistence v1 is implemented.
- Outcome SQLite Persistence v1 is implemented.
- Performance Report v1 is implemented.
- EXOS Desktop Performance Surface v0 is implemented.
- EXOS Desktop Symbol-scoped Performance v1 is implemented.
- EXOS Desktop Research Surface v1 is implemented.
- EXOS Desktop Research real analysis/context loading foundation is implemented.
- EXOS Desktop Signal History tab v0 is implemented.
- Chart -> Data Source v1 integration foundation is implemented.
- Chart Data Source v1 integration coverage is implemented.
- ChartWorkspace app integration coverage is implemented.
- Canonical Result Model v1 contracts and adapter foundation are implemented.
- Current full test baseline: 573 tests passing with `py -m unittest discover -s tests`.

## Completed Foundation Work

- Deterministic Brain v1 analysis path.
- Analysis Pipeline v2 foundation.
- Backtest, validation, and Backtest Persistence v1 foundations.
- Data Source v1 public read-only boundary.
- Context calculators for market, sector, relative strength, volume, and support/resistance.
- Signal contracts for EXOS-generated signals.
- Outcome contracts and pure outcome calculation from future OHLCV rows.
- Standalone Outcome SQLite repository for durable `OutcomeRecord` reads/writes.
- In-memory Signal Ledger repository.
- SQLite-backed Signal Ledger repository for signals and linked outcomes.
- Deterministic Performance Report v1 from signal/outcome repositories.
- Main EXOS Desktop Performance tab.
- Selected-symbol scoped Performance tab metrics with global reference summary.
- Main EXOS Desktop Research tab with grouped read-only context cards.
- Read-only Research tab loading from Data Source v1 rows and Analysis Pipeline v2 canonical Brain output where available.
- Main EXOS Desktop Signal History tab for saved signals and linked outcomes.
- Chart Data Source v1 adapter foundation with legacy desktop loader fallback.
- SQLite-backed Chart Data Source v1 integration coverage for adapter reads, fallback behavior, ordering, values, and read-only guarantees.
- ChartWorkspace app-level coverage for adapter injection, successful loads, fallback paths, symbol switching, and repeated refreshes.
- Canonical Result Model v1 typed output contracts.
- Canonical Result adapter foundation for identity, Brain, prediction, and diagnostics sections.

## Next Prioritized Tasks

1. Canonical Result -> Signal adapter
   - Add pure adapter helpers that derive `SignalRecord` candidates from `CanonicalResultV1`.
   - Do not wire into runtime automatically yet.

2. Explicit/manual Signal creation flow
   - Let the user intentionally save deterministic research output as a signal.
   - No runtime auto-persistence.
   - No trading actions.

3. Outcome evaluation flow
   - Evaluate saved signals against future OHLCV rows.
   - Persist outcomes through existing repositories.

4. Performance report with real accumulated signal data
   - Feed Performance Report v1 from saved signals and evaluated outcomes.
   - Keep global and selected-symbol views useful.

5. Context validation/backtest comparison
   - Compare Brain v1 against Brain v1 plus context layers.
   - Adopt only context signals that demonstrate measurable improvement.

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
