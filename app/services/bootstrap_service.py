from sqlalchemy.ext.asyncio import AsyncSession

from app.core.meta_types import (
    SYSTEM_META_GROUPS,
    SYSTEM_META_ITEMS,
    get_meta_item_type_kind,
)
from app.models.codeset import Code, CodeSet, CodeVersion
from app.models.meta_types import (
    CustomMetaGroup,
    CustomMetaItem,
)
from app.models.taxonomy import Taxonomy, Term


async def bootstrap_demo(session: AsyncSession):
    """Create a sample taxonomy, codeset, meta types/items for quick manual tests."""
    # Let the caller handle the transaction
    tax = Taxonomy(taxonomy_code="DATA_DOMAIN", name="Data Domain")
    session.add(tax)
    await session.flush()

    # Terms (flat for demo)
    t_fin = Term(taxonomy_id=tax.taxonomy_id, term_key="FIN", display_name="Finance")
    t_hr = Term(taxonomy_id=tax.taxonomy_id, term_key="HR", display_name="Human Resources")
    session.add_all([t_fin, t_hr])

    cs = CodeSet(codeset_code="PII_LEVEL", name="PII Level")
    session.add(cs)
    await session.flush()

    c_public = Code(codeset_id=cs.codeset_id, code_key="PUBLIC")
    c_restricted = Code(codeset_id=cs.codeset_id, code_key="RESTRICTED")
    session.add_all([c_public, c_restricted])
    await session.flush()

    # seed code versions and move pointers
    for code, label in [(c_public, "Public"), (c_restricted, "Restricted")]:
        vno = 1
        ver = CodeVersion(code_id=code.code_id, version_no=vno, label_default=label)
        session.add(ver)
        await session.flush()
        code.current_version_id = ver.code_version_id

    # Meta types are now managed in code - no database records needed!

    # Create meta groups from code definitions
    meta_groups = {}
    for group_def in SYSTEM_META_GROUPS.values():
        grp = CustomMetaGroup(
            group_code=group_def.code,
            display_name=group_def.display_name,
            sort_order=group_def.sort_order
        )
        session.add(grp)
        meta_groups[group_def.code] = grp
    await session.flush()

    # Create meta items from code definitions
    for item_def in SYSTEM_META_ITEMS.values():
        # Get type_kind from code instead of database
        type_kind = get_meta_item_type_kind(item_def.code)

        item = CustomMetaItem(
            item_code=item_def.code,
            display_name=item_def.display_name,
            group_id=meta_groups[item_def.group_code].group_id,
            type_kind=type_kind.value,  # Store directly in item
            is_required=item_def.is_required,
            selection_mode=item_def.selection_mode,
            default_json=item_def.default_json
        )
        session.add(item)
