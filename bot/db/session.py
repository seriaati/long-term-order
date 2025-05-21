from __future__ import annotations

from typing import Any

from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel.ext.asyncio.session import AsyncSession

from bot.config import CONFIG

engine = create_async_engine(CONFIG.db_url)


class DatabaseSession:
    """A database session manager for async applications."""

    @staticmethod
    async def get_session() -> AsyncSession:
        """Create and return a new database session."""
        return AsyncSession(engine, autocommit=False, autoflush=False, expire_on_commit=False)

    @staticmethod
    async def commit_session(session: AsyncSession) -> None:
        """Commit the session and close it."""
        try:
            await session.commit()
        finally:
            await session.close()

    @staticmethod
    async def rollback_session(session: AsyncSession) -> None:
        """Rollback the session and close it."""
        try:
            await session.rollback()
        finally:
            await session.close()


class AsyncSessionContext:
    def __init__(self) -> None:
        self.session: AsyncSession | None = None

    async def __aenter__(self) -> AsyncSession:
        self.session = await DatabaseSession.get_session()
        return self.session

    async def __aexit__(self, exc_type: type[Exception] | None, *args: Any) -> None:
        if self.session is not None:
            if exc_type is not None:
                await DatabaseSession.rollback_session(self.session)
            else:
                await DatabaseSession.commit_session(self.session)


def get_db() -> AsyncSessionContext:
    return AsyncSessionContext()
