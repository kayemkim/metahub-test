import json
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.deps import get_session
from app.core.meta_types import MetaTypeKind, get_meta_item_type_kind
from app.models.meta_types import CustomMetaItem
from app.models.meta_values import (
    CustomMetaValue,
    CustomMetaValueVersion,
)
from app.schemas.base import (
    MetaValueVersionOut,
    MetaValueWithVersionOut,
)
from app.services.meta_value_service import (
    get_meta_value_unified,
    set_meta_value_unified,
)

router = APIRouter(prefix="/meta-values", tags=["meta-values"])


class MetaValueUnified(BaseModel):
    """Unified meta value input model."""
    type: str
    value: Any | None = None  # For PRIMITIVE/STRING
    code_key: str | None = None  # For CODESET
    term_keys: list[str] | None = None  # For TAXONOMY
    selection_mode: str | None = None  # For TAXONOMY (SINGLE/MULTI)
    author: str | None = None
    reason: str | None = None


class MetaValueResponse(BaseModel):
    """Meta value response with unified format."""
    target_type: str
    target_id: str
    item_code: str
    value_data: dict[str, Any]


async def _parse_version_data_v2(session: AsyncSession, version: CustomMetaValueVersion, item_type_kind: MetaTypeKind) -> dict:
    """Parse version data from value_json (unified format)"""
    if not version.value_json:
        return {}

    try:
        data = json.loads(version.value_json)
        return data
    except (json.JSONDecodeError, KeyError):
        return {}


@router.put("/{target_type}/{target_id}/{item_code}")
async def set_meta_value(
    target_type: str,
    target_id: str,
    item_code: str,
    data: MetaValueUnified,
):
    """Set a meta value using unified JSON structure."""
    try:
        # Convert input to unified format
        value_data = {"type": data.type}

        if data.type in ["PRIMITIVE", "STRING"]:
            if data.value is None:
                raise HTTPException(400, f"{data.type} requires 'value' field")
            value_data["value"] = data.value

        elif data.type == "CODESET":
            if data.code_key is None:
                raise HTTPException(400, "CODESET requires 'code_key' field")
            value_data["code_key"] = data.code_key

        elif data.type == "TAXONOMY":
            if data.term_keys is None or len(data.term_keys) == 0:
                raise HTTPException(400, "TAXONOMY requires 'term_keys' field")
            value_data["term_keys"] = data.term_keys
            value_data["selection_mode"] = data.selection_mode or "SINGLE"

        else:
            raise HTTPException(400, f"Invalid type: {data.type}")

        version_id = await set_meta_value_unified(
            target_type=target_type,
            target_id=target_id,
            item_code=item_code,
            value_data=value_data,
            author=data.author,
            reason=data.reason
        )
        return {"version_id": version_id}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Failed to set meta value: {str(e)}")


