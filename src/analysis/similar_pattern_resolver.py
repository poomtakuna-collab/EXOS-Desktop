from __future__ import annotations

from typing import Any

from src.analysis.similarity import calculate_weighted_similarity


DEFAULT_TOP_K = 20


def resolve_similar_patterns(
    snapshot: dict[str, Any],
    pattern_library: list[dict[str, Any]],
    top_k: int = DEFAULT_TOP_K,
) -> dict[str, list[dict[str, object]]]:
    if top_k <= 0 or not pattern_library:
        return {"matches": []}

    matches = [
        _build_match(snapshot, pattern, index)
        for index, pattern in enumerate(pattern_library)
    ]
    matches.sort(
        key=lambda match: (
            float(match["similarity"]),
            -int(match["_index"]),
        ),
        reverse=True,
    )

    return {
        "matches": [
            _public_match(match)
            for match in matches[:top_k]
        ],
    }


def _build_match(
    snapshot: dict[str, Any],
    pattern: dict[str, Any],
    index: int,
) -> dict[str, object]:
    return {
        "pattern_id": pattern.get("pattern_id"),
        "similarity": calculate_weighted_similarity(snapshot, pattern),
        "outcome": _resolve_outcome(pattern),
        "pattern": dict(pattern),
        "_index": index,
    }


def _public_match(match: dict[str, object]) -> dict[str, object]:
    return {
        "pattern_id": match["pattern_id"],
        "similarity": match["similarity"],
        "outcome": match["outcome"],
        "pattern": match["pattern"],
    }


def _resolve_outcome(pattern: dict[str, Any]) -> object:
    for key in ("outcome", "dominant_label", "label_10d"):
        value = pattern.get(key)
        if value is not None:
            return value
    return None
