from __future__ import annotations

from typing import TYPE_CHECKING

import sqlmodel

from bot.db.models.base import BaseModel
from bot.db.session import get_db

if TYPE_CHECKING:
    from collections.abc import Sequence
    from types import EllipsisType


class Order(BaseModel, table=True):
    stock_id: str = sqlmodel.Field(primary_key=True)
    price: float
    quantity: int

    @classmethod
    async def get_or_none(cls, stock_id: str) -> Order | None:
        async with get_db() as db:
            order = await db.exec(sqlmodel.select(cls).where(cls.stock_id == stock_id))

        return order.first()

    @classmethod
    async def create(cls, *, stock_id: str, price: float, quantity: int) -> Order:
        order = cls(stock_id=stock_id, price=price, quantity=quantity)
        async with get_db() as db:
            db.add(order)
            await db.commit()
            await db.refresh(order)

        return order

    @classmethod
    async def all(cls) -> Sequence[Order]:
        async with get_db() as db:
            orders = await db.exec(sqlmodel.select(cls))

        return orders.all()

    @classmethod
    async def update(
        cls, stock_id: str, *, price: float | EllipsisType = ..., quantity: int | EllipsisType = ...
    ) -> Order:
        async with get_db() as db:
            order = await cls.get_or_none(stock_id)
            if order is None:
                msg = f"Order with stock_id {stock_id} not found"
                raise ValueError(msg)

            if price is not ...:
                order.price = price
            if quantity is not ...:
                order.quantity = quantity

            await db.commit()
            await db.refresh(order)

        return order

    async def delete(self) -> None:
        async with get_db() as db:
            await db.delete(self)
            await db.commit()
