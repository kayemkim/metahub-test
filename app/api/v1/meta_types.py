"""
Meta Types API - now code-based instead of database-based
"""
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_session
from app.core.meta_types import MetaTypeKind, SYSTEM_META_GROUPS, get_meta_item_type_kind, get_all_meta_type_kinds
from app.models.meta_types import CustomMetaGroup, CustomMetaItem
from app.schemas.base import (
    MetaGroupCreate,
    MetaGroupOut,
    MetaItemCreate,
    MetaItemOut,
    MetaTypeCreate,
    MetaTypeOut,
)

router = APIRouter(prefix="/meta", tags=["meta-types"])


# MetaType endpoints - return basic type kinds only
@router.get("/types", response_model=list[MetaTypeOut])
async def list_meta_types():
    """Get all supported meta type kinds"""
    return [
        MetaTypeOut(
            type_id=kind.value,
            type_code=kind.value,
            name=kind.value.title(),  # PRIMITIVE -> Primitive
            type_kind=kind.value,
            schema_json=None,
            created_at=datetime.utcnow()
        ) for kind in get_all_meta_type_kinds()
    ]


@router.get("/types/{type_code}", response_model=MetaTypeOut)
async def get_meta_type(type_code: str):
    """Get a specific meta type kind by code"""
    try:
        kind = MetaTypeKind(type_code.upper())
    except ValueError:
        raise HTTPException(404, f"Meta type '{type_code}' not found")
    
    return MetaTypeOut(
        type_id=kind.value,
        type_code=kind.value,
        name=kind.value.title(),
        type_kind=kind.value,
        schema_json=None,
        created_at=datetime.utcnow()
    )


@router.post("/types", response_model=MetaTypeOut)
async def create_meta_type(data: MetaTypeCreate):
    """Meta types are basic kinds - cannot be created via API"""
    raise HTTPException(400, "Meta type kinds are fixed. Use /meta/items to create specific metadata items.")


# MetaGroup endpoints - still database-based
@router.get("/groups", response_model=list[MetaGroupOut])
async def list_meta_groups(session: AsyncSession = Depends(get_session)):
    """Get all meta groups"""
    result = await session.execute(select(CustomMetaGroup).order_by(CustomMetaGroup.display_name))
    groups = result.scalars().all()
    return [MetaGroupOut(
        group_id=g.group_id,
        group_code=g.group_code,
        display_name=g.display_name,
        sort_order=g.sort_order,
        created_at=g.created_at
    ) for g in groups]


@router.get("/groups/{group_code}", response_model=MetaGroupOut)
async def get_meta_group(group_code: str, session: AsyncSession = Depends(get_session)):
    """Get a specific meta group by code"""
    result = await session.execute(
        select(CustomMetaGroup).where(CustomMetaGroup.group_code == group_code)
    )
    group = result.scalar_one_or_none()
    if not group:
        raise HTTPException(404, "meta group not found")
    
    return MetaGroupOut(
        group_id=group.group_id,
        group_code=group.group_code,
        display_name=group.display_name,
        sort_order=group.sort_order,
        created_at=group.created_at
    )


@router.post("/groups", response_model=MetaGroupOut)
async def create_meta_group(data: MetaGroupCreate, session: AsyncSession = Depends(get_session)):
    """Create a new meta group"""
    # Check if group code already exists
    result = await session.execute(
        select(CustomMetaGroup).where(CustomMetaGroup.group_code == data.group_code)
    )
    if result.scalar_one_or_none():
        raise HTTPException(400, f"Meta group '{data.group_code}' already exists")

    group = CustomMetaGroup(
        group_code=data.group_code,
        display_name=data.display_name,
        sort_order=data.sort_order or 0
    )
    session.add(group)
    await session.commit()
    
    return MetaGroupOut(
        group_id=group.group_id,
        group_code=group.group_code,
        display_name=group.display_name,
        sort_order=group.sort_order,
        created_at=group.created_at
    )


# MetaItem endpoints - now with type_kind instead of type_id
@router.get("/items", response_model=list[MetaItemOut])
async def list_meta_items(session: AsyncSession = Depends(get_session)):
    """Get all meta items"""
    result = await session.execute(
        select(CustomMetaItem).options(
            # No need to load type relationship anymore
        ).order_by(CustomMetaItem.display_name)
    )
    items = result.scalars().all()
    return [MetaItemOut(
        item_id=item.item_id,
        item_code=item.item_code,
        display_name=item.display_name,
        group_id=item.group_id,
        type_kind=item.type_kind,
        is_required=item.is_required,
        default_json=item.default_json,
        selection_mode=item.selection_mode,
        created_at=item.created_at
    ) for item in items]


@router.get("/items/{item_code}", response_model=MetaItemOut)
async def get_meta_item(item_code: str, session: AsyncSession = Depends(get_session)):
    """Get a specific meta item by code"""
    result = await session.execute(
        select(CustomMetaItem).where(CustomMetaItem.item_code == item_code)
    )
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(404, "meta item not found")
    
    return MetaItemOut(
        item_id=item.item_id,
        item_code=item.item_code,
        display_name=item.display_name,
        group_id=item.group_id,
        type_kind=item.type_kind,
        is_required=item.is_required,
        default_json=item.default_json,
        selection_mode=item.selection_mode,
        created_at=item.created_at
    )


@router.post("/items", response_model=MetaItemOut)
async def create_meta_item(data: MetaItemCreate, session: AsyncSession = Depends(get_session)):
    """Create a new meta item"""
    # Check if item code already exists
    result = await session.execute(
        select(CustomMetaItem).where(CustomMetaItem.item_code == data.item_code)
    )
    if result.scalar_one_or_none():
        raise HTTPException(400, f"Meta item '{data.item_code}' already exists")
    
    # Validate group exists
    group_result = await session.execute(
        select(CustomMetaGroup).where(CustomMetaGroup.group_id == data.group_id)
    )
    if not group_result.scalar_one_or_none():
        raise HTTPException(400, f"Meta group '{data.group_id}' not found")
    
    # Validate type_kind is valid
    from app.core.meta_types import validate_meta_type_kind
    if not validate_meta_type_kind(data.type_kind):
        raise HTTPException(400, f"Invalid type_kind: {data.type_kind}")

    item = CustomMetaItem(
        item_code=data.item_code,
        display_name=data.display_name,
        group_id=data.group_id,
        type_kind=data.type_kind,
        is_required=data.is_required or False,
        selection_mode=data.selection_mode or "SINGLE",
        default_json=data.default_json
    )
    session.add(item)
    await session.commit()
    
    return MetaItemOut(
        item_id=item.item_id,
        item_code=item.item_code,
        display_name=item.display_name,
        group_id=item.group_id,
        type_kind=item.type_kind,
        is_required=item.is_required,
        default_json=item.default_json,
        selection_mode=item.selection_mode,
        created_at=item.created_at
    )