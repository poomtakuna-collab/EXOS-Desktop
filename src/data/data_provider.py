from __future__ import annotations

from typing import Protocol


class DataProvider(Protocol):
    def get_historical_data(self, symbol: str) -> list[dict[str, object]]:
        pass


class EmptyDataProvider:
    def get_historical_data(self, symbol: str) -> list[dict[str, object]]:
        return []
