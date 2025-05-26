from __future__ import annotations

from typing import TYPE_CHECKING

from loguru import logger

from bot.config import CONFIG
from bot.shioaji import AsyncShioaji

if TYPE_CHECKING:
    from types import EllipsisType

    from shioaji.contracts import StreamStockContracts


async def get_shioaji(simulation: bool | EllipsisType = ...) -> AsyncShioaji:
    simulation = simulation if simulation is not ... else CONFIG.simulation
    api = AsyncShioaji(simulation)
    await api.login(api_key=CONFIG.shioaji_api_key, secret_key=CONFIG.shioaji_api_secret)
    await api.activate_ca(
        ca_path=CONFIG.ca_path, ca_passwd=CONFIG.ca_password, person_id=CONFIG.ca_person_id
    )
    logger.info(f"Initialized shioaji api with simulation={simulation}")
    return api


def get_stock_name(stock_id: str, stocks: StreamStockContracts) -> str:
    contract = stocks.get(stock_id)
    if contract is None:
        return stock_id
    return contract.name
