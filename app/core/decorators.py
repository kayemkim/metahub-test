"""
Transaction management decorators
"""
from functools import wraps
from typing import Callable, Any
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import transaction_manager
import logging

logger = logging.getLogger(__name__)


def transactional(func: Callable) -> Callable:
    """
    Decorator that automatically handles database transactions
    
    Usage:
        @transactional
        async def some_service_function(session: AsyncSession, ...):
            # This will automatically commit/rollback
            pass
    """
    @wraps(func)
    async def wrapper(*args, **kwargs) -> Any:
        # First argument should be the session
        if not args or not isinstance(args[0], AsyncSession):
            raise ValueError("First argument must be AsyncSession")
        
        session = args[0]
        
        try:
            async with transaction_manager(session):
                result = await func(*args, **kwargs)
                return result
        except Exception as e:
            logger.error(f"Transaction failed in {func.__name__}: {e}")
            raise
    
    return wrapper


def endpoint_transaction(func: Callable) -> Callable:
    """
    Decorator for API endpoints that need transaction management
    Expects session to be in kwargs as 'session'
    """
    @wraps(func)
    async def wrapper(*args, **kwargs) -> Any:
        session = kwargs.get('session')
        if not session or not isinstance(session, AsyncSession):
            raise ValueError("session parameter is required and must be AsyncSession")
        
        try:
            async with transaction_manager(session):
                result = await func(*args, **kwargs)
                return result
        except Exception as e:
            logger.error(f"Endpoint transaction failed in {func.__name__}: {e}")
            raise
    
    return wrapper


# Usage example:
"""
@router.put("/meta-values/{target_type}/{target_id}/string/{item_code}")
@endpoint_transaction  
async def set_string_value(
    target_type: str,
    target_id: str,
    item_code: str,
    data: MetaValueString,
    session: AsyncSession = Depends(get_session)
):
    # Transaction automatically handled
    version_id = await set_meta_value_string(
        session, target_type, target_id, item_code, data
    )
    return {"version_id": version_id}
"""