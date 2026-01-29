"""
项目工作流服务
职责: 任务取消、恢复、编排等
"""

from typing import Any, Dict

from apps.projects.models import ProjectStage


def cancel_project_tasks(project_id: str) -> int:
    """
    取消项目的所有正在运行的Celery任务

    Args:
        project_id: 项目ID

    Returns:
        取消的任务数量
    """
    from celery.result import AsyncResult

    from config.celery import app

    # 获取所有正在处理的阶段
    processing_stages = ProjectStage.objects.filter(project_id=project_id, status="processing")

    cancelled_count = 0

    for stage in processing_stages:
        # 如果有Celery任务ID，尝试取消
        if hasattr(stage, "celery_task_id") and stage.celery_task_id:
            task_result = AsyncResult(stage.celery_task_id, app=app)

            if task_result.state in ["PENDING", "PROGRESS", "RETRY"]:
                # 取消任务
                task_result.revoke(terminate=True)
                cancelled_count += 1

        # 更新阶段状态为pending
        stage.status = "pending"
        stage.started_at = None
        stage.save()

    return cancelled_count


def resume_project_pipeline(project_id: str) -> Dict[str, Any]:
    """
    恢复暂停的项目，从当前阶段继续执行

    Args:
        project_id: 项目ID

    Returns:
        恢复信息字典
    """
    from apps.projects.models import Project
    from apps.projects.tasks import execute_full_pipeline

    project = Project.objects.get(id=project_id)

    if project.status != "paused":
        raise ValueError(f"项目状态不是paused: {project.status}")

    # 找到下一个需要执行的阶段
    stages = project.stages.all().order_by("created_at")
    next_stage = None

    stage_order = [
        "rewrite",
        "storyboard",
        "image_generation",
        "camera_movement",
        "video_generation",
    ]
    for stage_type in stage_order:
        stage = stages.filter(stage_type=stage_type).first()
        if stage and stage.status in ["pending", "failed"]:
            next_stage = stage
            break

    if not next_stage:
        raise ValueError("没有找到可恢复的阶段")

    # 更新项目状态
    project.status = "processing"
    project.save()

    # 启动完整工作流（它会自动跳过已完成的阶段）
    task = execute_full_pipeline.delay(project_id=str(project.id), user_id=project.user.id)

    return {
        "project_id": str(project.id),
        "next_stage": next_stage.stage_type,
        "task_id": task.id,
        "status": "resumed",
    }
