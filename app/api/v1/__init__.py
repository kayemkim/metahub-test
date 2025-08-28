from fastapi import APIRouter

from app.api.v1 import bootstrap, codeset, health, meta_types, meta_values, taxonomy

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(health.router)
api_router.include_router(taxonomy.router)
api_router.include_router(codeset.router)
api_router.include_router(meta_types.router)
api_router.include_router(meta_values.router)
api_router.include_router(bootstrap.router)
