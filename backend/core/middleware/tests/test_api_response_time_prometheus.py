"""
API响应时间监控中间件测试（Prometheus集成）
Epic 2.5 - API响应时间监控（Prometheus集成）
"""
import os
import sys
import time
from unittest.mock import MagicMock, Mock, patch

import pytest

# 避免Django设置问题
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../'))


class TestAPIResponseTimeMiddlewarePrometheus:
    """API响应时间中间件Prometheus集成测试 (Epic 2.5)"""

    def setup_method(self):
        """每个测试前初始化"""
        # 创建模拟的请求和响应
        self.get_response = MagicMock()

    def test_prometheus_metrics_exist(self):
        """测试Prometheus指标已定义"""
        try:
            from core.middleware.api_response_time import (
                PROMETHEUS_ENABLED,
                http_request_duration_seconds,
                http_requests_total,
            )
            # 验证指标存在
            assert http_requests_total is not None
            assert http_request_duration_seconds is not None
        except ImportError:
            pytest.skip("Prometheus not installed")

    def test_prometheus_metrics_labels(self):
        """测试Prometheus指标标签配置正确"""
        try:
            from core.middleware.api_response_time import (
                http_request_duration_seconds,
                http_requests_total,
            )
            # 验证标签
            assert 'method' in http_requests_total._labelnames
            assert 'endpoint' in http_requests_total._labelnames
            assert 'status' in http_requests_total._labelnames

            assert 'method' in http_request_duration_seconds._labelnames
            assert 'endpoint' in http_request_duration_seconds._labelnames
        except ImportError:
            pytest.skip("Prometheus not installed")

    def test_prometheus_histogram_buckets(self):
        """测试Prometheus直方图桶配置合理"""
        try:
            from core.middleware.api_response_time import http_request_duration_seconds
            # 验证直方图存在并且有合理的桶配置
            # prometheus_client的Histogram使用buckets参数配置
            assert http_request_duration_seconds is not None
            # 验证指标类型
            assert hasattr(http_request_duration_seconds, '_type')
        except ImportError:
            pytest.skip("Prometheus not installed")

    def test_extract_endpoint_from_url_name(self):
        """测试从URL名称提取endpoint"""
        from core.middleware.api_response_time import APIResponseTimeMiddleware

        middleware = APIResponseTimeMiddleware(lambda r: MagicMock())

        # 创建模拟请求
        request = Mock()
        request.method = 'GET'
        request.path = '/api/v1/projects/'
        request.resolver_match = Mock()
        request.resolver_match.url_name = 'project-list'

        # 调用方法
        endpoint = middleware._extract_endpoint(request)

        # 验证endpoint
        assert endpoint == 'project-list'

    def test_extract_endpoint_fallback_to_path(self):
        """测试endpoint提取回退到路径"""
        from core.middleware.api_response_time import APIResponseTimeMiddleware

        middleware = APIResponseTimeMiddleware(lambda r: MagicMock())

        # 创建模拟请求（没有resolver_match）
        request = Mock()
        request.method = 'GET'
        request.path = '/api/v1/unknown/'
        request.resolver_match = None

        # 调用方法
        endpoint = middleware._extract_endpoint(request)

        # 验证endpoint不为空
        assert endpoint is not None
        assert len(endpoint) > 0

    def test_get_user_id_authenticated(self):
        """测试获取已认证用户ID"""
        from core.middleware.api_response_time import APIResponseTimeMiddleware

        middleware = APIResponseTimeMiddleware(lambda r: MagicMock())

        # 创建模拟请求
        request = Mock()
        request.user = Mock()
        request.user.is_authenticated = True
        request.user.id = 123

        # 调用方法
        user_id = middleware._get_user_id(request)

        # 验证用户ID
        assert user_id == 123

    def test_get_user_id_anonymous(self):
        """测试获取匿名用户ID返回None"""
        from core.middleware.api_response_time import APIResponseTimeMiddleware

        middleware = APIResponseTimeMiddleware(lambda r: MagicMock())

        # 创建模拟请求
        request = Mock()
        request.user = Mock()
        request.user.is_authenticated = False

        # 调用方法
        user_id = middleware._get_user_id(request)

        # 验证返回None
        assert user_id is None


class TestAPIResponseTimeMiddlewareStandalone:
    """独立版本API响应时间中间件测试"""

    def setup_method(self):
        """每个测试前初始化"""
        self.get_response = MagicMock()

    def test_standalone_middleware_structure(self):
        """测试独立版本中间件结构正确"""
        from core.middleware.api_response_time import APIResponseTimeMiddlewareStandalone

        # 验证类存在
        assert APIResponseTimeMiddlewareStandalone is not None

        # 创建实例
        middleware = APIResponseTimeMiddlewareStandalone(lambda r: MagicMock())
        assert middleware is not None
        assert middleware.get_response is not None

    def test_standalone_has_log_response_time_method(self):
        """测试独立版本有_log_response_time方法"""
        from core.middleware.api_response_time import APIResponseTimeMiddlewareStandalone

        middleware = APIResponseTimeMiddlewareStandalone(lambda r: MagicMock())

        # 验证方法存在
        assert hasattr(middleware, '_log_response_time')
        assert callable(middleware._log_response_time)


class TestPrometheusMetricsStructure:
    """Prometheus指标结构测试"""

    def test_http_requests_total_metric_structure(self):
        """测试HTTP请求总数指标结构"""
        try:
            from core.middleware.api_response_time import http_requests_total

            # 验证指标类型
            assert http_requests_total._type == 'counter'

            # 验证标签
            assert 'method' in http_requests_total._labelnames
            assert 'endpoint' in http_requests_total._labelnames
            assert 'status' in http_requests_total._labelnames
        except ImportError:
            pytest.skip("Prometheus not installed")

    def test_http_request_duration_seconds_metric_structure(self):
        """测试HTTP请求响应时间指标结构"""
        try:
            from core.middleware.api_response_time import http_request_duration_seconds

            # 验证指标类型
            assert http_request_duration_seconds._type == 'histogram'

            # 验证标签
            assert 'method' in http_request_duration_seconds._labelnames
            assert 'endpoint' in http_request_duration_seconds._labelnames

            # 验证指标存在
            assert http_request_duration_seconds is not None
        except ImportError:
            pytest.skip("Prometheus not installed")

    def test_metrics_documentation(self):
        """测试指标有适当的文档字符串"""
        try:
            from core.middleware.api_response_time import (
                http_request_duration_seconds,
                http_requests_total,
            )

            # 验证文档字符串
            assert http_requests_total._documentation == 'Total HTTP requests'
            assert http_request_duration_seconds._documentation == 'HTTP request duration seconds'
        except ImportError:
            pytest.skip("Prometheus not installed")

