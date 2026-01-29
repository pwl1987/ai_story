"""
Prometheus metrics中间件
Epic 2.5 - API响应时间监控

自动收集和导出API请求指标
"""

import time

from django.utils.deprecation import MiddlewareMixin
from prometheus_client import Counter, Histogram

# HTTP请求总数
http_requests_total = Counter(
    "http_requests_total", "Total HTTP requests", ["method", "endpoint", "status"]
)

# HTTP请求响应时间（直方图）
http_request_duration_seconds = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration",
    ["method", "endpoint"],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
)

# 数据库连接池
db_connections = Histogram(
    "db_connections",
    "Database connections",
    ["state"],  # idle, active
    buckets=(1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 20, 50, 100),
)

# Celery Workers
celery_workers_gauge = Histogram(
    "celery_workers", "Celery workers", buckets=(0, 1, 2, 3, 4, 5, 10, 20, 50)
)

# Celery队列长度
celery_queue_length = Histogram(
    "celery_queue_length",
    "Celery queue length",
    ["queue"],
    buckets=(0, 1, 2, 5, 10, 20, 50, 100, 200, 500, 1000),
)


class PrometheusMetricsMiddleware(MiddlewareMixin):
    """
    Prometheus metrics中间件

    自动记录每个HTTP请求的指标
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start_time = time.time()

        # 处理请求
        response = self.get_response(request)

        # 记录指标
        self._record_metrics(request, response, start_time)

        return response

    def _record_metrics(self, request, response, start_time):
        """记录prometheus指标"""
        # 计算响应时间
        duration = time.time() - start_time

        # 提取endpoint名称
        endpoint = self._extract_endpoint(request)

        # 记录请求总数
        http_requests_total.labels(
            method=request.method, endpoint=endpoint, status=response.status_code
        ).inc()

        # 记录响应时间
        http_request_duration_seconds.labels(method=request.method, endpoint=endpoint).observe(
            duration
        )

    def _extract_endpoint(self, request):
        """从request中提取endpoint名称"""
        # 尝试从resolve match中获取
        if hasattr(request, "resolver_match"):
            try:
                # 获取URL模式名称
                match = request.resolver_match
                if hasattr(match, "url_name"):
                    return match.url_name or "unknown"
                elif hasattr(match, "route"):
                    return match.route or "unknown"
            except Exception:
                pass

        # 回退到请求路径
        path = request.path
        # 去掉参数和尾部斜杠
        if "?" in path:
            path = path.split("?")[0]
        path = path.rstrip("/") or "/"

        # 将路径转换为有效的metric label
        # 替换特殊字符
        path = path.replace("/", "_").replace("-", "_")
        if path.startswith("_"):
            path = "root" + path

        return path if path else "unknown"
