from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shioaji.contracts import StreamStockContracts


def get_stock_name(stock_id: str, stocks: StreamStockContracts) -> str:
    contract = stocks.get(stock_id)
    if contract is None:
        return stock_id
    return contract.name
