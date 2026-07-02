# SnapshotPayloadV2 Contract

Status: FROZEN.

SnapshotPayloadV2 is the canonical analysis record for EXOS. It is the durable, lossless daily research snapshot payload stored in `daily_research_snapshots.canonical_snapshot_json` and is ready to be consumed by Statistics, Backtest, Pattern Library, and future AI layers.

## Compatibility Rules

- Existing SnapshotPayloadV2 fields must not be removed.
- Existing SnapshotPayloadV2 fields must not be renamed.
- Future SnapshotPayloadV2 changes must be additive.
- Breaking payload changes require a new `SnapshotPayloadV3` contract.
- Database schema changes are separate from this payload contract and are not implied by the frozen payload status.

## Required Sections

SnapshotPayloadV2 records must retain these top-level sections:

- `identity`
- `provenance`
- `input`
- `analysis`
- `context`
- `strategy`
- `display_summary`
- `diagnostics`
- `compatibility`

The `identity.payload_schema_version` value must be `snapshot_payload_v2`.

## Quality Gate

The official developer quality gate for saved SnapshotPayloadV2 records is `validate_snapshot_payload_v2_records` in `src.developer`.

The validator checks:

- required sections exist
- `identity.payload_schema_version == "snapshot_payload_v2"`
- `input.ohlcv_window.row_count > 0`
- `analysis.brain_snapshot.indicators` is populated
- required context sections are populated

Saved payload validation is read-only. It must not mutate stored snapshots.
