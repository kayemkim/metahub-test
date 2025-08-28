from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, new_uuid, utcnow


class CodeSet(Base):
    __tablename__ = "cm_codeset"

    codeset_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    codeset_code: Mapped[str] = mapped_column(String(100), unique=True)
    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    codes: Mapped[list[Code]] = relationship(back_populates="codeset")
    type_links: Mapped[list[CustomMetaTypeCodeSet]] = relationship(back_populates="codeset")


class Code(Base):
    __tablename__ = "cm_code"

    code_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    codeset_id: Mapped[str] = mapped_column(ForeignKey("cm_codeset.codeset_id"))
    code_key: Mapped[str] = mapped_column(String(150))
    current_version_id: Mapped[str | None] = mapped_column(String(36))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    __table_args__ = (
        UniqueConstraint("codeset_id", "code_key", name="uq_code_key_per_set"),
    )

    codeset: Mapped[CodeSet] = relationship(back_populates="codes")
    current_version: Mapped[CodeVersion | None] = relationship(
        primaryjoin="Code.current_version_id==CodeVersion.code_version_id",
        foreign_keys="Code.current_version_id",
        viewonly=True,
    )


class CodeVersion(Base):
    __tablename__ = "cm_code_version"

    code_version_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    code_id: Mapped[str] = mapped_column(ForeignKey("cm_code.code_id"), index=True)
    version_no: Mapped[int] = mapped_column(Integer)

    label_default: Mapped[str] = mapped_column(String(200))
    sort_order: Mapped[int] = mapped_column(Integer, default=0)

    parent_code_id: Mapped[str | None] = mapped_column(ForeignKey("cm_code.code_id"))  # optional hierarchy
    valid_from: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    valid_to: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    tx_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    is_active: Mapped[bool] = mapped_column(default=True)
    extra_json: Mapped[str | None] = mapped_column(Text)

    __table_args__ = (
        UniqueConstraint("code_id", "version_no", name="uq_code_version_no"),
    )
