"""
项目进度历史记录服务
Epic 3: 实时通信稳定性 - 历史进度记录功能
职责: 记录和查询项目进度历史
遵循单一职责原则(SRP)
"""

import logging
from datetime import timedelta
from typing import Dict, List, Optional

from django.db import models
from django.utils import timezone

from apps.projects.models import Project, ProjectProgressHistory

logger = logging.getLogger(__name__)


class ProgressHistoryRecorder:
    """
    进度历史记录器

    职责:
    - 记录项目进度更新
    - 提供历史进度查询接口

    使用示例:
    >>> ProgressHistoryRecorder.record_progress(
    ...     project_id='uuid',
    ...     stage='rewrite',
    ...     progress=50,
    ...     status='processing',
    ...     message='正在生成...',
    ...     message_type='stage_update'
    ... )
    """

    @staticmethod
    def record_progress(
        project_id: str,
        stage: str,
        progress: int = 0,
        status: str = "pending",
        message: str = "",
        message_type: str = "stage_update",
        metadata: Optional[Dict] = None,
    ) -> ProjectProgressHistory:
        """
        记录项目进度更新

        Args:
            project_id: 项目ID
            stage: 阶段名称 (rewrite, storyboard, etc.)
            progress: 进度百分比 (0-100)
            status: 状态 (pending, processing, completed, failed)
            message: 消息内容
            message_type: 消息类型 (stage_update, progress, done, error, token, connected)
            metadata: 额外的元数据(JSON格式)

        Returns:
            ProjectProgressHistory: 创建的历史记录对象

        Raises:
            Project.DoesNotExist: 如果项目不存在
        """
        try:
            project = Project.objects.get(id=project_id)
        except Project.DoesNotExist:
            logger.error(f"项目不存在: {project_id}")
            raise

        # 创建历史记录
        history = ProjectProgressHistory.objects.create(
            project=project,
            stage=stage,
            message_type=message_type,
            progress=progress,
            status=status,
            message=message,
            metadata=metadata or {},
        )

        logger.debug(
            f"记录进度: 项目={project.name}, 阶段={stage}, 进度={progress}%, 状态={status}"
        )

        return history

    @staticmethod
    def record_token(
        project_id: str, stage: str, content: str, full_text: str, metadata: Optional[Dict] = None
    ) -> ProjectProgressHistory:
        """
        记录token消息

        Args:
            project_id: 项目ID
            stage: 阶段名称
            content: token内容
            full_text: 完整文本
            metadata: 额外元数据

        Returns:
            ProjectProgressHistory: 创建的历史记录
        """
        return ProgressHistoryRecorder.record_progress(
            project_id=project_id,
            stage=stage,
            message_type="token",
            message=content,
            metadata={**(metadata or {}), "full_text": full_text, "token_length": len(content)},
        )

    @staticmethod
    def record_stage_update(
        project_id: str, stage: str, status: str, progress: int, message: str
    ) -> ProjectProgressHistory:
        """
        记录阶段更新

        Args:
            project_id: 项目ID
            stage: 阶段名称
            status: 状态
            progress: 进度百分比
            message: 消息

        Returns:
            ProjectProgressHistory: 创建的历史记录
        """
        return ProgressHistoryRecorder.record_progress(
            project_id=project_id,
            stage=stage,
            progress=progress,
            status=status,
            message=message,
            message_type="stage_update",
        )

    @staticmethod
    def record_done(
        project_id: str, stage: str, result: str, metadata: Optional[Dict] = None
    ) -> ProjectProgressHistory:
        """
        记录任务完成

        Args:
            project_id: 项目ID
            stage: 阶段名称
            result: 完整结果
            metadata: 额外元数据(如latency_ms, tokens_used等)

        Returns:
            ProjectProgressHistory: 创建的历史记录
        """
        return ProgressHistoryRecorder.record_progress(
            project_id=project_id,
            stage=stage,
            progress=100,
            status="completed",
            message="Task completed",
            message_type="done",
            metadata={
                **(metadata or {}),
                "result": result,
                "result_length": len(result) if result else 0,
            },
        )

    @staticmethod
    def record_error(
        project_id: str, stage: str, error: str, retry_count: int = 0
    ) -> ProjectProgressHistory:
        """
        记录错误

        Args:
            project_id: 项目ID
            stage: 阶段名称
            error: 错误信息
            retry_count: 重试次数

        Returns:
            ProjectProgressHistory: 创建的历史记录
        """
        return ProgressHistoryRecorder.record_progress(
            project_id=project_id,
            stage=stage,
            status="failed",
            message=error,
            message_type="error",
            metadata={"retry_count": retry_count},
        )


