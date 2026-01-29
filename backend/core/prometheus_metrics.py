"""
Prometheus指标导出模块
Epic 2优化：提供系统监控指标

功能:
- API请求计数器
- API响应时间直方图
- Celery任务计数器
- Celery任务执行时间直方图
- 慢请求和慢任务监控

遵循SOLID原则:
- 单一职责：仅负责Prometheus指标定义和导出
- 开闭原则：可扩展新的指标类型
- 依赖倒置：依赖prometheus_client抽象
"""

import time
from functools import wraps
from typing import Callable

from django.conf import settings
from django.http import HttpRequest, HttpResponse

try:
    from prometheus_client import CONTENT_TYPE_LATEST, Counter, Gauge, Histogram, generate_latest

    PROMETHEUS_AVAILABLE = True
except ImportError:
    # 如果prometheus_client未安装，提供mock实现
    PROMETHEUS_AVAILABLE = False

    class Counter:
        def __init__(self, *args, **kwargs):
            pass

        def inc(self, amount=1):
            pass

        def labels(self, **kwargs):
            return self

    class Histogram:
        def __init__(self, *args, **kwargs):
            pass

        def observe(self, amount):
            pass

        def labels(self, **kwargs):
            return self

        def time(self):
            def decorator(func):
                @wraps(func)
                def wrapper(*args, **kwargs):
                    return func(*args, **kwargs)

                return wrapper

            return decorator

    class Gauge:
        def __init__(self, *args, **kwargs):
            pass

        def set(self, value):
            pass

        def inc(self, amount=1):
            pass

        def dec(self, amount=1):
            pass

        def labels(self, **kwargs):
            return self

    def generate_latest():
        return b""

    CONTENT_TYPE_LATEST = "text/plain"


# ============ API指标 ============

# API请求计数器
api_request_counter = Counter(
    "api_requests_total", "Total API requests", ["method", "endpoint", "status"]
)

# API响应时间直方图（毫秒）
api_response_time_histogram = Histogram(
    "api_response_time_milliseconds",
    "API response time in milliseconds",
    ["method", "endpoint"],
    buckets=[5, 10, 25, 50, 100, 250, 500, 1000, 2500, 5000, 10000],
)

# 慢请求计数器
api_slow_request_counter = Counter(
    "api_slow_requests_total", "Total slow API requests (above threshold)", ["method", "endpoint"]
)

# ============ Celery指标 ============
# 注意: Celery指标已在 config/celery.py 中定义，避免重复注册


# ============ 辅助函数 ============


def get_endpoint_from_request(request: HttpRequest) -> str:
    """
    从请求中提取端点名称

    Args:
        request: HTTP请求对象

    Returns:
        str: 端点名称（如 /api/v1/projects/）
    """
    # 尝试从路由模式获取端点
    if hasattr(request, "resolver_match") and request.resolver_match:
        # 使用路由模式（如 api:project-list）
        route_pattern = getattr(request.resolver_match, "route", None)
        if route_pattern:
            return route_pattern

        # 使用URL名称
        url_name = request.resolver_match.url_name
        if url_name:
            return (
                f"{request.resolver_match.namespace}:{url_name}"
                if request.resolver_match.namespace
                else url_name
            )

    # 回退到路径
    return request.path


def track_api_request(func: Callable) -> Callable:
    """
    装饰器：跟踪API请求指标

    Args:
        func: 被装饰的函数

    Returns:
        包装后的函数
    """

    @wraps(func)
    def wrapper(request: HttpRequest, *args, **kwargs):
        # 记录开始时间
        start_time = time.time()

        # 提取端点信息
        endpoint = get_endpoint_from_request(request)
        method = request.method

        try:
            # 执行请求
            response = func(request, *args, **kwargs)

            # 记录请求计数
            api_request_counter.labels(
                method=method, endpoint=endpoint, status=response.status_code
            ).inc()

            # 记录响应时间
            elapsed_ms = (time.time() - start_time) * 1000
            api_response_time_histogram.labels(method=method, endpoint=endpoint).observe(elapsed_ms)

            # 检查是否为慢请求
            slow_threshold = getattr(settings, "SLOW_REQUEST_THRESHOLD_MS", 500)
            if elapsed_ms > slow_threshold:
                api_slow_request_counter.labels(method=method, endpoint=endpoint).inc()

            return response

        except Exception:
            # 记录失败的请求
            api_request_counter.labels(method=method, endpoint=endpoint, status=500).inc()

            raise

    return wrapper


def metrics_view(request: HttpRequest) -> HttpResponse:
    """
    Prometheus指标导出视图

    Args:
        request: HTTP请求对象

    Returns:
        HttpResponse: Prometheus格式的指标数据
    """
    if not PROMETHEUS_AVAILABLE:
        return HttpResponse(
            "# Prometheus metrics not available (prometheus_client not installed)",
            content_type="text/plain",
            status=501,
        )

    metrics_data = generate_latest()
    return HttpResponse(metrics_data, content_type=CONTENT_TYPE_LATEST)


# ============ 中间件集成 ============


class PrometheusMetricsMiddleware:
    """
    Prometheus指标中间件

    自动记录所有API请求的指标
    """

    def __init__(self, get_response):
        """
        初始化中间件

        Args:
            get_response: 下一个中间件或视图的响应函数
        """
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        """
        处理请求，记录Prometheus指标

        Args:
            request: HTTP请求对象

        Returns:
            HttpResponse: HTTP响应对象
        """
        if not PROMETHEUS_AVAILABLE:
            return self.get_response(request)

        # 记录开始时间
        start_time = time.time()

        # 提取请求信息
        endpoint = get_endpoint_from_request(request)
        method = request.method

        try:
            # 处理请求
            response = self.get_response(request)

            # 记录请求计数
            api_request_counter.labels(
                method=method, endpoint=endpoint, status=response.status_code
            ).inc()

            # 记录响应时间
            elapsed_ms = (time.time() - start_time) * 1000
            api_response_time_histogram.labels(method=method, endpoint=endpoint).observe(elapsed_ms)

            # 检查是否为慢请求
            slow_threshold = getattr(settings, "SLOW_REQUEST_THRESHOLD_MS", 500)
            if elapsed_ms > slow_threshold:
                api_slow_request_counter.labels(method=method, endpoint=endpoint).inc()

            return response

        except Exception:
            # 记录失败的请求
            api_request_counter.labels(method=method, endpoint=endpoint, status=500).inc()

            raise
