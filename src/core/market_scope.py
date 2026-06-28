from __future__ import annotations


MARKET_SCOPE = "NASDAQ"


def is_supported_market_symbol(symbol: str) -> bool:
    normalized_symbol = symbol.strip().upper()
    return (
        1 <= len(normalized_symbol) <= 5
        and normalized_symbol.isalpha()
        and normalized_symbol.isascii()
    )
