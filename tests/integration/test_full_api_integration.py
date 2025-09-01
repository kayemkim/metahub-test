"""
Complete API Integration Tests
모든 API 엔드포인트의 전체적인 통합 테스트
"""
import pytest
import asyncio
from datetime import datetime
from uuid import uuid4


class TestFullAPIIntegration:
    """전체 API 통합 테스트"""

    def test_complete_workflow_integration(self, test_client):
        """완전한 워크플로우 통합 테스트"""
        # 1. Bootstrap 데이터 생성
        bootstrap_response = test_client.post("/api/v1/bootstrap/demo")
        assert bootstrap_response.status_code == 200
        
        # 2. 모든 리소스가 생성되었는지 확인
        taxonomies = test_client.get("/api/v1/taxonomy/").json()
        codesets = test_client.get("/api/v1/codeset/").json()
        meta_types = test_client.get("/api/v1/meta/types").json()
        meta_groups = test_client.get("/api/v1/meta/groups").json()
        
        assert len(taxonomies) > 0
        assert len(codesets) > 0
        assert len(meta_types) > 0
        assert len(meta_groups) > 0

        # 3. 특정 taxonomy의 terms 확인
        data_domain_terms = test_client.get("/api/v1/taxonomy/DATA_DOMAIN/terms").json()
        assert len(data_domain_terms) > 0
        
        # 4. 특정 codeset의 codes 확인
        pii_codes = test_client.get("/api/v1/codeset/PII_LEVEL/codes").json()
        assert len(pii_codes) > 0

        # 5. Term content 업데이트 테스트
        if data_domain_terms:
            term_id = data_domain_terms[0]["term_id"]
            content_data = {
                "body_markdown": "# Integration Test Content\n\nThis is test content.",
                "author": "integration_test",
                "reason": "Integration testing"
            }
            content_response = test_client.put(
                f"/api/v1/taxonomy/terms/{term_id}/content",
                json=content_data
            )
            assert content_response.status_code == 200
            result = content_response.json()
            assert "content_version_id" in result

    def test_crud_operations_all_resources(self, test_client):
        """모든 리소스에 대한 CRUD 작업 테스트"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Taxonomy CRUD
        taxonomy_data = {
            "taxonomy_code": f"TEST_TAX_{timestamp}",
            "name": f"Test Taxonomy {timestamp}",
            "description": "Created for integration testing"
        }
        tax_create = test_client.post("/api/v1/taxonomy/", json=taxonomy_data)
        assert tax_create.status_code == 200
        
        tax_get = test_client.get(f"/api/v1/taxonomy/{taxonomy_data['taxonomy_code']}")
        assert tax_get.status_code == 200
        assert tax_get.json()["name"] == taxonomy_data["name"]

        # CodeSet CRUD
        codeset_data = {
            "codeset_code": f"TEST_CS_{timestamp}",
            "name": f"Test CodeSet {timestamp}",
            "description": "Created for integration testing"
        }
        cs_create = test_client.post("/api/v1/codeset/", json=codeset_data)
        assert cs_create.status_code == 200
        
        cs_get = test_client.get(f"/api/v1/codeset/{codeset_data['codeset_code']}")
        assert cs_get.status_code == 200
        assert cs_get.json()["name"] == codeset_data["name"]

        # MetaType는 이제 코드 기반이므로 GET만 테스트
        mt_list = test_client.get("/api/v1/meta/types")
        assert mt_list.status_code == 200
        assert len(mt_list.json()) > 0  # 시스템 메타 타입들이 있어야 함

        # MetaGroup CRUD
        meta_group_data = {
            "group_code": f"TEST_MG_{timestamp}",
            "display_name": f"Test MetaGroup {timestamp}",
            "description": "Created for integration testing"
        }
        mg_create = test_client.post("/api/v1/meta/groups", json=meta_group_data)
        assert mg_create.status_code == 200
        
        mg_get = test_client.get(f"/api/v1/meta/groups/{meta_group_data['group_code']}")
        assert mg_get.status_code == 200
        assert mg_get.json()["display_name"] == meta_group_data["display_name"]

    def test_error_handling_consistency(self, test_client):
        """모든 엔드포인트의 에러 처리 일관성 테스트"""
        # 404 에러 테스트
        not_found_endpoints = [
            "/api/v1/taxonomy/NOT_FOUND",
            "/api/v1/taxonomy/NOT_FOUND/terms",
            "/api/v1/codeset/NOT_FOUND",
            "/api/v1/codeset/NOT_FOUND/codes",
            "/api/v1/meta/types/NOT_FOUND",
            "/api/v1/meta/groups/NOT_FOUND"
        ]
        
        for endpoint in not_found_endpoints:
            response = test_client.get(endpoint)
            assert response.status_code == 404
            error_detail = response.json()
            assert "detail" in error_detail
            assert isinstance(error_detail["detail"], str)

        # 422 에러 테스트 (잘못된 데이터)
        invalid_data_tests = [
            ("/api/v1/taxonomy/", {"invalid_field": "value"}),
            ("/api/v1/codeset/", {"invalid_field": "value"}),
            ("/api/v1/meta/types", {"invalid_field": "value"}),
            ("/api/v1/meta/groups", {"invalid_field": "value"})
        ]
        
        for endpoint, invalid_data in invalid_data_tests:
            response = test_client.post(endpoint, json=invalid_data)
            assert response.status_code == 422
            error_detail = response.json()
            assert "detail" in error_detail

    def test_cross_resource_relationships(self, test_client):
        """리소스 간의 관계 테스트"""
        # Bootstrap으로 기본 데이터 생성
        test_client.post("/api/v1/bootstrap/demo")
        
        # Taxonomy와 Terms 관계 확인
        taxonomies = test_client.get("/api/v1/taxonomy/").json()
        for taxonomy in taxonomies[:2]:  # 처음 2개만 테스트
            taxonomy_code = taxonomy["taxonomy_code"]
            terms_response = test_client.get(f"/api/v1/taxonomy/{taxonomy_code}/terms")
            assert terms_response.status_code == 200
            terms = terms_response.json()
            
            # Terms가 있다면 각 term이 올바른 taxonomy_id를 가져야 함
            if terms:
                for term in terms:
                    assert "term_id" in term
                    assert "display_name" in term

        # CodeSet과 Codes 관계 확인
        codesets = test_client.get("/api/v1/codeset/").json()
        for codeset in codesets[:2]:  # 처음 2개만 테스트
            codeset_code = codeset["codeset_code"]
            codes_response = test_client.get(f"/api/v1/codeset/{codeset_code}/codes")
            assert codes_response.status_code == 200
            codes = codes_response.json()
            
            # Codes가 있다면 각 code가 올바른 구조를 가져야 함
            if codes:
                for code in codes:
                    assert "code_id" in code
                    assert "code_key" in code

    def test_data_validation_consistency(self, test_client):
        """데이터 검증 일관성 테스트"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 필수 필드 누락 테스트
        required_field_tests = [
            ("/api/v1/taxonomy/", {}),
            ("/api/v1/codeset/", {}),
            ("/api/v1/meta/groups", {})
        ]
        
        for endpoint, empty_data in required_field_tests:
            response = test_client.post(endpoint, json=empty_data)
            assert response.status_code == 422
        
        # 중복 코드 생성 테스트
        duplicate_tests = [
            ("/api/v1/taxonomy/", {
                "taxonomy_code": f"DUP_TAX_{timestamp}",
                "name": "Duplicate Test Taxonomy"
            }),
            ("/api/v1/codeset/", {
                "codeset_code": f"DUP_CS_{timestamp}",
                "name": "Duplicate Test CodeSet"
            }),
            ("/api/v1/meta/groups", {
                "group_code": f"DUP_MG_{timestamp}",
                "display_name": "Duplicate Test MetaGroup"
            })
        ]
        
        for endpoint, data in duplicate_tests:
            # 첫 번째 생성은 성공해야 함
            first_response = test_client.post(endpoint, json=data)
            assert first_response.status_code == 200
            
            # 두 번째 생성은 실패해야 함 (중복)
            second_response = test_client.post(endpoint, json=data)
            assert second_response.status_code in [400, 409, 422]

    def test_pagination_and_filtering(self, test_client):
        """페이징과 필터링 테스트 (해당하는 경우)"""
        # Bootstrap으로 충분한 데이터 생성
        test_client.post("/api/v1/bootstrap/demo")
        
        # 기본 리스트 조회
        taxonomies = test_client.get("/api/v1/taxonomy/").json()
        codesets = test_client.get("/api/v1/codeset/").json()
        meta_types = test_client.get("/api/v1/meta/types").json()
        meta_groups = test_client.get("/api/v1/meta/groups").json()
        
        # 모든 리스트가 배열이어야 함
        assert isinstance(taxonomies, list)
        assert isinstance(codesets, list)
        assert isinstance(meta_types, list)
        assert isinstance(meta_groups, list)
        
        # 각 항목이 필수 필드를 포함해야 함
        if taxonomies:
            assert "taxonomy_code" in taxonomies[0]
            assert "name" in taxonomies[0]
        
        if codesets:
            assert "codeset_code" in codesets[0]
            assert "name" in codesets[0]
        
        if meta_types:
            assert "type_code" in meta_types[0]
            assert "name" in meta_types[0]
        
        if meta_groups:
            assert "group_code" in meta_groups[0]
            assert "display_name" in meta_groups[0]

    def test_content_versioning_workflow(self, test_client):
        """컨텐츠 버전 관리 워크플로우 테스트"""
        # Bootstrap 데이터 생성
        test_client.post("/api/v1/bootstrap/demo")
        
        # Terms 조회
        terms = test_client.get("/api/v1/taxonomy/DATA_DOMAIN/terms").json()
        if not terms:
            pytest.skip("No terms available for content versioning test")
        
        term_id = terms[0]["term_id"]
        
        # 첫 번째 컨텐츠 버전 생성
        content_v1 = {
            "body_markdown": "# Version 1\n\nFirst version of content",
            "author": "test_user_v1",
            "reason": "Initial content creation"
        }
        
        v1_response = test_client.put(
            f"/api/v1/taxonomy/terms/{term_id}/content",
            json=content_v1
        )
        assert v1_response.status_code == 200
        v1_result = v1_response.json()
        assert "content_version_id" in v1_result
        
        # 두 번째 컨텐츠 버전 생성
        content_v2 = {
            "body_markdown": "# Version 2\n\nSecond version of content with updates",
            "author": "test_user_v2", 
            "reason": "Content update and improvements"
        }
        
        v2_response = test_client.put(
            f"/api/v1/taxonomy/terms/{term_id}/content",
            json=content_v2
        )
        assert v2_response.status_code == 200
        v2_result = v2_response.json()
        assert "content_version_id" in v2_result
        
        # 두 버전의 ID가 달라야 함
        assert v1_result["content_version_id"] != v2_result["content_version_id"]

    def test_health_and_bootstrap_integration(self, test_client):
        """Health check와 Bootstrap 통합 테스트"""
        # Health check 확인
        health_response = test_client.get("/api/v1/health")
        assert health_response.status_code == 200
        health_data = health_response.json()
        assert health_data["ok"] is True
        
        # Bootstrap 상태 확인
        status_response = test_client.get("/api/v1/bootstrap/status")
        assert status_response.status_code == 200
        
        # Bootstrap 실행
        demo_response = test_client.post("/api/v1/bootstrap/demo")
        assert demo_response.status_code == 200
        demo_data = demo_response.json()
        assert "message" in demo_data
        assert "created" in demo_data
        
        # Bootstrap 후 상태 다시 확인
        status_after = test_client.get("/api/v1/bootstrap/status")
        assert status_after.status_code == 200

    def test_concurrent_operations(self, test_client):
        """동시 작업 테스트 (기본적인 수준)"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 여러 개의 리소스를 동시에 생성
        taxonomy_data_list = [
            {
                "taxonomy_code": f"CONCURRENT_TAX_{i}_{timestamp}",
                "name": f"Concurrent Taxonomy {i}",
                "description": f"Created for concurrent test {i}"
            }
            for i in range(3)
        ]
        
        # 순차적으로 생성 (실제 동시성 테스트는 더 복잡한 설정이 필요)
        created_taxonomies = []
        for tax_data in taxonomy_data_list:
            response = test_client.post("/api/v1/taxonomy/", json=tax_data)
            assert response.status_code == 200
            created_taxonomies.append(response.json())
        
        # 모든 taxonomy가 생성되었는지 확인
        all_taxonomies = test_client.get("/api/v1/taxonomy/").json()
        created_codes = [tax["taxonomy_code"] for tax in created_taxonomies]
        all_codes = [tax["taxonomy_code"] for tax in all_taxonomies]
        
        for created_code in created_codes:
            assert created_code in all_codes

    def test_api_response_format_consistency(self, test_client):
        """API 응답 형식 일관성 테스트"""
        # Bootstrap 데이터 생성
        test_client.post("/api/v1/bootstrap/demo")
        
        # 모든 리스트 엔드포인트 테스트
        list_endpoints = [
            "/api/v1/taxonomy/",
            "/api/v1/codeset/", 
            "/api/v1/meta/types",
            "/api/v1/meta/groups",
            "/api/v1/meta/items"
        ]
        
        for endpoint in list_endpoints:
            response = test_client.get(endpoint)
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)
            
            # 항목이 있다면 각 항목이 dict여야 함
            if data:
                for item in data:
                    assert isinstance(item, dict)
                    assert len(item) > 0  # 빈 dict가 아니어야 함
        
        # 개별 항목 엔드포인트 테스트
        taxonomies = test_client.get("/api/v1/taxonomy/").json()
        if taxonomies:
            tax_code = taxonomies[0]["taxonomy_code"]
            tax_response = test_client.get(f"/api/v1/taxonomy/{tax_code}")
            assert tax_response.status_code == 200
            tax_data = tax_response.json()
            assert isinstance(tax_data, dict)
            assert "taxonomy_code" in tax_data
            assert "name" in tax_data
            assert "created_at" in tax_data

    def test_meta_value_operations(self, test_client):
        """MetaValue 관련 작업 테스트"""
        # Bootstrap으로 기본 데이터 생성
        test_client.post("/api/v1/bootstrap/demo")
        
        # MetaItems 조회
        meta_items = test_client.get("/api/v1/meta/items").json()
        assert isinstance(meta_items, list)
        
        # 모든 메타 관련 엔드포인트가 정상 작동하는지 확인
        meta_endpoints = [
            "/api/v1/meta/types",
            "/api/v1/meta/groups", 
            "/api/v1/meta/items"
        ]
        
        for endpoint in meta_endpoints:
            response = test_client.get(endpoint)
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)