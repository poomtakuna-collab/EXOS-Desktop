from __future__ import annotations


class StateManager:
    def __init__(self) -> None:
        self.current_symbol: str | None = None

    def set_current_symbol(self, symbol: str | None) -> None:
        normalized_symbol = symbol.strip().upper() if symbol else ""
        self.current_symbol = normalized_symbol or None

    def clear_current_symbol(self) -> None:
        self.current_symbol = None
