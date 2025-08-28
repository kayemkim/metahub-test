from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, new_uuid, utcnow


class CustomMetaType(Base):
    __tablename__ = "custom_meta_type"

    type_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    type_code: Mapped[str] = mapped_column(String(100), unique=True)
    name: Mapped[str] = mapped_column(String(200))
    type_kind: Mapped[str] = mapped_column(String(30), default="PRIMITIVE")  # PRIMITIVE|CODESET|TAXONOMY
    schema_json: Mapped[str | None] = mapped_column(Text)  # validation rules for PRIMITIVE
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    codeset_link: Mapped[CustomMetaTypeCodeSet | None] = relationship(back_populates="meta_type", uselist=False)
    taxonomy_link: Mapped[CustomMetaTypeTaxonomy | None] = relationship(back_populates="meta_type", uselist=False)


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
    type_id: Mapped[str] = mapped_column(ForeignKey("custom_meta_type.type_id"))

    is_required: Mapped[bool] = mapped_column(default=False)
    default_json: Mapped[str | None] = mapped_column(Text)
    selection_mode: Mapped[str] = mapped_column(String(10), default="SINGLE")  # SINGLE|MULTI (TAXONOMY only)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    group: Mapped[CustomMetaGroup] = relationship()
    type: Mapped[CustomMetaType] = relationship()


class CustomMetaTypeCodeSet(Base):
    __tablename__ = "custom_meta_type_codeset"

    type_id: Mapped[str] = mapped_column(ForeignKey("custom_meta_type.type_id"), primary_key=True)
    codeset_id: Mapped[str] = mapped_column(ForeignKey("cm_codeset.codeset_id"))

    meta_type: Mapped[CustomMetaType] = relationship(back_populates="codeset_link")
    codeset: Mapped[CodeSet] = relationship(back_populates="type_links")


class CustomMetaTypeTaxonomy(Base):
    __tablename__ = "custom_meta_type_taxonomy"

    type_id: Mapped[str] = mapped_column(ForeignKey("custom_meta_type.type_id"), primary_key=True)
    taxonomy_id: Mapped[str] = mapped_column(ForeignKey("tx_taxonomy.taxonomy_id"))

    meta_type: Mapped[CustomMetaType] = relationship(back_populates="taxonomy_link")
    taxonomy: Mapped[Taxonomy] = relationship(back_populates="type_links")
