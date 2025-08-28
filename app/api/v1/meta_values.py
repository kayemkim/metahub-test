from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_session
from app.schemas.base import (
    MetaValueCode,
    MetaValuePrimitive,
    MetaValueTaxMulti,
    MetaValueTaxSingle,
)
from app.services.meta_value_service import (
    set_meta_value_codeset,
    set_meta_value_primitive,
    set_meta_value_taxonomy_multi,
    set_meta_value_taxonomy_single,
)

router = APIRouter(prefix="/meta-values", tags=["meta-values"])


@router.put("/{target_type}/{target_id}/primitive/{item_code}")
async def set_primitive_value(
    target_type: str,
    target_id: str,
    item_code: str,
    data: MetaValuePrimitive,
    session: AsyncSession = Depends(get_session)
):
    """Set a primitive meta value for a target"""
    try:
        version_id = await set_meta_value_primitive(
            session,
            target_type=target_type,
            target_id=target_id,
            item_code=item_code,
            payload=data
        )
        return {"version_id": version_id}
    except Exception as e:
        if "not found" in str(e).lower():
            raise HTTPException(404, str(e))
        if "not PRIMITIVE" in str(e):
            raise HTTPException(400, str(e))
        raise HTTPException(500, str(e))


@router.put("/{target_type}/{target_id}/codeset/{item_code}")
async def set_codeset_value(
    target_type: str,
    target_id: str,
    item_code: str,
    data: MetaValueCode,
    session: AsyncSession = Depends(get_session)
):
    """Set a codeset meta value for a target"""
    try:
        version_id = await set_meta_value_codeset(
            session,
            target_type=target_type,
            target_id=target_id,
            item_code=item_code,
            payload=data
        )
        return {"version_id": version_id}
    except Exception as e:
        if "not found" in str(e).lower():
            raise HTTPException(404, str(e))
        if "not CODESET" in str(e):
            raise HTTPException(400, str(e))
        if "invalid code" in str(e).lower():
            raise HTTPException(400, str(e))
        raise HTTPException(500, str(e))


@router.put("/{target_type}/{target_id}/taxonomy-single/{item_code}")
async def set_taxonomy_single_value(
    target_type: str,
    target_id: str,
    item_code: str,
    data: MetaValueTaxSingle,
    session: AsyncSession = Depends(get_session)
):
    """Set a single taxonomy meta value for a target"""
    try:
        version_id = await set_meta_value_taxonomy_single(
            session,
            target_type=target_type,
            target_id=target_id,
            item_code=item_code,
            payload=data
        )
        return {"version_id": version_id}
    except Exception as e:
        if "not found" in str(e).lower():
            raise HTTPException(404, str(e))
        if "not TAXONOMY" in str(e):
            raise HTTPException(400, str(e))
        if "must be SINGLE" in str(e):
            raise HTTPException(400, str(e))
        if "invalid term" in str(e).lower():
            raise HTTPException(400, str(e))
        raise HTTPException(500, str(e))


@router.put("/{target_type}/{target_id}/taxonomy-multi/{item_code}")
async def set_taxonomy_multi_value(
    target_type: str,
    target_id: str,
    item_code: str,
    data: MetaValueTaxMulti,
    session: AsyncSession = Depends(get_session)
):
    """Set multiple taxonomy meta values for a target"""
    try:
        version_id = await set_meta_value_taxonomy_multi(
            session,
            target_type=target_type,
            target_id=target_id,
            item_code=item_code,
            payload=data
        )
        return {"version_id": version_id}
    except Exception as e:
        if "not found" in str(e).lower():
            raise HTTPException(404, str(e))
        if "not TAXONOMY" in str(e):
            raise HTTPException(400, str(e))
        if "must be MULTI" in str(e):
            raise HTTPException(400, str(e))
        if "invalid term" in str(e).lower():
            raise HTTPException(400, str(e))
        raise HTTPException(500, str(e))
