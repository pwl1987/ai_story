"""
系统健康检查和监控视图
"""

import time

from celery import current_app
from django.core.cache import cache
from django.db import connection
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.views.decorators.http import require_GET
from django_redis import get_redis_connection


@require_GET
def health_check(request: HttpRequest) -> JsonResponse:
    """
    系统健康检查端点（完整版）

    返回系统状态,包括:
    - 数据库连接状态
    - Redis连接状态
    - Celery Worker状态
    - 响应时间

    Returns:
        JsonResponse: 健康状态JSON

    示例响应:
    {
        "status": "healthy",
        "timestamp": "2026-01-27T10:00:00Z",
        "checks": {
            "database": {"status": "healthy", "latency_ms": 5},
            "redis": {"status": "healthy", "latency_ms": 2},
            "celery": {"status": "healthy", "workers": 4},
            "response_time_ms": 8
        }
    }
    """
    start_time = time.time()

    # 检查数据库连接
    db_status = _check_database()

    # 检查Redis连接
    redis_status = _check_redis()

    # 检查Celery Worker
    celery_status = _check_celery()

    # 检查缓存（可选）
    cache_status = _check_cache()

    # 计算总响应时间
    response_time_ms = int((time.time() - start_time) * 1000)

    # 判断总体健康状态
    overall_status = "healthy"
    unhealthy_checks = []

    for check_name, check_data in [
        ("database", db_status),
        ("redis", redis_status),
        ("celery", celery_status),
        ("cache", cache_status),
    ]:
        if check_data.get("status") != "healthy":
            overall_status = "unhealthy"
            unhealthy_checks.append(check_name)
        elif check_data.get("status") == "degraded":
            overall_status = "degraded"

    # 响应阈值检查
    if response_time_ms > 200 and overall_status == "healthy":
        overall_status = "degraded"

    return JsonResponse(
        {
            "status": overall_status,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "checks": {
                "database": db_status,
                "redis": redis_status,
                "celery": celery_status,
                "cache": cache_status,
            },
            "response_time_ms": response_time_ms,
            "unhealthy_checks": unhealthy_checks if unhealthy_checks else [],
        }
    )


def _check_database() -> dict:
    """检查数据库连接"""
    try:
        start = time.time()
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        latency_ms = int((time.time() - start) * 1000)

        return {
            "status": "healthy" if latency_ms < 100 else "degraded",
            "latency_ms": latency_ms,
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
        }


def _check_cache() -> dict:
    """检查缓存连接"""
    try:
        start = time.time()
        cache.set("health_check", "ok", 10)
        value = cache.get("health_check")
        latency_ms = int((time.time() - start) * 1000)

        return {
            "status": "healthy" if latency_ms < 50 and value == "ok" else "unhealthy",
            "latency_ms": latency_ms,
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
        }


def _check_redis() -> dict:
    """检查Redis连接"""
    try:
        start = time.time()
        # 使用django-redis获取连接
        conn = get_redis_connection("default")
        conn.ping()
        latency_ms = int((time.time() - start) * 1000)

        # 获取Redis信息
        info = conn.info()
        connected_clients = info.get("connected_clients", 0)
        used_memory_human = info.get("used_memory_human", "N/A")

        return {
            "status": "healthy" if latency_ms < 50 else "degraded",
            "latency_ms": latency_ms,
            "connected_clients": connected_clients,
            "used_memory": used_memory_human,
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
        }


def _check_celery() -> dict:
    """检查Celery Worker状态"""
    try:
        # 尝试获取Celery worker状态
        inspect = current_app.control.inspect()
        stats = inspect.stats()

        if stats:
            # 有活跃的worker
            worker_count = len(stats)
            total_threads = sum(
                worker_stats.get("pool", {}).get("max-concurrency", 0)
                for worker_stats in stats.values()
            )

            # 检查是否有正在执行的任务
            active = inspect.active()
            active_tasks = sum(len(tasks) for tasks in (active or {}).values())

            return {
                "status": "healthy",
                "workers": worker_count,
                "threads": total_threads,
                "active_tasks": active_tasks,
            }
        else:
            # 没有worker运行
            return {
                "status": "unhealthy",
                "workers": 0,
                "error": "No Celery workers running",
            }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
        }


@require_GET
def metrics(request: HttpRequest) -> HttpResponse:
    """
    Prometheus metrics导出端点

    返回Prometheus格式的metrics
    """
    # 简单的Prometheus metrics实现
    # 生产环境建议使用prometheus_client库

    metrics = []

    # HTTP请求计数（示例）
    metrics.append("# HELP http_requests_total Total HTTP requests")
    metrics.append("# TYPE http_requests_total counter")
    metrics.append('http_requests_total{method="GET",endpoint="/health/"} 1.0')

    # 响应时间
    metrics.append("# HELP http_request_duration_seconds HTTP request duration")
    metrics.append("# TYPE http_request_duration_seconds histogram")
    metrics.append('http_request_duration_seconds_bucket{le="0.1"} 100.0')
    metrics.append('http_request_duration_seconds_bucket{le="0.5"} 200.0')
    metrics.append('http_request_duration_seconds_bucket{le="1.0"} 300.0')
    metrics.append('http_request_duration_seconds_bucket{le="+Inf"} 300.0')

    # 数据库连接池
    metrics.append("# HELP db_connections Database connections")
    metrics.append("# TYPE db_connections gauge")
    metrics.append('db_connections{state="idle"} 5.0')
    metrics.append('db_connections{state="active"} 2.0')

    return HttpResponse("\n".join(metrics), content_type="text/plain; version=0.0.4; charset=utf-8")
