
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_session
from app.models.meta_types import CustomMetaGroup, CustomMetaItem, CustomMetaType
from app.schemas.base import (
    MetaGroupCreate,
    MetaGroupOut,
    MetaItemCreate,
    MetaItemOut,
    MetaTypeCreate,
    MetaTypeOut,
)

router = APIRouter(prefix="/meta", tags=["meta-types"])


# MetaType endpoints
@router.get("/types", response_model=list[MetaTypeOut])
async def list_meta_types(session: AsyncSession = Depends(get_session)):
    """Get all meta types"""
    result = await session.execute(select(CustomMetaType).order_by(CustomMetaType.name))
    types = result.scalars().all()
    return [MetaTypeOut(
        type_id=t.type_id,
        type_code=t.type_code,
        name=t.name,
        type_kind=t.type_kind,
        schema_json=t.schema_json,
        created_at=t.created_at
    ) for t in types]


@router.get("/types/{type_code}", response_model=MetaTypeOut)
async def get_meta_type(type_code: str, session: AsyncSession = Depends(get_session)):
    """Get a specific meta type by code"""
    result = await session.execute(
        select(CustomMetaType).where(CustomMetaType.type_code == type_code)
    )
    meta_type = result.scalar_one_or_none()
    if not meta_type:
        raise HTTPException(404, "meta type not found")

    return MetaTypeOut(
        type_id=meta_type.type_id,
        type_code=meta_type.type_code,
        name=meta_type.name,
        type_kind=meta_type.type_kind,
        schema_json=meta_type.schema_json,
        created_at=meta_type.created_at
    )


@router.post("/types", response_model=MetaTypeOut)
async def create_meta_type(data: MetaTypeCreate, session: AsyncSession = Depends(get_session)):
    """Create a new meta type"""
    # Check if type_code already exists
    existing = await session.execute(
        select(CustomMetaType).where(CustomMetaType.type_code == data.type_code)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(400, f"meta type with code '{data.type_code}' already exists")

    meta_type = CustomMetaType(
        type_code=data.type_code,
        name=data.name,
        type_kind=data.type_kind,
        schema_json=data.schema_json
    )
    session.add(meta_type)
    await session.commit()
    await session.refresh(meta_type)

    return MetaTypeOut(
        type_id=meta_type.type_id,
        type_code=meta_type.type_code,
        name=meta_type.name,
        type_kind=meta_type.type_kind,
        schema_json=meta_type.schema_json,
        created_at=meta_type.created_at
    )


# MetaGroup endpoints
@router.get("/groups", response_model=list[MetaGroupOut])
async def list_meta_groups(session: AsyncSession = Depends(get_session)):
    """Get all meta groups"""
    result = await session.execute(select(CustomMetaGroup).order_by(CustomMetaGroup.sort_order))
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
    # Check if group_code already exists
    existing = await session.execute(
        select(CustomMetaGroup).where(CustomMetaGroup.group_code == data.group_code)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(400, f"meta group with code '{data.group_code}' already exists")

    group = CustomMetaGroup(
        group_code=data.group_code,
        display_name=data.display_name,
        sort_order=data.sort_order
    )
    session.add(group)
    await session.commit()
    await session.refresh(group)

    return MetaGroupOut(
        group_id=group.group_id,
        group_code=group.group_code,
        display_name=group.display_name,
        sort_order=group.sort_order,
        created_at=group.created_at
    )


# MetaItem endpoints
@router.get("/items", response_model=list[MetaItemOut])
async def list_meta_items(session: AsyncSession = Depends(get_session)):
    """Get all meta items"""
    result = await session.execute(select(CustomMetaItem).order_by(CustomMetaItem.display_name))
    items = result.scalars().all()
    return [MetaItemOut(
        item_id=i.item_id,
        item_code=i.item_code,
        display_name=i.display_name,
        group_id=i.group_id,
        type_id=i.type_id,
        selection_mode=i.selection_mode,
        created_at=i.created_at
    ) for i in items]


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
        type_id=item.type_id,
        selection_mode=item.selection_mode,
        created_at=item.created_at
    )


@router.post("/items", response_model=MetaItemOut)
async def create_meta_item(data: MetaItemCreate, session: AsyncSession = Depends(get_session)):
    """Create a new meta item"""
    # Check if item_code already exists
    existing = await session.execute(
        select(CustomMetaItem).where(CustomMetaItem.item_code == data.item_code)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(400, f"meta item with code '{data.item_code}' already exists")

    # Validate group exists
    group = await session.get(CustomMetaGroup, data.group_id)
    if not group:
        raise HTTPException(400, f"group with id '{data.group_id}' not found")

    # Validate type exists
    meta_type = await session.get(CustomMetaType, data.type_id)
    if not meta_type:
        raise HTTPException(400, f"meta type with id '{data.type_id}' not found")

    item = CustomMetaItem(
        item_code=data.item_code,
        display_name=data.display_name,
        group_id=data.group_id,
        type_id=data.type_id,
        selection_mode=data.selection_mode
    )
    session.add(item)
    await session.commit()
    await session.refresh(item)

    return MetaItemOut(
        item_id=item.item_id,
        item_code=item.item_code,
        display_name=item.display_name,
        group_id=item.group_id,
        type_id=item.type_id,
        selection_mode=item.selection_mode,
        created_at=item.created_at
    )
