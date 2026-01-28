"""
Core应用API视图
提供系统级别的API端点
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone

from core.services.percentile_stats import PercentileStats
import logging

logger = logging.getLogger('apps.core')


class PercentileStatsView(APIView):
    """
    百分位数统计查询视图

    GET /api/v1/core/percentile-stats/ - 获取最新的百分位数统计
    """

    def get(self, request):
        """
        获取最新的百分位数统计

        Query Parameters:
            - type: 统计类型 ('api', 'celery', 或 'all')
            - time_window: 时间窗口（分钟），可选，默认15分钟

        Returns:
            Response: 百分位数统计结果
        """
        stats_type = request.query_params.get('type', 'all')
        time_window = request.query_params.get('time_window')

        # 解析时间窗口
        time_window_minutes = None
        if time_window:
            try:
                time_window_minutes = int(time_window)
            except ValueError:
                return Response(
                    {'error': 'Invalid time_window parameter, must be an integer'},
                    status=status.HTTP_400_BAD_REQUEST
                )

        logger.info(
            f"查询百分位数统计",
            extra={'extra_fields': {
                'stats_type': stats_type,
                'time_window_minutes': time_window_minutes
            }}
        )

        try:
            if stats_type == 'api':
                # 仅返回API统计
                stats = PercentileStats.calculate_api_percentiles(time_window_minutes)
                return Response(stats, status=status.HTTP_200_OK)

            elif stats_type == 'celery':
                # 仅返回Celery统计
                stats = PercentileStats.calculate_celery_percentiles(time_window_minutes)
                return Response(stats, status=status.HTTP_200_OK)

            elif stats_type == 'all':
                # 返回所有统计
                stats = PercentileStats.calculate_all_percentiles(time_window_minutes)
                return Response(stats, status=status.HTTP_200_OK)

            else:
                return Response(
                    {'error': 'Invalid type parameter, must be "api", "celery", or "all"'},
                    status=status.HTTP_400_BAD_REQUEST
                )

        except Exception as e:
            logger.error(
                f"查询百分位数统计失败: {e}",
                exc_info=True
            )
            return Response(
                {'error': f'Internal server error: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class LatestPercentileStatsView(APIView):
    """
    最新百分位数统计视图

    GET /api/v1/core/percentile-stats/latest/ - 获取缓存的最新统计
    """

    def get(self, request):
        """
        获取缓存的最新百分位数统计

        Query Parameters:
            - type: 统计类型 ('api' 或 'celery', 默认'api')

        Returns:
            Response: 最新统计结果
        """
        stats_type = request.query_params.get('type', 'api')

        logger.info(
            f"查询最新缓存的百分位数统计",
            extra={'extra_fields': {'stats_type': stats_type}}
        )

        try:
            stats = PercentileStats.get_latest_stats(stats_type)

            if stats is None:
                return Response(
                    {'error': 'No cached stats available', 'type': stats_type},
                    status=status.HTTP_404_NOT_FOUND
                )

            return Response(stats, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(
                f"查询最新统计失败: {e}",
                exc_info=True
            )
            return Response(
                {'error': f'Internal server error: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
