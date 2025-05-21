from __future__ import annotations

from typing import TYPE_CHECKING, Any

import discord
from discord import ui
from loguru import logger

from bot.db.models.order import Order

if TYPE_CHECKING:
    from bot.types import Interaction


class OrderModal(ui.Modal):
    stock_id = ui.TextInput(label="股票代號", placeholder="2330", max_length=5)
    price = ui.TextInput(label="價格", placeholder="28.3", max_length=5)
    quantity = ui.TextInput(label="數量", placeholder="1", max_length=2, default="1")

    async def on_submit(self, i: Interaction) -> Any:
        await i.response.defer()
        self.stop()


class OrderView(ui.View):
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

        contract = i.client.get_contract(stock_id)
        if contract is None:
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
        embed.add_field(name="股票", value=f"[{contract.code}] {contract.name}")
        embed.add_field(name="價格", value=str(order.price))
        embed.add_field(name="數量", value=str(order.quantity))

        await i.followup.send(embed=embed, ephemeral=True)
