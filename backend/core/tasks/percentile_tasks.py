"""
P95/P99自动化统计定时任务
Epic 2优化：Celery Beat定时任务自动计算百分位数

功能:
- 每15分钟自动计算API响应时间百分位数
- 每15分钟自动计算Celery任务执行时间百分位数
- 结果自动缓存到Django cache
- 支持手动触发计算

遵循SOLID原则:
- 单一职责：仅负责定时任务调度
- 开闭原则：可扩展新的统计任务
"""

import logging

from celery import shared_task

from core.services.percentile_stats import PercentileStats

logger = logging.getLogger("apps.core")


@shared_task(
    name="core.calculate_percentile_stats",
    bind=True,
    max_retries=3,
    default_retry_delay=60,  # 1分钟后重试
)
def calculate_percentile_stats_task(self, time_window_minutes: int = 15):
    """
    计算百分位数统计的定时任务

    计算API响应时间和Celery任务执行时间的百分位数

    Args:
        self: Celery任务实例
        time_window_minutes: 时间窗口（分钟），默认15分钟

    Returns:
        Dict: 统计结果
    """
    logger.info(
        "开始执行百分位数统计任务",
        extra={
            "extra_fields": {"task_id": self.request.id, "time_window_minutes": time_window_minutes}
        },
    )

    try:
        # 计算所有百分位数
        result = PercentileStats.calculate_all_percentiles(time_window_minutes)

        logger.info(
            "百分位数统计任务完成",
            extra={
                "extra_fields": {
                    "task_id": self.request.id,
                    "api_sample_count": result["api"]["sample_count"],
                    "celery_sample_count": result["celery"]["sample_count"],
                    "api_p95": result["api"]["percentiles"].get("p95"),
                    "api_p99": result["api"]["percentiles"].get("p99"),
                    "celery_p95": result["celery"]["percentiles"].get("p95"),
                    "celery_p99": result["celery"]["percentiles"].get("p99"),
                }
            },
        )

        return result

    except Exception as e:
        logger.error(
            f"百分位数统计任务失败: {e}",
            exc_info=True,
            extra={
                "extra_fields": {
                    "task_id": self.request.id,
                    "error": str(e),
                    "retries": self.request.retries,
                }
            },
        )
        raise


@shared_task(name="core.calculate_api_percentiles", bind=True, max_retries=3)
def calculate_api_percentiles_task(self, time_window_minutes: int = 15):
    """
    计算API响应时间百分位数

    Args:
        self: Celery任务实例
        time_window_minutes: 时间窗口（分钟）

    Returns:
        Dict: API百分位数统计
    """
    logger.info(
        "开始计算API响应时间百分位数",
        extra={
            "extra_fields": {"task_id": self.request.id, "time_window_minutes": time_window_minutes}
        },
    )

    try:
        result = PercentileStats.calculate_api_percentiles(time_window_minutes)

        logger.info(
            "API百分位数计算完成",
            extra={
                "extra_fields": {
                    "task_id": self.request.id,
                    "sample_count": result["sample_count"],
                    "p95": result["percentiles"].get("p95"),
                    "p99": result["percentiles"].get("p99"),
                }
            },
        )

        return result

    except Exception as e:
        logger.error(
            f"API百分位数计算失败: {e}",
            exc_info=True,
            extra={"extra_fields": {"task_id": self.request.id, "error": str(e)}},
        )
        raise


@shared_task(name="core.calculate_celery_percentiles", bind=True, max_retries=3)
def calculate_celery_percentiles_task(self, time_window_minutes: int = 15):
    """
    计算Celery任务执行时间百分位数

    Args:
        self: Celery任务实例
        time_window_minutes: 时间窗口（分钟）

    Returns:
        Dict: Celery百分位数统计
    """
    logger.info(
        "开始计算Celery任务执行时间百分位数",
        extra={
            "extra_fields": {"task_id": self.request.id, "time_window_minutes": time_window_minutes}
        },
    )

    try:
        result = PercentileStats.calculate_celery_percentiles(time_window_minutes)

        logger.info(
            "Celery百分位数计算完成",
            extra={
                "extra_fields": {
                    "task_id": self.request.id,
                    "sample_count": result["sample_count"],
                    "p95": result["percentiles"].get("p95"),
                    "p99": result["percentiles"].get("p99"),
                }
            },
        )

        return result

    except Exception as e:
        logger.error(
            f"Celery百分位数计算失败: {e}",
            exc_info=True,
            extra={"extra_fields": {"task_id": self.request.id, "error": str(e)}},
        )
        raise
