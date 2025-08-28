"""
Health 엔드포인트 테스트 - 간단한 버전
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestHealthEndpoint:
    """Health 엔드포인트 테스트 클래스"""
    
    def test_health_check(self):
        """헬스체크 엔드포인트 기본 테스트"""
        response = client.get("/api/v1/health")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "ok" in data
        assert "ts" in data
        assert data["ok"] is True
        assert isinstance(data["ts"], str)
    
    def test_health_check_timestamp_format(self):
        """헬스체크 타임스탬프 포맷 검증"""
        response = client.get("/api/v1/health")
        
        assert response.status_code == 200
        data = response.json()
        
        # ISO 8601 format check (basic validation)
        timestamp = data["ts"]
        assert "T" in timestamp
        assert ":" in timestamp
    
    def test_health_check_multiple_calls(self):
        """헬스체크 여러 번 호출 테스트"""
        # First call
        response1 = client.get("/api/v1/health")
        assert response1.status_code == 200
        
        # Second call
        response2 = client.get("/api/v1/health")
        assert response2.status_code == 200
        
        # Both should be successful
        data1 = response1.json()
        data2 = response2.json()
        
        assert data1["ok"] is True
        assert data2["ok"] is True
        
        # Both should have timestamps
        assert "ts" in data1
        assert "ts" in data2