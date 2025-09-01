from fastapi import FastAPI

import app.models  # Import to register all models
from app.api.v1 import api_router
from app.core.config import get_settings
from app.db.base import Base
from app.db.session import engine

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    debug=settings.debug,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Include API routes
app.include_router(api_router)


# Database tables are now managed by Alembic migrations
# No need for automatic table creation on startup
# Use: alembic upgrade head


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
