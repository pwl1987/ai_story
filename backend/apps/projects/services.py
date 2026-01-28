"""
项目工作流服务层
职责: 工作流状态管理和阶段编排
遵循单一职责原则(SRP)和依赖倒置原则(DIP)
"""

from typing import Any, Dict, Optional

from django.db import transaction
from django.utils import timezone

from .models import Project, ProjectStage


class ProjectWorkflowService:
    """
    项目工作流服务
    负责管理项目的工作流状态转换和阶段协调
    """

    # 阶段执行顺序
    STAGE_ORDER = [
        'rewrite',
        'storyboard',
        'image_generation',
        'camera_movement',
        'video_generation'
    ]

    @staticmethod
    def get_stage_index(stage_type: str) -> int:
        """获取阶段在工作流中的索引"""
        try:
            return ProjectWorkflowService.STAGE_ORDER.index(stage_type)
        except ValueError:
            return -1

    @staticmethod
    def get_next_stage(current_stage: str) -> Optional[str]:
        """获取下一个阶段"""
        current_index = ProjectWorkflowService.get_stage_index(current_stage)
        if current_index == -1 or current_index >= len(ProjectWorkflowService.STAGE_ORDER) - 1:
            return None
        return ProjectWorkflowService.STAGE_ORDER[current_index + 1]

    @staticmethod
    def get_previous_stage(current_stage: str) -> Optional[str]:
        """获取上一个阶段"""
        current_index = ProjectWorkflowService.get_stage_index(current_stage)
        if current_index <= 0:
            return None
        return ProjectWorkflowService.STAGE_ORDER[current_index - 1]

    @staticmethod
    @transaction.atomic
    def start_stage(project_id: str, stage_type: str, input_data: Dict[str, Any] = None) -> ProjectStage:
        """
        开始执行阶段

        Args:
            project_id: 项目ID
            stage_type: 阶段类型
            input_data: 输入数据

        Returns:
            更新后的ProjectStage对象

        Raises:
            ValueError: 阶段不存在或状态不正确
        """
        try:
            stage = ProjectStage.objects.select_for_update().get(
                project_id=project_id,
                stage_type=stage_type
            )
        except ProjectStage.DoesNotExist:
            raise ValueError(f"阶段 {stage_type} 不存在")

        # 检查阶段状态
        if stage.status == 'processing':
            raise ValueError(f"阶段 {stage_type} 正在处理中")

        # 检查前置阶段是否完成
        ProjectWorkflowService._check_prerequisites(project_id, stage_type)

        # 更新阶段状态
        stage.status = 'processing'
        stage.started_at = timezone.now()
        if input_data:
            stage.input_data = input_data
        stage.save()

        # 更新项目状态为处理中
        Project.objects.filter(id=project_id).update(status='processing')

        return stage

    @staticmethod
    @transaction.atomic
    def complete_stage(
        project_id: str,
        stage_type: str,
        output_data: Dict[str, Any],
        auto_next: bool = False
    ) -> Dict[str, Any]:
        """
        完成阶段执行

        Args:
            project_id: 项目ID
            stage_type: 阶段类型
            output_data: 输出数据
            auto_next: 是否自动开始下一阶段

        Returns:
            包含阶段信息和下一阶段信息的字典
        """
        try:
            stage = ProjectStage.objects.select_for_update().get(
                project_id=project_id,
                stage_type=stage_type
            )
        except ProjectStage.DoesNotExist:
            raise ValueError(f"阶段 {stage_type} 不存在")

        # 更新阶段状态
        stage.status = 'completed'
        stage.output_data = output_data
        stage.completed_at = timezone.now()
        stage.error_message = ''
        stage.save()

        # 检查是否所有阶段都完成
        project = Project.objects.get(id=project_id)
        all_completed = project.stages.filter(status='completed').count() == len(ProjectWorkflowService.STAGE_ORDER)

        result = {
            'stage': stage,
            'completed': True,
            'next_stage': None,
        }

        if all_completed:
            # 所有阶段完成,更新项目状态
            project.status = 'completed'
            project.completed_at = timezone.now()
            project.save()
            result['project_completed'] = True
        else:
            # 获取下一阶段
            next_stage_type = ProjectWorkflowService.get_next_stage(stage_type)
            if next_stage_type and auto_next:
                # 自动开始下一阶段
                next_stage = ProjectWorkflowService.start_stage(project_id, next_stage_type)
                result['next_stage'] = next_stage

        return result

    @staticmethod
    @transaction.atomic
    def fail_stage(
        project_id: str,
        stage_type: str,
        error_message: str,
        auto_retry: bool = True
    ) -> Dict[str, Any]:
        """
        标记阶段失败

        Args:
            project_id: 项目ID
            stage_type: 阶段类型
            error_message: 错误信息
            auto_retry: 是否自动重试

        Returns:
            包含阶段信息和重试状态的字典
        """
        try:
            stage = ProjectStage.objects.select_for_update().get(
                project_id=project_id,
                stage_type=stage_type
            )
        except ProjectStage.DoesNotExist:
            raise ValueError(f"阶段 {stage_type} 不存在")

        # 更新阶段状态
        stage.error_message = error_message
        stage.completed_at = timezone.now()

        result = {
            'stage': stage,
            'failed': True,
            'will_retry': False,
        }

        # 检查是否可以重试
        if auto_retry and stage.retry_count < stage.max_retries:
            stage.retry_count += 1
            stage.status = 'processing'
            stage.started_at = timezone.now()
            result['will_retry'] = True
            result['retry_count'] = stage.retry_count
        else:
            stage.status = 'failed'
            # 更新项目状态为失败
            Project.objects.filter(id=project_id).update(status='failed')
            result['max_retries_reached'] = True

        stage.save()
        return result

    @staticmethod
    def _check_prerequisites(project_id: str, stage_type: str):
        """
        检查前置阶段是否完成

        Args:
            project_id: 项目ID
            stage_type: 当前阶段类型

        Raises:
            ValueError: 前置阶段未完成
        """
        current_index = ProjectWorkflowService.get_stage_index(stage_type)
        if current_index <= 0:
            # 第一个阶段,无需检查
            return

        # 检查所有前置阶段
        for i in range(current_index):
            prev_stage_type = ProjectWorkflowService.STAGE_ORDER[i]
            try:
                prev_stage = ProjectStage.objects.get(
                    project_id=project_id,
                    stage_type=prev_stage_type
                )
                if prev_stage.status != 'completed':
                    raise ValueError(
                        f"前置阶段 {prev_stage.get_stage_type_display()} 未完成,状态: {prev_stage.get_status_display()}"
                    )
            except ProjectStage.DoesNotExist:
                raise ValueError(f"前置阶段 {prev_stage_type} 不存在")

    @staticmethod
    @transaction.atomic
    def rollback_to_stage(project_id: str, stage_type: str) -> Dict[str, Any]:
        """
        回滚到指定阶段

        Args:
            project_id: 项目ID
            stage_type: 目标阶段类型

        Returns:
            回滚信息字典
        """
        current_index = ProjectWorkflowService.get_stage_index(stage_type)
        if current_index == -1:
            raise ValueError(f"无效的阶段类型: {stage_type}")

        # 重置当前及后续所有阶段
        reset_count = 0
        for i in range(current_index, len(ProjectWorkflowService.STAGE_ORDER)):
            stage_to_reset = ProjectWorkflowService.STAGE_ORDER[i]
            updated = ProjectStage.objects.filter(
                project_id=project_id,
                stage_type=stage_to_reset
            ).update(
                status='pending',
                output_data={},
                error_message='',
                retry_count=0,
                started_at=None,
                completed_at=None
            )
            reset_count += updated

        # 更新项目状态
        Project.objects.filter(id=project_id).update(
            status='draft',
            completed_at=None
        )

        return {
            'rolled_back_to': stage_type,
            'reset_stages_count': reset_count,
            'project_status': 'draft',
        }

    @staticmethod
    def get_workflow_progress(project_id: str) -> Dict[str, Any]:
        """
        获取工作流进度信息

        Args:
            project_id: 项目ID

        Returns:
            进度信息字典
        """
        stages = ProjectStage.objects.filter(project_id=project_id).order_by('created_at')

        stage_info = []
        for stage in stages:
            info = {
                'stage_type': stage.stage_type,
                'stage_name': stage.get_stage_type_display(),
                'status': stage.status,
                'status_display': stage.get_status_display(),
                'retry_count': stage.retry_count,
                'started_at': stage.started_at,
                'completed_at': stage.completed_at,
                'error_message': stage.error_message,
            }
            stage_info.append(info)

        total_stages = len(ProjectWorkflowService.STAGE_ORDER)
        completed_stages = stages.filter(status='completed').count()
        failed_stages = stages.filter(status='failed').count()
        processing_stages = stages.filter(status='processing').count()

        return {
            'stages': stage_info,
            'total_stages': total_stages,
            'completed_stages': completed_stages,
            'failed_stages': failed_stages,
            'processing_stages': processing_stages,
            'progress_percentage': round((completed_stages / total_stages) * 100, 2) if total_stages > 0 else 0,
            'current_stage': ProjectWorkflowService._get_current_stage(stages),
        }

    @staticmethod
    def _get_current_stage(stages) -> Optional[Dict[str, str]]:
        """获取当前正在处理的阶段"""
        processing_stage = stages.filter(status='processing').first()
        if processing_stage:
            return {
                'stage_type': processing_stage.stage_type,
                'stage_name': processing_stage.get_stage_type_display(),
            }

        # 如果没有正在处理的,返回下一个待处理的
        for stage_type in ProjectWorkflowService.STAGE_ORDER:
            stage = stages.filter(stage_type=stage_type).first()
            if stage and stage.status == 'pending':
                return {
                    'stage_type': stage.stage_type,
                    'stage_name': stage.get_stage_type_display(),
                }

        return None

