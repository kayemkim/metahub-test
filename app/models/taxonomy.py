from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, new_uuid, utcnow


class Taxonomy(Base):
    __tablename__ = "tx_taxonomy"

    taxonomy_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    taxonomy_code: Mapped[str] = mapped_column(String(100), unique=True)
    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    # type_links removed - meta types are now managed in code


class Term(Base):
    __tablename__ = "tx_term"

    term_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    taxonomy_id: Mapped[str] = mapped_column(ForeignKey("tx_taxonomy.taxonomy_id"), index=True)
    term_key: Mapped[str] = mapped_column(String(150))
    display_name: Mapped[str] = mapped_column(String(200))
    parent_term_id: Mapped[str | None] = mapped_column(ForeignKey("tx_term.term_id"), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    __table_args__ = (
        UniqueConstraint("taxonomy_id", "term_key", name="uq_term_key_per_taxonomy"),
    )

    parent: Mapped[Term | None] = relationship(remote_side="Term.term_id", backref="children")


class TermContent(Base):
    __tablename__ = "tx_term_content"

    content_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    term_id: Mapped[str] = mapped_column(ForeignKey("tx_term.term_id"), unique=True)
    current_version_id: Mapped[str | None] = mapped_column(String(36))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    term: Mapped[Term] = relationship()
    current_version: Mapped[TermContentVersion | None] = relationship(
        primaryjoin="TermContent.current_version_id==TermContentVersion.content_version_id",
        foreign_keys="TermContent.current_version_id",
        viewonly=True,
    )


class TermContentVersion(Base):
    __tablename__ = "tx_term_content_version"

    content_version_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    content_id: Mapped[str] = mapped_column(ForeignKey("tx_term_content.content_id"), index=True)
    version_no: Mapped[int] = mapped_column(Integer)

    body_json: Mapped[str | None] = mapped_column(Text)
    body_markdown: Mapped[str | None] = mapped_column(Text)

    tx_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    valid_from: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    valid_to: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    author: Mapped[str | None] = mapped_column(String(200))
    change_reason: Mapped[str | None] = mapped_column(String(1000))

    __table_args__ = (
        UniqueConstraint("content_id", "version_no", name="uq_term_content_version_no"),
    )
