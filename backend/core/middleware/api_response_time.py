"""
API响应时间监控中间件
记录API调用耗时，标记慢请求

功能:
- 记录API响应时间（毫秒）
- 对超过500ms的慢请求标记为WARNING级别
- 结构化日志记录
- 支持P95/P99响应时间分析

遵循SOLID原则:
- 单一职责：仅负责响应时间监控
- 开闭原则：可扩展新的监控指标
- 依赖倒置：依赖Django抽象接口
"""

import logging
import time
from typing import Any

from django.conf import settings
from django.http import HttpRequest, HttpResponse

from core.middleware.api_error_logging import APIErrorLoggingMiddleware

logger = logging.getLogger("apps.api")

# 慢请求阈值（毫秒）- 从settings读取，便于运维调整
SLOW_REQUEST_THRESHOLD_MS = getattr(settings, "SLOW_REQUEST_THRESHOLD_MS", 500)

# Epic 2.5: Prometheus metrics
try:
    from prometheus_client import Counter, Histogram

    PROMETHEUS_ENABLED = True

    # HTTP请求总数
    http_requests_total = Counter(
        "http_requests_total", "Total HTTP requests", ["method", "endpoint", "status"]
    )

    # HTTP请求响应时间（直方图）
    http_request_duration_seconds = Histogram(
        "http_request_duration_seconds",
        "HTTP request duration seconds",
        ["method", "endpoint"],
        buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
    )
except ImportError:
    # prometheus_client未安装，禁用Prometheus
    PROMETHEUS_ENABLED = False
    logger.warning("prometheus_client not installed, Prometheus metrics disabled")


class APIResponseTimeMiddleware(APIErrorLoggingMiddleware):
    """
    API响应时间监控中间件

    继承自APIErrorLoggingMiddleware，在错误处理的基础上
    添加响应时间监控功能

    Epic 2优化: 慢请求阈值从settings配置读取
    """

    def __call__(self, request: HttpRequest) -> HttpResponse:
        """
        处理请求，记录响应时间

        Args:
            request: HTTP请求对象

        Returns:
            HttpResponse: HTTP响应对象
        """
        # 记录开始时间
        start_time = time.time()

        try:
            # 调用父类处理（包含错误处理）
            response = super().__call__(request)
        except Exception:
            # 即使有异常，也记录响应时间
            elapsed_ms = (time.time() - start_time) * 1000
            # 异常情况下没有response对象，传递None
            self._log_response_time(request, None, elapsed_ms, had_error=True)
            raise

        # 计算响应时间
        elapsed_ms = (time.time() - start_time) * 1000

        # 记录响应时间
        self._log_response_time(request, response, elapsed_ms, had_error=False)

        # 添加响应时间到响应头（可选，用于调试）
        response["X-Response-Time-ms"] = f"{elapsed_ms:.2f}ms"

        return response

    def _log_response_time(
        self, request: HttpRequest, response, elapsed_ms: float, had_error: bool = False
    ) -> None:
        """
        记录响应时间（结构化日志 + Prometheus metrics）

        Epic 2.5: 添加Prometheus metrics导出

        Args:
            request: HTTP请求对象
            response: HTTP响应对象
            elapsed_ms: 响应时间（毫秒）
            had_error: 是否有错误
        """
        # Epic 2.5: 记录Prometheus metrics
        if PROMETHEUS_ENABLED:
            try:
                endpoint = self._extract_endpoint(request)
                # 处理response为None的情况（异常时）
                status = getattr(response, "status_code", 0) if response else 0

                # 记录请求总数
                http_requests_total.labels(
                    method=request.method, endpoint=endpoint, status=status
                ).inc()

                # 记录响应时间（秒）
                http_request_duration_seconds.labels(
                    method=request.method, endpoint=endpoint
                ).observe(elapsed_ms / 1000)
            except Exception as e:
                logger.warning(f"Failed to record Prometheus metrics: {e}")

        # 确定日志级别
        if elapsed_ms > SLOW_REQUEST_THRESHOLD_MS:
            log_level = logging.WARNING
        else:
            log_level = logging.INFO

        # 构建日志上下文
        context = {
            "request_id": getattr(request, "request_id", "unknown"),
            "method": request.method,
            "path": request.path,
            "response_time_ms": round(elapsed_ms, 2),
            "is_slow_request": elapsed_ms > SLOW_REQUEST_THRESHOLD_MS,
            "had_error": had_error,
        }

        # 添加用户ID（如果可用）
        user_id = self._get_user_id(request)
        if user_id is not None:
            context["user_id"] = user_id

        # 记录日志
        logger.log(
            log_level,
            f"API Request: {request.method} {request.path} - {elapsed_ms:.2f}ms",
            extra={"extra_fields": context},
        )

    def _extract_endpoint(self, request: HttpRequest) -> str:
        """
        Epic 2.5: 从request中提取endpoint名称

        Args:
            request: HTTP请求对象

        Returns:
            str: endpoint名称
        """
        # 尝试从resolve match中获取
        if hasattr(request, "resolver_match"):
            try:
                match = request.resolver_match
                if hasattr(match, "url_name"):
                    return match.url_name or "unknown"
                elif hasattr(match, "route"):
                    return match.route or "unknown"
            except Exception:
                pass

        # 回退到请求路径
        path = request.path
        if "?" in path:
            path = path.split("?")[0]
        path = path.rstrip("/") or "/"

        # 转换为有效的metric label
        path = path.replace("/", "_").replace("-", "_")
        if path.startswith("_"):
            path = "root" + path

        return path if path else "unknown"

    def _get_user_id(self, request: HttpRequest) -> Any:
        """
        获取用户ID

        Args:
            request: HTTP请求对象

        Returns:
            Any: 用户ID
        """
        try:
            if hasattr(request, "user") and request.user.is_authenticated:
                return request.user.id
        except Exception:
            pass
        return None


class APIResponseTimeMiddlewareStandalone:
    """
    API响应时间监控中间件（独立版本）

    如果不想继承APIErrorLoggingMiddleware，可以使用这个版本
    仍然提供完整的响应时间监控功能

    Epic 2优化: 慢请求阈值从settings配置读取
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
        处理请求，记录响应时间

        Args:
            request: HTTP请求对象

        Returns:
            HttpResponse: HTTP响应对象
        """
        # 记录开始时间
        start_time = time.time()

        # 处理请求
        response = self.get_response(request)

        # 计算响应时间
        elapsed_ms = (time.time() - start_time) * 1000

        # 记录响应时间
        self._log_response_time(request, response, elapsed_ms)

        # 添加响应时间到响应头
        response["X-Response-Time-ms"] = f"{elapsed_ms:.2f}ms"

        return response

    def _log_response_time(self, request: HttpRequest, response, elapsed_ms: float) -> None:
        """
        记录响应时间（结构化日志）

        Args:
            request: HTTP请求对象
            response: HTTP响应对象
            elapsed_ms: 响应时间（毫秒）
        """
        # 确定日志级别
        if elapsed_ms > SLOW_REQUEST_THRESHOLD_MS:
            log_level = logging.WARNING
        else:
            log_level = logging.INFO

        # 构建日志上下文
        context = {
            "request_id": getattr(request, "request_id", "unknown"),
            "method": request.method,
            "path": request.path,
            "response_time_ms": round(elapsed_ms, 2),
            "is_slow_request": elapsed_ms > SLOW_REQUEST_THRESHOLD_MS,
        }

        # 记录日志
        logger.log(
            log_level,
            f"API Request: {request.method} {request.path} - {elapsed_ms:.2f}ms",
            extra={"extra_fields": context},
        )
