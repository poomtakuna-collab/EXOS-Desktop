from __future__ import annotations

from src.data.data_provider import DataProvider, EmptyDataProvider


class DataManager:
    def __init__(self, data_provider: DataProvider | None = None) -> None:
        self._data_provider = data_provider or EmptyDataProvider()

    def get_historical_data(self, symbol: str) -> list[dict[str, object]]:
        normalized_symbol = symbol.strip().upper()
        if not normalized_symbol:
            return []

        return self._data_provider.get_historical_data(normalized_symbol)
