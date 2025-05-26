from __future__ import annotations

from typing import TYPE_CHECKING, Any

import discord
from discord import ui

from bot.utils import get_shioaji, get_stock_name

if TYPE_CHECKING:
    from collections.abc import Sequence

    from shioaji.contracts import StreamStockContracts
    from shioaji.order import Trade

    from bot.types import Interaction


class TradeDeleteConfirmView(ui.View):
    def __init__(self, trade: Trade) -> None:
        super().__init__(timeout=None)
        self.trade = trade

    @ui.button(label="確認取消", style=discord.ButtonStyle.danger, custom_id="confirm_delete")
    async def confirm_delete(self, i: Interaction, _: ui.Button) -> Any:
        await i.response.defer()

        api = await get_shioaji()
        await api.cancel_order(self.trade)
        await i.edit_original_response(content="預約單已取消", view=None)

    @ui.button(label="取消", style=discord.ButtonStyle.secondary, custom_id="cancel_delete")
    async def cancel_delete(self, i: Interaction, _: ui.Button) -> Any:
        await i.response.edit_message(content="已取消", view=None, embed=None)


class TradeManageView(ui.View):
    def __init__(self, trades: Sequence[Trade], stocks: StreamStockContracts) -> None:
        super().__init__(timeout=None)
        self.trade = trades[0]
        self.stocks = stocks

        self.add_item(TradeSelect(trades=trades, stocks=stocks))

    @ui.button(label="取消", style=discord.ButtonStyle.danger, custom_id="delete_trade", row=1)
    async def delete_trade(self, i: Interaction, _: ui.Button) -> Any:
        view = TradeDeleteConfirmView(self.trade)
        await i.response.edit_message(content="你確定要取消這個預約單嗎?", view=view)


class TradeSelect(ui.Select):
    def __init__(self, trades: Sequence[Trade], stocks: StreamStockContracts) -> None:
        super().__init__(
            options=[
                discord.SelectOption(
                    label=f"{t.order.id} | [{t.contract.code}] {get_stock_name(t.contract.code, stocks)}",
                    description=f"價格: {t.order.price}, 數量: {t.order.quantity}",
                    value=t.order.id,
                    default=t.order.id == trades[0].order.id,
                )
                for t in trades
            ],
            placeholder="選擇一個預約單",
            custom_id="trade_select",
        )
        self.trades = trades
        self.stocks = stocks

    @staticmethod
    def get_embed(trade: Trade, stocks: StreamStockContracts) -> discord.Embed:
        embed = discord.Embed(title="預約單詳情", color=discord.Color.purple())
        embed.add_field(name="預約單 ID", value=str(trade.order.id), inline=False)
        embed.add_field(
            name="股票",
            value=f"[{trade.contract.code}] {get_stock_name(trade.contract.code, stocks)}",
            inline=False,
        )
        embed.add_field(name="價格", value=str(trade.order.price), inline=False)
        embed.add_field(name="數量", value=str(trade.order.quantity), inline=False)
        return embed

    async def callback(self, i: Interaction) -> Any:
        self.view: TradeManageView
        await i.response.defer()

        for o in self.options:
            o.default = o.value in self.values

        trade = next((t for t in self.trades if t.order.id == self.values[0]), None)
        if trade is None:
            await i.response.send_message("找不到該預約單", ephemeral=True)
            return

        self.view.trade = trade
        embed = self.get_embed(trade, self.stocks)
        await i.edit_original_response(embed=embed, view=self.view)
