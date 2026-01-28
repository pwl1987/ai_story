"""
健康检查端点单元测试
Epic 2.2 - 健康检查端点完整实现
"""
import pytest
from django.test import Client
from django.urls import reverse
from unittest.mock import patch, MagicMock
import time


@pytest.mark.django_db
class TestHealthCheckEndpoint:
    """健康检查端点测试"""

    def setup_method(self):
        """每个测试前初始化"""
        self.client = Client()

    def test_health_check_success(self):
        """测试健康检查成功"""
        response = self.client.get('/api/v1/health/')

        assert response.status_code == 200
        data = response.json()

        # 验证响应结构
        assert 'status' in data
        assert 'timestamp' in data
        assert 'checks' in data
        assert 'response_time_ms' in data

        # 验证各个检查项存在
        checks = data['checks']
        assert 'database' in checks
        assert 'redis' in checks
        assert 'celery' in checks
        assert 'cache' in checks

    def test_health_check_response_time_fast(self):
        """测试健康检查响应时间<200ms"""
        start = time.time()
        response = self.client.get('/api/v1/health/')
        end = time.time()

        response_time_ms = int((end - start) * 1000)

        # 响应应该很快（允许客户端处理时间）
        assert response_time_ms < 500  # 宽松限制

        # 服务端响应时间应该在200ms内
        data = response.json()
        assert data['response_time_ms'] < 200

    def test_health_check_all_healthy(self):
        """测试所有组件健康"""
        response = self.client.get('/api/v1/health/')
        data = response.json()

        # 如果所有服务运行，应该是healthy
        # 注意：在测试环境中可能没有Celery worker运行
        if data['checks']['celery']['status'] == 'healthy':
            assert data['status'] == 'healthy'

    def test_health_check_contains_unhealthy_list(self):
        """测试包含不健康组件列表"""
        response = self.client.get('/api/v1/health/')
        data = response.json()

        # 应该有unhealthy_checks字段
        assert 'unhealthy_checks' in data
        assert isinstance(data['unhealthy_checks'], list)

    @patch('apps.core.views._check_database')
    def test_health_check_database_unhealthy(self, mock_check_db):
        """测试数据库不健康场景"""
        mock_check_db.return_value = {
            'status': 'unhealthy',
            'error': 'Connection failed'
        }

        response = self.client.get('/api/v1/health/')
        data = response.json()

        assert data['status'] in ['unhealthy', 'degraded']
        assert 'database' in data.get('unhealthy_checks', [])

    @patch('apps.core.views._check_redis')
    def test_health_check_redis_unhealthy(self, mock_check_redis):
        """测试Redis不健康场景"""
        mock_check_redis.return_value = {
            'status': 'unhealthy',
            'error': 'Redis connection failed'
        }

        response = self.client.get('/api/v1/health/')
        data = response.json()

        assert data['status'] in ['unhealthy', 'degraded']
        assert 'redis' in data.get('unhealthy_checks', [])


@pytest.mark.django_db
class TestMetricsEndpoint:
    """Prometheus metrics端点测试"""

    def setup_method(self):
        """每个测试前初始化"""
        self.client = Client()

    def test_metrics_endpoint_exists(self):
        """测试metrics端点可访问"""
        response = self.client.get('/api/v1/metrics/')

        assert response.status_code == 200
        assert response['Content-Type'] == 'text/plain; version=0.0.4; charset=utf-8'

    def test_metrics_format(self):
        """测试metrics格式正确"""
        response = self.client.get('/api/v1/metrics/')

        content = response.content.decode('utf-8')

        # 应该包含Prometheus格式的metrics
        assert '# HELP' in content or '# TYPE' in content
        assert 'http_requests_total' in content
        assert 'http_request_duration_seconds' in content
        assert 'db_connections' in content

    def test_metrics_response_type(self):
        """测试返回正确的content-type"""
        response = self.client.get('/api/v1/metrics/')

        # Prometheus使用text/plain格式
        assert 'text/plain' in response['Content-Type']


@pytest.mark.django_db
class TestDatabaseCheck:
    """数据库检查功能测试"""

    def test_database_check_healthy(self):
        """测试数据库健康检查"""
        from apps.core.views import _check_database

        result = _check_database()

        assert 'status' in result
        assert 'latency_ms' in result
        assert isinstance(result['latency_ms'], int)


@pytest.mark.django_db
class TestRedisCheck:
    """Redis检查功能测试"""

    def test_redis_check_healthy(self):
        """测试Redis健康检查"""
        from apps.core.views import _check_redis

        result = _check_redis()

        assert 'status' in result
        assert 'latency_ms' in result
        assert isinstance(result['latency_ms'], int)


@pytest.mark.django_db
class TestCeleryCheck:
    """Celery检查功能测试"""

    def test_celery_check_structure(self):
        """测试Celery检查返回结构"""
        from apps.core.views import _check_celery

        result = _check_celery()

        assert 'status' in result
        assert 'workers' in result
        assert isinstance(result['workers'], int)
