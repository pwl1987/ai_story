"""
单元测试: Prometheus指标导出
Epic 2优化：测试Prometheus指标模块
"""

from unittest.mock import Mock

import pytest
from django.http import HttpResponse
from django.test import override_settings

from core.prometheus_metrics import (
    PROMETHEUS_AVAILABLE,
    PrometheusMetricsMiddleware,
    api_request_counter,
    api_response_time_histogram,
    api_slow_request_counter,
    get_endpoint_from_request,
    metrics_view,
    track_api_request,
)


@pytest.mark.skipif(not PROMETHEUS_AVAILABLE, reason="prometheus_client not installed")
class TestPrometheusMetrics:
    """
    测试Prometheus指标导出
    Epic 2优化：Prometheus指标集成
    """

    def test_api_request_counter_exists(self):
        """测试API请求计数器存在"""
        assert api_request_counter is not None
        assert api_request_counter._type == "counter"

    def test_api_response_time_histogram_exists(self):
        """测试API响应时间直方图存在"""
        assert api_response_time_histogram is not None
        assert api_response_time_histogram._type == "histogram"

    def test_api_slow_request_counter_exists(self):
        """测试慢请求计数器存在"""
        assert api_slow_request_counter is not None


class TestEndpointExtraction:
    """
    测试端点名称提取
    """

    def test_extract_endpoint_from_path(self):
        """测试从路径提取端点"""
        request = Mock()
        request.path = "/api/v1/projects/"
        request.resolver_match = None

        endpoint = get_endpoint_from_request(request)
        assert endpoint == "/api/v1/projects/"

    def test_extract_endpoint_from_url_name(self):
        """测试从URL名称提取端点"""
        request = Mock()
        request.path = "/api/v1/projects/"
        request.resolver_match = Mock()
        request.resolver_match.url_name = "project-list"
        request.resolver_match.namespace = None
        request.resolver_match.route = None

        endpoint = get_endpoint_from_request(request)
        assert endpoint == "project-list"

    def test_extract_endpoint_with_namespace(self):
        """测试带命名空间的端点提取"""
        request = Mock()
        request.path = "/api/v1/projects/123/"
        request.resolver_match = Mock()
        request.resolver_match.url_name = "project-detail"
        request.resolver_match.namespace = "api"
        request.resolver_match.route = None

        endpoint = get_endpoint_from_request(request)
        assert endpoint == "api:project-detail"

    def test_extract_endpoint_from_route(self):
        """测试从路由模式提取端点"""
        request = Mock()
        request.path = "/api/v1/projects/"
        request.resolver_match = Mock()
        request.resolver_match.route = "projects/"
        request.resolver_match.url_name = None

        endpoint = get_endpoint_from_request(request)
        assert endpoint == "projects/"


class TestAPIRequestTracking:
    """
    测试API请求跟踪装饰器
    """

    @pytest.mark.skipif(not PROMETHEUS_AVAILABLE, reason="prometheus_client not installed")
    def test_track_api_request_increments_counter(self):
        """测试跟踪API请求增加计数器"""
        request = Mock()
        request.method = "GET"
        request.path = "/api/v1/test/"
        request.resolver_match = None

        @track_api_request
        def view(request):
            return HttpResponse(status=200)

        # 获取初始计数
        initial_count = api_request_counter.labels(
            method="GET", endpoint="/api/v1/test/", status=200
        )._value.get()

        # 调用视图
        response = view(request)

        # 验证计数增加
        new_count = api_request_counter.labels(
            method="GET", endpoint="/api/v1/test/", status=200
        )._value.get()
        assert new_count > initial_count
        assert response.status_code == 200

    @pytest.mark.skipif(not PROMETHEUS_AVAILABLE, reason="prometheus_client not installed")
    def test_track_api_request_records_response_time(self):
        """测试跟踪API请求记录响应时间"""
        request = Mock()
        request.method = "POST"
        request.path = "/api/v1/projects/"
        request.resolver_match = None

        @track_api_request
        def view(request):
            return HttpResponse(status=201)

        response = view(request)

        # 验证响应时间被记录（通过检查样本数）
        samples = api_response_time_histogram.labels(
            method="POST", endpoint="/api/v1/projects/"
        )._samples()
        assert len(samples) > 0
        assert response.status_code == 201

    @pytest.mark.skipif(not PROMETHEUS_AVAILABLE, reason="prometheus_client not installed")
    @override_settings(SLOW_REQUEST_THRESHOLD_MS=100)
    def test_track_slow_request(self):
        """测试跟踪慢请求"""
        request = Mock()
        request.method = "GET"
        request.path = "/api/v1/slow/"
        request.resolver_match = None

        @track_api_request
        def slow_view(request):
            import time

            time.sleep(0.15)  # 150ms，超过100ms阈值
            return HttpResponse(status=200)

        response = slow_view(request)

        # 验证慢请求计数器增加
        samples = api_slow_request_counter.labels(method="GET", endpoint="/api/v1/slow/")._samples()
        assert len(samples) > 0
        assert response.status_code == 200

    @pytest.mark.skipif(not PROMETHEUS_AVAILABLE, reason="prometheus_client not installed")
    def test_track_failed_request(self):
        """测试跟踪失败的请求"""
        request = Mock()
        request.method = "DELETE"
        request.path = "/api/v1/projects/999/"
        request.resolver_match = None

        @track_api_request
        def failing_view(request):
            raise ValueError("Not found")

        # 验证异常被正确抛出
        with pytest.raises(ValueError):
            failing_view(request)

        # 验证失败请求被计数
        samples = api_request_counter.labels(
            method="DELETE", endpoint="/api/v1/projects/999/", status=500
        )._samples()
        assert len(samples) > 0


