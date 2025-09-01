
import json
from typing import Any

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import transactional
from app.core.deps import get_repository_session
from app.core.meta_types import MetaTypeKind, get_meta_item_type_kind
from app.db.base import utcnow
from app.models.codeset import Code
from app.models.meta_types import CustomMetaItem
from app.models.meta_values import (
    CustomMetaValue,
    CustomMetaValueVersion,
)
from app.models.taxonomy import Term
from app.schemas.base import (
    MetaValueCode,
    MetaValuePrimitive,
    MetaValueString,
    MetaValueTaxMulti,
    MetaValueTaxSingle,
)
from app.services.utils import _next_version_no


async def _ensure_value_row(session: AsyncSession, target_type: str, target_id: str, item: CustomMetaItem) -> CustomMetaValue:
    res = await session.execute(
        select(CustomMetaValue)
        .where(
            CustomMetaValue.target_type == target_type,
            CustomMetaValue.target_id == target_id,
            CustomMetaValue.item_id == item.item_id,
        )
        .with_for_update()
    )
    mv = res.scalar_one_or_none()
    if not mv:
        mv = CustomMetaValue(target_type=target_type, target_id=target_id, item_id=item.item_id)
        session.add(mv)
        await session.flush()
    return mv


@transactional()
async def set_meta_value_primitive(
    *,
    target_type: str,
    target_id: str,
    item_code: str,
    payload: MetaValuePrimitive,
) -> str:
        session = await get_repository_session()

        # Validate meta item type using code definitions
        try:
            item_type_kind = get_meta_item_type_kind(item_code)
        except ValueError:
            raise HTTPException(404, f"meta item not found: {item_code}")

        if item_type_kind != MetaTypeKind.PRIMITIVE:
            raise HTTPException(400, f"item {item_code} is not PRIMITIVE, it's {item_type_kind}")

        # Still need to get the CustomMetaItem for database operations
        item = (await session.execute(select(CustomMetaItem).where(CustomMetaItem.item_code == item_code))).scalar_one_or_none()
        if not item:
            raise HTTPException(500, f"meta item {item_code} not found in database - sync issue")

        mv = await _ensure_value_row(session, target_type, target_id, item)

        # Close prev
        if mv.current_version_id:
            prev = await session.get(CustomMetaValueVersion, mv.current_version_id, with_for_update=True)
            if prev and prev.valid_to is None:
                prev.valid_to = utcnow()

        version_no = await _next_version_no(session, CustomMetaValueVersion, "value_id", mv.value_id)
        # Store in unified JSON format
        unified_value = {
            "type": "PRIMITIVE",
            "value": payload.value_json
        }
        v = CustomMetaValueVersion(
            value_id=mv.value_id,
            version_no=version_no,
            value_json_v2=json.dumps(unified_value),
            author=payload.author,
            reason=payload.reason,
        )
        session.add(v)
        await session.flush()
        mv.current_version_id = v.version_id
        return v.version_id


@transactional()
async def set_meta_value_string(
    *,
    target_type: str,
    target_id: str,
    item_code: str,
    payload: MetaValueString,
) -> str:
        session = await get_repository_session()

        # Validate meta item type using code definitions
        try:
            item_type_kind = get_meta_item_type_kind(item_code)
        except ValueError:
            raise HTTPException(404, f"meta item not found: {item_code}")

        if item_type_kind != MetaTypeKind.STRING:
            raise HTTPException(400, f"item {item_code} is not STRING, it's {item_type_kind}")

        # Still need to get the CustomMetaItem for database operations
        item = (await session.execute(select(CustomMetaItem).where(CustomMetaItem.item_code == item_code))).scalar_one_or_none()
        if not item:
            raise HTTPException(500, f"meta item {item_code} not found in database - sync issue")

        mv = await _ensure_value_row(session, target_type, target_id, item)

        # Close prev
        if mv.current_version_id:
            prev = await session.get(CustomMetaValueVersion, mv.current_version_id, with_for_update=True)
            if prev and prev.valid_to is None:
                prev.valid_to = utcnow()

        version_no = await _next_version_no(session, CustomMetaValueVersion, "value_id", mv.value_id)
        # Store in unified JSON format
        unified_value = {
            "type": "STRING",
            "value": payload.value_string
        }
        v = CustomMetaValueVersion(
            value_id=mv.value_id,
            version_no=version_no,
            value_json_v2=json.dumps(unified_value),
            author=payload.author,
            reason=payload.reason,
        )
        session.add(v)
        await session.flush()
        mv.current_version_id = v.version_id
        return v.version_id


