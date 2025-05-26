from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import discord
from discord.ext import commands
from loguru import logger
from sqlmodel import SQLModel

from bot.db.session import engine
from bot.ui.main import MainView
from bot.utils import get_shioaji

if TYPE_CHECKING:
    from shioaji.contracts import Contract


class Bot(commands.Bot):
    def __init__(self) -> None:
        super().__init__(commands.when_mentioned, intents=discord.Intents.default())

    def get_contract(self, stock_id: str) -> Contract | None:
        api = get_shioaji()
        contract = api.Contracts.Stocks.get(stock_id)
        if contract is None:
            logger.warning(f"Contract {stock_id} not found")
            return None
        return contract

    async def setup_hook(self) -> None:
        # Initialize db
        async with engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)

        # Load cogs
        for filepath in Path("bot/cogs").glob("**/*.py"):
            cog_name = Path(filepath).stem
            try:
                await self.load_extension(f"bot.cogs.{cog_name}")
                logger.info(f"Loaded cog {cog_name!r}")
            except Exception:
                logger.exception(f"Failed to load cog {cog_name!r}")

        # Add persistent view
        self.add_view(MainView())
