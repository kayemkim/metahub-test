"""
API Performance Integration Tests
API 성능 및 부하 테스트
"""
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

import pytest


class TestAPIPerformance:
    """API 성능 테스트"""

    def test_response_times(self, test_client):
        """기본 응답 시간 테스트"""
        # Bootstrap 데이터 생성
        test_client.post("/api/v1/bootstrap/demo")

        # 주요 엔드포인트들의 응답 시간 측정
        endpoints_to_test = [
            "/api/v1/health",
            "/api/v1/taxonomy/",
            "/api/v1/codeset/",
            "/api/v1/meta/types",
            "/api/v1/meta/groups",
            "/api/v1/meta/items"
        ]

        response_times = {}

        for endpoint in endpoints_to_test:
            start_time = time.time()
            response = test_client.get(endpoint)
            end_time = time.time()

            response_time = end_time - start_time
            response_times[endpoint] = response_time

            # 응답이 성공적이어야 함
            assert response.status_code == 200
            # 응답 시간이 2초를 넘지 않아야 함 (로컬 테스트 기준)
            assert response_time < 2.0, f"Response time for {endpoint} is too slow: {response_time:.2f}s"

        # 평균 응답 시간 확인
        avg_response_time = sum(response_times.values()) / len(response_times)
        assert avg_response_time < 1.0, f"Average response time too slow: {avg_response_time:.2f}s"

    def test_multiple_concurrent_requests(self, test_client):
        """동시 요청 처리 테스트"""
        # Bootstrap 데이터 생성
        test_client.post("/api/v1/bootstrap/demo")

        # Health check 엔드포인트로 동시 요청 테스트
        def make_request():
            response = test_client.get("/api/v1/health")
            return response.status_code, response.json()

        # 10개의 동시 요청
        num_requests = 10
        start_time = time.time()

        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(make_request) for _ in range(num_requests)]
            results = []

            for future in as_completed(futures):
                status_code, data = future.result()
                results.append((status_code, data))

        end_time = time.time()
        total_time = end_time - start_time

        # 모든 요청이 성공해야 함
        assert len(results) == num_requests
        for status_code, data in results:
            assert status_code == 200
            assert data["ok"] is True

        # 전체 시간이 합리적이어야 함
        assert total_time < 5.0, f"Concurrent requests took too long: {total_time:.2f}s"

    def test_large_data_handling(self, test_client):
        """대량 데이터 처리 테스트"""
        # Bootstrap으로 기본 데이터 생성
        test_client.post("/api/v1/bootstrap/demo")

        # 여러 개의 taxonomy 생성
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        created_taxonomies = []

        start_time = time.time()

        for i in range(20):  # 20개 생성
            tax_data = {
                "taxonomy_code": f"PERF_TAX_{i}_{timestamp}",
                "name": f"Performance Test Taxonomy {i}",
                "description": f"Created for performance testing #{i}"
            }

            response = test_client.post("/api/v1/taxonomy/", json=tax_data)
            assert response.status_code == 200
            created_taxonomies.append(response.json())

        creation_time = time.time() - start_time

        # 생성 시간이 합리적이어야 함
        assert creation_time < 10.0, f"Creating 20 taxonomies took too long: {creation_time:.2f}s"

        # 모든 taxonomy 조회
        start_time = time.time()
        all_taxonomies = test_client.get("/api/v1/taxonomy/").json()
        retrieval_time = time.time() - start_time

        # 조회 시간이 합리적이어야 함
        assert retrieval_time < 2.0, f"Retrieving all taxonomies took too long: {retrieval_time:.2f}s"

        # 생성한 모든 taxonomy가 포함되어 있어야 함
        all_codes = [tax["taxonomy_code"] for tax in all_taxonomies]
        created_codes = [tax["taxonomy_code"] for tax in created_taxonomies]

        for created_code in created_codes:
            assert created_code in all_codes

    def test_repeated_operations_performance(self, test_client):
        """반복 작업 성능 테스트"""
        # Bootstrap 데이터 생성
        test_client.post("/api/v1/bootstrap/demo")

        # 같은 엔드포인트를 여러 번 호출
        endpoint = "/api/v1/taxonomy/"
        num_calls = 50

        response_times = []

        for i in range(num_calls):
            start_time = time.time()
            response = test_client.get(endpoint)
            end_time = time.time()

            assert response.status_code == 200
            response_times.append(end_time - start_time)

        # 통계 계산
        avg_time = sum(response_times) / len(response_times)
        max_time = max(response_times)
        min_time = min(response_times)

        # 성능 기준 검증
        assert avg_time < 0.5, f"Average response time too slow: {avg_time:.3f}s"
        assert max_time < 2.0, f"Maximum response time too slow: {max_time:.3f}s"
        assert min_time < 1.0, f"Minimum response time too slow: {min_time:.3f}s"

        # 성능이 일관적이어야 함 (표준편차 확인)
        variance = sum((t - avg_time) ** 2 for t in response_times) / len(response_times)
        std_dev = variance ** 0.5
        assert std_dev < 0.2, f"Response time variance too high: {std_dev:.3f}s"

    def test_memory_usage_stability(self, test_client):
        """메모리 사용량 안정성 테스트"""
        # Bootstrap 데이터 생성
        test_client.post("/api/v1/bootstrap/demo")

        # 반복적으로 데이터 생성/조회
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        for cycle in range(10):  # 10 사이클
            # 데이터 생성
            for i in range(5):
                tax_data = {
                    "taxonomy_code": f"MEM_TAX_{cycle}_{i}_{timestamp}",
                    "name": f"Memory Test Taxonomy {cycle}-{i}",
                    "description": f"Memory test cycle {cycle}, item {i}"
                }

                response = test_client.post("/api/v1/taxonomy/", json=tax_data)
                assert response.status_code == 200

            # 데이터 조회
            all_taxonomies = test_client.get("/api/v1/taxonomy/").json()
            assert len(all_taxonomies) >= 5 * (cycle + 1)  # 최소한 생성한 만큼은 있어야 함

            # Terms 조회 (있다면)
            for tax in all_taxonomies[:3]:  # 처음 3개만 테스트
                taxonomy_code = tax["taxonomy_code"]
                terms_response = test_client.get(f"/api/v1/taxonomy/{taxonomy_code}/terms")
                assert terms_response.status_code == 200

    def test_database_connection_efficiency(self, test_client):
        """데이터베이스 연결 효율성 테스트"""
        # Bootstrap 데이터 생성
        test_client.post("/api/v1/bootstrap/demo")

        # 여러 엔드포인트를 연속으로 호출
        endpoints = [
            "/api/v1/taxonomy/",
            "/api/v1/codeset/",
            "/api/v1/meta/types",
            "/api/v1/meta/groups"
        ]

        # 여러 라운드로 테스트
        for round_num in range(5):
            start_time = time.time()

            for endpoint in endpoints:
                response = test_client.get(endpoint)
                assert response.status_code == 200
                data = response.json()
                assert isinstance(data, list)

            round_time = time.time() - start_time

            # 각 라운드가 합리적인 시간 내에 완료되어야 함
            assert round_time < 3.0, f"Round {round_num} took too long: {round_time:.2f}s"

    def test_error_handling_performance(self, test_client):
        """에러 처리 성능 테스트"""
        # 404 에러 처리 시간 측정
        not_found_endpoints = [
            "/api/v1/taxonomy/NOT_FOUND_404",
            "/api/v1/codeset/NOT_FOUND_404",
            "/api/v1/meta/types/NOT_FOUND_404",
            "/api/v1/meta/groups/NOT_FOUND_404"
        ]

        error_response_times = []

        for endpoint in not_found_endpoints:
            start_time = time.time()
            response = test_client.get(endpoint)
            end_time = time.time()

            response_time = end_time - start_time
            error_response_times.append(response_time)

            assert response.status_code == 404
            assert "detail" in response.json()

            # 에러 응답도 빨라야 함
            assert response_time < 1.0, f"Error response for {endpoint} too slow: {response_time:.3f}s"

        # 평균 에러 응답 시간
        avg_error_time = sum(error_response_times) / len(error_response_times)
        assert avg_error_time < 0.5, f"Average error response time too slow: {avg_error_time:.3f}s"

    def test_content_size_handling(self, test_client):
        """컨텐츠 크기 처리 테스트"""
        # Bootstrap 데이터 생성
        test_client.post("/api/v1/bootstrap/demo")

        # Terms 조회
        terms = test_client.get("/api/v1/taxonomy/DATA_DOMAIN/terms").json()
        if not terms:
            pytest.skip("No terms available for content size test")

        term_id = terms[0]["term_id"]

        # 큰 컨텐츠 생성 테스트
        large_content = "# Large Content Test\n\n" + "This is a line of content. " * 1000

        content_data = {
            "body_markdown": large_content,
            "author": "performance_test",
            "reason": "Testing large content handling"
        }

        start_time = time.time()
        response = test_client.put(
            f"/api/v1/taxonomy/terms/{term_id}/content",
            json=content_data
        )
        end_time = time.time()

        response_time = end_time - start_time

        assert response.status_code == 200
        assert "content_version_id" in response.json()

        # 큰 컨텐츠 처리도 합리적인 시간 내에 완료되어야 함
        assert response_time < 5.0, f"Large content processing took too long: {response_time:.2f}s"
