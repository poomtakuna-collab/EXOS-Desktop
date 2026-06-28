from __future__ import annotations

from typing import Protocol


MarketDataRow = dict[str, object]


class DataProvider(Protocol):
    source_name: str

    def get_historical_data(self, symbol: str) -> list[MarketDataRow]:
        pass


class YahooFinanceDataProvider:
    source_name = "Yahoo Finance"
    history_period = "10y"

    def get_historical_data(self, symbol: str) -> list[MarketDataRow]:
        import yfinance as yf

        ticker = yf.Ticker(symbol)
        history = ticker.history(
            period=self.history_period, interval="1d", auto_adjust=False
        )

        if history.empty:
            return []

        rows: list[MarketDataRow] = []

        for date, row in history.iterrows():
            rows.append(
                {
                    "date": date.date().isoformat(),
                    "open": float(row["Open"]),
                    "high": float(row["High"]),
                    "low": float(row["Low"]),
                    "close": float(row["Close"]),
                    "volume": int(row["Volume"]),
                }
            )

        return rows
