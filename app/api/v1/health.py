from fastapi import APIRouter

from app.db.base import utcnow

router = APIRouter(tags=["health"])


@router.get("/health")
async def health():
    """Health check endpoint"""
    return {"ok": True, "ts": utcnow().isoformat()}