@router.get("/{target_type}/{target_id}/{item_code}/unified", response_model=MetaValueResponse)
async def get_unified_meta_value(
    target_type: str,
    target_id: str,
    item_code: str,
    session: AsyncSession = Depends(get_session)
):
    """Get a meta value in unified JSON format."""
    try:
        value_data = await get_meta_value_unified(
            session,
            target_type=target_type,
            target_id=target_id,
            item_code=item_code
        )

        if not value_data:
            raise HTTPException(404, "Meta value not found")

        return MetaValueResponse(
            target_type=target_type,
            target_id=target_id,
            item_code=item_code,
            value_data=value_data
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Failed to get meta value: {str(e)}")


@router.get("/{target_type}/{target_id}/unified", response_model=list[MetaValueResponse])
async def get_all_unified_meta_values(
    target_type: str,
    target_id: str,
    session: AsyncSession = Depends(get_session)
):
    """Get all meta values for a target in unified JSON format."""
    try:
        from sqlalchemy import select

        from app.models.meta_types import CustomMetaItem

        # Get all meta items to check for values
        items = (await session.execute(select(CustomMetaItem))).scalars().all()

        results = []
        for item in items:
            value_data = await get_meta_value_unified(
                session,
                target_type=target_type,
                target_id=target_id,
                item_code=item.item_code
            )

            if value_data:
                results.append(MetaValueResponse(
                    target_type=target_type,
                    target_id=target_id,
                    item_code=item.item_code,
                    value_data=value_data
                ))

        return results

    except Exception as e:
        raise HTTPException(500, f"Failed to get meta values: {str(e)}")



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
            selectinload(CustomMetaValue.item),  # No need to load type relationship anymore
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
                    # Use unified parsing from V2 service
                    try:
                        item_type_kind = get_meta_item_type_kind(meta_value.item.item_code)
                    except ValueError:
                        # Fallback to database type for unknown items
                        item_type_kind = meta_value.item.type_kind

                    parsed_data = await _parse_version_data_v2(session, current_version, item_type_kind)

                    # Build version data in V1 format
                    version_data = {
                        "version_id": current_version.version_id,
                        "version_no": current_version.version_no,
                        "valid_from": current_version.valid_from,
                        "valid_to": current_version.valid_to,
                        "author": current_version.author,
                        "reason": current_version.reason,
                        "value_json": parsed_data.get("value") if item_type_kind == MetaTypeKind.PRIMITIVE else None,
                        "value_string": parsed_data.get("value") if item_type_kind == MetaTypeKind.STRING else None,
                        "code_id": parsed_data.get("code_id"),
                        "code_key": parsed_data.get("code_key"),
                        "code_label": parsed_data.get("code_label"),
                        "taxonomy_term_id": parsed_data.get("term_keys", [None])[0] if parsed_data.get("term_keys") and len(parsed_data.get("term_keys", [])) == 1 else None,
                        "term_key": parsed_data.get("term_keys", [None])[0] if parsed_data.get("term_keys") and len(parsed_data.get("term_keys", [])) == 1 else None,
                        "term_display_name": parsed_data.get("term_display_names", [None])[0] if parsed_data.get("term_display_names") and len(parsed_data.get("term_display_names", [])) == 1 else None,
                        "term_keys": parsed_data.get("term_keys") if parsed_data.get("term_keys") and len(parsed_data.get("term_keys", [])) > 1 else None,
                        "term_display_names": parsed_data.get("term_display_names") if parsed_data.get("term_display_names") and len(parsed_data.get("term_display_names", [])) > 1 else None,
                    }

                    current_version_data = MetaValueVersionOut(**version_data)

            # Build response object
            response_value = MetaValueWithVersionOut(
                value_id=meta_value.value_id,
                target_type=meta_value.target_type,
                target_id=meta_value.target_id,
                item_id=meta_value.item_id,
                item_code=meta_value.item.item_code,
                item_display_name=meta_value.item.display_name,
                type_kind=meta_value.item.type_kind,
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
        item_stmt = select(CustomMetaItem).where(CustomMetaItem.item_code == item_code)

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
                # Use unified parsing from V2 service
                try:
                    item_type_kind = get_meta_item_type_kind(item.item_code)
                except ValueError:
                    # Fallback to database type for unknown items
                    item_type_kind = item.type_kind

                parsed_data = await _parse_version_data_v2(session, current_version, item_type_kind)

                # Build version data in V1 format
                version_data = {
                    "version_id": current_version.version_id,
                    "version_no": current_version.version_no,
                    "valid_from": current_version.valid_from,
                    "valid_to": current_version.valid_to,
                    "author": current_version.author,
                    "reason": current_version.reason,
                    "value_json": parsed_data.get("value") if item_type_kind == MetaTypeKind.PRIMITIVE else None,
                    "value_string": parsed_data.get("value") if item_type_kind == MetaTypeKind.STRING else None,
                    "code_id": parsed_data.get("code_id"),
                    "code_key": parsed_data.get("code_key"),
                    "code_label": parsed_data.get("code_label"),
                    "taxonomy_term_id": parsed_data.get("term_keys", [None])[0] if parsed_data.get("term_keys") and len(parsed_data.get("term_keys", [])) == 1 else None,
                    "term_key": parsed_data.get("term_keys", [None])[0] if parsed_data.get("term_keys") and len(parsed_data.get("term_keys", [])) == 1 else None,
                    "term_display_name": parsed_data.get("term_display_names", [None])[0] if parsed_data.get("term_display_names") and len(parsed_data.get("term_display_names", [])) == 1 else None,
                    "term_keys": parsed_data.get("term_keys") if parsed_data.get("term_keys") and len(parsed_data.get("term_keys", [])) > 1 else None,
                    "term_display_names": parsed_data.get("term_display_names") if parsed_data.get("term_display_names") and len(parsed_data.get("term_display_names", [])) > 1 else None,
                }

                current_version_data = MetaValueVersionOut(**version_data)

        return MetaValueWithVersionOut(
            value_id=meta_value.value_id,
            target_type=meta_value.target_type,
            target_id=meta_value.target_id,
            item_id=meta_value.item_id,
            item_code=item.item_code,
            item_display_name=item.display_name,
            type_kind=item.type_kind,
            created_at=meta_value.created_at,
            current_version=current_version_data
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Failed to retrieve meta value: {str(e)}")
