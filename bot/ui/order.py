from __future__ import annotations

from typing import TYPE_CHECKING, Any

import discord
from discord import ui

from bot.utils import get_stock_name

if TYPE_CHECKING:
    from collections.abc import Sequence

    from shioaji.contracts import StreamStockContracts

    from bot.db.models.order import Order
    from bot.types import Interaction


class OrderModal(ui.Modal):
    stock_id = ui.TextInput(label="股票代號", placeholder="2330", max_length=5)
    price = ui.TextInput(label="價格", placeholder="28.3", max_length=5)
    quantity = ui.TextInput(label="數量", placeholder="1", max_length=2, default="1")

    async def on_submit(self, i: Interaction) -> Any:
        await i.response.defer()
        self.stop()


class OrderDeleteConfirmView(ui.View):
    def __init__(self, order: Order) -> None:
        super().__init__(timeout=None)
        self.order = order

    @ui.button(label="確認刪除", style=discord.ButtonStyle.danger, custom_id="confirm_delete")
    async def confirm_delete(self, i: Interaction, _: ui.Button) -> Any:
        await i.response.defer()
        await self.order.delete()
        await i.edit_original_response(content="長效單已刪除", view=None)

    @ui.button(label="取消", style=discord.ButtonStyle.secondary, custom_id="cancel_delete")
    async def cancel_delete(self, i: Interaction, _: ui.Button) -> Any:
        await i.response.edit_message(content="已取消", view=None, embed=None)


class OrderManageView(ui.View):
    def __init__(self, orders: Sequence[Order], stocks: StreamStockContracts) -> None:
        super().__init__(timeout=None)
        self.order = orders[0]
        self.stock_names = stocks

        self.add_item(OrderSelect(orders=orders, stocks=stocks))

    @ui.button(label="刪除", style=discord.ButtonStyle.danger, custom_id="delete_order", row=1)
    async def delete_order(self, i: Interaction, _: ui.Button) -> Any:
        view = OrderDeleteConfirmView(self.order)
        await i.response.edit_message(content="你確定要刪除這個長效單嗎?", view=view)


class OrderSelect(ui.Select):
    def __init__(self, orders: Sequence[Order], stocks: StreamStockContracts) -> None:
        super().__init__(
            options=[
                discord.SelectOption(
                    label=f"[{o.stock_id}] {get_stock_name(o.stock_id, stocks)}",
                    description=f"價格: {o.price}, 數量: {o.quantity}",
                    value=o.stock_id,
                    default=o.stock_id == orders[0].stock_id,
                )
                for o in orders
            ],
            placeholder="選擇一個長效單",
            custom_id="order_select",
        )
        self.order_or_trades = orders
        self.stocks = stocks

    @staticmethod
    def get_embed(order: Order, stocks: StreamStockContracts) -> discord.Embed:
        embed = discord.Embed(title="長效單詳情", color=discord.Color.blue())
        embed.add_field(
            name="股票", value=f"[{order.stock_id}] {get_stock_name(order.stock_id, stocks)}"
        )
        embed.add_field(name="價格", value=str(order.price))
        embed.add_field(name="數量", value=str(order.quantity))
        return embed

    async def callback(self, i: Interaction) -> Any:
        self.view: OrderManageView
        await i.response.defer()

        for o in self.options:
            o.default = o.value in self.values

        order = next((o for o in self.order_or_trades if o.stock_id == self.values[0]), None)
        if order is None:
            await i.response.send_message("找不到該長效單", ephemeral=True)
            return

        self.view.order = order
        embed = self.get_embed(order, self.stocks)
        await i.edit_original_response(embed=embed, view=self.view)
