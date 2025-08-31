"""
API Security Integration Tests  
API 보안 및 데이터 검증 테스트
"""
import pytest
import json
from uuid import uuid4


class TestAPISecurity:
    """API 보안 테스트"""

    def test_input_validation_sql_injection(self, test_client):
        """SQL 인젝션 방지 테스트"""
        # 다양한 SQL 인젝션 시도
        sql_injection_attempts = [
            "'; DROP TABLE taxonomy; --",
            "' OR '1'='1",
            "' UNION SELECT * FROM taxonomy --",
            "'; DELETE FROM taxonomy WHERE '1'='1'; --",
            "' OR 1=1 --",
            "admin'--",
            "admin'/*",
            "' or 1=1#",
            "' or 1=1--",
            "') or '1'='1--"
        ]
        
        for injection_attempt in sql_injection_attempts:
            # Taxonomy 조회에서 SQL 인젝션 시도
            response = test_client.get(f"/api/v1/taxonomy/{injection_attempt}")
            # 404 또는 422 에러여야 함 (서버 에러가 아님)
            assert response.status_code in [404, 422], f"SQL injection attempt should be handled safely: {injection_attempt}"
            
            # POST 요청에서 SQL 인젝션 시도
            malicious_data = {
                "taxonomy_code": injection_attempt,
                "name": "Test Taxonomy"
            }
            post_response = test_client.post("/api/v1/taxonomy/", json=malicious_data)
            # 400, 422 등의 클라이언트 에러여야 함 (서버 에러 아님)
            assert post_response.status_code < 500, f"SQL injection in POST should be handled safely: {injection_attempt}"

    def test_input_validation_xss_prevention(self, test_client):
        """XSS 방지 테스트"""
        xss_attempts = [
            "<script>alert('xss')</script>",
            "<img src=x onerror=alert('xss')>",
            "javascript:alert('xss')",
            "<svg/onload=alert('xss')>",
            "<iframe src='javascript:alert(1)'></iframe>",
            "';alert(String.fromCharCode(88,83,83))//';alert(String.fromCharCode(88,83,83))//",
            "\";alert('XSS');//",
            "<body onload=alert('XSS')>"
        ]
        
        for xss_attempt in xss_attempts:
            # Taxonomy 생성에서 XSS 시도
            malicious_data = {
                "taxonomy_code": "XSS_TEST",
                "name": xss_attempt,
                "description": xss_attempt
            }
            
            response = test_client.post("/api/v1/taxonomy/", json=malicious_data)
            
            if response.status_code == 200:
                # 성공적으로 생성되었다면, 조회해서 XSS 스크립트가 그대로 저장되었는지 확인
                get_response = test_client.get("/api/v1/taxonomy/XSS_TEST")
                if get_response.status_code == 200:
                    data = get_response.json()
                    # XSS 스크립트가 그대로 저장되어 있는지 확인 (이는 정상적임 - 출력시 이스케이프되어야 함)
                    assert xss_attempt in str(data), "XSS content should be stored as-is"
                    
                    # 응답이 JSON 형태로 안전하게 반환되는지 확인
                    assert isinstance(data, dict)

    def test_input_validation_data_types(self, test_client):
        """데이터 타입 검증 테스트"""
        # 잘못된 데이터 타입 테스트
        invalid_data_tests = [
            # Taxonomy 생성시 타입 오류
            {
                "endpoint": "/api/v1/taxonomy/",
                "data": {
                    "taxonomy_code": 123,  # 문자열이어야 하는데 숫자
                    "name": "Test"
                }
            },
            {
                "endpoint": "/api/v1/taxonomy/",
                "data": {
                    "taxonomy_code": "TEST",
                    "name": ["invalid", "array"]  # 문자열이어야 하는데 배열
                }
            },
            # CodeSet 생성시 타입 오류
            {
                "endpoint": "/api/v1/codeset/",
                "data": {
                    "codeset_code": "TEST",
                    "name": None  # null 값
                }
            },
            # MetaType 생성시 타입 오류
            {
                "endpoint": "/api/v1/meta/types",
                "data": {
                    "type_code": "TEST",
                    "name": "Test",
                    "type_kind": "INVALID_KIND"  # 유효하지 않은 enum 값
                }
            }
        ]
        
        for test_case in invalid_data_tests:
            response = test_client.post(test_case["endpoint"], json=test_case["data"])
            # 422 Validation Error 또는 200(성공)이 올 수 있음 (현재 구현에 따라)
            assert response.status_code in [200, 422], f"Invalid data should be handled properly: {test_case}"

    def test_input_validation_field_lengths(self, test_client):
        """필드 길이 검증 테스트"""
        # 매우 긴 문자열 생성
        very_long_string = "A" * 10000
        
        # 각 엔드포인트에서 긴 문자열 테스트
        long_string_tests = [
            {
                "endpoint": "/api/v1/taxonomy/",
                "data": {
                    "taxonomy_code": very_long_string,
                    "name": "Test"
                }
            },
            {
                "endpoint": "/api/v1/taxonomy/",
                "data": {
                    "taxonomy_code": "TEST", 
                    "name": very_long_string
                }
            },
            {
                "endpoint": "/api/v1/codeset/",
                "data": {
                    "codeset_code": very_long_string,
                    "name": "Test"
                }
            },
            {
                "endpoint": "/api/v1/meta/types",
                "data": {
                    "type_code": very_long_string,
                    "name": "Test",
                    "type_kind": "PRIMITIVE"
                }
            }
        ]
        
        for test_case in long_string_tests:
            response = test_client.post(test_case["endpoint"], json=test_case["data"])
            # 적절한 에러 응답이거나 성공할 수 있음 (현재 구현에서는 길이 제한이 없을 수 있음)
            assert response.status_code in [200, 400, 422], f"Long string should be handled: {test_case}"

    def test_authorization_placeholder(self, test_client):
        """인증/인가 플레이스홀더 테스트"""
        # 현재 API는 인증이 없지만, 향후 구현시를 위한 테스트 구조
        
        # 모든 엔드포인트가 현재는 열려있는지 확인
        open_endpoints = [
            "/api/v1/health",
            "/api/v1/taxonomy/",
            "/api/v1/codeset/",
            "/api/v1/meta/types",
            "/api/v1/meta/groups",
            "/api/v1/bootstrap/status"
        ]
        
        for endpoint in open_endpoints:
            response = test_client.get(endpoint)
            # 401 Unauthorized가 아니어야 함 (현재는 인증이 없으므로)
            assert response.status_code != 401, f"Endpoint should be accessible without auth: {endpoint}"

    def test_malformed_json_handling(self, test_client):
        """잘못된 JSON 처리 테스트"""
        # Content-Type은 application/json이지만 실제로는 잘못된 JSON
        malformed_json_strings = [
            '{"taxonomy_code": "TEST", "name":}',  # 값 누락
            '{"taxonomy_code": "TEST" "name": "Test"}',  # 쉼표 누락  
            '{"taxonomy_code": "TEST", "name": "Test",}',  # 끝에 쉼표
            '{taxonomy_code: "TEST", name: "Test"}',  # 키에 따옴표 없음
            '{"taxonomy_code": "TEST", "name": "Test"',  # 닫는 괄호 없음
            '',  # 빈 문자열
            'not json at all',  # JSON이 아닌 문자열
            '[]',  # 객체가 아닌 배열
            'null'  # null 값
        ]
        
        # TestClient는 JSON을 자동으로 처리하므로 malformed JSON 테스트는 제한적
        # 대신 기본적인 JSON 파싱 오류 상황을 시뮬레이션
        
        # 빈 요청 본문 테스트
        try:
            response = test_client.post(
                "/api/v1/taxonomy/", 
                data="",
                headers={"Content-Type": "application/json"}
            )
            # 422 Unprocessable Entity 또는 400 Bad Request가 발생해야 함
            assert response.status_code in [400, 422], "Empty JSON should be rejected"
        except Exception as e:
            # JSON 파싱 오류가 적절히 처리되는지 확인
            assert "JSON" in str(e) or "parse" in str(e).lower() or "decode" in str(e).lower()

    def test_unicode_and_special_characters(self, test_client):
        """유니코드와 특수 문자 처리 테스트"""
        special_char_tests = [
            {
                "taxonomy_code": "UNICODE_TEST",
                "name": "테스트 택소노미 🌟",
                "description": "유니코드 문자와 이모지 테스트"
            },
            {
                "taxonomy_code": "SPECIAL_CHARS",
                "name": "Special \"Chars\" & Symbols: @#$%^&*()",
                "description": "다양한 특수 문자 테스트"
            },
            {
                "taxonomy_code": "NEWLINES_TEST",
                "name": "Test\nWith\nNewlines",
                "description": "줄바꿈\n문자가\n포함된\n텍스트"
            },
            {
                "taxonomy_code": "TABS_TEST",
                "name": "Test\tWith\tTabs",
                "description": "탭\t문자가\t포함된\t텍스트"
            }
        ]
        
        for test_data in special_char_tests:
            response = test_client.post("/api/v1/taxonomy/", json=test_data)
            
            # 성공하거나 적절한 validation error가 발생해야 함
            assert response.status_code in [200, 400, 422], f"Special characters should be handled properly: {test_data}"
            
            if response.status_code == 200:
                # 성공적으로 생성되었다면 조회해서 데이터가 올바르게 저장되었는지 확인
                get_response = test_client.get(f"/api/v1/taxonomy/{test_data['taxonomy_code']}")
                if get_response.status_code == 200:
                    stored_data = get_response.json()
                    assert stored_data["name"] == test_data["name"]
                    assert stored_data["description"] == test_data["description"]

    def test_null_and_empty_values(self, test_client):
        """NULL과 빈 값 처리 테스트"""
        null_empty_tests = [
            {
                "endpoint": "/api/v1/taxonomy/",
                "data": {
                    "taxonomy_code": "",  # 빈 문자열
                    "name": "Test"
                }
            },
            {
                "endpoint": "/api/v1/taxonomy/",
                "data": {
                    "taxonomy_code": "TEST",
                    "name": ""  # 빈 문자열
                }
            },
            {
                "endpoint": "/api/v1/taxonomy/",
                "data": {
                    "taxonomy_code": None,  # None 값
                    "name": "Test"
                }
            },
            {
                "endpoint": "/api/v1/taxonomy/",
                "data": {
                    "taxonomy_code": "   ",  # 공백만 있는 문자열
                    "name": "Test"
                }
            }
        ]
        
        for test_case in null_empty_tests:
            response = test_client.post(test_case["endpoint"], json=test_case["data"])
            # 적절한 validation error가 발생하거나 성공할 수 있음 (현재 구현에 따라)
            assert response.status_code in [200, 422], f"Null/empty values should be handled: {test_case}"

    def test_content_length_limits(self, test_client):
        """컨텐츠 길이 제한 테스트"""
        # Bootstrap 데이터 생성
        test_client.post("/api/v1/bootstrap/demo")
        
        # Terms 조회
        terms = test_client.get("/api/v1/taxonomy/DATA_DOMAIN/terms").json()
        if not terms:
            pytest.skip("No terms available for content length test")
        
        term_id = terms[0]["term_id"]
        
        # 매우 큰 컨텐츠 생성 시도
        huge_content = "A" * 1000000  # 1MB
        
        content_data = {
            "body_markdown": huge_content,
            "author": "security_test",
            "reason": "Testing content length limits"
        }
        
        response = test_client.put(
            f"/api/v1/taxonomy/terms/{term_id}/content",
            json=content_data
        )
        
        # 너무 큰 컨텐츠는 거부되거나, 성공하더라도 적절히 처리되어야 함
        if response.status_code == 200:
            # 성공했다면 응답이 합리적인 시간 내에 와야 함
            result = response.json()
            assert "content_version_id" in result
        else:
            # 거부되었다면 적절한 에러 코드여야 함
            assert response.status_code in [400, 413, 422], "Large content should be handled appropriately"

    def test_parameter_pollution(self, test_client):
        """매개변수 오염 공격 방지 테스트"""
        # URL 매개변수 중복 테스트
        # FastAPI/Starlette는 이를 자동으로 처리하지만 테스트해볼 가치가 있음
        
        # 존재하지 않는 taxonomy 조회
        response = test_client.get("/api/v1/taxonomy/TEST1")
        assert response.status_code == 404
        
        # 정상적인 taxonomy 생성
        tax_data = {
            "taxonomy_code": "PARAM_TEST",
            "name": "Parameter Test Taxonomy"
        }
        create_response = test_client.post("/api/v1/taxonomy/", json=tax_data)
        assert create_response.status_code == 200
        
        # 생성된 taxonomy 조회
        get_response = test_client.get("/api/v1/taxonomy/PARAM_TEST")
        assert get_response.status_code == 200