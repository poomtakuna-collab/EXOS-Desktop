from __future__ import annotations

import sqlite3

from src.statistics.probability import predict_probability_for_snapshot


EMPTY_PREDICTION = {
    "expected_price_5d": 0.0,
    "expected_price_10d": 0.0,
    "expected_price_20d": 0.0,
    "target_zone_low": 0.0,
    "target_zone_high": 0.0,
    "risk_zone_low": 0.0,
    "risk_zone_high": 0.0,
    "expected_return": 0.0,
    "confidence": 0.0,
    "time_horizon": "10D",
    "best_pattern_id": None,
    "best_similarity": 0.0,
}


def build_prediction(
    probability: dict[str, object],
    current_price: float,
) -> dict[str, object]:
    price = float(current_price)
    confidence = _optional_float(probability.get("confidence")) or 0.0
    if price <= 0 or confidence <= 0:
        return {
            **EMPTY_PREDICTION,
            "expected_price_5d": round(max(price, 0.0), 4),
            "expected_price_10d": round(max(price, 0.0), 4),
            "expected_price_20d": round(max(price, 0.0), 4),
            "target_zone_low": round(max(price, 0.0), 4),
            "target_zone_high": round(max(price, 0.0), 4),
            "risk_zone_low": round(max(price, 0.0), 4),
            "risk_zone_high": round(max(price, 0.0), 4),
            "best_pattern_id": probability.get("best_pattern_id"),
            "best_similarity": _optional_float(probability.get("best_similarity"))
            or 0.0,
        }

    expected_return_5d = _optional_float(probability.get("expected_return_5d")) or 0.0
    expected_return_10d = _optional_float(probability.get("expected_return_10d")) or 0.0
    expected_return_20d = _optional_float(probability.get("expected_return_20d")) or 0.0
    expected_max_gain = _optional_float(probability.get("expected_max_gain_10d")) or 0.0
    expected_drawdown = _optional_float(probability.get("expected_drawdown_10d")) or 0.0
    confidence_ratio = min(max(confidence, 0.0), 100.0) / 100.0

    expected_price_5d = _project_price(price, expected_return_5d)
    expected_price_10d = _project_price(price, expected_return_10d)
    expected_price_20d = _project_price(price, expected_return_20d)

    target_low_return = expected_return_10d * confidence_ratio
    target_high_return = expected_return_10d + (
        max(expected_max_gain, expected_return_10d) - expected_return_10d
    ) * confidence_ratio
    target_prices = sorted(
        (
            _project_price(price, target_low_return),
            _project_price(price, target_high_return),
        )
    )

    drawdown_return = min(expected_drawdown, 0.0)
    risk_prices = sorted(
        (
            _project_price(price, drawdown_return),
            _project_price(price, drawdown_return * 0.5),
        )
    )

    return {
        "expected_price_5d": expected_price_5d,
        "expected_price_10d": expected_price_10d,
        "expected_price_20d": expected_price_20d,
        "target_zone_low": target_prices[0],
        "target_zone_high": target_prices[1],
        "risk_zone_low": risk_prices[0],
        "risk_zone_high": risk_prices[1],
        "expected_return": round(expected_return_10d, 4),
        "confidence": round(confidence, 4),
        "time_horizon": "10D",
        "best_pattern_id": probability.get("best_pattern_id"),
        "best_similarity": _optional_float(probability.get("best_similarity")) or 0.0,
    }


def predict_snapshot(
    conn: sqlite3.Connection,
    snapshot: dict[str, object],
    current_price: float,
    top_n: int = 10,
) -> dict[str, object]:
    probability_result = predict_probability_for_snapshot(conn, snapshot, top_n=top_n)
    probability = probability_result["probability"]
    return {
        "prediction": build_prediction(probability, current_price),
        "probability": probability,
        "matches": probability_result["matches"],
    }


def _project_price(current_price: float, expected_return: float) -> float:
    return round(current_price * (1 + expected_return / 100), 4)


def _optional_float(value: object) -> float | None:
    if value is None:
        return None
    return float(value)
