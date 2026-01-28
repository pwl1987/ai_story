"""
P95/P99自动化统计服务
Epic 2优化：自动计算和存储API响应时间与Celery任务执行时间的百分位数

功能:
- 定期计算P50/P75/P90/P95/P99百分位数
- 从日志中提取响应时间数据
- 存储统计结果到Redis
- 提供API查询端点

遵循SOLID原则:
- 单一职责：仅负责百分位数计算
- 开闭原则：可扩展新的统计指标
- 依赖倒置：依赖Redis抽象
"""

import json
import logging
from datetime import datetime, timedelta
from statistics import median
from typing import Any, Dict, List, Optional

from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger('apps.core')


class PercentileStats:
    """
    百分位数统计服务

    计算API响应时间和Celery任务执行时间的百分位数
    """

    # 统计时间窗口（分钟）
    TIME_WINDOW_MINUTES = 15

    # 百分位数配置
    PERCENTILES = [50, 75, 90, 95, 99]

    # 缓存key前缀
    API_STATS_KEY = 'percentile_stats:api:latest'
    CELERY_STATS_KEY = 'percentile_stats:celery:latest'

    @classmethod
    def calculate_api_percentiles(
        cls,
        time_window_minutes: int = None
    ) -> Dict[str, Any]:
        """
        计算API响应时间的百分位数

        Args:
            time_window_minutes: 时间窗口（分钟），默认使用配置值

        Returns:
            Dict: 百分位数统计结果
        """
        if time_window_minutes is None:
            time_window_minutes = cls.TIME_WINDOW_MINUTES

        logger.info(
            "计算API响应时间百分位数",
            extra={'extra_fields': {
                'time_window_minutes': time_window_minutes,
                'percentiles': cls.PERCENTILES
            }}
        )

        try:
            # 模拟数据收集（实际应从日志或metrics收集）
            # 这里使用模拟数据进行演示
            response_times = cls._collect_api_metrics(time_window_minutes)

            if not response_times:
                logger.warning("未找到API响应时间数据")
                stats = cls._get_empty_stats('api', time_window_minutes)
                cls._cache_stats(cls.API_STATS_KEY, stats)
                return stats

            # 计算百分位数
            percentiles = cls._calculate_percentiles(response_times)

            # 构建统计结果
            stats = {
                'type': 'api',
                'time_window_minutes': time_window_minutes,
                'sample_count': len(response_times),
                'percentiles': percentiles,
                'statistics': {
                    'min': round(min(response_times), 2),
                    'max': round(max(response_times), 2),
                    'avg': round(sum(response_times) / len(response_times), 2),
                    'median': round(median(response_times), 2)
                },
                'calculated_at': datetime.now().isoformat()
            }

            # 缓存统计结果
            cls._cache_stats(cls.API_STATS_KEY, stats)

            logger.info(
                "API响应时间百分位数计算完成",
                extra={'extra_fields': {
                    'sample_count': len(response_times),
                    'p95': percentiles.get('p95'),
                    'p99': percentiles.get('p99')
                }}
            )

            return stats

        except Exception as e:
            logger.error(
                f"计算API百分位数失败: {e}",
                exc_info=True,
                extra={'extra_fields': {'error': str(e)}}
            )
            stats = cls._get_empty_stats('api', time_window_minutes)
            stats['error'] = str(e)
            cls._cache_stats(cls.API_STATS_KEY, stats)
            return stats

    @classmethod
    def calculate_celery_percentiles(
        cls,
        time_window_minutes: int = None
    ) -> Dict[str, Any]:
        """
        计算Celery任务执行时间的百分位数

        Args:
            time_window_minutes: 时间窗口（分钟），默认使用配置值

        Returns:
            Dict: 百分位数统计结果
        """
        if time_window_minutes is None:
            time_window_minutes = cls.TIME_WINDOW_MINUTES

        logger.info(
            "计算Celery任务执行时间百分位数",
            extra={'extra_fields': {
                'time_window_minutes': time_window_minutes,
                'percentiles': cls.PERCENTILES
            }}
        )

        try:
            # 模拟数据收集（实际应从日志或metrics收集）
            execution_times = cls._collect_celery_metrics(time_window_minutes)

            if not execution_times:
                logger.warning("未找到Celery任务执行时间数据")
                stats = cls._get_empty_stats('celery', time_window_minutes)
                cls._cache_stats(cls.CELERY_STATS_KEY, stats)
                return stats

            # 计算百分位数
            percentiles = cls._calculate_percentiles(execution_times)

            # 构建统计结果
            stats = {
                'type': 'celery',
                'time_window_minutes': time_window_minutes,
                'sample_count': len(execution_times),
                'percentiles': percentiles,
                'statistics': {
                    'min': round(min(execution_times), 2),
                    'max': round(max(execution_times), 2),
                    'avg': round(sum(execution_times) / len(execution_times), 2),
                    'median': round(median(execution_times), 2)
                },
                'calculated_at': datetime.now().isoformat()
            }

            # 缓存统计结果
            cls._cache_stats(cls.CELERY_STATS_KEY, stats)

            logger.info(
                "Celery任务执行时间百分位数计算完成",
                extra={'extra_fields': {
                    'sample_count': len(execution_times),
                    'p95': percentiles.get('p95'),
                    'p99': percentiles.get('p99')
                }}
            )

            return stats

        except Exception as e:
            logger.error(
                f"计算Celery百分位数失败: {e}",
                exc_info=True,
                extra={'extra_fields': {'error': str(e)}}
            )
            stats = cls._get_empty_stats('celery', time_window_minutes)
            stats['error'] = str(e)
            cls._cache_stats(cls.CELERY_STATS_KEY, stats)
            return stats

    @classmethod
    def _collect_api_metrics(cls, time_window_minutes: int) -> List[float]:
        """
        收集API响应时间数据

        Args:
            time_window_minutes: 时间窗口（分钟）

        Returns:
            List[float]: 响应时间列表（毫秒）
        """
        # TODO: 实际应从日志或Prometheus收集数据
        # 这里使用模拟数据进行演示
        import random

        # 生成模拟数据：正常响应时间分布
        # 大部分请求在50-500ms之间，少数慢请求
        sample_count = 1000
        response_times = []

        for _ in range(sample_count):
            rand = random.random()
            if rand < 0.7:
                # 70%的请求在50-200ms
                response_times.append(random.uniform(50, 200))
            elif rand < 0.9:
                # 20%的请求在200-500ms
                response_times.append(random.uniform(200, 500))
            elif rand < 0.98:
                # 8%的请求在500-2000ms
                response_times.append(random.uniform(500, 2000))
            else:
                # 2%的请求在2-10秒（慢请求）
                response_times.append(random.uniform(2000, 10000))

        return response_times

    @classmethod
    def _collect_celery_metrics(cls, time_window_minutes: int) -> List[float]:
        """
        收集Celery任务执行时间数据

        Args:
            time_window_minutes: 时间窗口（分钟）

        Returns:
            List[float]: 执行时间列表（秒）
        """
        # TODO: 实际应从日志或Prometheus收集数据
        # 这里使用模拟数据进行演示
        import random

        # 生成模拟数据：任务执行时间分布
        sample_count = 500
        execution_times = []

        for _ in range(sample_count):
            rand = random.random()
            if rand < 0.6:
                # 60%的任务在5-30秒
                execution_times.append(random.uniform(5, 30))
            elif rand < 0.85:
                # 25%的任务在30-60秒
                execution_times.append(random.uniform(30, 60))
            elif rand < 0.95:
                # 10%的任务在60-120秒
                execution_times.append(random.uniform(60, 120))
            else:
                # 5%的任务在2-10分钟（慢任务）
                execution_times.append(random.uniform(120, 600))

        return execution_times

    @classmethod
    def _calculate_percentiles(cls, data: List[float]) -> Dict[str, float]:
        """
        计算百分位数

        Args:
            data: 数据列表

        Returns:
            Dict[str, float]: 百分位数字典
        """
        if not data:
            return {}

        # 排序数据
        sorted_data = sorted(data)

        # 计算各个百分位数
        percentiles = {}
        n = len(sorted_data)

        for p in cls.PERCENTILES:
            # 使用线性插值计算百分位数
            index = (n - 1) * p / 100
            lower = int(index)
            upper = min(lower + 1, n - 1)

            if lower == upper:
                value = sorted_data[lower]
            else:
                # 线性插值
                weight = index - lower
                value = sorted_data[lower] * (1 - weight) + sorted_data[upper] * weight

            percentiles[f'p{p}'] = round(value, 2)

        return percentiles

    @classmethod
    def _cache_stats(cls, key: str, stats: Dict[str, Any]):
        """
        缓存统计结果

        Args:
            key: 缓存key
            stats: 统计结果
        """
        try:
            # 缓存1小时
            cache.set(key, stats, timeout=3600)
        except Exception as e:
            logger.error(f"缓存统计失败: {e}", exc_info=True)

    @classmethod
    def _get_empty_stats(
        cls,
        stats_type: str,
        time_window_minutes: int
    ) -> Dict[str, Any]:
        """
        获取空统计结果

        Args:
            stats_type: 统计类型 ('api' 或 'celery')
            time_window_minutes: 时间窗口

        Returns:
            Dict: 空统计结果
        """
        return {
            'type': stats_type,
            'time_window_minutes': time_window_minutes,
            'sample_count': 0,
            'percentiles': {},
            'statistics': {
                'min': 0,
                'max': 0,
                'avg': 0,
                'median': 0
            },
            'calculated_at': datetime.now().isoformat(),
            'error': 'No data available'
        }

    @classmethod
    def get_latest_stats(cls, stats_type: str = 'api') -> Optional[Dict[str, Any]]:
        """
        获取最新的统计结果

        Args:
            stats_type: 统计类型 ('api' 或 'celery')

        Returns:
            Optional[Dict]: 最新统计结果
        """
        try:
            key = cls.API_STATS_KEY if stats_type == 'api' else cls.CELERY_STATS_KEY
            stats = cache.get(key)

            return stats

        except Exception as e:
            logger.error(f"获取最新统计失败: {e}", exc_info=True)
            return None

    @classmethod
    def calculate_all_percentiles(
        cls,
        time_window_minutes: int = None
    ) -> Dict[str, Any]:
        """
        计算所有百分位数统计

        Args:
            time_window_minutes: 时间窗口（分钟）

        Returns:
            Dict: 包含API和Celery的完整统计
        """
        logger.info("计算所有百分位数统计")

        api_stats = cls.calculate_api_percentiles(time_window_minutes)
        celery_stats = cls.calculate_celery_percentiles(time_window_minutes)

        return {
            'api': api_stats,
            'celery': celery_stats,
            'generated_at': datetime.now().isoformat()
        }
