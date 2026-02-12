"""
工作流命令服务 (Story 12-4 修复 - P1-1)

封装工作流控制逻辑，解决视图层直接依赖 Celery Task 的问题（依赖倒置原则 DIP）
"""

import logging
from typing import Any, Dict

from django.core.exceptions import ValidationError
from django.db import transaction

logger = logging.getLogger(__name__)

from ..models import ChapterWorkflow, WorkflowEvent


class WorkflowCommandService:
    """
    工作流命令服务 (Story 12-4 修复 - P1-1)

    封装工作流控制逻辑，解决视图层直接依赖 Celery Task 的问题。

    职责:
    - 工作流启动、暂停、恢复、状态查询
    - 业务规则验证（运行中检查、场景数量检查）
    - 事务管理
    - Celery 任务生命周期管理

    遵循 SOLID 原则:
    - 单一职责：只负责工作流命令协调
    - 开闭原则：通过 WorkflowTaskLauncher 扩展
    - 依赖倒置：依赖抽象的任务启动器，而非具体实现
    """

    def __init__(self, chapter):
        """
        初始化工作流命令服务

        Args:
            chapter: Chapter 实例
        """
        self.chapter = chapter
        self._task_launcher = None  # 延迟加载

    @property
    def task_launcher(self):
        """获取任务启动器（延迟加载避免循环导入）"""
        if self._task_launcher is None:
            from ..tasks import resume_chapter_workflow_task, start_chapter_workflow_task
            self._task_launcher = WorkflowTaskLauncher(
                start_task=start_chapter_workflow_task,
                resume_task=resume_chapter_workflow_task
            )
        return self._task_launcher

    def start(self) -> Dict[str, Any]:
        """
        启动工作流

        Returns:
            Dict: 序列化后的工作流数据

        Raises:
            ValidationError: 业务规则验证失败
        """
        # 检查运行中工作流（使用锁防止并发）
        running = ChapterWorkflow.objects.filter(
            chapter=self.chapter,
            status=ChapterWorkflow.Status.RUNNING,
            is_deleted=False
        ).select_for_update().exists()

        if running:
            raise ValidationError("该章节已有运行中的工作流")

        # 计算场景总数
        total_scenes = self.chapter.scenes.count()
        if total_scenes == 0:
            raise ValidationError("章节没有可处理的场景")

        # 使用事务保护原子性
        with transaction.atomic():
            # 创建工作流记录
            workflow = ChapterWorkflow.objects.create(
                chapter=self.chapter,
                status=ChapterWorkflow.Status.PENDING,
                total_scenes=total_scenes,
            )

            # 记录启动事件
            WorkflowEvent.objects.create(
                workflow=workflow,
                event_type=WorkflowEvent.EventType.WORKFLOW_STARTED,
                message="工作流已启动",
            )

            # 启动异步任务（通过任务启动器）
            task = self.task_launcher.start(workflow.workflow_id)

            # 更新 Celery 任务 ID
            workflow.celery_task_id = task.id
            workflow.save(update_fields=["celery_task_id"])

        from ..serializers import ChapterWorkflowSerializer
        return ChapterWorkflowSerializer(workflow).data

    def pause(self) -> Dict[str, Any]:
        """
        暂停工作流

        Returns:
            Dict: 序列化后的工作流数据

        Raises:
            ValidationError: 没有运行中的工作流
        """
        # 获取运行中工作流（使用锁防止并发）
        workflow = ChapterWorkflow.objects.filter(
            chapter=self.chapter,
            status=ChapterWorkflow.Status.RUNNING,
            is_deleted=False
        ).select_for_update().first()

        if not workflow:
            raise ValidationError("没有运行中的工作流")

        # 通过模型方法暂停
        workflow.pause()

        # 取消 Celery 任务
        if workflow.celery_task_id:
            self.task_launcher.cancel(workflow.celery_task_id)

        from ..serializers import ChapterWorkflowSerializer
        return ChapterWorkflowSerializer(workflow).data

    def resume(self) -> Dict[str, Any]:
        """
        恢复工作流

        Returns:
            Dict: 序列化后的工作流数据

        Raises:
            ValidationError: 没有暂停的工作流
        """
        # 获取暂停工作流（使用锁防止并发）
        workflow = ChapterWorkflow.objects.filter(
            chapter=self.chapter,
            status=ChapterWorkflow.Status.PAUSED,
            is_deleted=False
        ).select_for_update().first()

        if not workflow:
            raise ValidationError("没有暂停的工作流")

        # 通过模型方法恢复
        workflow.resume()

        # 启动新的异步任务（通过任务启动器，不转换 UUID）
        task = self.task_launcher.resume(workflow.workflow_id)

        workflow.celery_task_id = task.id
        workflow.save(update_fields=["celery_task_id"])

        from ..serializers import ChapterWorkflowSerializer
        return ChapterWorkflowSerializer(workflow).data

    def get_status(self) -> Dict[str, Any]:
        """
        获取工作流状态

        Returns:
            Dict: 序列化后的工作流数据

        Raises:
            ValidationError: 没有找到工作流
        """
        # 使用模型方法获取最新工作流
        workflow = ChapterWorkflow.get_latest_for_chapter(self.chapter.id)

        if not workflow:
            raise ValidationError("没有找到工作流")

        from ..serializers import ChapterWorkflowSerializer
        return ChapterWorkflowSerializer(workflow).data


class WorkflowTaskLauncher:
    """
    工作流任务启动器封装 (Story 12-4 修复 - P1-1)

    封装 Celery 任务启动逻辑，实现依赖倒置原则。
    视图层依赖此抽象接口，而非直接导入 Celery Task。
    """

    def __init__(self, start_task, resume_task):
        """
        初始化任务启动器

        Args:
            start_task: Celery 启动任务函数
            resume_task: Celery 恢复任务函数
        """
        self.start_task = start_task
        self.resume_task = resume_task

    def start(self, workflow_id):
        """
        启动工作流任务

        Args:
            workflow_id: UUID 工作流 ID（不转换为字符串）

        Returns:
            AsyncResult: Celery 任务结果
        """
        return self.start_task.delay(workflow_id)

    def resume(self, workflow_id):
        """
        恢复工作流任务

        Args:
            workflow_id: UUID 工作流 ID（不转换为字符串）

        Returns:
            AsyncResult: Celery 任务结果
        """
        return self.resume_task.delay(workflow_id)

    def cancel(self, task_id):
        """
        取消 Celery 任务

        Args:
            task_id: UUID 任务 ID
        """
        try:
            from celery import current_app
            current_app.control.revoke(
                str(task_id),  # Celery revoke 需要字符串
                terminate=True,
                signal="SIGTERM",
            )
            logger.info(f"已取消 Celery 任务: {task_id}")
        except Exception as e:
            logger.error(f"取消 Celery 任务失败: {e}")
