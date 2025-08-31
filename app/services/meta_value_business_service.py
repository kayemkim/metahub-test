"""
Business service for meta values with @transactional decorator
Clean separation: Repository(data) ← Service(business) ← API(presentation)
"""
import json
from datetime import datetime
from typing import Optional
from fastapi import HTTPException

from app.core.database import transactional, get_current_session
from app.core.meta_types import MetaTypeKind, get_meta_item_type_kind
from app.repositories.meta_value_repository import MetaValueRepository
from app.models.meta_values import CustomMetaValue, CustomMetaValueVersion
from app.schemas.base import (
    MetaValuePrimitive, 
    MetaValueString, 
    MetaValueCode,
    MetaValueTaxSingle,
    MetaValueTaxMulti
)


class MetaValueBusinessService:
    """
    Business service for meta value operations
    Uses @transactional decorator for automatic transaction management
    """
    
    def __init__(self, repository: MetaValueRepository):
        self.repo = repository
    
    @transactional()
    async def set_primitive_value(
        self,
        target_type: str,
        target_id: str, 
        item_code: str,
        payload: MetaValuePrimitive
    ) -> str:
        """Set primitive meta value"""
        # Code-based validation
        item_type_kind = get_meta_item_type_kind(item_code)
        if item_type_kind != MetaTypeKind.PRIMITIVE:
            raise HTTPException(400, f"item {item_code} is not PRIMITIVE, it's {item_type_kind}")
        
        # Get meta item
        item = await self.repo.get_meta_item_by_code(item_code)
        if not item:
            raise HTTPException(404, f"meta item not found: {item_code}")
        
        # Get or create meta value
        meta_value = await self.repo.get_meta_value(target_type, target_id, item.item_id)
        if not meta_value:
            meta_value = CustomMetaValue(
                target_type=target_type,
                target_id=target_id,
                item_id=item.item_id,
                created_at=datetime.utcnow()
            )
            meta_value = await self.repo.create_meta_value(meta_value)
        
        # Close previous version if exists
        if meta_value.current_version_id:
            await self.repo.close_previous_version(meta_value.current_version_id)
        
        # Create new version
        version = await self.repo.create_meta_value_version(meta_value, {
            'value_json': json.dumps(payload.value_json),
            'author': payload.author,
            'reason': payload.reason
        })
        
        # Update current version reference
        await self.repo.update_meta_value_current_version(meta_value, version.version_id)
        
        return version.version_id
    
    @transactional()
    async def set_string_value(
        self,
        target_type: str,
        target_id: str,
        item_code: str, 
        payload: MetaValueString
    ) -> str:
        """Set string meta value with JSON wrapping"""
        # Code-based validation
        item_type_kind = get_meta_item_type_kind(item_code)
        if item_type_kind != MetaTypeKind.STRING:
            raise HTTPException(400, f"item {item_code} is not STRING, it's {item_type_kind}")
        
        # Get meta item
        item = await self.repo.get_meta_item_by_code(item_code)
        if not item:
            raise HTTPException(404, f"meta item not found: {item_code}")
        
        # Get or create meta value
        meta_value = await self.repo.get_meta_value(target_type, target_id, item.item_id)
        if not meta_value:
            meta_value = CustomMetaValue(
                target_type=target_type,
                target_id=target_id,
                item_id=item.item_id,
                created_at=datetime.utcnow()
            )
            meta_value = await self.repo.create_meta_value(meta_value)
        
        # Close previous version
        if meta_value.current_version_id:
            await self.repo.close_previous_version(meta_value.current_version_id)
        
        # Create new version with JSON wrapping
        version = await self.repo.create_meta_value_version(meta_value, {
            'value_json': json.dumps({"value": payload.value_string}),
            'author': payload.author,
            'reason': payload.reason
        })
        
        # Update current version reference
        await self.repo.update_meta_value_current_version(meta_value, version.version_id)
        
        return version.version_id
    
    @transactional()
    async def set_codeset_value(
        self,
        target_type: str,
        target_id: str,
        item_code: str,
        payload: MetaValueCode
    ) -> str:
        """Set codeset meta value"""
        # Code-based validation
        item_type_kind = get_meta_item_type_kind(item_code)
        if item_type_kind != MetaTypeKind.CODESET:
            raise HTTPException(400, f"item {item_code} is not CODESET, it's {item_type_kind}")
        
        # Get meta item
        item = await self.repo.get_meta_item_by_code(item_code)
        if not item:
            raise HTTPException(404, f"meta item not found: {item_code}")
        
        # Validate code exists
        code = await self.repo.get_code_by_key_or_id(payload.code_key_or_id)
        if not code:
            raise HTTPException(400, f"invalid code: {payload.code_key_or_id}")
        
        # Get or create meta value
        meta_value = await self.repo.get_meta_value(target_type, target_id, item.item_id)
        if not meta_value:
            meta_value = CustomMetaValue(
                target_type=target_type,
                target_id=target_id,
                item_id=item.item_id,
                created_at=datetime.utcnow()
            )
            meta_value = await self.repo.create_meta_value(meta_value)
        
        # Close previous version
        if meta_value.current_version_id:
            await self.repo.close_previous_version(meta_value.current_version_id)
        
        # Create new version
        version = await self.repo.create_meta_value_version(meta_value, {
            'code_id': code.code_id,
            'author': payload.author,
            'reason': payload.reason
        })
        
        # Update current version reference
        await self.repo.update_meta_value_current_version(meta_value, version.version_id)
        
        return version.version_id
    
    @transactional()
    async def set_taxonomy_single_value(
        self,
        target_type: str,
        target_id: str,
        item_code: str,
        payload: MetaValueTaxSingle
    ) -> str:
        """Set single taxonomy meta value"""
        # Code-based validation
        item_type_kind = get_meta_item_type_kind(item_code)
        if item_type_kind != MetaTypeKind.TAXONOMY:
            raise HTTPException(400, f"item {item_code} is not TAXONOMY, it's {item_type_kind}")
        
        # Get meta item and validate selection mode
        item = await self.repo.get_meta_item_by_code(item_code)
        if not item:
            raise HTTPException(404, f"meta item not found: {item_code}")
        
        if item.selection_mode != "SINGLE":
            raise HTTPException(400, f"item {item_code} selection mode must be SINGLE, got {item.selection_mode}")
        
        # Validate term exists
        term = await self.repo.get_term_by_key_or_id(payload.term_key_or_id)
        if not term:
            raise HTTPException(400, f"invalid term: {payload.term_key_or_id}")
        
        # Get or create meta value
        meta_value = await self.repo.get_meta_value(target_type, target_id, item.item_id)
        if not meta_value:
            meta_value = CustomMetaValue(
                target_type=target_type,
                target_id=target_id,
                item_id=item.item_id,
                created_at=datetime.utcnow()
            )
            meta_value = await self.repo.create_meta_value(meta_value)
        
        # Close previous version
        if meta_value.current_version_id:
            await self.repo.close_previous_version(meta_value.current_version_id)
        
        # Create new version
        version = await self.repo.create_meta_value_version(meta_value, {
            'taxonomy_term_id': term.term_id,
            'author': payload.author,
            'reason': payload.reason
        })
        
        # Update current version reference
        await self.repo.update_meta_value_current_version(meta_value, version.version_id)
        
        return version.version_id
    
    @transactional()
    async def set_taxonomy_multi_value(
        self,
        target_type: str,
        target_id: str,
        item_code: str,
        payload: MetaValueTaxMulti
    ) -> str:
        """Set multiple taxonomy meta values"""
        # Code-based validation
        item_type_kind = get_meta_item_type_kind(item_code)
        if item_type_kind != MetaTypeKind.TAXONOMY:
            raise HTTPException(400, f"item {item_code} is not TAXONOMY, it's {item_type_kind}")
        
        # Get meta item and validate selection mode
        item = await self.repo.get_meta_item_by_code(item_code)
        if not item:
            raise HTTPException(404, f"meta item not found: {item_code}")
        
        if item.selection_mode != "MULTI":
            raise HTTPException(400, f"item {item_code} selection mode must be MULTI, got {item.selection_mode}")
        
        # Validate all terms exist
        term_ids = []
        for term_key_or_id in payload.term_keys_or_ids:
            term = await self.repo.get_term_by_key_or_id(term_key_or_id)
            if not term:
                raise HTTPException(400, f"invalid term: {term_key_or_id}")
            term_ids.append(term.term_id)
        
        # Get or create meta value
        meta_value = await self.repo.get_meta_value(target_type, target_id, item.item_id)
        if not meta_value:
            meta_value = CustomMetaValue(
                target_type=target_type,
                target_id=target_id,
                item_id=item.item_id,
                created_at=datetime.utcnow()
            )
            meta_value = await self.repo.create_meta_value(meta_value)
        
        # Close previous version
        if meta_value.current_version_id:
            await self.repo.close_previous_version(meta_value.current_version_id)
        
        # Create new version
        version = await self.repo.create_meta_value_version(meta_value, {
            'author': payload.author,
            'reason': payload.reason
        })
        
        # Add terms to version
        await self.repo.add_version_terms(version.version_id, term_ids)
        
        # Update current version reference
        await self.repo.update_meta_value_current_version(meta_value, version.version_id)
        
        return version.version_id
    
    @transactional(read_only=True)
    async def get_meta_values_for_target(
        self, 
        target_type: str, 
        target_id: str
    ):
        """Get all meta values for a target (read-only transaction)"""
        meta_values = await self.repo.get_meta_values_for_target(target_type, target_id)
        
        # Build response with detailed version data
        response_values = []
        for meta_value in meta_values:
            # Process each meta value and build response
            # (Implementation details from original API code)
            pass
            
        return response_values