from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from src.analysis.indicator_engine import calculate_indicator_snapshot
from src.analysis.market_structure import calculate_market_structure_snapshot
from src.analysis.score import analyze_score
from src.analysis.squeeze import calculate_squeeze_snapshot
from src.analysis.trend_slope import calculate_trend_slope_snapshot
from src.data import MarketDataRow


SNAPSHOT_VERSION = "core_indicators_v1"


@dataclass(frozen=True)
class EXOSSnapshot:
    version: str
    metadata: dict[str, object]
    trend: dict[str, object]
    trend_slope: dict[str, object]
    squeeze: dict[str, object]
    market_structure: dict[str, object]
    indicators: dict[str, object]
    score: dict[str, object]

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def build_exos_snapshot(
    rows: list[MarketDataRow],
    symbol: str | None = None,
    timeframe: str | None = None,
) -> dict[str, object]:
    trend_snapshot = calculate_indicator_snapshot(rows) or {}
    trend_slope_snapshot = calculate_trend_slope_snapshot(rows) or {}
    squeeze_snapshot = calculate_squeeze_snapshot(rows)
    market_structure_snapshot = calculate_market_structure_snapshot(rows)

    snapshot = EXOSSnapshot(
        version=SNAPSHOT_VERSION,
        metadata={
            "symbol": symbol or "",
            "timeframe": timeframe or "",
            "rows": len(rows),
        },
        trend=_trend_section(trend_snapshot),
        trend_slope=_trend_slope_section(trend_slope_snapshot),
        squeeze=_squeeze_section(squeeze_snapshot),
        market_structure=_market_structure_section(market_structure_snapshot),
        indicators={},
        score={},
    ).to_dict()
    snapshot["score"] = analyze_score(snapshot)
    return snapshot


def _trend_section(snapshot: dict[str, Any]) -> dict[str, object]:
    alignment = str(snapshot.get("ema_alignment", "mixed"))
    if alignment == "bullish":
        state = "bullish"
        score = 70.0
    elif alignment == "bearish":
        state = "bearish"
        score = 30.0
    else:
        state = "mixed"
        score = 50.0

    confidence = 100.0 if snapshot else 0.0
    return {
        "state": state,
        "score": score,
        "confidence": confidence,
    }


def _trend_slope_section(snapshot: dict[str, Any]) -> dict[str, object]:
    trend_slope = float(snapshot.get("trend_slope", 0.0))
    direction = str(snapshot.get("trend_slope_state", "flat"))
    return {
        "score": round(_clamp(50 + trend_slope * 5, 0, 100), 2),
        "direction": direction,
        "confidence": 100.0 if snapshot else 0.0,
    }


def _squeeze_section(snapshot: dict[str, Any]) -> dict[str, object]:
    return {
        "state": str(snapshot.get("state", "NONE")),
        "compression_ratio": float(snapshot.get("compression_ratio", 0.0)),
        "score": float(snapshot.get("compression_score", 0.0)),
        "release_probability": float(snapshot.get("release_probability", 0.0)),
        "confidence": _percent_confidence(snapshot.get("confidence", 0.0)),
    }


def _market_structure_section(snapshot: dict[str, Any]) -> dict[str, object]:
    return {
        "state": str(snapshot.get("structure_state", "UNKNOWN")),
        "score": float(snapshot.get("structure_score", 0.0)),
        "swing_high": float(snapshot.get("swing_high", 0.0)),
        "swing_low": float(snapshot.get("swing_low", 0.0)),
        "last_pivot_high": float(snapshot.get("last_pivot_high", 0.0)),
        "last_pivot_low": float(snapshot.get("last_pivot_low", 0.0)),
        "bos": str(snapshot.get("bos", "none")),
        "choch": str(snapshot.get("choch", "none")),
        "confidence": _percent_confidence(snapshot.get("confidence", 0.0)),
    }


def _percent_confidence(value: object) -> float:
    confidence = float(value)
    if confidence <= 1:
        confidence *= 100
    return round(_clamp(confidence, 0, 100), 2)


def _clamp(value: float, minimum: float, maximum: float) -> float:
    return min(max(value, minimum), maximum)