@transactional()
async def set_meta_value_codeset(
    *,
    target_type: str,
    target_id: str,
    item_code: str,
    payload: MetaValueCode,
) -> str:
        session = await get_repository_session()

        # Validate meta item type using code definitions
        try:
            item_type_kind = get_meta_item_type_kind(item_code)
        except ValueError:
            raise HTTPException(404, f"meta item not found: {item_code}")

        if item_type_kind != MetaTypeKind.CODESET:
            raise HTTPException(400, f"item {item_code} is not CODESET, it's {item_type_kind}")

        # Still need to get the CustomMetaItem for database operations
        item = (await session.execute(select(CustomMetaItem).where(CustomMetaItem.item_code == item_code))).scalar_one_or_none()
        if not item:
            raise HTTPException(500, f"meta item {item_code} not found in database - sync issue")

        # For CODESET type, directly find code by key within the appropriate codeset
        # Assume the codeset_code matches the item_code for simplicity
        code = (
            (await session.execute(select(Code).where(Code.code_id == payload.code_key_or_id))).scalar_one_or_none()
            or (
                await session.execute(
                    select(Code).join(Code.codeset).where(
                        Code.code_key == payload.code_key_or_id
                    )
                )
            ).scalar_one_or_none()
        )
        if not code:
            raise HTTPException(400, "invalid code for codeset")

        mv = await _ensure_value_row(session, target_type, target_id, item)
        if mv.current_version_id:
            prev = await session.get(CustomMetaValueVersion, mv.current_version_id, with_for_update=True)
            if prev and prev.valid_to is None:
                prev.valid_to = utcnow()

        version_no = await _next_version_no(session, CustomMetaValueVersion, "value_id", mv.value_id)
        # Store in unified JSON format
        unified_value = {
            "type": "CODESET",
            "code_id": code.code_id,
            "code_key": code.code_key
        }
        v = CustomMetaValueVersion(
            value_id=mv.value_id,
            version_no=version_no,
            value_json_v2=json.dumps(unified_value),
        )
        session.add(v)
        await session.flush()
        mv.current_version_id = v.version_id
        return v.version_id


@transactional()
async def set_meta_value_taxonomy_single(
    *,
    target_type: str,
    target_id: str,
    item_code: str,
    payload: MetaValueTaxSingle,
) -> str:
        session = await get_repository_session()

        # Validate meta item type using code definitions
        try:
            item_type_kind = get_meta_item_type_kind(item_code)
        except ValueError:
            raise HTTPException(404, f"meta item not found: {item_code}")

        if item_type_kind != MetaTypeKind.TAXONOMY:
            raise HTTPException(400, f"item {item_code} is not TAXONOMY, it's {item_type_kind}")

        # Still need to get the CustomMetaItem for database operations and selection_mode
        item = (await session.execute(select(CustomMetaItem).where(CustomMetaItem.item_code == item_code))).scalar_one_or_none()
        if not item:
            raise HTTPException(500, f"meta item {item_code} not found in database - sync issue")
        if item.selection_mode != "SINGLE":
            raise HTTPException(400, f"item {item_code} selection_mode must be SINGLE")

        # For TAXONOMY type, directly find term by key
        # Assume the taxonomy_code matches the item_code for simplicity
        from app.models.taxonomy import Taxonomy
        term = (
            (await session.execute(select(Term).where(Term.term_id == payload.term_key_or_id))).scalar_one_or_none()
            or (
                await session.execute(
                    select(Term).join(Taxonomy, Term.taxonomy_id == Taxonomy.taxonomy_id).where(
                        Term.term_key == payload.term_key_or_id
                    )
                )
            ).scalar_one_or_none()
        )
        if not term:
            raise HTTPException(400, "invalid term for taxonomy")

        mv = await _ensure_value_row(session, target_type, target_id, item)
        if mv.current_version_id:
            prev = await session.get(CustomMetaValueVersion, mv.current_version_id, with_for_update=True)
            if prev and prev.valid_to is None:
                prev.valid_to = utcnow()

        version_no = await _next_version_no(session, CustomMetaValueVersion, "value_id", mv.value_id)
        # Store in unified JSON format
        unified_value = {
            "type": "TAXONOMY",
            "selection_mode": "SINGLE",
            "term_keys": [term.term_key]
        }
        v = CustomMetaValueVersion(
            value_id=mv.value_id,
            version_no=version_no,
            value_json_v2=json.dumps(unified_value),
        )
        session.add(v)
        await session.flush()
        mv.current_version_id = v.version_id
        return v.version_id


