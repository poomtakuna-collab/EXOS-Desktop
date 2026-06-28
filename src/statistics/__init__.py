from src.statistics.schema import (
    CREATE_OUTCOMES_TABLE_SQL,
    CREATE_PATTERNS_TABLE_SQL,
    CREATE_SNAPSHOTS_TABLE_SQL,
    REQUIRED_INDEX_SQL,
    initialize_statistics_db,
)
from src.statistics.collector import collect_snapshot, collect_snapshots_for_series
from src.statistics.outcome_calculator import (
    calculate_outcome_for_snapshot,
    calculate_outcomes_for_series,
    insert_or_update_outcome,
    label_10d,
)
from src.statistics.pattern_discovery import (
    discover_best_patterns,
    discover_patterns,
    discover_strong_bull_patterns,
    summarize_factor_distribution,
    summarize_pattern_statistics,
)
from src.statistics.pattern_library import (
    get_pattern,
    load_pattern_library,
    rebuild_pattern_library,
)
from src.statistics.similarity import (
    calculate_similarity,
    find_best_match,
    find_similar_patterns,
)
from src.statistics.snapshot_store import insert_snapshot, prepare_snapshot_record

__all__ = [
    "CREATE_OUTCOMES_TABLE_SQL",
    "CREATE_PATTERNS_TABLE_SQL",
    "CREATE_SNAPSHOTS_TABLE_SQL",
    "REQUIRED_INDEX_SQL",
    "calculate_similarity",
    "collect_snapshot",
    "collect_snapshots_for_series",
    "calculate_outcome_for_snapshot",
    "calculate_outcomes_for_series",
    "discover_best_patterns",
    "discover_patterns",
    "discover_strong_bull_patterns",
    "find_best_match",
    "find_similar_patterns",
    "get_pattern",
    "initialize_statistics_db",
    "insert_snapshot",
    "insert_or_update_outcome",
    "label_10d",
    "load_pattern_library",
    "prepare_snapshot_record",
    "rebuild_pattern_library",
    "summarize_factor_distribution",
    "summarize_pattern_statistics",
]
