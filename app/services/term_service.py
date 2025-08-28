import json

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import utcnow
from app.models.taxonomy import TermContent, TermContentVersion
from app.schemas.base import TermContentUpdate
from app.services.utils import _next_version_no


async def upsert_term_content(
    session: AsyncSession,
    term_id: str,
    payload: TermContentUpdate,
) -> str:
    """Create new content version for a term; maintain current pointer.
    Returns new content_version_id.
    """
    # Remove the session.begin() - let the caller handle transactions
    # Ensure container exists (one per term)
    res = await session.execute(select(TermContent).where(TermContent.term_id == term_id).with_for_update())
    content = res.scalar_one_or_none()
    if not content:
        content = TermContent(term_id=term_id)
        session.add(content)
        await session.flush()  # get content_id

    # Close previous current version (if any)
    if content.current_version_id:
        prev = await session.get(TermContentVersion, content.current_version_id, with_for_update=True)
        if prev and prev.valid_to is None:
            prev.valid_to = utcnow()

    # Create new version
    version_no = await _next_version_no(session, TermContentVersion, "content_id", content.content_id)
    v = TermContentVersion(
        content_id=content.content_id,
        version_no=version_no,
        body_markdown=payload.body_markdown,
        body_json=None if payload.body_json is None else json.dumps(payload.body_json),
        author=payload.author,
        change_reason=payload.reason,
    )
    session.add(v)
    await session.flush()

    # Move pointer
    content.current_version_id = v.content_version_id

    return v.content_version_id