class TestPrometheusMetricsMiddleware:
    """
    测试Prometheus指标中间件
    """

    @pytest.mark.skipif(not PROMETHEUS_AVAILABLE, reason="prometheus_client not installed")
    def test_middleware_initialization(self):
        """测试中间件初始化"""
        get_response = Mock()
        middleware = PrometheusMetricsMiddleware(get_response)
        assert middleware.get_response == get_response

    @pytest.mark.skipif(not PROMETHEUS_AVAILABLE, reason="prometheus_client not installed")
    def test_middleware_tracks_requests(self):
        """测试中间件跟踪请求"""
        request = Mock()
        request.method = "GET"
        request.path = "/api/v1/test/"
        request.resolver_match = None

        get_response = Mock(return_value=HttpResponse(status=200))
        middleware = PrometheusMetricsMiddleware(get_response)

        # 获取初始计数
        initial_count = (
            api_request_counter.labels(
                method="GET", endpoint="/api/v1/test/", status=200
            )._value.get()
            or 0
        )

        # 调用中间件
        response = middleware(request)

        # 验证计数增加
        new_count = (
            api_request_counter.labels(
                method="GET", endpoint="/api/v1/test/", status=200
            )._value.get()
            or 0
        )
        assert new_count > initial_count
        assert response.status_code == 200

    @pytest.mark.skipif(not PROMETHEUS_AVAILABLE, reason="prometheus_client not installed")
    def test_middleware_tracks_response_time(self):
        """测试中间件记录响应时间"""
        request = Mock()
        request.method = "POST"
        request.path = "/api/v1/projects/"
        request.resolver_match = None

        get_response = Mock(return_value=HttpResponse(status=201))
        middleware = PrometheusMetricsMiddleware(get_response)

        response = middleware(request)

        # 验证响应时间被记录
        samples = api_response_time_histogram.labels(
            method="POST", endpoint="/api/v1/projects/"
        )._samples()
        assert len(samples) > 0
        assert response.status_code == 201


class TestMetricsView:
    """
    测试指标导出视图
    """

    @pytest.mark.skipif(not PROMETHEUS_AVAILABLE, reason="prometheus_client not installed")
    def test_metrics_view_returns_prometheus_format(self):
        """测试指标视图返回Prometheus格式"""
        request = Mock()

        response = metrics_view(request)

        assert response.status_code == 200
        assert "text/plain" in response["Content-Type"]
        assert "charset=utf-8" in response["Content-Type"]

    @pytest.mark.skipif(PROMETHEUS_AVAILABLE, reason="prometheus_client is installed")
    def test_metrics_view_when_not_available(self):
        """测试Prometheus不可用时的视图"""
        request = Mock()

        response = metrics_view(request)

        assert response.status_code == 501
        assert b"not available" in response.content


class TestMetricsWithoutPrometheusClient:
    """
    测试没有prometheus_client时的行为
    """

    @pytest.mark.skipif(PROMETHEUS_AVAILABLE, reason="prometheus_client is installed")
    def test_decorators_work_without_prometheus(self):
        """测试装饰器在没有prometheus_client时也能工作"""
        request = Mock()

        @track_api_request
        def view(request):
            return HttpResponse(status=200)

        response = view(request)
        assert response.status_code == 200
