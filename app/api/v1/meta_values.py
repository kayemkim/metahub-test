from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.deps import get_session
from app.models.meta_values import CustomMetaValue, CustomMetaValueVersion, CustomMetaValueVersionTerm
from app.models.meta_types import CustomMetaItem, CustomMetaType
from app.models.codeset import Code, CodeVersion
from app.models.taxonomy import Term
from app.schemas.base import (
    MetaValueCode,
    MetaValuePrimitive,
    MetaValueTaxMulti,
    MetaValueTaxSingle,
    MetaValueWithVersionOut,
    MetaValueVersionOut,
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


@router.get("/{target_type}/{target_id}", response_model=list[MetaValueWithVersionOut])
async def get_meta_values_for_target(
    target_type: str,
    target_id: str,
    session: AsyncSession = Depends(get_session)
):
    """Get all meta values for a specific target"""
    try:
        # Query meta values with their current versions and related data
        stmt = select(CustomMetaValue).options(
            selectinload(CustomMetaValue.item).selectinload(CustomMetaItem.type),
            selectinload(CustomMetaValue.current_version)
        ).where(
            CustomMetaValue.target_type == target_type,
            CustomMetaValue.target_id == target_id
        )
        
        result = await session.execute(stmt)
        meta_values = result.scalars().all()
        
        response_values = []
        
        for meta_value in meta_values:
            # Get current version details
            current_version_data = None
            if meta_value.current_version_id:
                # Get the current version with all related data
                version_stmt = select(CustomMetaValueVersion).where(
                    CustomMetaValueVersion.version_id == meta_value.current_version_id
                )
                version_result = await session.execute(version_stmt)
                current_version = version_result.scalar_one_or_none()
                
                if current_version:
                    # Build version output based on type
                    version_data = {
                        "version_id": current_version.version_id,
                        "version_no": current_version.version_no,
                        "valid_from": current_version.valid_from,
                        "valid_to": current_version.valid_to,
                        "author": current_version.author,
                        "reason": current_version.reason,
                    }
                    
                    if meta_value.item.type.type_kind == "PRIMITIVE":
                        version_data["value_json"] = current_version.value_json
                    
                    elif meta_value.item.type.type_kind == "CODESET":
                        if current_version.code_id:
                            # Get code details
                            code_stmt = select(Code).options(
                                selectinload(Code.current_version)
                            ).where(Code.code_id == current_version.code_id)
                            code_result = await session.execute(code_stmt)
                            code = code_result.scalar_one_or_none()
                            
                            if code:
                                version_data["code_id"] = code.code_id
                                version_data["code_key"] = code.code_key
                                if code.current_version:
                                    version_data["code_label"] = code.current_version.label_default
                    
                    elif meta_value.item.type.type_kind == "TAXONOMY":
                        if meta_value.item.selection_mode == "SINGLE":
                            if current_version.taxonomy_term_id:
                                # Get single term details
                                term_stmt = select(Term).where(Term.term_id == current_version.taxonomy_term_id)
                                term_result = await session.execute(term_stmt)
                                term = term_result.scalar_one_or_none()
                                
                                if term:
                                    version_data["taxonomy_term_id"] = term.term_id
                                    version_data["term_key"] = term.term_key
                                    version_data["term_display_name"] = term.display_name
                        
                        else:  # MULTI selection
                            # Get multi-term details
                            multi_terms_stmt = select(CustomMetaValueVersionTerm).options(
                                selectinload(CustomMetaValueVersionTerm.term)
                            ).where(CustomMetaValueVersionTerm.version_id == current_version.version_id)
                            
                            multi_terms_result = await session.execute(multi_terms_stmt)
                            multi_terms = multi_terms_result.scalars().all()
                            
                            if multi_terms:
                                version_data["term_keys"] = [mt.term.term_key for mt in multi_terms]
                                version_data["term_display_names"] = [mt.term.display_name for mt in multi_terms]
                    
                    current_version_data = MetaValueVersionOut(**version_data)
            
            # Build response object
            response_value = MetaValueWithVersionOut(
                value_id=meta_value.value_id,
                target_type=meta_value.target_type,
                target_id=meta_value.target_id,
                item_id=meta_value.item_id,
                item_code=meta_value.item.item_code,
                item_display_name=meta_value.item.display_name,
                type_kind=meta_value.item.type.type_kind,
                created_at=meta_value.created_at,
                current_version=current_version_data
            )
            response_values.append(response_value)
        
        return response_values
        
    except Exception as e:
        raise HTTPException(500, f"Failed to retrieve meta values: {str(e)}")


@router.get("/{target_type}/{target_id}/{item_code}", response_model=MetaValueWithVersionOut)
async def get_meta_value_for_target_and_item(
    target_type: str,
    target_id: str,
    item_code: str,
    session: AsyncSession = Depends(get_session)
):
    """Get a specific meta value for target and item"""
    try:
        # First get the item by code
        item_stmt = select(CustomMetaItem).options(
            selectinload(CustomMetaItem.type)
        ).where(CustomMetaItem.item_code == item_code)
        
        item_result = await session.execute(item_stmt)
        item = item_result.scalar_one_or_none()
        
        if not item:
            raise HTTPException(404, f"Meta item '{item_code}' not found")
        
        # Query meta value
        stmt = select(CustomMetaValue).where(
            CustomMetaValue.target_type == target_type,
            CustomMetaValue.target_id == target_id,
            CustomMetaValue.item_id == item.item_id
        )
        
        result = await session.execute(stmt)
        meta_value = result.scalar_one_or_none()
        
        if not meta_value:
            raise HTTPException(404, f"Meta value not found for target {target_type}:{target_id} and item {item_code}")
        
        # Get current version details (same logic as above)
        current_version_data = None
        if meta_value.current_version_id:
            version_stmt = select(CustomMetaValueVersion).where(
                CustomMetaValueVersion.version_id == meta_value.current_version_id
            )
            version_result = await session.execute(version_stmt)
            current_version = version_result.scalar_one_or_none()
            
            if current_version:
                version_data = {
                    "version_id": current_version.version_id,
                    "version_no": current_version.version_no,
                    "valid_from": current_version.valid_from,
                    "valid_to": current_version.valid_to,
                    "author": current_version.author,
                    "reason": current_version.reason,
                }
                
                if item.type.type_kind == "PRIMITIVE":
                    version_data["value_json"] = current_version.value_json
                
                elif item.type.type_kind == "CODESET":
                    if current_version.code_id:
                        code_stmt = select(Code).options(
                            selectinload(Code.current_version)
                        ).where(Code.code_id == current_version.code_id)
                        code_result = await session.execute(code_stmt)
                        code = code_result.scalar_one_or_none()
                        
                        if code:
                            version_data["code_id"] = code.code_id
                            version_data["code_key"] = code.code_key
                            if code.current_version:
                                version_data["code_label"] = code.current_version.label_default
                
                elif item.type.type_kind == "TAXONOMY":
                    if item.selection_mode == "SINGLE":
                        if current_version.taxonomy_term_id:
                            term_stmt = select(Term).where(Term.term_id == current_version.taxonomy_term_id)
                            term_result = await session.execute(term_stmt)
                            term = term_result.scalar_one_or_none()
                            
                            if term:
                                version_data["taxonomy_term_id"] = term.term_id
                                version_data["term_key"] = term.term_key
                                version_data["term_display_name"] = term.display_name
                    
                    else:  # MULTI selection
                        multi_terms_stmt = select(CustomMetaValueVersionTerm).options(
                            selectinload(CustomMetaValueVersionTerm.term)
                        ).where(CustomMetaValueVersionTerm.version_id == current_version.version_id)
                        
                        multi_terms_result = await session.execute(multi_terms_stmt)
                        multi_terms = multi_terms_result.scalars().all()
                        
                        if multi_terms:
                            version_data["term_keys"] = [mt.term.term_key for mt in multi_terms]
                            version_data["term_display_names"] = [mt.term.display_name for mt in multi_terms]
                
                current_version_data = MetaValueVersionOut(**version_data)
        
        return MetaValueWithVersionOut(
            value_id=meta_value.value_id,
            target_type=meta_value.target_type,
            target_id=meta_value.target_id,
            item_id=meta_value.item_id,
            item_code=item.item_code,
            item_display_name=item.display_name,
            type_kind=item.type.type_kind,
            created_at=meta_value.created_at,
            current_version=current_version_data
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Failed to retrieve meta value: {str(e)}")
