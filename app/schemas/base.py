from datetime import datetime
from typing import Any

from pydantic import BaseModel


class MetaValuePrimitive(BaseModel):
    value_json: dict[str, Any]
    author: str | None = None
    reason: str | None = None


class MetaValueCode(BaseModel):
    code_key_or_id: str
    author: str | None = None
    reason: str | None = None


class MetaValueTaxSingle(BaseModel):
    term_key_or_id: str
    author: str | None = None
    reason: str | None = None


class MetaValueTaxMulti(BaseModel):
    term_keys_or_ids: list[str]
    author: str | None = None
    reason: str | None = None


class TermContentUpdate(BaseModel):
    body_markdown: str | None = None
    body_json: dict[str, Any] | None = None
    author: str | None = None
    reason: str | None = None


class TermOut(BaseModel):
    term_id: str
    term_key: str
    display_name: str
    parent_term_id: str | None


class TermContentIn(BaseModel):
    body_markdown: str | None = None
    body_json: dict[str, Any] | None = None
    author: str | None = None
    reason: str | None = None


# CodeSet schemas
class CodeSetOut(BaseModel):
    codeset_id: str
    codeset_code: str
    name: str
    description: str | None = None
    created_at: datetime

class CodeSetCreate(BaseModel):
    codeset_code: str
    name: str
    description: str | None = None

class CodeOut(BaseModel):
    code_id: str
    code_key: str
    codeset_id: str
    current_version_id: str | None = None
    created_at: datetime

class CodeCreate(BaseModel):
    code_key: str
    label_default: str | None = None


# MetaType schemas
class MetaTypeOut(BaseModel):
    type_id: str
    type_code: str
    name: str
    type_kind: str
    schema_json: str | None = None
    created_at: datetime

class MetaTypeCreate(BaseModel):
    type_code: str
    name: str
    type_kind: str = "PRIMITIVE"
    schema_json: str | None = None

class MetaGroupOut(BaseModel):
    group_id: str
    group_code: str
    display_name: str
    sort_order: int
    created_at: datetime

class MetaGroupCreate(BaseModel):
    group_code: str
    display_name: str
    sort_order: int = 0

class MetaItemOut(BaseModel):
    item_id: str
    item_code: str
    display_name: str
    group_id: str
    type_id: str
    selection_mode: str
    created_at: datetime

class MetaItemCreate(BaseModel):
    item_code: str
    display_name: str
    group_id: str
    type_id: str
    selection_mode: str = "SINGLE"


# Taxonomy schemas
class TaxonomyOut(BaseModel):
    taxonomy_id: str
    taxonomy_code: str
    name: str
    description: str | None = None
    created_at: datetime

class TaxonomyCreate(BaseModel):
    taxonomy_code: str
    name: str
    description: str | None = None
