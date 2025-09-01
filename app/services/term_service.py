import json

from sqlalchemy import select

from app.core.database import transactional
from app.core.deps import get_repository_session
from app.db.base import utcnow
from app.models.taxonomy import Term, TermVersion
from app.schemas.base import TermContentUpdate
from app.services.utils import _next_version_no


@transactional()
async def upsert_term_content(
    term_id: str,
    payload: TermContentUpdate,
) -> str:
    """Create new content version for a term; maintain current pointer.
    Returns new version_id.
    """
    session = await get_repository_session()

    # Get the term (must exist)
    term = await session.get(Term, term_id, with_for_update=True)
    if not term:
        raise ValueError(f"Term not found: {term_id}")

    # Close previous current version (if any)
    if term.current_version_id:
        prev = await session.get(TermVersion, term.current_version_id, with_for_update=True)
        if prev and prev.valid_to is None:
            prev.valid_to = utcnow()

    # Create new version
    version_no = await _next_version_no(session, TermVersion, "term_id", term_id)
    v = TermVersion(
        term_id=term_id,
        version_no=version_no,
        body_markdown=payload.body_markdown,
        body_json=None if payload.body_json is None else json.dumps(payload.body_json),
        author=payload.author,
        change_reason=payload.reason,
    )
    session.add(v)
    await session.flush()

    # Move pointer
    term.current_version_id = v.version_id

    return v.version_id
