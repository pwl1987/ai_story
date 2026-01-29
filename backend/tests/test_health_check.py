"""
健康检查端点测试
"""

import pytest
from django.test import Client


@pytest.mark.django_db
class TestHealthCheckEndpoint:
    """健康检查端点测试类"""

    def test_health_check_endpoint_exists(self):
        """测试健康检查端点存在"""
        client = Client()
        response = client.get("/api/v1/core/health/")

        assert response.status_code == 200

    def test_health_check_response_format(self):
        """测试健康检查响应格式"""
        client = Client()
        response = client.get("/api/v1/core/health/")

        assert response.status_code == 200
        data = response.json()

        # 验证必需字段
        assert "status" in data
        assert "timestamp" in data
        assert "checks" in data
        assert "response_time_ms" in data

        # 验证checks结构
        assert "database" in data["checks"]
        assert "cache" in data["checks"]

    def test_health_check_database_status(self):
        """测试数据库健康检查"""
        client = Client()
        response = client.get("/api/v1/core/health/")

        data = response.json()
        db_check = data["checks"]["database"]

        # 验证数据库检查包含必需字段
        assert "status" in db_check
        assert "latency_ms" in db_check
        assert db_check["status"] in ["healthy", "degraded", "unhealthy"]
        assert isinstance(db_check["latency_ms"], int)

    def test_health_check_cache_status(self):
        """测试缓存健康检查"""
        client = Client()
        response = client.get("/api/v1/core/health/")

        data = response.json()
        cache_check = data["checks"]["cache"]

        # 验证缓存检查包含必需字段
        assert "status" in cache_check
        assert cache_check["status"] in ["healthy", "unhealthy"]

        # 如果缓存可用，验证latency_ms字段
        if cache_check["status"] == "healthy":
            assert "latency_ms" in cache_check
            assert isinstance(cache_check["latency_ms"], int)
        else:
            # 如果缓存不可用，应该有error字段
            assert "error" in cache_check

    def test_health_check_response_time(self):
        """测试健康检查响应时间"""
        client = Client()
        response = client.get("/api/v1/core/health/")

        data = response.json()
        response_time = data["response_time_ms"]

        # 验证响应时间<200ms
        assert response_time < 200
        assert isinstance(response_time, int)

    def test_health_check_overall_status(self):
        """测试健康检查总体状态"""
        client = Client()
        response = client.get("/api/v1/core/health/")

        data = response.json()
        overall_status = data["status"]

        # 验证总体状态
        assert overall_status in ["healthy", "degraded", "unhealthy"]

        # 如果数据库和缓存都健康,总体状态应该是healthy
        db_status = data["checks"]["database"]["status"]
        cache_status = data["checks"]["cache"]["status"]

        if db_status == "healthy" and cache_status == "healthy":
            assert overall_status in ["healthy", "degraded"]  # degraded如果响应时间慢
