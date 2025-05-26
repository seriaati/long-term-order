from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

import shioaji as sj

if TYPE_CHECKING:
    from shioaji.contracts import Contract
    from shioaji.order import Order, Trade
    from shioaji.position import FuturePosition, StockPosition


class AsyncShioaji(sj.Shioaji):
    async def place_order(self, contract: Contract, order: Order) -> Trade:
        return await asyncio.to_thread(super().place_order, contract, order)

    async def list_trades(self) -> list[Trade]:
        return await asyncio.to_thread(super().list_trades)

    async def cancel_order(self, trade: Trade) -> None:
        await asyncio.to_thread(super().cancel_order, trade)

    async def login(self, api_key: str, secret_key: str) -> None:
        await asyncio.to_thread(super().login, api_key, secret_key)

    async def activate_ca(self, ca_path: str, ca_passwd: str, person_id: str) -> None:
        await asyncio.to_thread(super().activate_ca, ca_path, ca_passwd, person_id)

    async def list_positions(self) -> list[StockPosition | FuturePosition]:
        return await asyncio.to_thread(super().list_positions, self.stock_account)  # pyright: ignore[reportArgumentType]

    async def update_status(self) -> None:
        await asyncio.to_thread(super().update_status, self.stock_account)  # pyright: ignore[reportArgumentType]

    def get_stock(self, stock_id: str) -> Contract | None:
        return self.Contracts.Stocks.get(stock_id)