@transactional()
async def set_meta_value_taxonomy_multi(
    *,
    target_type: str,
    target_id: str,
    item_code: str,
    payload: MetaValueTaxMulti,
) -> str:
        session = await get_repository_session()

        # Validate meta item type using code definitions
        try:
            item_type_kind = get_meta_item_type_kind(item_code)
        except ValueError:
            raise HTTPException(404, f"meta item not found: {item_code}")

        if item_type_kind != MetaTypeKind.TAXONOMY:
            raise HTTPException(400, f"item {item_code} is not TAXONOMY, it's {item_type_kind}")

        # Still need to get the CustomMetaItem for database operations and selection_mode
        item = (await session.execute(select(CustomMetaItem).where(CustomMetaItem.item_code == item_code))).scalar_one_or_none()
        if not item:
            raise HTTPException(500, f"meta item {item_code} not found in database - sync issue")
        if item.selection_mode != "MULTI":
            raise HTTPException(400, f"item {item_code} selection_mode must be MULTI")

        # For TAXONOMY type, directly find terms by key
        # Assume the taxonomy_code matches the item_code for simplicity
        from app.models.taxonomy import Taxonomy
        terms: list[Term] = []
        for key in payload.term_keys_or_ids:
            term = (
                (await session.execute(select(Term).where(Term.term_id == key))).scalar_one_or_none()
                or (
                    await session.execute(
                        select(Term).join(Taxonomy, Term.taxonomy_id == Taxonomy.taxonomy_id).where(
                            Term.term_key == key
                        )
                    )
                ).scalar_one_or_none()
            )
            if not term:
                raise HTTPException(400, f"invalid term: {key}")
            terms.append(term)

        mv = await _ensure_value_row(session, target_type, target_id, item)

        # Close prev version
        if mv.current_version_id:
            prev = await session.get(CustomMetaValueVersion, mv.current_version_id, with_for_update=True)
            if prev and prev.valid_to is None:
                prev.valid_to = utcnow()

        version_no = await _next_version_no(session, CustomMetaValueVersion, "value_id", mv.value_id)
        # Store in unified JSON format
        unified_value = {
            "type": "TAXONOMY",
            "selection_mode": "MULTI",
            "term_keys": [t.term_key for t in terms]
        }
        v = CustomMetaValueVersion(
            value_id=mv.value_id,
            version_no=version_no,
            value_json_v2=json.dumps(unified_value)
        )
        session.add(v)
        await session.flush()

        mv.current_version_id = v.version_id
        return v.version_id


# ==============================================================================
# UNIFIED API - New interface using value_json column
# ==============================================================================

