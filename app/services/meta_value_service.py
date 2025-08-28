
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import utcnow
from app.models.codeset import Code
from app.models.meta_types import CustomMetaItem
from app.models.meta_values import (
    CustomMetaValue,
    CustomMetaValueVersion,
    CustomMetaValueVersionTerm,
)
from app.models.taxonomy import Term
from app.schemas.base import (
    MetaValueCode,
    MetaValuePrimitive,
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


async def set_meta_value_primitive(
    session: AsyncSession,
    *,
    target_type: str,
    target_id: str,
    item_code: str,
    payload: MetaValuePrimitive,
) -> str:
    async with session.begin():
        item = (await session.execute(select(CustomMetaItem).where(CustomMetaItem.item_code == item_code))).scalar_one_or_none()
        if not item:
            raise HTTPException(404, f"meta item not found: {item_code}")
        if item.type.type_kind != "PRIMITIVE":
            raise HTTPException(400, f"item {item_code} is not PRIMITIVE")

        mv = await _ensure_value_row(session, target_type, target_id, item)

        # Close prev
        if mv.current_version_id:
            prev = await session.get(CustomMetaValueVersion, mv.current_version_id, with_for_update=True)
            if prev and prev.valid_to is None:
                prev.valid_to = utcnow()

        version_no = await _next_version_no(session, CustomMetaValueVersion, "value_id", mv.value_id)
        v = CustomMetaValueVersion(
            value_id=mv.value_id,
            version_no=version_no,
            value_json=str(payload.value_json),
            author=payload.author,
            reason=payload.reason,
        )
        session.add(v)
        await session.flush()
        mv.current_version_id = v.version_id
        return v.version_id


async def set_meta_value_codeset(
    session: AsyncSession,
    *,
    target_type: str,
    target_id: str,
    item_code: str,
    payload: MetaValueCode,
) -> str:
    async with session.begin():
        item = (await session.execute(select(CustomMetaItem).where(CustomMetaItem.item_code == item_code))).scalar_one_or_none()
        if not item:
            raise HTTPException(404, f"meta item not found: {item_code}")
        if item.type.type_kind != "CODESET":
            raise HTTPException(400, f"item {item_code} is not CODESET")

        # Resolve codeset
        link = item.type.codeset_link
        if not link:
            raise HTTPException(400, f"meta type {item.type.type_code} has no codeset link")

        # Accept either code_id or code_key
        code = (
            (await session.execute(select(Code).where(Code.code_id == payload.code_key_or_id))).scalar_one_or_none()
            or (
                await session.execute(
                    select(Code).where(
                        Code.codeset_id == link.codeset_id,
                        Code.code_key == payload.code_key_or_id,
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
        v = CustomMetaValueVersion(
            value_id=mv.value_id,
            version_no=version_no,
            code_id=code.code_id,
        )
        session.add(v)
        await session.flush()
        mv.current_version_id = v.version_id
        return v.version_id


async def set_meta_value_taxonomy_single(
    session: AsyncSession,
    *,
    target_type: str,
    target_id: str,
    item_code: str,
    payload: MetaValueTaxSingle,
) -> str:
    async with session.begin():
        item = (await session.execute(select(CustomMetaItem).where(CustomMetaItem.item_code == item_code))).scalar_one_or_none()
        if not item:
            raise HTTPException(404, f"meta item not found: {item_code}")
        if item.type.type_kind != "TAXONOMY":
            raise HTTPException(400, f"item {item_code} is not TAXONOMY")
        if item.selection_mode != "SINGLE":
            raise HTTPException(400, f"item {item_code} selection_mode must be SINGLE")

        link = item.type.taxonomy_link
        if not link:
            raise HTTPException(400, f"meta type {item.type.type_code} has no taxonomy link")

        # Resolve term by id or key
        term = (
            (await session.execute(select(Term).where(Term.term_id == payload.term_key_or_id))).scalar_one_or_none()
            or (
                await session.execute(
                    select(Term).where(
                        Term.taxonomy_id == link.taxonomy_id,
                        Term.term_key == payload.term_key_or_id,
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
        v = CustomMetaValueVersion(
            value_id=mv.value_id,
            version_no=version_no,
            taxonomy_term_id=term.term_id,
        )
        session.add(v)
        await session.flush()
        mv.current_version_id = v.version_id
        return v.version_id


async def set_meta_value_taxonomy_multi(
    session: AsyncSession,
    *,
    target_type: str,
    target_id: str,
    item_code: str,
    payload: MetaValueTaxMulti,
) -> str:
    async with session.begin():
        item = (await session.execute(select(CustomMetaItem).where(CustomMetaItem.item_code == item_code))).scalar_one_or_none()
        if not item:
            raise HTTPException(404, f"meta item not found: {item_code}")
        if item.type.type_kind != "TAXONOMY":
            raise HTTPException(400, f"item {item_code} is not TAXONOMY")
        if item.selection_mode != "MULTI":
            raise HTTPException(400, f"item {item_code} selection_mode must be MULTI")

        link = item.type.taxonomy_link
        if not link:
            raise HTTPException(400, f"meta type {item.type.type_code} has no taxonomy link")

        # Resolve all terms (id or key)
        terms: list[Term] = []
        for key in payload.term_keys_or_ids:
            term = (
                (await session.execute(select(Term).where(Term.term_id == key))).scalar_one_or_none()
                or (
                    await session.execute(
                        select(Term).where(
                            Term.taxonomy_id == link.taxonomy_id,
                            Term.term_key == key,
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
        v = CustomMetaValueVersion(value_id=mv.value_id, version_no=version_no)
        session.add(v)
        await session.flush()

        # Link N terms
        for t in terms:
            session.add(CustomMetaValueVersionTerm(version_id=v.version_id, term_id=t.term_id))

        mv.current_version_id = v.version_id
        return v.version_id
