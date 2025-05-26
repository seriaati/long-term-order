from __future__ import annotations

from typing import TYPE_CHECKING, Any

import discord
import shioaji.constant as sjc
from discord import ui
from loguru import logger

from bot.db.models.order import Order
from bot.ui.order import OrderManageView, OrderModal, OrderSelect
from bot.ui.trade import TradeManageView, TradeSelect
from bot.utils import get_shioaji

if TYPE_CHECKING:
    from bot.types import Interaction


class MainView(ui.View):
    def __init__(self) -> None:
        super().__init__(timeout=None)

    @ui.button(label="下長效單", style=discord.ButtonStyle.primary, custom_id="order_long")
    async def place_order(self, i: Interaction, _: ui.Button) -> Any:
        modal = OrderModal(title="填寫下單資訊")
        await i.response.send_modal(modal)

        timed_out = await modal.wait()
        if timed_out:
            return

        # Validate inputs
        try:
            price = float(modal.price.value)
        except ValueError:
            await i.followup.send("價格必須是數字", ephemeral=True)
            return

        try:
            quantity = int(modal.quantity.value)
        except ValueError:
            await i.followup.send("數量必須是整數", ephemeral=True)
            return

        if quantity <= 0:
            await i.followup.send("數量必須大於 0", ephemeral=True)
            return

        if price <= 0:
            await i.followup.send("價格必須大於 0", ephemeral=True)
            return

        stock_id = modal.stock_id.value

        logger.info(f"Recieved modal values: {stock_id=}, {price=}, {quantity=}")

        api = await get_shioaji()
        stock = api.get_stock(stock_id)
        if stock is None:
            await i.followup.send(f"找不到代號為 {stock_id} 的股票", ephemeral=True)
            return

        existing = await Order.get_or_none(stock_id)
        if existing is not None:
            order = await Order.update(stock_id, price=price, quantity=quantity)
            logger.info(f"Updated order: {order}")
        else:
            order = await Order.create(stock_id=stock_id, price=price, quantity=quantity)
            logger.info(f"Created order: {order}")

        embed = discord.Embed(title="下單成功", color=discord.Color.green())
        embed.add_field(name="股票", value=f"[{stock.code}] {stock.name}")
        embed.add_field(name="價格", value=str(order.price))
        embed.add_field(name="數量", value=str(order.quantity))

        await i.followup.send(embed=embed, ephemeral=True)

    @ui.button(label="查看所有長效單", style=discord.ButtonStyle.secondary, custom_id="view_orders")
    async def view_orders(self, i: Interaction, _: ui.Button) -> Any:
        await i.response.send_message(content="稍等, 正在獲取長效單", ephemeral=True)

        orders = await Order.all()
        if not orders:
            await i.edit_original_response(content="目前沒有任何長效單")
            return

        api = await get_shioaji()
        view = OrderManageView(orders, api.Contracts.Stocks)
        await i.edit_original_response(
            embed=OrderSelect.get_embed(view.order, api.Contracts.Stocks), view=view, content=None
        )

    @ui.button(label="查看所有預約單", style=discord.ButtonStyle.secondary, custom_id="view_trades")
    async def view_trades(self, i: Interaction, _: ui.Button) -> Any:
        await i.response.send_message(content="稍等, 正在獲取預約單", ephemeral=True)

        api = await get_shioaji()
        await api.update_status()

        trades = await api.list_trades()
        trades = [t for t in trades if t.status.status == sjc.Status.PreSubmitted]
        if not trades:
            await i.edit_original_response(content="目前沒有任何預約單")
            return

        view = TradeManageView(trades, api.Contracts.Stocks)
        await i.edit_original_response(
            embed=TradeSelect.get_embed(view.trade, api.Contracts.Stocks), view=view, content=None
        )
