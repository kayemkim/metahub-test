from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, new_uuid, utcnow


# CustomMetaType is now managed in code via app/core/meta_types.py
# Database table is no longer needed - all type information comes from code


class CustomMetaGroup(Base):
    __tablename__ = "custom_meta_group"

    group_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    group_code: Mapped[str] = mapped_column(String(100), unique=True)
    display_name: Mapped[str] = mapped_column(String(200))
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class CustomMetaItem(Base):
    __tablename__ = "custom_meta_item"

    item_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    item_code: Mapped[str] = mapped_column(String(150), unique=True)
    display_name: Mapped[str] = mapped_column(String(200))

    group_id: Mapped[str] = mapped_column(ForeignKey("custom_meta_group.group_id"))
    type_kind: Mapped[str] = mapped_column(String(30), default="PRIMITIVE")  # PRIMITIVE|STRING|CODESET|TAXONOMY

    is_required: Mapped[bool] = mapped_column(default=False)
    default_json: Mapped[str | None] = mapped_column(Text)
    selection_mode: Mapped[str] = mapped_column(String(10), default="SINGLE")  # SINGLE|MULTI (TAXONOMY only)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    group: Mapped[CustomMetaGroup] = relationship()


# CustomMetaTypeCodeSet and CustomMetaTypeTaxonomy are no longer needed
# Type-specific validation is now handled in code via SYSTEM_META_TYPES definitions
