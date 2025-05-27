from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

import shioaji as sj
from loguru import logger

from bot.config import CONFIG

if TYPE_CHECKING:
    from types import EllipsisType

    from shioaji.contracts import Contract
    from shioaji.order import Order, Trade
    from shioaji.position import FuturePosition, StockPosition


class AsyncShioaji(sj.Shioaji):
    def __init__(self, *, simulation: bool | EllipsisType = ...) -> None:
        self.simulation = simulation if simulation is not ... else CONFIG.simulation

    async def __aenter__(self) -> AsyncShioaji:
        await self.login(api_key=CONFIG.shioaji_api_key, secret_key=CONFIG.shioaji_api_secret)
        await self.activate_ca(
            ca_path=CONFIG.ca_path, ca_passwd=CONFIG.ca_password, person_id=CONFIG.ca_person_id
        )
        logger.info(f"Initialized shioaji api with simulation={self.simulation}")
        return self

    async def __aexit__(self, exc_type, exc_value, traceback) -> None:  # noqa: ANN001
        await self.logout()

    async def place_order(self, contract: Contract, order: Order) -> Trade:
        return await asyncio.to_thread(super().place_order, contract, order)

    async def list_trades(self) -> list[Trade]:
        return await asyncio.to_thread(super().list_trades)

    async def cancel_order(self, trade: Trade) -> None:
        await asyncio.to_thread(super().cancel_order, trade)

    async def login(self, api_key: str, secret_key: str) -> None:
        await asyncio.to_thread(super().login, api_key, secret_key)

    async def logout(self) -> None:
        await asyncio.to_thread(super().logout)

    async def activate_ca(self, ca_path: str, ca_passwd: str, person_id: str) -> None:
        await asyncio.to_thread(super().activate_ca, ca_path, ca_passwd, person_id)

    async def list_positions(self) -> list[StockPosition | FuturePosition]:
        return await asyncio.to_thread(super().list_positions, self.stock_account)  # pyright: ignore[reportArgumentType]

    async def update_status(self) -> None:
        await asyncio.to_thread(super().update_status, self.stock_account)  # pyright: ignore[reportArgumentType]

    def get_stock(self, stock_id: str) -> Contract | None:
        for _ in range(3):
            stock = self.Contracts.Stocks.get(stock_id)
            if stock is not None:
                return stock

        return None
