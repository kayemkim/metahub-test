"""
테스트용 공통 fixture
"""
import asyncio
import uuid

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.api.v1 import api_router
from app.core.config import get_settings
from app.core.database import _current_session
from app.core.deps import get_session
from app.db.base import Base


@pytest.fixture(scope="function")
def test_client():
    """각 테스트마다 완전히 새로운 앱과 데이터베이스 생성"""
    # 각 테스트마다 완전히 고유한 파일 DB (원래 방식)
    unique_id = str(uuid.uuid4())
    test_db_url = f"sqlite+aiosqlite:///{unique_id}.db"

    # Test용 엔진과 세션 팩토리 생성
    engine = None

    async def get_test_session():
        nonlocal engine
        engine = create_async_engine(
            test_db_url,
            echo=False,
            connect_args={"check_same_thread": False}
        )

        # Create all tables
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        TestSessionLocal = sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
        session = TestSessionLocal()
        # Set session in context for @transactional to work
        token = _current_session.set(session)
        try:
            yield session
        finally:
            _current_session.reset(token)
            await session.close()

    # Create a completely new FastAPI app instance for this test
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        debug=settings.debug,
    )

    # Include routers
    app.include_router(api_router)

    # Override the dependency with our test session
    app.dependency_overrides[get_session] = get_test_session

    # Create test client
    try:
        with TestClient(app) as client:
            yield client
    finally:
        # Cleanup
        if engine:
            asyncio.run(engine.dispose())
        # Remove the temporary DB file
        import os
        if os.path.exists(f"{unique_id}.db"):
            os.remove(f"{unique_id}.db")
