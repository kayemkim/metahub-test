"""
Taxonomy API 테스트 - 수정된 버전
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.main import app as fastapi_app
from app.db.base import Base
from app.core.deps import get_session
import app.models

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

async def get_test_session():
    """테스트용 세션 생성"""
    engine = create_async_engine(TEST_DATABASE_URL)
    
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    TestSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    session = TestSessionLocal()
    try:
        yield session
    finally:
        await session.close()
        await engine.dispose()

# Override dependency for testing
fastapi_app.dependency_overrides[get_session] = get_test_session

client = TestClient(fastapi_app)


class TestTaxonomyAPI:
    """Taxonomy API 테스트 클래스"""
    
    def test_list_terms_not_found(self):
        """존재하지 않는 taxonomy 조회 테스트"""
        response = client.get("/api/v1/taxonomy/NONEXISTENT/terms")
        
        assert response.status_code == 404
        assert response.json()["detail"] == "taxonomy not found"
    
    def test_put_term_content_not_found(self):
        """존재하지 않는 term에 content 업데이트 테스트"""
        fake_term_id = "00000000-0000-0000-0000-000000000000"
        content_data = {
            "body_markdown": "# Test Content",
            "author": "test_user"
        }
        
        response = client.put(f"/api/v1/taxonomy/terms/{fake_term_id}/content", json=content_data)
        
        assert response.status_code == 404
        assert response.json()["detail"] == "term not found"
    
    def test_various_invalid_requests(self):
        """다양한 잘못된 요청 테스트"""
        # Invalid taxonomy code
        response1 = client.get("/api/v1/taxonomy/INVALID123/terms")
        assert response1.status_code == 404
        
        # Invalid term ID format  
        response2 = client.put("/api/v1/taxonomy/terms/invalid-id/content", json={})
        assert response2.status_code == 404
        
        # Empty taxonomy code
        response3 = client.get("/api/v1/taxonomy//terms")
        # This might be 404 or 405 depending on routing
        assert response3.status_code in [404, 405]
    
    def test_taxonomy_endpoints_exist(self):
        """Taxonomy 엔드포인트가 존재하는지 확인"""
        # Check that the routes are registered
        routes = [route.path for route in fastapi_app.routes]
        
        # Should have routes with taxonomy patterns
        taxonomy_routes = [route for route in routes if "taxonomy" in route]
        assert len(taxonomy_routes) > 0, f"No taxonomy routes found in: {routes}"
        
        # The 404 responses prove the endpoints exist but data is missing
        # which is expected without a proper database setup