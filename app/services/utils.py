from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession


async def _next_version_no(session: AsyncSession, table, filter_col: str, filter_val) -> int:
    """Get the next version number for a versioned entity"""
    stmt = select(func.coalesce(func.max(table.version_no), 0)).where(getattr(table, filter_col) == filter_val)
    res = await session.execute(stmt)
    return int(res.scalar_one() or 0) + 1
