from __future__ import annotations

import datetime
from typing import TYPE_CHECKING, Any

import shioaji.constant as sjc
from discord.ext import commands, tasks
from loguru import logger

from bot.config import CONFIG
from bot.db.models.order import Order
from bot.ui.main import MainView
from bot.utils import get_shioaji

if TYPE_CHECKING:
    from shioaji.contracts import Contract

    from bot.main import Bot
    from bot.shioaji import AsyncShioaji


class Cog(commands.Cog):
    def __init__(self, bot: Bot) -> None:
        self.bot = bot

    async def cog_load(self) -> None:
        self.place_orders.start()

    async def cog_unload(self) -> None:
        self.place_orders.cancel()

    def get_contract(self, api: AsyncShioaji, *, stock_id: str) -> Contract | None:
        contract = api.Contracts.Stocks.get(stock_id)
        if contract is None:
            logger.warning(f"Contract {stock_id} not found")
            return None
        return contract

    async def _place_order(self, api: AsyncShioaji, *, order: Order) -> None:
        contract = api.get_stock(order.stock_id)
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
        trade = await api.place_order(contract, order_obj)
        logger.info(f"Placed order: {trade}")

    @tasks.loop(
        time=datetime.time(hour=8, minute=30, tzinfo=datetime.timezone(datetime.timedelta(hours=8)))
    )
    async def place_orders(self) -> None:
        logger.info("Place orders task started")

        api = await get_shioaji()

        if not CONFIG.simulation:
            positions = await api.list_positions()
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

            await self._place_order(api, order=o)

    @place_orders.before_loop
    async def before_place_orders(self) -> None:
        await self.bot.wait_until_ready()

    @commands.is_owner()
    @commands.command(name="view")
    async def view(self, ctx: commands.Context) -> Any:
        await ctx.send(view=MainView())

    @commands.is_owner()
    @commands.command(name="task")
    async def task(self, ctx: commands.Context) -> Any:
        message = await ctx.send("Place orders task started")
        await self.place_orders()
        await message.edit(content="Place orders task finished")


async def setup(bot: Bot) -> None:
    await bot.add_cog(Cog(bot))
