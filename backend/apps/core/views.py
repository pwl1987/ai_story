"""
系统健康检查和监控视图
"""

from django.http import JsonResponse, HttpRequest
from django.views.decorators.http import require_GET
from django.db import connection
from django.core.cache import cache
import time


@require_GET
def health_check(request: HttpRequest) -> JsonResponse:
    """
    系统健康检查端点

    返回系统状态,包括:
    - 数据库连接状态
    - Redis缓存状态
    - 响应时间

    Returns:
        JsonResponse: 健康状态JSON

    示例响应:
    {
        "status": "healthy",
        "timestamp": "2026-01-27T10:00:00Z",
        "checks": {
            "database": {"status": "healthy", "latency_ms": 5},
            "cache": {"status": "healthy", "latency_ms": 2},
            "response_time_ms": 8
        }
    }
    """
    start_time = time.time()

    # 检查数据库连接
    db_status = _check_database()

    # 检查缓存连接
    cache_status = _check_cache()

    # 计算总响应时间
    response_time_ms = int((time.time() - start_time) * 1000)

    # 判断总体健康状态
    overall_status = "healthy"
    if db_status["status"] != "healthy" or cache_status["status"] != "healthy":
        overall_status = "unhealthy"

    # 响应阈值检查
    if response_time_ms > 200:
        overall_status = "degraded"

    return JsonResponse({
        "status": overall_status,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "checks": {
            "database": db_status,
            "cache": cache_status,
        },
        "response_time_ms": response_time_ms,
    })


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
