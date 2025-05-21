from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import discord
import shioaji as sj
from discord.ext import commands
from loguru import logger
from sqlmodel import SQLModel

from bot.config import CONFIG
from bot.db.session import engine
from bot.ui import OrderView

if TYPE_CHECKING:
    from shioaji.contracts import Contract


class Bot(commands.Bot):
    def __init__(self) -> None:
        super().__init__(commands.when_mentioned, intents=discord.Intents.default())
        self.shioaji: sj.Shioaji

    def get_contract(self, stock_id: str) -> Contract | None:
        api = self.shioaji
        contract = api.Contracts.Stocks.get(stock_id)
        if contract is None:
            logger.warning(f"Contract {stock_id} not found")
            return None
        return contract

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

        # Load cogs
        for filepath in Path("bot/cogs").glob("**/*.py"):
            cog_name = Path(filepath).stem
            try:
                await self.load_extension(f"bot.cogs.{cog_name}")
                logger.info(f"Loaded cog {cog_name!r}")
            except Exception:
                logger.exception(f"Failed to load cog {cog_name!r}")

        # Add persistent view
        self.add_view(OrderView())
