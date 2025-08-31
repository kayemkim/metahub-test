"""
Repository for meta value data access
Pure data access layer - no business logic, no transaction management
"""
from typing import Optional, List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.meta_values import CustomMetaValue, CustomMetaValueVersion, CustomMetaValueVersionTerm
from app.models.meta_types import CustomMetaItem
from app.models.codeset import Code, CodeVersion  
from app.models.taxonomy import Term
from app.services.utils import _next_version_no
from app.db.base import utcnow


class MetaValueRepository:
    """Repository for meta value operations"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_meta_item_by_code(self, item_code: str) -> Optional[CustomMetaItem]:
        """Get meta item by code"""
        stmt = select(CustomMetaItem).options(
            selectinload(CustomMetaItem.type)
        ).where(CustomMetaItem.item_code == item_code)
        
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_meta_value(
        self, 
        target_type: str, 
        target_id: str, 
        item_id: str
    ) -> Optional[CustomMetaValue]:
        """Get existing meta value"""
        stmt = select(CustomMetaValue).where(
            CustomMetaValue.target_type == target_type,
            CustomMetaValue.target_id == target_id,
            CustomMetaValue.item_id == item_id
        )
        
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def create_meta_value(self, meta_value: CustomMetaValue) -> CustomMetaValue:
        """Create new meta value"""
        self.session.add(meta_value)
        await self.session.flush()  # Get ID without commit
        return meta_value
    
    async def create_meta_value_version(self, meta_value: CustomMetaValue, version_data: dict) -> CustomMetaValueVersion:
        """Create new meta value version with proper version_no"""
        # Calculate next version number
        version_no = await _next_version_no(self.session, CustomMetaValueVersion, "value_id", meta_value.value_id)
        
        # Create version with proper fields
        version = CustomMetaValueVersion(
            value_id=meta_value.value_id,
            version_no=version_no,
            valid_from=utcnow(),
            **version_data
        )
        self.session.add(version)
        await self.session.flush()
        return version
    
    async def update_meta_value_current_version(
        self, 
        meta_value: CustomMetaValue, 
        version_id: str
    ) -> None:
        """Update current version reference"""
        meta_value.current_version_id = version_id
        await self.session.flush()
    
    async def close_previous_version(self, version_id: str) -> None:
        """Close previous version by setting valid_to"""
        version = await self.session.get(CustomMetaValueVersion, version_id, with_for_update=True)
        
        if version and version.valid_to is None:
            version.valid_to = utcnow()
            await self.session.flush()
    
    async def get_code_by_key_or_id(self, code_key_or_id: str) -> Optional[Code]:
        """Get code by key or ID"""
        stmt = select(Code).options(
            selectinload(Code.current_version)
        ).where(
            (Code.code_key == code_key_or_id) | 
            (Code.code_id == code_key_or_id)
        )
        
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_term_by_key_or_id(self, term_key_or_id: str) -> Optional[Term]:
        """Get term by key or ID"""  
        stmt = select(Term).where(
            (Term.term_key == term_key_or_id) |
            (Term.term_id == term_key_or_id)
        )
        
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_meta_values_for_target(
        self, 
        target_type: str, 
        target_id: str
    ) -> List[CustomMetaValue]:
        """Get all meta values for a target"""
        stmt = select(CustomMetaValue).options(
            selectinload(CustomMetaValue.item).selectinload(CustomMetaItem.type),
            selectinload(CustomMetaValue.current_version)
        ).where(
            CustomMetaValue.target_type == target_type,
            CustomMetaValue.target_id == target_id
        )
        
        result = await self.session.execute(stmt)
        return result.scalars().all()
    
    async def get_meta_value_version(self, version_id: str) -> Optional[CustomMetaValueVersion]:
        """Get meta value version by ID"""
        stmt = select(CustomMetaValueVersion).where(
            CustomMetaValueVersion.version_id == version_id
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def add_version_terms(self, version_id: str, term_ids: List[str]) -> None:
        """Add terms to version (for multi-taxonomy)"""
        for term_id in term_ids:
            version_term = CustomMetaValueVersionTerm(
                version_id=version_id,
                term_id=term_id
            )
            self.session.add(version_term)
        await self.session.flush()
    
    async def get_version_terms(self, version_id: str) -> List[CustomMetaValueVersionTerm]:
        """Get terms for a version"""
        stmt = select(CustomMetaValueVersionTerm).options(
            selectinload(CustomMetaValueVersionTerm.term)
        ).where(CustomMetaValueVersionTerm.version_id == version_id)
        
        result = await self.session.execute(stmt)
        return result.scalars().all()