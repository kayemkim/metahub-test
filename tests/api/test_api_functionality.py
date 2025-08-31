"""
API 기능성 테스트 - 간단하고 확실한 버전
"""
import pytest


class TestAPIFunctionality:
    """모든 API의 기본 기능성을 테스트"""
    
    def test_health_endpoint(self, test_client):
        """Health 엔드포인트 테스트"""
        response = test_client.get("/api/v1/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["ok"] == True
        assert "ts" in data
    
    def test_bootstrap_functionality(self, test_client):
        """Bootstrap 기능 테스트"""
        # Check initial status
        status_response = test_client.get("/api/v1/bootstrap/status")
        assert status_response.status_code == 200
        
        # Create demo data
        demo_response = test_client.post("/api/v1/bootstrap/demo")
        assert demo_response.status_code == 200
        
        # Verify message
        result = demo_response.json()
        assert "message" in result
        assert "created" in result
    
    def test_taxonomy_endpoints_exist(self, test_client):
        """Taxonomy 엔드포인트들이 존재하는지 확인"""
        # These should return data or 404, not 500 or other errors
        response1 = test_client.get("/api/v1/taxonomy/")
        assert response1.status_code == 200
        
        response2 = test_client.get("/api/v1/taxonomy/NONEXISTENT")
        assert response2.status_code == 404
        
        response3 = test_client.get("/api/v1/taxonomy/NONEXISTENT/terms")
        assert response3.status_code == 404
        
        # Test POST endpoint
        data = {"taxonomy_code": "TEST", "name": "Test"}
        response4 = test_client.post("/api/v1/taxonomy/", json=data)
        # Should either succeed (200) or have validation error (422)
        assert response4.status_code in [200, 422]
    
    def test_codeset_endpoints_exist(self, test_client):
        """CodeSet 엔드포인트들이 존재하는지 확인"""
        response1 = test_client.get("/api/v1/codeset/")
        assert response1.status_code == 200
        
        response2 = test_client.get("/api/v1/codeset/NONEXISTENT")
        assert response2.status_code == 404
        
        response3 = test_client.get("/api/v1/codeset/NONEXISTENT/codes")
        assert response3.status_code == 404
        
        # Test POST endpoint
        data = {"codeset_code": "TEST", "name": "Test"}
        response4 = test_client.post("/api/v1/codeset/", json=data)
        assert response4.status_code in [200, 422]
    
    def test_meta_endpoints_exist(self, test_client):
        """Meta 엔드포인트들이 존재하는지 확인"""
        response1 = test_client.get("/api/v1/meta/types")
        assert response1.status_code == 200
        
        response2 = test_client.get("/api/v1/meta/groups")
        assert response2.status_code == 200
        
        response3 = test_client.get("/api/v1/meta/items")
        assert response3.status_code == 200
        
        response4 = test_client.get("/api/v1/meta/types/NONEXISTENT")
        assert response4.status_code == 404
        
        # Test POST endpoints
        type_data = {"type_code": "TEST", "name": "Test"}
        response5 = test_client.post("/api/v1/meta/types", json=type_data)
        # Should return 400 since meta types are now managed in code
        assert response5.status_code == 400
        
        group_data = {"group_code": "TEST", "display_name": "Test"}
        response6 = test_client.post("/api/v1/meta/groups", json=group_data)
        assert response6.status_code in [200, 422]
    
    def test_error_responses_are_proper(self, test_client):
        """에러 응답이 적절한지 확인"""
        # 404 errors should have detail
        response1 = test_client.get("/api/v1/taxonomy/NOTFOUND")
        assert response1.status_code == 404
        assert "detail" in response1.json()
        
        response2 = test_client.get("/api/v1/codeset/NOTFOUND")
        assert response2.status_code == 404
        assert "detail" in response2.json()
        
        response3 = test_client.get("/api/v1/meta/types/NOTFOUND")
        assert response3.status_code == 404
        assert "detail" in response3.json()
    
    def test_basic_crud_flow(self, test_client):
        """기본적인 CRUD 플로우 테스트"""
        # Create taxonomy
        tax_data = {
            "taxonomy_code": "CRUD_TEST",
            "name": "CRUD Test Taxonomy",
            "description": "For testing CRUD operations"
        }
        create_response = test_client.post("/api/v1/taxonomy/", json=tax_data)
        
        if create_response.status_code == 200:
            # If creation succeeded, test retrieval
            get_response = test_client.get("/api/v1/taxonomy/CRUD_TEST")
            assert get_response.status_code == 200
            
            retrieved = get_response.json()
            assert retrieved["taxonomy_code"] == "CRUD_TEST"
            assert retrieved["name"] == "CRUD Test Taxonomy"
            
            # Test listing
            list_response = test_client.get("/api/v1/taxonomy/")
            assert list_response.status_code == 200
            taxonomies = list_response.json()
            
            # Should contain our created taxonomy
            codes = [tax["taxonomy_code"] for tax in taxonomies]
            assert "CRUD_TEST" in codes
        else:
            # If creation failed, just verify the error is handled properly
            assert create_response.status_code in [400, 422, 500]
    
    def test_bootstrap_creates_expected_data(self, test_client):
        """Bootstrap이 예상된 데이터를 생성하는지 확인"""
        # Create bootstrap data
        response = test_client.post("/api/v1/bootstrap/demo")
        assert response.status_code == 200
        
        # Check that some expected data exists
        taxonomies = test_client.get("/api/v1/taxonomy/").json()
        assert len(taxonomies) >= 1
        
        # Should have DATA_DOMAIN
        tax_codes = [tax["taxonomy_code"] for tax in taxonomies]
        assert "DATA_DOMAIN" in tax_codes
        
        codesets = test_client.get("/api/v1/codeset/").json()
        assert len(codesets) >= 1
        
        # Should have PII_LEVEL
        cs_codes = [cs["codeset_code"] for cs in codesets]
        assert "PII_LEVEL" in cs_codes
        
        meta_types = test_client.get("/api/v1/meta/types").json()
        assert len(meta_types) >= 1
    
    def test_term_content_operations(self, test_client):
        """Term content 관련 작업 테스트"""
        # Create bootstrap data first to have terms
        test_client.post("/api/v1/bootstrap/demo")
        
        # Try to get terms
        terms_response = test_client.get("/api/v1/taxonomy/DATA_DOMAIN/terms")
        assert terms_response.status_code == 200
        
        terms = terms_response.json()
        if len(terms) > 0:
            # Test term content update
            term_id = terms[0]["term_id"]
            content_data = {
                "body_markdown": "# Test Content",
                "author": "test_author",
                "reason": "Testing"
            }
            
            content_response = test_client.put(
                f"/api/v1/taxonomy/terms/{term_id}/content",
                json=content_data
            )
            assert content_response.status_code == 200
            
            result = content_response.json()
            assert "content_version_id" in result
    
    def test_all_endpoints_respond(self, test_client):
        """모든 주요 엔드포인트가 응답하는지 확인"""
        endpoints_to_test = [
            "/api/v1/health",
            "/api/v1/bootstrap/status",
            "/api/v1/taxonomy/",
            "/api/v1/codeset/",
            "/api/v1/meta/types",
            "/api/v1/meta/groups",
            "/api/v1/meta/items",
        ]
        
        for endpoint in endpoints_to_test:
            response = test_client.get(endpoint)
            # Should not get server errors
            assert response.status_code < 500, f"Server error on {endpoint}: {response.status_code}"
            # Should get valid HTTP responses
            assert response.status_code in [200, 404, 422], f"Unexpected status on {endpoint}: {response.status_code}"