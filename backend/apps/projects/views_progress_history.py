"""
项目进度历史API视图
Epic 3: 实时通信稳定性 - 历史进度记录功能
职责: 提供进度历史查询API
"""

import logging
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from apps.projects.models import Project
from apps.projects.services import ProgressHistoryQuery

logger = logging.getLogger(__name__)


class ProjectProgressHistoryViewSet(viewsets.ViewSet):
    """
    项目进度历史API

    提供进度历史查询功能

    端点:
    - GET /api/v1/projects/{project_id}/progress-history/ - 查询项目历史
    - GET /api/v1/projects/{project_id}/progress-history/latest/ - 获取最新进度
    - GET /api/v1/projects/{project_id}/progress-history/stats/ - 获取统计信息
    - DELETE /api/v1/projects/{project_id}/progress-history/cleanup/ - 清理旧记录
    """

    def list(self, request, project_id=None):
        """
        查询项目进度历史

        URL: GET /api/v1/projects/{project_id}/progress-history/

        Query Parameters:
        - stage: 过滤阶段名称 (可选)
        - message_type: 过滤消息类型 (可选)
        - limit: 返回记录数限制 (默认100)
        - offset: 偏移量 (默认0,用于分页)

        Returns:
        {
            "project_id": "uuid",
            "history": [
                {
                    "id": "uuid",
                    "stage": "rewrite",
                    "message_type": "stage_update",
                    "progress": 50,
                    "status": "processing",
                    "message": "正在生成...",
                    "timestamp": "2026-01-28T10:00:00Z"
                },
                ...
            ],
            "total": 100
        }
        """
        # 验证项目存在
        project = get_object_or_404(Project, id=project_id)

        # 获取查询参数
        stage = request.query_params.get('stage')
        message_type = request.query_params.get('message_type')
        limit = int(request.query_params.get('limit', 100))
        offset = int(request.query_params.get('offset', 0))

        # 限制最大返回数量
        limit = min(limit, 1000)

        try:
            # 查询历史
            history = ProgressHistoryQuery.get_project_history(
                project_id=project_id,
                stage=stage,
                message_type=message_type,
                limit=limit,
                offset=offset
            )

            # 序列化
            history_data = [
                {
                    'id': str(h.id),
                    'stage': h.stage,
                    'message_type': h.message_type,
                    'progress': h.progress,
                    'status': h.status,
                    'message': h.message,
                    'metadata': h.metadata,
                    'timestamp': h.timestamp.isoformat()
                }
                for h in history
            ]

            return Response({
                'project_id': str(project.id),
                'project_name': project.name,
                'history': history_data,
                'total': len(history_data),
                'filters': {
                    'stage': stage,
                    'message_type': message_type,
                    'limit': limit,
                    'offset': offset
                }
            })

        except Exception as e:
            logger.error(f"查询历史失败: {str(e)}")
            return Response(
                {'error': f'查询失败: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'], url_path='latest')
    def latest(self, request, project_id=None):
        """
        获取最新进度信息

        URL: GET /api/v1/projects/{project_id}/progress-history/latest/

        Query Parameters:
        - stage: 阶段名称 (可选,不指定则返回所有阶段)

        Returns:
        {
            "project_id": "uuid",
            "latest_progress": {
                "rewrite": {
                    "progress": 75,
                    "status": "processing",
                    "message": "正在生成...",
                    "timestamp": "2026-01-28T10:00:00Z"
                },
                "storyboard": {
                    "progress": 0,
                    "status": "pending",
                    "message": "",
                    "timestamp": "2026-01-28T09:00:00Z"
                }
            }
        }
        """
        # 验证项目存在
        project = get_object_or_404(Project, id=project_id)

        # 获取查询参数
        stage = request.query_params.get('stage')

        try:
            # 查询最新进度
            latest = ProgressHistoryQuery.get_latest_progress(
                project_id=project_id,
                stage=stage
            )

            if stage:
                # 单个阶段的最新进度
                return Response({
                    'project_id': str(project.id),
                    'project_name': project.name,
                    'stage': stage,
                    'latest_progress': latest
                })
            else:
                # 所有阶段的最新进度
                return Response({
                    'project_id': str(project.id),
                    'project_name': project.name,
                    'latest_progress': latest
                })

        except Exception as e:
            logger.error(f"查询最新进度失败: {str(e)}")
            return Response(
                {'error': f'查询失败: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'], url_path='stats')
    def stats(self, request, project_id=None):
        """
        获取历史统计信息

        URL: GET /api/v1/projects/{project_id}/progress-history/stats/

        Query Parameters:
        - stage: 阶段名称 (可选)

        Returns:
        {
            "project_id": "uuid",
            "total_records": 1000,
            "by_stage": {
                "rewrite": 500,
                "storyboard": 300,
                ...
            },
            "by_type": {
                "token": 800,
                "stage_update": 150,
                ...
            },
            "earliest_timestamp": "2026-01-27T10:00:00Z",
            "latest_timestamp": "2026-01-28T10:00:00Z"
        }
        """
        # 验证项目存在
        project = get_object_or_404(Project, id=project_id)

        # 获取查询参数
        stage = request.query_params.get('stage')

        try:
            # 查询统计信息
            stats = ProgressHistoryQuery.get_history_stats(
                project_id=project_id,
                stage=stage
            )

            return Response({
                'project_id': str(project.id),
                'project_name': project.name,
                **stats
            })

        except Exception as e:
            logger.error(f"查询统计信息失败: {str(e)}")
            return Response(
                {'error': f'查询失败: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['delete'], url_path='cleanup')
    def cleanup(self, request, project_id=None):
        """
        清理旧的历史记录

        URL: DELETE /api/v1/projects/{project_id}/progress-history/cleanup/

        Query Parameters:
        - stage: 阶段名称 (可选)
        - keep_recent: 保留最近的N条记录 (默认1000)
        - days_old: 清理N天前的记录 (默认30)

        Returns:
        {
            "project_id": "uuid",
            "deleted_count": 500,
            "message": "已清理500条旧记录"
        }
        """
        # 验证项目存在
        project = get_object_or_404(Project, id=project_id)

        # 获取查询参数
        stage = request.query_params.get('stage')
        keep_recent = int(request.query_params.get('keep_recent', 1000))
        days_old = int(request.query_params.get('days_old', 30))

        # 限制参数范围
        keep_recent = min(max(keep_recent, 100), 10000)
        days_old = min(max(days_old, 1), 365)

        try:
            # 清理旧记录
            deleted_count = ProgressHistoryQuery.cleanup_old_history(
                project_id=project_id,
                stage=stage,
                keep_recent=keep_recent,
                days_old=days_old
            )

            return Response({
                'project_id': str(project.id),
                'project_name': project.name,
                'deleted_count': deleted_count,
                'message': f'已清理{deleted_count}条旧记录',
                'filters': {
                    'stage': stage,
                    'keep_recent': keep_recent,
                    'days_old': days_old
                }
            })

        except Exception as e:
            logger.error(f"清理旧记录失败: {str(e)}")
            return Response(
                {'error': f'清理失败: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
