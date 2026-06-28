from __future__ import annotations

from src.data import MarketDataRow


EMA_PERIODS = (20, 50, 200)


def calculate_indicator_snapshot(rows: list[MarketDataRow]) -> dict[str, object] | None:
    if not rows:
        return None

    close = float(rows[-1]["close"])
    ema_by_period = {
        period: calculate_ema_values(rows, period)[-1]
        for period in EMA_PERIODS
    }

    return {
        "ema20": ema_by_period[20],
        "ema50": ema_by_period[50],
        "ema200": ema_by_period[200],
        "price_vs_ema20": price_vs_ema(close, ema_by_period[20]),
        "price_vs_ema50": price_vs_ema(close, ema_by_period[50]),
        "price_vs_ema200": price_vs_ema(close, ema_by_period[200]),
        "ema_alignment": ema_alignment(
            ema_by_period[20],
            ema_by_period[50],
            ema_by_period[200],
        ),
    }


def calculate_ema_values(rows: list[MarketDataRow], period: int) -> list[float]:
    closes = [float(row["close"]) for row in rows]
    if not closes:
        return []

    multiplier = 2 / (period + 1)
    ema_values = [closes[0]]
    for close in closes[1:]:
        ema_values.append(
            round((close - ema_values[-1]) * multiplier + ema_values[-1], 4)
        )
    return ema_values


def price_vs_ema(price: float, ema: float) -> str:
    if price > ema:
        return "above"
    if price < ema:
        return "below"
    return "equal"


def ema_alignment(ema20: float, ema50: float, ema200: float) -> str:
    if ema20 > ema50 > ema200:
        return "bullish"
    if ema20 < ema50 < ema200:
        return "bearish"
    return "mixed"
