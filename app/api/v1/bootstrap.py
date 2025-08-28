from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_session
from app.services.bootstrap_service import bootstrap_demo

router = APIRouter(prefix="/bootstrap", tags=["bootstrap"])


@router.post("/demo")
async def create_demo_data(session: AsyncSession = Depends(get_session)):
    """Create demo data for testing and development"""
    await bootstrap_demo(session)
    await session.commit()

    return {
        "message": "Demo data created successfully",
        "created": {
            "taxonomies": 1,
            "terms": 2,
            "codesets": 1,
            "codes": 2,
            "meta_types": 3,
            "meta_groups": 1,
            "meta_items": 3
        }
    }


@router.get("/status")
async def check_bootstrap_status(session: AsyncSession = Depends(get_session)):
    """Check if demo data exists"""
    from sqlalchemy import func, select

    from app.models.codeset import CodeSet
    from app.models.meta_types import CustomMetaGroup, CustomMetaItem, CustomMetaType
    from app.models.taxonomy import Taxonomy

    # Count existing data
    taxonomy_count = (await session.execute(select(func.count(Taxonomy.taxonomy_id)))).scalar()
    codeset_count = (await session.execute(select(func.count(CodeSet.codeset_id)))).scalar()
    meta_type_count = (await session.execute(select(func.count(CustomMetaType.type_id)))).scalar()
    meta_group_count = (await session.execute(select(func.count(CustomMetaGroup.group_id)))).scalar()
    meta_item_count = (await session.execute(select(func.count(CustomMetaItem.item_id)))).scalar()

    return {
        "demo_data_exists": taxonomy_count > 0 or codeset_count > 0,
        "counts": {
            "taxonomies": taxonomy_count,
            "codesets": codeset_count,
            "meta_types": meta_type_count,
            "meta_groups": meta_group_count,
            "meta_items": meta_item_count
        }
    }
