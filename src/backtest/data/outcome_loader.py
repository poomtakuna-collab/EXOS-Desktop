from __future__ import annotations

from typing import Any


class OutcomeLoader:
    """Public interface for loading stored outcome records for Backtest."""

    def load_outcome(self, snapshot_id: str) -> dict[str, Any] | None:
        """Load one outcome record associated with `snapshot_id`.

        Implementations must not calculate new outcomes or modify stored records.
        Missing outcomes should be represented deterministically.
        """
        raise NotImplementedError("OutcomeLoader.load_outcome is not implemented yet")

    def load_outcomes(
        self,
        snapshot_ids: list[str],
    ) -> dict[str, dict[str, Any]]:
        """Load outcome records for the provided snapshot ids.

        Implementations must preserve the `snapshot_id` relationship and should
        report missing outcomes without raising for normal absence.
        """
        raise NotImplementedError("OutcomeLoader.load_outcomes is not implemented yet")
