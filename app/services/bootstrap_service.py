from sqlalchemy.ext.asyncio import AsyncSession

from app.models.codeset import Code, CodeSet, CodeVersion
from app.models.meta_types import (
    CustomMetaGroup,
    CustomMetaItem,
    CustomMetaType,
    CustomMetaTypeCodeSet,
    CustomMetaTypeTaxonomy,
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

    # Meta types
    mt_prim = CustomMetaType(type_code="RETENTION_DAYS", name="Retention (days)")
    mt_code = CustomMetaType(type_code="PII_LEVEL_TYPE", name="PII Level", type_kind="CODESET")
    mt_tax = CustomMetaType(type_code="DOMAIN", name="Domain", type_kind="TAXONOMY")
    session.add_all([mt_prim, mt_code, mt_tax])
    await session.flush()

    session.add(CustomMetaTypeCodeSet(type_id=mt_code.type_id, codeset_id=cs.codeset_id))
    session.add(CustomMetaTypeTaxonomy(type_id=mt_tax.type_id, taxonomy_id=tax.taxonomy_id))

    grp = CustomMetaGroup(group_code="BIZ_META", display_name="Business Meta")
    session.add(grp)
    await session.flush()

    item_ret = CustomMetaItem(item_code="retention_days", display_name="Retention Days", group_id=grp.group_id, type_id=mt_prim.type_id)
    item_pii = CustomMetaItem(item_code="pii_level", display_name="PII Level", group_id=grp.group_id, type_id=mt_code.type_id)
    item_dom = CustomMetaItem(item_code="domain", display_name="Domain", group_id=grp.group_id, type_id=mt_tax.type_id, selection_mode="SINGLE")
    session.add_all([item_ret, item_pii, item_dom])
