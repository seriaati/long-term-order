from __future__ import annotations

import asyncio
import contextlib

from bot.config import CONFIG
from bot.logging import setup_logging
from bot.main import Bot


async def main() -> None:
    async with Bot() as bot:
        with contextlib.suppress(KeyboardInterrupt, asyncio.CancelledError):
            await bot.start(CONFIG.discord_token)


if __name__ == "__main__":
    setup_logging()
    asyncio.run(main())
