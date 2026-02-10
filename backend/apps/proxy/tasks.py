"""
Celery 任务 - 代理健康检查
Story 9.10: Celery Beat健康检查实现

任务:
- check_proxy_health: 定期检查代理健康状态
- 连续失败阈值: 3次
- 健康恢复阈值: 连续3次成功
- 执行间隔: 5分钟（300秒）

@Author: Epic 9 Team
@Created: 2026-01-31
"""

import logging

import httpx
from celery import shared_task
from django.utils import timezone

from .models import ProxyConfig, ProxyUsageLog

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=0)
def check_proxy_health(self):
    """
    检查所有启用代理的健康状态 - Story 9.10

    测试流程：
    1. 查询所有 is_active=True 的代理
    2. 通过代理访问 https://httpbin.org/ip
    3. 连续失败 > 3次 → is_healthy = False
    4. 连续成功 3次 → is_healthy = True
    5. 记录测试结果到 ProxyUsageLog

    Args:
        self: Celery task instance

    Returns:
        dict: 统计信息 {total, healthy_count, unhealthy_count, errors}

    Raises:
        Exception: 任务执行失败时抛出（Celery会重试）
    """
    # 查询所有启用的代理
    active_proxies = ProxyConfig.objects.filter(is_active=True)
    total = active_proxies.count()

    if total == 0:
        logger.info("没有启用的代理需要检查")
        return {"total": 0, "healthy_count": 0, "unhealthy_count": 0, "errors": []}

    healthy_count = 0
    unhealthy_count = 0
    errors = []

    for proxy in active_proxies:
        try:
            # 获取代理URL
            proxy_url = proxy.get_proxy_url()

            # 发送测试请求（5秒超时）
            start_time = timezone.now()
            with httpx.Client(timeout=5.0) as client:
                response = client.get(
                    "https://httpbin.org/ip",
                    proxies={"all://": proxy_url},
                )
                response.raise_for_status()

            # 解析响应
            result = response.json()
            origin_ip = result.get("origin", "")

            # 计算响应时间
            end_time = timezone.now()
            response_time_ms = int((end_time - start_time).total_seconds() * 1000)

            # 测试成功
            proxy.consecutive_failures = 0  # 重置连续失败计数
            proxy.consecutive_successes += 1  # 增加连续成功计数

            # 健康恢复逻辑：连续3次成功 → is_healthy = True
            if proxy.consecutive_successes >= 3:
                if not proxy.is_healthy:
                    logger.info(
                        f"代理 {proxy.name} 健康恢复（连续{proxy.consecutive_successes}次成功）"
                    )
                proxy.is_healthy = True

            proxy.save(
                update_fields=["consecutive_failures", "consecutive_successes", "is_healthy"]
            )
            healthy_count += 1

            # 记录成功的日志
            ProxyUsageLog.objects.create(
                proxy=proxy,
                ai_provider="celery",
                endpoint="https://httpbin.org/ip",
                response_time_ms=response_time_ms,
                success=True,
            )

            logger.info(
                f"✓ 代理 {proxy.name} 健康检查通过（IP: {origin_ip}，{response_time_ms}ms）"
            )

        except httpx.TimeoutException:
            # 超时错误
            logger.warning(f"✗ 代理 {proxy.name} 健康检查超时")

            # 增加连续失败计数
            proxy.consecutive_failures += 1
            proxy.consecutive_successes = 0  # 重置连续成功计数

            # 连续失败逻辑：>3次 → is_healthy = False
            if proxy.consecutive_failures > 3:
                if proxy.is_healthy:
                    logger.error(
                        f"代理 {proxy.name} 标记为不健康（连续{proxy.consecutive_failures}次失败）"
                    )
                proxy.is_healthy = False

            proxy.save(
                update_fields=["consecutive_failures", "consecutive_successes", "is_healthy"]
            )
            unhealthy_count += 1

            # 记录失败的日志
            ProxyUsageLog.objects.create(
                proxy=proxy,
                ai_provider="celery",
                endpoint="https://httpbin.org/ip",
                response_time_ms=5000,  # 超时时间
                success=False,
                error_message="Connection timeout",
            )

        except httpx.HTTPStatusError as e:
            # HTTP错误
            logger.warning(f"✗ 代理 {proxy.name} 健康检查HTTP错误: {e.response.status_code}")

            # 增加连续失败计数
            proxy.consecutive_failures += 1
            proxy.consecutive_successes = 0

            # 连续失败逻辑
            if proxy.consecutive_failures > 3:
                if proxy.is_healthy:
                    logger.error(
                        f"代理 {proxy.name} 标记为不健康（连续{proxy.consecutive_failures}次失败）"
                    )
                proxy.is_healthy = False

            proxy.save(
                update_fields=["consecutive_failures", "consecutive_successes", "is_healthy"]
            )
            unhealthy_count += 1

            # 记录失败的日志
            ProxyUsageLog.objects.create(
                proxy=proxy,
                ai_provider="celery",
                endpoint="https://httpbin.org/ip",
                response_time_ms=0,
                success=False,
                error_message=f"HTTP error {e.response.status_code}",
            )

        except Exception as e:
            # 其他错误
            logger.error(f"✗ 代理 {proxy.name} 健康检查异常: {e}", exc_info=True)

            # 增加连续失败计数
            proxy.consecutive_failures += 1
            proxy.consecutive_successes = 0

            # 连续失败逻辑
            if proxy.consecutive_failures > 3:
                if proxy.is_healthy:
                    logger.error(
                        f"代理 {proxy.name} 标记为不健康（连续{proxy.consecutive_failures}次失败）"
                    )
                proxy.is_healthy = False

            proxy.save(
                update_fields=["consecutive_failures", "consecutive_successes", "is_healthy"]
            )
            unhealthy_count += 1

            # 记录失败的日志
            ProxyUsageLog.objects.create(
                proxy=proxy,
                ai_provider="celery",
                endpoint="https://httpbin.org/ip",
                response_time_ms=0,
                success=False,
                error_message=str(e),
            )

    # 汇总统计
    errors = []
    if unhealthy_count > 0:
        errors.append(f"{unhealthy_count} 个代理不健康")

    result = {
        "total": total,
        "healthy_count": healthy_count,
        "unhealthy_count": unhealthy_count,
        "errors": errors,
    }

    logger.info(f"健康检查完成：总计 {total}，健康 {healthy_count}，不健康 {unhealthy_count}")

    return result
