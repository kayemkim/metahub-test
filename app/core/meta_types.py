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
class MetaTypeDefinition:
    """Definition of a meta type"""
    code: str
    name: str
    kind: MetaTypeKind
    description: Optional[str] = None
    schema_json: Optional[str] = None  # validation rules for PRIMITIVE types


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
    type_code: str  # references MetaTypeDefinition.code
    group_code: str  # references MetaGroupDefinition.code
    is_required: bool = False
    selection_mode: str = "SINGLE"  # SINGLE|MULTI (for TAXONOMY only)
    default_json: Optional[str] = None
    description: Optional[str] = None


# System-defined meta types
SYSTEM_META_TYPES: Dict[str, MetaTypeDefinition] = {
    "RETENTION_DAYS": MetaTypeDefinition(
        code="RETENTION_DAYS",
        name="Retention (days)",
        kind=MetaTypeKind.PRIMITIVE,
        description="Data retention period configuration in days"
    ),
    "TABLE_DESCRIPTION": MetaTypeDefinition(
        code="TABLE_DESCRIPTION", 
        name="Table Description",
        kind=MetaTypeKind.STRING,
        description="Human-readable description of table purpose and content"
    ),
    "PII_LEVEL_TYPE": MetaTypeDefinition(
        code="PII_LEVEL_TYPE",
        name="PII Level", 
        kind=MetaTypeKind.CODESET,
        description="Personal Information classification level"
    ),
    "DOMAIN": MetaTypeDefinition(
        code="DOMAIN",
        name="Domain",
        kind=MetaTypeKind.TAXONOMY, 
        description="Business domain classification"
    ),
}

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
        type_code="RETENTION_DAYS",
        group_code="BIZ_META",
        description="Number of days to retain this data"
    ),
    "table_description": MetaItemDefinition(
        code="table_description",
        display_name="Table Description",
        type_code="TABLE_DESCRIPTION",
        group_code="BIZ_META", 
        description="Descriptive text explaining table purpose"
    ),
    "pii_level": MetaItemDefinition(
        code="pii_level",
        display_name="PII Level",
        type_code="PII_LEVEL_TYPE", 
        group_code="BIZ_META",
        description="Classification of personal information sensitivity"
    ),
    "domain": MetaItemDefinition(
        code="domain",
        display_name="Domain",
        type_code="DOMAIN",
        group_code="BIZ_META",
        selection_mode="SINGLE",
        description="Business domain this data belongs to"
    ),
}


def get_meta_type_kind(type_code: str) -> MetaTypeKind:
    """Get the kind of a meta type by its code"""
    type_def = SYSTEM_META_TYPES.get(type_code)
    if not type_def:
        raise ValueError(f"Unknown meta type code: {type_code}")
    return type_def.kind


def validate_meta_type_code(type_code: str) -> bool:
    """Validate if a meta type code is supported"""
    return type_code in SYSTEM_META_TYPES


def get_meta_item_type_kind(item_code: str) -> MetaTypeKind:
    """Get the type kind for a meta item by its code"""
    item_def = SYSTEM_META_ITEMS.get(item_code)
    if not item_def:
        raise ValueError(f"Unknown meta item code: {item_code}")
    return get_meta_type_kind(item_def.type_code)