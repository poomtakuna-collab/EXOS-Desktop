from __future__ import annotations


class StateManager:
    def __init__(self) -> None:
        self.current_symbol: str | None = None
        self.market_data_rows: int = 0
        self.market_data_source: str = ""
        self.last_load_time: float | None = None
        self.status: str = "Ready"

    def set_current_symbol(self, symbol: str | None) -> None:
        normalized_symbol = symbol.strip().upper() if symbol else ""
        self.current_symbol = normalized_symbol or None
        self.clear_market_data_state()

    def clear_current_symbol(self) -> None:
        self.current_symbol = None
        self.clear_market_data_state()

    def set_market_data_state(
        self, rows: int, source: str, last_load_time: float | None
    ) -> None:
        self.market_data_rows = rows
        self.market_data_source = source
        self.last_load_time = last_load_time
        self.status = "Ready"

    def set_error_status(self, status: str) -> None:
        self.market_data_rows = 0
        self.market_data_source = ""
        self.last_load_time = None
        self.status = status or "Ready"

    def clear_market_data_state(self) -> None:
        self.market_data_rows = 0
        self.market_data_source = ""
        self.last_load_time = None
        self.status = "Ready"
