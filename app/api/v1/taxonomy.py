
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_session
from app.models import Term as TermModel
from app.models.taxonomy import Taxonomy
from app.schemas.base import (
    TaxonomyCreate,
    TaxonomyOut,
    TermContentIn,
    TermContentUpdate,
    TermOut,
)
from app.services.term_service import upsert_term_content

router = APIRouter(prefix="/taxonomy", tags=["taxonomy"])


@router.get("/{taxonomy_code}/terms", response_model=list[TermOut])
async def list_terms(taxonomy_code: str, session: AsyncSession = Depends(get_session)):
    """Get all terms in a taxonomy"""
    tax = (
        await session.execute(select(Taxonomy).where(Taxonomy.taxonomy_code == taxonomy_code))
    ).scalar_one_or_none()
    if not tax:
        raise HTTPException(404, "taxonomy not found")

    rows = (
        await session.execute(select(TermModel).where(TermModel.taxonomy_id == tax.taxonomy_id).order_by(TermModel.display_name))
    ).scalars().all()
    return [TermOut(term_id=r.term_id, term_key=r.term_key, display_name=r.display_name, parent_term_id=r.parent_term_id) for r in rows]


@router.get("/", response_model=list[TaxonomyOut])
async def list_taxonomies(session: AsyncSession = Depends(get_session)):
    """Get all taxonomies"""
    result = await session.execute(select(Taxonomy).order_by(Taxonomy.name))
    taxonomies = result.scalars().all()
    return [TaxonomyOut(
        taxonomy_id=tax.taxonomy_id,
        taxonomy_code=tax.taxonomy_code,
        name=tax.name,
        description=tax.description,
        created_at=tax.created_at
    ) for tax in taxonomies]


@router.get("/{taxonomy_code}", response_model=TaxonomyOut)
async def get_taxonomy(taxonomy_code: str, session: AsyncSession = Depends(get_session)):
    """Get a specific taxonomy by code"""
    result = await session.execute(
        select(Taxonomy).where(Taxonomy.taxonomy_code == taxonomy_code)
    )
    taxonomy = result.scalar_one_or_none()
    if not taxonomy:
        raise HTTPException(404, "taxonomy not found")

    return TaxonomyOut(
        taxonomy_id=taxonomy.taxonomy_id,
        taxonomy_code=taxonomy.taxonomy_code,
        name=taxonomy.name,
        description=taxonomy.description,
        created_at=taxonomy.created_at
    )


@router.post("/", response_model=TaxonomyOut)
async def create_taxonomy(data: TaxonomyCreate, session: AsyncSession = Depends(get_session)):
    """Create a new taxonomy"""
    # Check if taxonomy_code already exists
    existing = await session.execute(
        select(Taxonomy).where(Taxonomy.taxonomy_code == data.taxonomy_code)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(400, f"taxonomy with code '{data.taxonomy_code}' already exists")

    taxonomy = Taxonomy(
        taxonomy_code=data.taxonomy_code,
        name=data.name,
        description=data.description
    )
    session.add(taxonomy)
    await session.commit()
    await session.refresh(taxonomy)

    return TaxonomyOut(
        taxonomy_id=taxonomy.taxonomy_id,
        taxonomy_code=taxonomy.taxonomy_code,
        name=taxonomy.name,
        description=taxonomy.description,
        created_at=taxonomy.created_at
    )


@router.put("/terms/{term_id}/content")
async def put_term_content(term_id: str, body: TermContentIn, session: AsyncSession = Depends(get_session)):
    """Update term content with versioning"""
    # Ensure term exists
    term = await session.get(TermModel, term_id)
    if not term:
        raise HTTPException(404, "term not found")
    vid = await upsert_term_content(term_id, TermContentUpdate(**body.model_dump()))
    await session.commit()
    return {"content_version_id": vid}
