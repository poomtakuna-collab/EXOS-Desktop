from __future__ import annotations

from dataclasses import asdict, dataclass
from math import sqrt

from src.data import MarketDataRow


SQUEEZE_LENGTH = 20
BB_MULTIPLIER = 2.0
KC_MULTIPLIER = 1.5


@dataclass(frozen=True)
class SqueezeAnalysis:
    compression_ratio: float
    compression_score: float
    state: str
    release_probability: float
    confidence: float

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def analyze_squeeze(rows: list[MarketDataRow]) -> SqueezeAnalysis:
    if len(rows) < SQUEEZE_LENGTH + 1:
        return _default_analysis()

    current = _compression_ratio(rows)
    previous = _compression_ratio(rows[:-1])
    if current is None:
        return _default_analysis()

    previous_ratio = previous if previous is not None else current
    compression_score = _compression_score(current)
    previous_score = _compression_score(previous_ratio)
    state = _squeeze_state(
        compression_ratio=current,
        previous_ratio=previous_ratio,
        compression_score=compression_score,
        previous_score=previous_score,
    )

    return SqueezeAnalysis(
        compression_ratio=round(current, 4),
        compression_score=round(compression_score, 2),
        state=state,
        release_probability=round(
            _release_probability(
                state=state,
                compression_ratio=current,
                previous_ratio=previous_ratio,
                previous_score=previous_score,
            ),
            2,
        ),
        confidence=1.0,
    )


def calculate_squeeze_snapshot(
    rows: list[MarketDataRow],
) -> dict[str, object]:
    return analyze_squeeze(rows).to_dict()


def _compression_ratio(rows: list[MarketDataRow]) -> float | None:
    if len(rows) < SQUEEZE_LENGTH:
        return None

    window = rows[-SQUEEZE_LENGTH:]
    closes = [float(row["close"]) for row in window]
    bb_width = _bb_width(closes)
    kc_width = _kc_width(window)
    if kc_width == 0:
        return None

    return bb_width / kc_width


def _bb_width(closes: list[float]) -> float:
    middle = sum(closes) / len(closes)
    variance = sum((close - middle) ** 2 for close in closes) / len(closes)
    standard_deviation = sqrt(variance)
    upper = middle + BB_MULTIPLIER * standard_deviation
    lower = middle - BB_MULTIPLIER * standard_deviation
    return upper - lower


def _kc_width(rows: list[MarketDataRow]) -> float:
    atr = _atr(rows)
    return 2 * KC_MULTIPLIER * atr


def _atr(rows: list[MarketDataRow]) -> float:
    true_ranges: list[float] = []
    previous_close: float | None = None
    for row in rows:
        high = float(row["high"])
        low = float(row["low"])
        if previous_close is None:
            true_range = high - low
        else:
            true_range = max(
                high - low,
                abs(high - previous_close),
                abs(low - previous_close),
            )
        true_ranges.append(true_range)
        previous_close = float(row["close"])

    return sum(true_ranges) / len(true_ranges) if true_ranges else 0.0


def _compression_score(compression_ratio: float) -> float:
    return _clamp((1.5 - compression_ratio) / 0.75 * 100, 0, 100)


def _squeeze_state(
    compression_ratio: float,
    previous_ratio: float,
    compression_score: float,
    previous_score: float,
) -> str:
    is_expanding = compression_ratio > previous_ratio
    was_compressed = previous_score >= 50

    if is_expanding and was_compressed:
        return "RELEASING"
    if compression_ratio <= 1.0:
        return "SQUEEZE"
    if compression_score >= 35:
        return "BUILDING"
    if compression_ratio >= 1.5:
        return "EXPANDED"
    return "NONE"


def _release_probability(
    state: str,
    compression_ratio: float,
    previous_ratio: float,
    previous_score: float,
) -> float:
    if state == "RELEASING":
        expansion = max(compression_ratio - previous_ratio, 0)
        return _clamp(previous_score + expansion * 100, 0, 100)
    if state == "SQUEEZE":
        return _clamp(previous_score * 0.65, 0, 100)
    if state == "BUILDING":
        return _clamp(previous_score * 0.4, 0, 100)
    return 0.0


def _default_analysis() -> SqueezeAnalysis:
    return SqueezeAnalysis(
        compression_ratio=0.0,
        compression_score=0.0,
        state="NONE",
        release_probability=0.0,
        confidence=0.0,
    )


def _clamp(value: float, minimum: float, maximum: float) -> float:
    return min(max(value, minimum), maximum)
