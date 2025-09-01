from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, new_uuid, utcnow


class CustomMetaValue(Base):
    __tablename__ = "custom_meta_value"

    value_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    target_type: Mapped[str] = mapped_column(String(50))  # 'table','column','job', etc.
    target_id: Mapped[str] = mapped_column(String(200))
    item_id: Mapped[str] = mapped_column(ForeignKey("custom_meta_item.item_id"))
    current_version_id: Mapped[str | None] = mapped_column(String(36))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    __table_args__ = (
        UniqueConstraint("target_type", "target_id", "item_id", name="uq_value_target_item"),
        Index("ix_value_target", "target_type", "target_id"),
    )

    item: Mapped[CustomMetaItem] = relationship()
    current_version: Mapped[CustomMetaValueVersion | None] = relationship(
        primaryjoin="CustomMetaValue.current_version_id==CustomMetaValueVersion.version_id",
        foreign_keys="CustomMetaValue.current_version_id",
        viewonly=True,
    )


class CustomMetaValueVersion(Base):
    __tablename__ = "custom_meta_value_version"

    version_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    value_id: Mapped[str] = mapped_column(ForeignKey("custom_meta_value.value_id"), index=True)
    version_no: Mapped[int] = mapped_column(Integer)

    # Unified JSON column for all meta value types
    value_json: Mapped[str | None] = mapped_column(Text)

    valid_from: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    valid_to: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    tx_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    author: Mapped[str | None] = mapped_column(String(200))
    reason: Mapped[str | None] = mapped_column(String(1000))

    __table_args__ = (
        UniqueConstraint("value_id", "version_no", name="uq_value_version_no"),
    )


# ❌ REMOVED: CustomMetaValueVersionTerm model
# Multi-term taxonomy values are now stored in CustomMetaValueVersion.value_json as:
# {"type": "TAXONOMY", "selection_mode": "MULTI", "terms": [...]}
