from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from src.core.market_scope import is_supported_market_symbol


class DashboardManager:
    def __init__(self, storage_path: Path | None = None) -> None:
        self._storage_path = storage_path or Path("data") / "dashboard.json"

    def load_symbols(self) -> list[dict[str, Any]]:
        self._ensure_storage_file()

        with self._storage_path.open("r", encoding="utf-8") as file:
            data = json.load(file)

        symbols = data.get("symbols", [])
        if not isinstance(symbols, list):
            return []

        return [symbol for symbol in symbols if isinstance(symbol, dict)]

    def add_symbol(self, symbol: str) -> bool:
        normalized_symbol = self._normalize_symbol(symbol)
        if not normalized_symbol:
            return False
        if not is_supported_market_symbol(normalized_symbol):
            return False

        symbols = self.load_symbols()
        if self._symbol_exists(symbols, normalized_symbol):
            return False

        symbols.append({"symbol": normalized_symbol, "note": "", "priority": 0})
        self._save_symbols(symbols)
        return True

    def remove_symbol(self, symbol: str) -> bool:
        normalized_symbol = self._normalize_symbol(symbol)
        if not normalized_symbol:
            return False

        symbols = self.load_symbols()
        updated_symbols = [
            item
            for item in symbols
            if self._normalize_symbol(str(item.get("symbol", ""))) != normalized_symbol
        ]

        if len(updated_symbols) == len(symbols):
            return False

        self._save_symbols(updated_symbols)
        return True

    def _save_symbols(self, symbols: list[dict[str, Any]]) -> None:
        self._ensure_storage_file()
        self._storage_path.write_text(
            json.dumps({"symbols": symbols}, indent=2) + "\n",
            encoding="utf-8",
        )

    def _ensure_storage_file(self) -> None:
        if self._storage_path.exists():
            return

        self._storage_path.parent.mkdir(parents=True, exist_ok=True)
        self._storage_path.write_text(
            json.dumps({"symbols": []}, indent=2) + "\n",
            encoding="utf-8",
        )

    def _normalize_symbol(self, symbol: str) -> str:
        return symbol.strip().upper()

    def _symbol_exists(self, symbols: list[dict[str, Any]], symbol: str) -> bool:
        return any(
            self._normalize_symbol(str(item.get("symbol", ""))) == symbol
            for item in symbols
        )
