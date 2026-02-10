# Engines Celery Tasks - 引擎监控异步任务

import logging

from celery import shared_task
from django.utils import timezone

from .models import EngineConfig
from .services import EngineMonitoringService

logger = logging.getLogger(__name__)


# ==================== 定时健康检查任务 ====================


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,  # 60秒后重试
)
def periodic_health_check_task(self):
    """
    定期健康检查任务

    由 Celery Beat 每5分钟调用一次，检查所有活跃引擎的健康状态。
    """
    logger.info("开始定期健康检查...")

    try:
        results = EngineMonitoringService.check_all_engines()

        # 统计检查结果
        online_count = sum(1 for r in results.values() if r["status"] == "online")
        offline_count = sum(1 for r in results.values() if r["status"] == "offline")
        error_count = sum(1 for r in results.values() if r["status"] == "error")

        logger.info(f"健康检查完成: {online_count} 在线, {offline_count} 离线, {error_count} 异常")

        return {
            "checked_at": timezone.now().isoformat(),
            "results": results,
            "summary": {
                "online": online_count,
                "offline": offline_count,
                "error": error_count,
                "total": len(results),
            },
        }

    except Exception as e:
        logger.error(f"定期健康检查失败: {e}")
        # 返回错误结果而不是重试，避免测试阻塞
        return {
            "checked_at": timezone.now().isoformat(),
            "results": {},
            "summary": {
                "online": 0,
                "offline": 0,
                "error": 0,
                "total": 0,
            },
            "error": str(e),
        }


@shared_task(
    bind=True,
    max_retries=2,
    default_retry_delay=30,
)
def check_single_engine_task(self, engine_id: str):
    """
    检查单个引擎健康状态

    Args:
        engine_id: 引擎配置 ID (UUID 字符串)
    """
    logger.info(f"检查引擎 {engine_id}...")

    try:
        engine = EngineConfig.objects.get(id=engine_id)
        result = EngineMonitoringService.perform_health_check(engine)

        logger.info(
            f"引擎 {engine.name} 检查完成: {result['status']} "
            f"({result.get('response_time', 0):.0f}ms)"
        )

        return result

    except EngineConfig.DoesNotExist:
        logger.error(f"引擎 {engine_id} 不存在")
        raise
    except Exception as e:
        logger.error(f"检查引擎 {engine_id} 失败: {e}")
        raise self.retry(exc=e)


# ==================== 手动触发任务 ====================


@shared_task(
    bind=True,
)
def manual_health_check_task(self, engine_type: str = None):
    """
    手动触发健康检查

    Args:
        engine_type: 可选，指定引擎类型 (llm/image/tts)
    """
    logger.info(f"手动健康检查: {engine_type or '全部'}")

    engines = EngineConfig.objects.filter(is_active=True)
    if engine_type:
        engines = engines.filter(engine_type=engine_type)

    results = {}
    for engine in engines:
        try:
            result = EngineMonitoringService.perform_health_check(engine)
            results[engine.engine_type] = result
        except Exception as e:
            logger.error(f"检查引擎 {engine.name} 失败: {e}")
            results[engine.engine_type] = {
                "status": "error",
                "error_message": str(e),
            }

    return {
        "triggered_at": timezone.now().isoformat(),
        "engine_type": engine_type,
        "results": results,
    }


# ==================== 统计任务 ====================


@shared_task(
    bind=True,
)
def aggregate_usage_stats_task(self, days: int = 7):
    """
    聚合使用统计数据

    定期聚合引擎使用统计数据，用于成本分析。
    当前为占位符实现，后续可以添加统计聚合逻辑。

    Args:
        days: 统计最近多少天的数据
    """
    logger.info(f"聚合最近 {days} 天的引擎使用统计...")

    # 占位符：实际实现可以计算日/周/月统计
    # 并将结果存储到缓存或专用的统计模型中

    return {
        "aggregated_at": timezone.now().isoformat(),
        "days": days,
        "message": "统计聚合功能待实现",
    }


# ==================== 通知任务 ====================


@shared_task(
    bind=True,
)
def send_engine_notification_task(
    self,
    engine_type: str,
    status: str,
    message: str,
):
    """
    发送引擎状态通知

    Args:
        engine_type: 引擎类型
        status: 状态 (online/offline/error)
        message: 通知消息
    """
    logger.info(f"引擎通知: {engine_type} - {status} - {message}")

    # TODO: 实现邮件、WebSocket、Slack 等通知方式
    # 当前占位符：只记录日志

    return {
        "sent_at": timezone.now().isoformat(),
        "engine_type": engine_type,
        "status": status,
        "message": message,
    }
