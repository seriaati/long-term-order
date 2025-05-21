from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any

from bot.config import CONFIG
from bot.logging import setup_logging
from bot.main import Bot
from bot.ui import OrderView

if TYPE_CHECKING:
    from discord.ext import commands


bot = Bot()


@bot.command(name="view")
async def view(ctx: commands.Context) -> Any:
    await ctx.send(view=OrderView())


@bot.command(name="task")
async def task(ctx: commands.Context) -> Any:
    message = await ctx.send("Place orders task started")
    await bot.place_orders()
    await message.edit(content="Place orders task finished")


setup_logging()
asyncio.run(bot.start(CONFIG.discord_token))