@transactional()
async def set_meta_value_unified(
    *,
    target_type: str,
    target_id: str,
    item_code: str,
    value_data: dict[str, Any],
    author: str | None = None,
    reason: str | None = None,
) -> str:
    """
    Set a meta value using unified JSON structure.
    
    Args:
        value_data: Unified JSON structure containing type and value information
        
    Expected formats:
        PRIMITIVE: {"type": "PRIMITIVE", "value": any_json_serializable}
        STRING: {"type": "STRING", "value": "string_content"}
        CODESET: {"type": "CODESET", "code_key": "CODE", "code_label": "Label", ...}
        TAXONOMY: {"type": "TAXONOMY", "selection_mode": "SINGLE|MULTI", "term_keys": ["KEY1", ...]}
    """
    session = await get_repository_session()

    # Validate meta item exists
    try:
        item_type_kind = get_meta_item_type_kind(item_code)
    except ValueError:
        raise HTTPException(404, f"meta item not found: {item_code}")

    # Get database item for constraints
    item = (await session.execute(select(CustomMetaItem).where(CustomMetaItem.item_code == item_code))).scalar_one_or_none()
    if not item:
        raise HTTPException(500, f"meta item {item_code} not found in database - sync issue")

    # Validate value_data structure matches expected type
    if "type" not in value_data:
        raise HTTPException(400, "value_data must include 'type' field")

    if value_data["type"] != item_type_kind.value:
        raise HTTPException(400, f"value_data type '{value_data['type']}' doesn't match item type '{item_type_kind.value}'")

    # Validate specific type requirements
    await _validate_unified_value_data(session, item, value_data)

    # Create enriched JSON with full reference data
    enriched_json = await _enrich_value_data(session, value_data)

    # Create version
    mv = await _ensure_value_row(session, target_type, target_id, item)

    # Close previous version
    if mv.current_version_id:
        prev = await session.get(CustomMetaValueVersion, mv.current_version_id, with_for_update=True)
        if prev and prev.valid_to is None:
            prev.valid_to = utcnow()

    # Create new version with unified JSON
    version_no = await _next_version_no(session, CustomMetaValueVersion, "value_id", mv.value_id)
    v = CustomMetaValueVersion(
        value_id=mv.value_id,
        version_no=version_no,
        value_json=json.dumps(enriched_json),
        author=author,
        reason=reason,
    )
    session.add(v)
    await session.flush()
    mv.current_version_id = v.version_id
    return v.version_id


async def _validate_unified_value_data(
    session: AsyncSession,
    item: CustomMetaItem,
    value_data: dict[str, Any]
) -> None:
    """Validate unified value data structure."""

    value_type = value_data["type"]

    if value_type == "PRIMITIVE":
        if "value" not in value_data:
            raise HTTPException(400, "PRIMITIVE type requires 'value' field")

    elif value_type == "STRING":
        if "value" not in value_data:
            raise HTTPException(400, "STRING type requires 'value' field")
        if not isinstance(value_data["value"], str):
            raise HTTPException(400, "STRING type 'value' must be a string")

    elif value_type == "CODESET":
        if "code_key" not in value_data:
            raise HTTPException(400, "CODESET type requires 'code_key' field")
        # Validate code exists
        from app.models.codeset import Code
        result = await session.execute(
            select(Code).where(Code.code_key == value_data["code_key"])
        )
        code = result.scalar_one_or_none()
        if not code:
            raise HTTPException(400, f"Invalid code_key: {value_data['code_key']}")

    elif value_type == "TAXONOMY":
        if "term_keys" not in value_data:
            raise HTTPException(400, "TAXONOMY type requires 'term_keys' field")
        if not isinstance(value_data["term_keys"], list):
            raise HTTPException(400, "TAXONOMY 'term_keys' must be a list")

        # Validate selection mode
        selection_mode = value_data.get("selection_mode", "SINGLE")
        if selection_mode == "SINGLE" and len(value_data["term_keys"]) != 1:
            raise HTTPException(400, "SINGLE selection mode requires exactly one term_key")
        elif selection_mode == "MULTI" and len(value_data["term_keys"]) == 0:
            raise HTTPException(400, "MULTI selection mode requires at least one term_key")

        # Validate terms exist
        from app.models.taxonomy import Term
        for term_key in value_data["term_keys"]:
            result = await session.execute(
                select(Term).where(Term.term_key == term_key)
            )
            term = result.scalar_one_or_none()
            if not term:
                raise HTTPException(400, f"Invalid term_key: {term_key}")


