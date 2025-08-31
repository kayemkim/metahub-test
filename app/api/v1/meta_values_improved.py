"""
Improved meta values API with Spring @Transactional style architecture
Repository ← Service ← API with dependency injection
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_session, get_repository_session
from app.core.database import get_current_session
from app.repositories.meta_value_repository import MetaValueRepository
from app.services.meta_value_business_service import MetaValueBusinessService
from app.schemas.base import (
    MetaValuePrimitive,
    MetaValueString, 
    MetaValueCode,
    MetaValueTaxSingle,
    MetaValueTaxMulti
)

router = APIRouter(prefix="/meta-values", tags=["meta-values-improved"])


# Dependency injection chain
def get_meta_value_repository() -> MetaValueRepository:
    """Get repository with current session from context"""
    session = get_current_session()
    if session is None:
        raise RuntimeError("No active session in context. This should be called within @transactional function.")
    return MetaValueRepository(session)


def get_meta_value_service(
    repo: MetaValueRepository = Depends(get_meta_value_repository)
) -> MetaValueBusinessService:
    """Get business service with injected repository"""
    return MetaValueBusinessService(repo)


# API Endpoints - Clean and simple!
@router.put("/{target_type}/{target_id}/primitive/{item_code}")
async def set_primitive_value(
    target_type: str,
    target_id: str,
    item_code: str,
    data: MetaValuePrimitive,
    session: AsyncSession = Depends(get_session),  # Sets context
    service: MetaValueBusinessService = Depends(get_meta_value_service)
):
    """Set primitive meta value - transaction handled by service @transactional"""
    try:
        version_id = await service.set_primitive_value(target_type, target_id, item_code, data)
        return {"version_id": version_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Unexpected error: {str(e)}")


@router.put("/{target_type}/{target_id}/string/{item_code}")
async def set_string_value(
    target_type: str,
    target_id: str,
    item_code: str,
    data: MetaValueString,
    session: AsyncSession = Depends(get_session),  # Sets context
    service: MetaValueBusinessService = Depends(get_meta_value_service)
):
    """Set string meta value - transaction handled by service @transactional"""
    try:
        version_id = await service.set_string_value(target_type, target_id, item_code, data)
        return {"version_id": version_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Unexpected error: {str(e)}")


@router.put("/{target_type}/{target_id}/codeset/{item_code}")
async def set_codeset_value(
    target_type: str,
    target_id: str,
    item_code: str,
    data: MetaValueCode,
    session: AsyncSession = Depends(get_session),  # Sets context
    service: MetaValueBusinessService = Depends(get_meta_value_service)
):
    """Set codeset meta value - transaction handled by service @transactional"""
    try:
        version_id = await service.set_codeset_value(target_type, target_id, item_code, data)
        return {"version_id": version_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Unexpected error: {str(e)}")


@router.put("/{target_type}/{target_id}/taxonomy-single/{item_code}")
async def set_taxonomy_single_value(
    target_type: str,
    target_id: str,
    item_code: str,
    data: MetaValueTaxSingle,
    session: AsyncSession = Depends(get_session),  # Sets context
    service: MetaValueBusinessService = Depends(get_meta_value_service)
):
    """Set single taxonomy meta value - transaction handled by service @transactional"""
    try:
        version_id = await service.set_taxonomy_single_value(target_type, target_id, item_code, data)
        return {"version_id": version_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Unexpected error: {str(e)}")


@router.put("/{target_type}/{target_id}/taxonomy-multi/{item_code}")
async def set_taxonomy_multi_value(
    target_type: str,
    target_id: str,
    item_code: str,
    data: MetaValueTaxMulti,
    session: AsyncSession = Depends(get_session),  # Sets context
    service: MetaValueBusinessService = Depends(get_meta_value_service)
):
    """Set multiple taxonomy meta values - transaction handled by service @transactional"""
    try:
        version_id = await service.set_taxonomy_multi_value(target_type, target_id, item_code, data)
        return {"version_id": version_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Unexpected error: {str(e)}")


@router.get("/{target_type}/{target_id}")
async def get_meta_values_for_target(
    target_type: str,
    target_id: str,
    session: AsyncSession = Depends(get_session),  # Sets context
    service: MetaValueBusinessService = Depends(get_meta_value_service)
):
    """Get all meta values for target - read-only transaction"""
    try:
        values = await service.get_meta_values_for_target(target_type, target_id)
        return values
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Unexpected error: {str(e)}")


# Example of batch operation with single transaction
@router.post("/{target_type}/{target_id}/batch")
async def set_multiple_values(
    target_type: str,
    target_id: str,
    values: dict,  # Complex payload with multiple meta values
    session: AsyncSession = Depends(get_session),
    service: MetaValueBusinessService = Depends(get_meta_value_service)
):
    """
    Example: Set multiple meta values in single transaction
    This demonstrates the power of @transactional decorator
    """
    try:
        # Service method with @transactional will handle all operations in single transaction
        results = await service.set_multiple_values(target_type, target_id, values)
        return results
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Unexpected error: {str(e)}")