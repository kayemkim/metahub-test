"""
Code-based meta type definitions for better type safety and consistency
"""
from enum import Enum
from dataclasses import dataclass
from typing import Dict, Optional


class MetaTypeKind(str, Enum):
    """Supported meta value types"""
    PRIMITIVE = "PRIMITIVE"
    STRING = "STRING" 
    CODESET = "CODESET"
    TAXONOMY = "TAXONOMY"


@dataclass 
class MetaGroupDefinition:
    """Definition of a meta group"""
    code: str
    display_name: str
    sort_order: int = 0
    description: Optional[str] = None


@dataclass
class MetaItemDefinition:
    """Definition of a meta item"""
    code: str
    display_name: str
    type_kind: MetaTypeKind  # Direct reference to MetaTypeKind
    group_code: str  # references MetaGroupDefinition.code
    is_required: bool = False
    selection_mode: str = "SINGLE"  # SINGLE|MULTI (for TAXONOMY only)
    default_json: Optional[str] = None
    description: Optional[str] = None

# System-defined meta groups
SYSTEM_META_GROUPS: Dict[str, MetaGroupDefinition] = {
    "BIZ_META": MetaGroupDefinition(
        code="BIZ_META",
        display_name="Business Metadata",
        sort_order=100,
        description="Business-oriented metadata for governance and discovery"
    ),
}

# System-defined meta items
SYSTEM_META_ITEMS: Dict[str, MetaItemDefinition] = {
    "retention_days": MetaItemDefinition(
        code="retention_days",
        display_name="Retention Days", 
        type_kind=MetaTypeKind.PRIMITIVE,
        group_code="BIZ_META",
        description="Number of days to retain this data"
    ),
    "table_description": MetaItemDefinition(
        code="table_description",
        display_name="Table Description",
        type_kind=MetaTypeKind.STRING,
        group_code="BIZ_META", 
        description="Descriptive text explaining table purpose"
    ),
    "pii_level": MetaItemDefinition(
        code="pii_level",
        display_name="PII Level",
        type_kind=MetaTypeKind.CODESET, 
        group_code="BIZ_META",
        description="Classification of personal information sensitivity"
    ),
    "domain": MetaItemDefinition(
        code="domain",
        display_name="Domain",
        type_kind=MetaTypeKind.TAXONOMY,
        group_code="BIZ_META",
        selection_mode="SINGLE",
        description="Business domain this data belongs to"
    ),
}


def validate_meta_type_kind(type_kind: str) -> bool:
    """Validate if a meta type kind is supported"""
    try:
        MetaTypeKind(type_kind)
        return True
    except ValueError:
        return False


def get_meta_item_type_kind(item_code: str) -> MetaTypeKind:
    """Get the type kind for a meta item by its code"""
    item_def = SYSTEM_META_ITEMS.get(item_code)
    if not item_def:
        raise ValueError(f"Unknown meta item code: {item_code}")
    return item_def.type_kind


def get_all_meta_type_kinds() -> list[MetaTypeKind]:
    """Get all supported meta type kinds"""
    return list(MetaTypeKind)