async def _enrich_value_data(
    session: AsyncSession,
    value_data: dict[str, Any]
) -> dict[str, Any]:
    """Enrich value data with full reference information."""

    enriched = value_data.copy()
    value_type = value_data["type"]

    if value_type == "CODESET":
        # Enrich with full code information
        from app.models.codeset import Code, CodeSet, CodeVersion
        result = await session.execute(
            select(Code)
            .join(CodeVersion, Code.current_version_id == CodeVersion.code_version_id)
            .join(CodeSet, Code.codeset_id == CodeSet.codeset_id)
            .where(Code.code_key == value_data["code_key"])
        )
        code = result.scalar_one()

        # Get current version and codeset separately to avoid lazy loading issues
        from app.models.codeset import CodeSet, CodeVersion
        cv_result = await session.execute(
            select(CodeVersion).where(CodeVersion.code_version_id == code.current_version_id)
        )
        current_version = cv_result.scalar_one()

        cs_result = await session.execute(
            select(CodeSet).where(CodeSet.codeset_id == code.codeset_id)
        )
        codeset = cs_result.scalar_one()

        enriched.update({
            "code_id": code.code_id,
            "code_key": code.code_key,
            "code_label": current_version.label_default,
            "codeset_code": codeset.codeset_code,
        })

    elif value_type == "TAXONOMY":
        # Enrich with full term information
        from app.models.taxonomy import Taxonomy, Term
        terms = []
        for term_key in value_data["term_keys"]:
            result = await session.execute(
                select(Term)
                .join(Taxonomy, Term.taxonomy_id == Taxonomy.taxonomy_id)
                .where(Term.term_key == term_key)
            )
            term = result.scalar_one()

            # Get taxonomy separately to avoid lazy loading
            from app.models.taxonomy import Taxonomy
            tax_result = await session.execute(
                select(Taxonomy).where(Taxonomy.taxonomy_id == term.taxonomy_id)
            )
            taxonomy = tax_result.scalar_one()

            terms.append({
                "term_id": term.term_id,
                "term_key": term.term_key,
                "display_name": term.display_name,
                "taxonomy_code": taxonomy.taxonomy_code,
            })

        enriched["terms"] = terms
        enriched["selection_mode"] = value_data.get("selection_mode", "SINGLE")

    return enriched


async def get_meta_value_unified(
    session: AsyncSession,
    *,
    target_type: str,
    target_id: str,
    item_code: str,
) -> dict[str, Any] | None:
    """Get a meta value in unified JSON format."""

    # Get meta item
    item = (await session.execute(
        select(CustomMetaItem).where(CustomMetaItem.item_code == item_code)
    )).scalar_one_or_none()
    if not item:
        return None

    # Get meta value
    mv = (await session.execute(
        select(CustomMetaValue).where(
            CustomMetaValue.target_type == target_type,
            CustomMetaValue.target_id == target_id,
            CustomMetaValue.item_id == item.item_id
        )
    )).scalar_one_or_none()

    if not mv or not mv.current_version_id:
        return None

    # Get current version
    version = (await session.execute(
        select(CustomMetaValueVersion).where(
            CustomMetaValueVersion.version_id == mv.current_version_id
        )
    )).scalar_one_or_none()

    if not version:
        return None

    # Return unified JSON if available, otherwise migrate on-demand
    if version.value_json:
        return json.loads(version.value_json)
    else:
        # Fallback: migrate legacy data on-the-fly (read-only)
        return await _migrate_legacy_data_on_demand(session, version, item)


async def _migrate_legacy_data_on_demand(
    session: AsyncSession,
    version: CustomMetaValueVersion,
    item: CustomMetaItem
) -> dict[str, Any] | None:
    """Migrate legacy data format to unified format on-demand (read-only)."""

    try:
        item_type_kind = get_meta_item_type_kind(item.item_code)
    except ValueError:
        item_type_kind = MetaTypeKind(item.type_kind)

    if item_type_kind == MetaTypeKind.PRIMITIVE and version.value_json_v2:
        data = json.loads(version.value_json_v2)
        return {
            "type": "PRIMITIVE",
            "value": data.get("value")
        }

    elif item_type_kind == MetaTypeKind.STRING and version.value_json_v2:
        data = json.loads(version.value_json_v2)
        return {
            "type": "STRING",
            "value": data.get("value", "")
        }

    elif item_type_kind == MetaTypeKind.CODESET and version.value_json_v2:
        data = json.loads(version.value_json_v2)
        return {
            "type": "CODESET",
            "code_id": data.get("code_id"),
            "code_key": data.get("code_key"),
            "code_label": data.get("code_label"),
            "codeset_code": data.get("codeset_code"),
        }

    elif item_type_kind == MetaTypeKind.TAXONOMY and version.value_json_v2:
        data = json.loads(version.value_json_v2)
        return {
            "type": "TAXONOMY",
            "selection_mode": data.get("selection_mode", "SINGLE"),
            "term_keys": data.get("term_keys", []),
            "terms": data.get("terms", [])
        }

    return None
