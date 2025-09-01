"""
Spring @Transactional style transaction management for FastAPI + SQLAlchemy 2.0
"""
import asyncio
import logging
from collections.abc import Callable
from contextvars import ContextVar
from functools import wraps
from typing import Any, Literal, TypeVar

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import AsyncSessionLocal

logger = logging.getLogger(__name__)

# Context variable to hold current session (thread-safe for async)
_current_session: ContextVar[AsyncSession | None] = ContextVar("current_session", default=None)

F = TypeVar("F", bound=Callable[..., Any])


def get_current_session() -> AsyncSession | None:
    """Get current session from context"""
    return _current_session.get()


def transactional(
    propagation: Literal["required", "requires_new", "nested"] = "required",
    read_only: bool = False,
) -> Callable[[F], F]:
    """
    Spring @Transactional style decorator for SQLAlchemy async
    
    Args:
        propagation: Transaction propagation behavior
            - "required": Join existing transaction or create new one (default)
            - "requires_new": Always create new transaction (independent)
            - "nested": Create savepoint within existing transaction
        read_only: If True, rollback instead of commit (for read operations)
    
    Usage:
        @transactional()
        async def create_user(name: str, email: str):
            # Business logic here - automatic commit/rollback
            pass
            
        @transactional(read_only=True)
        async def get_users():
            # Read-only operations
            pass
    """
    def decorator(func: F) -> F:
        if not asyncio.iscoroutinefunction(func):
            raise TypeError("@transactional can only be applied to async functions")

        @wraps(func)
        async def wrapper(*args, **kwargs):
            existing = get_current_session()
            use_new = (propagation == "requires_new" or
                      existing is None or
                      (read_only and propagation == "required" and existing is not None))

            session: AsyncSession
            token = None
            created_here = False

            if use_new:
                session = AsyncSessionLocal()
                token = _current_session.set(session)
                created_here = True
                logger.debug(f"Created new session for {func.__name__}")
            else:
                session = existing  # type: ignore[assignment]
                logger.debug(f"Reusing existing session for {func.__name__}")

            try:
                # Handle nested transactions with savepoints
                if propagation == "nested" and not use_new:
                    async with session.begin_nested():
                        logger.debug(f"Starting nested transaction for {func.__name__}")
                        result = await func(*args, **kwargs)
                        logger.debug(f"Nested transaction completed for {func.__name__}")
                    return result

                # Execute business logic
                result = await func(*args, **kwargs)

                # Handle commit/rollback for session created here
                if created_here:
                    if read_only:
                        logger.debug(f"Rolling back read-only transaction for {func.__name__}")
                        await session.rollback()
                    else:
                        logger.debug(f"Committing transaction for {func.__name__}")
                        await session.commit()
                elif read_only and propagation == "requires_new":
                    logger.debug(f"Rolling back requires_new read-only transaction for {func.__name__}")
                    await session.rollback()

                return result

            except Exception as e:
                logger.error(f"Transaction failed in {func.__name__}: {e}")
                try:
                    if session.in_transaction():
                        await session.rollback()
                        logger.debug(f"Rolled back transaction for {func.__name__}")
                except Exception as rollback_error:
                    logger.error(f"Rollback failed in {func.__name__}: {rollback_error}")
                raise
            finally:
                if created_here:
                    await session.close()
                    logger.debug(f"Closed session for {func.__name__}")
                    if token is not None:
                        _current_session.reset(token)

        return wrapper  # type: ignore[return-value]
    return decorator
