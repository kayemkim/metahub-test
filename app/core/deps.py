from typing import AsyncIterator
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends

from app.db.session import AsyncSessionLocal, get_session as legacy_get_session
from app.core.database import _current_session

__all__ = ["get_session", "get_repository_session"]


async def get_session() -> AsyncIterator[AsyncSession]:
    """
    FastAPI dependency for request-scoped session
    Used by services with @transactional decorator
    """
    session = AsyncSessionLocal()
    token = _current_session.set(session)
    try:
        yield session
    finally:
        _current_session.reset(token)
        await session.close()


async def get_repository_session() -> AsyncSession:
    """
    Get current session from context (for repositories)
    This should only be used within @transactional decorated functions
    """
    session = _current_session.get()
    if session is None:
        raise RuntimeError("No active session found. Make sure to call this within @transactional decorated function.")
    return session


# Keep legacy for backward compatibility
get_legacy_session = legacy_get_session
