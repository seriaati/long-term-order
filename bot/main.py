from __future__ import annotations

import asyncio
import datetime
from typing import TYPE_CHECKING

import discord
import shioaji as sj
import shioaji.constant as sjc
from discord.ext import commands, tasks
from loguru import logger
from sqlmodel import SQLModel

from bot.config import CONFIG
from bot.db.models.order import Order
from bot.db.session import engine
from bot.ui import OrderView

if TYPE_CHECKING:
    from shioaji.contracts import Contract
    from shioaji.position import FuturePosition, StockPosition


class Bot(commands.Bot):
    def __init__(self) -> None:
        super().__init__(commands.when_mentioned, intents=discord.Intents.default())
        self.shioaji: sj.Shioaji

    async def _get_positions(self) -> list[StockPosition | FuturePosition]:
        api = self.shioaji
        return await asyncio.to_thread(api.list_positions, api.stock_account)  # pyright: ignore[reportArgumentType]

    def get_contract(self, stock_id: str) -> Contract | None:
        api = self.shioaji
        contract = api.Contracts.Stocks.get(stock_id)
        if contract is None:
            logger.warning(f"Contract {stock_id} not found")
            return None
        return contract

    async def _place_order(self, order: Order) -> None:
        api = self.shioaji
        contract = self.get_contract(order.stock_id)
        if contract is None:
            logger.warning(f"Contract {order.stock_id} not found")
            await order.delete()
            return

        order_obj = api.Order(
            price=order.price,
            quantity=order.quantity,
            action=sjc.Action.Buy,
            price_type=sjc.StockPriceType.LMT,
            order_type=sjc.OrderType.ROD,
            account=api.stock_account,
        )
        trade = await asyncio.to_thread(api.place_order, contract, order_obj)
        logger.info(f"Placed order: {trade}")

    @tasks.loop(
        time=datetime.time(hour=8, minute=30, tzinfo=datetime.timezone(datetime.timedelta(hours=8)))
    )
    async def place_orders(self) -> None:
        if not CONFIG.simulation:
            positions = await self._get_positions()
            position_ids = {p.code for p in positions}
        else:
            position_ids = {}
        logger.info(f"Position IDs: {position_ids}")

        orders = await Order.all()

        for o in orders:
            logger.info(f"Processing order: {o}")

            if o.stock_id in position_ids:
                logger.info(f"Order {o.stock_id} already in positions, skipping and deleting order")
                await o.delete()
                continue

            await self._place_order(o)

    async def setup_hook(self) -> None:
        # Initialize db
        async with engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)

        # Initialize shioaji api
        api = sj.Shioaji(CONFIG.simulation)
        api.login(api_key=CONFIG.shioaji_api_key, secret_key=CONFIG.shioaji_api_secret)
        api.activate_ca(
            ca_path=CONFIG.ca_path, ca_passwd=CONFIG.ca_password, person_id=CONFIG.ca_person_id
        )
        self.shioaji = api
        logger.info(f"Initialized shioaji api with simulation={CONFIG.simulation}")

        # Add persistent view
        self.add_view(OrderView())