class ProgressHistoryQuery:
    """
    进度历史查询服务

    职责:
    - 查询项目进度历史
    - 提供过滤和排序功能

    使用示例:
    >>> history = ProgressHistoryQuery.get_project_history('project-uuid')
    >>> stage_history = ProgressHistoryQuery.get_stage_history('project-uuid', 'rewrite')
    """

    @staticmethod
    def get_project_history(
        project_id: str,
        stage: Optional[str] = None,
        message_type: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[ProjectProgressHistory]:
        """
        查询项目进度历史

        Args:
            project_id: 项目ID
            stage: 过滤阶段名称 (可选)
            message_type: 过滤消息类型 (可选)
            limit: 返回记录数限制
            offset: 偏移量 (用于分页)

        Returns:
            List[ProjectProgressHistory]: 历史记录列表(按时间倒序)

        Raises:
            Project.DoesNotExist: 如果项目不存在
        """
        # 验证项目存在
        try:
            Project.objects.get(id=project_id)
        except Project.DoesNotExist:
            logger.error(f"项目不存在: {project_id}")
            raise

        # 构建查询
        queryset = ProjectProgressHistory.objects.filter(project_id=project_id)

        # 应用过滤
        if stage:
            queryset = queryset.filter(stage=stage)

        if message_type:
            queryset = queryset.filter(message_type=message_type)

        # 排序和分页
        history = queryset.order_by("-timestamp")[offset : offset + limit]

        logger.debug(f"查询项目历史: project_id={project_id}, stage={stage}, count={len(history)}")

        return list(history)

    @staticmethod
    def get_stage_history(
        project_id: str, stage: str, limit: int = 100
    ) -> List[ProjectProgressHistory]:
        """
        查询指定阶段的历史

        Args:
            project_id: 项目ID
            stage: 阶段名称
            limit: 返回记录数限制

        Returns:
            List[ProjectProgressHistory]: 历史记录列表
        """
        return ProgressHistoryQuery.get_project_history(
            project_id=project_id, stage=stage, limit=limit
        )

    @staticmethod
    def get_latest_progress(project_id: str, stage: Optional[str] = None) -> Optional[Dict]:
        """
        获取最新的进度信息

        Args:
            project_id: 项目ID
            stage: 阶段名称 (可选,不指定则返回所有阶段的最新进度)

        Returns:
            Optional[Dict]: 最新进度信息
            {
                'stage': 'rewrite',
                'progress': 75,
                'status': 'processing',
                'message': '正在生成...',
                'timestamp': '2026-01-28T10:00:00Z'
            }
        """
        queryset = ProjectProgressHistory.objects.filter(project_id=project_id)

        if stage:
            queryset = queryset.filter(stage=stage)
            # 获取该阶段的最新记录
            latest = queryset.order_by("-timestamp").first()
            if latest:
                return {
                    "stage": latest.stage,
                    "progress": latest.progress,
                    "status": latest.status,
                    "message": latest.message,
                    "timestamp": latest.timestamp.isoformat(),
                }
            return None
        else:
            # 返回所有阶段的最新进度
            stages = (
                ProjectProgressHistory.objects.filter(project_id=project_id)
                .values_list("stage", flat=True)
                .distinct()
            )

            progress_by_stage = {}
            for stage_name in stages:
                latest = queryset.filter(stage=stage_name).order_by("-timestamp").first()
                if latest:
                    progress_by_stage[stage_name] = {
                        "progress": latest.progress,
                        "status": latest.status,
                        "message": latest.message,
                        "timestamp": latest.timestamp.isoformat(),
                    }

            return progress_by_stage if progress_by_stage else None

    @staticmethod
    def cleanup_old_history(
        project_id: str, stage: Optional[str] = None, keep_recent: int = 1000, days_old: int = 30
    ) -> int:
        """
        清理旧的历史记录

        Args:
            project_id: 项目ID
            stage: 阶段名称 (可选,不指定则清理所有阶段)
            keep_recent: 保留最近的N条记录
            days_old: 清理N天前的记录

        Returns:
            int: 删除的记录数
        """
        queryset = ProjectProgressHistory.objects.filter(project_id=project_id)

        if stage:
            queryset = queryset.filter(stage=stage)

        # 清理N天前的记录
        cutoff_date = timezone.now() - timedelta(days=days_old)
        old_records = queryset.filter(timestamp__lt=cutoff_date)

        # 统计
        count = old_records.count()

        # 删除
        old_records.delete()

        logger.info(f"清理旧历史记录: project_id={project_id}, stage={stage}, 删除={count}条")

        return count

    @staticmethod
    def get_history_stats(project_id: str, stage: Optional[str] = None) -> Dict:
        """
        获取历史统计信息

        Args:
            project_id: 项目ID
            stage: 阶段名称 (可选)

        Returns:
            Dict: 统计信息
            {
                'total_records': 1000,
                'by_stage': {
                    'rewrite': 500,
                    'storyboard': 300,
                    ...
                },
                'by_type': {
                    'token': 800,
                    'stage_update': 150,
                    ...
                },
                'earliest_timestamp': '...',
                'latest_timestamp': '...'
            }
        """
        queryset = ProjectProgressHistory.objects.filter(project_id=project_id)

        if stage:
            queryset = queryset.filter(stage=stage)

        # 总记录数
        total = queryset.count()

        # 按阶段统计
        by_stage = {}
        for stage_name, count in queryset.values_list("stage").annotate(count=models.Count("id")):
            by_stage[stage_name] = count

        # 按消息类型统计
        by_type = {}
        for msg_type, count in queryset.values_list("message_type").annotate(
            count=models.Count("id")
        ):
            by_type[msg_type] = count

        # 时间范围
        earliest = queryset.order_by("timestamp").first()
        latest = queryset.order_by("-timestamp").first()

        return {
            "total_records": total,
            "by_stage": by_stage,
            "by_type": by_type,
            "earliest_timestamp": earliest.timestamp.isoformat() if earliest else None,
            "latest_timestamp": latest.timestamp.isoformat() if latest else None,
        }
