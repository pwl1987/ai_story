"""
批量操作服务 (Story 11.5.1)

职责:
- 批量操作业务逻辑
- 错误收集和报告
- 进度追踪集成
"""

import logging
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

from django.db import models, transaction
from django.utils import timezone

from .models import GenerationProgress, Shot

logger = logging.getLogger(__name__)


@dataclass
class BatchOperationResult:
    """
    批量操作结果

    职责:
    - 记录操作成功/失败统计
    - 存储详细的错误信息
    - 提供结果报告
    """

    operation_type: str  # "delete", "regenerate", "move", "update_pose"
    total_count: int = 0
    success_count: int = 0
    failed_count: int = 0
    errors: List[Dict[str, Any]] = field(default_factory=list)
    success_ids: List[int] = field(default_factory=list)
    started_at: timezone.datetime = field(default_factory=timezone.now)
    completed_at: Optional[timezone.datetime] = None
    progress_id: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        duration = None
        if self.completed_at:
            duration = (self.completed_at - self.started_at).total_seconds()

        return {
            "operation_type": self.operation_type,
            "total_count": self.total_count,
            "success_count": self.success_count,
            "failed_count": self.failed_count,
            "success_rate": self._calculate_success_rate(),
            "errors": self.errors,
            "success_ids": self.success_ids,
            "duration_seconds": duration,
            "progress_id": self.progress_id,
        }

    def _calculate_success_rate(self) -> float:
        """计算成功率"""
        if self.total_count == 0:
            return 0.0
        return round((self.success_count / self.total_count) * 100, 2)

    def add_success(self, item_id: int):
        """添加成功项"""
        self.success_count += 1
        self.success_ids.append(item_id)
        self.total_count += 1

    def add_error(self, item_id: Optional[int], error_message: str, error_code: str = ""):
        """添加错误项"""
        self.failed_count += 1
        if item_id:
            self.total_count += 1
        self.errors.append(
            {
                "item_id": item_id,
                "error_message": error_message,
                "error_code": error_code,
                "timestamp": timezone.now().isoformat(),
            }
        )

    def mark_completed(self):
        """标记完成"""
        self.completed_at = timezone.now()


class BatchOperationService:
    """
    批量操作服务 (Story 11.5.1)

    职责:
    - 执行批量操作
    - 收集详细错误信息
    - 集成进度追踪
    - 提供统一的结果报告
    """

    def __init__(self, operation_type: str, user):
        """
        初始化批量操作服务

        Args:
            operation_type: 操作类型
            user: 执行操作的用户
        """
        self.operation_type = operation_type
        self.user = user
        self.result = BatchOperationResult(operation_type=operation_type)
        self.progress: Optional[GenerationProgress] = None

    def _create_progress(self, total_items: int) -> GenerationProgress:
        """
        创建进度追踪记录

        Args:
            total_items: 总项目数

        Returns:
            GenerationProgress: 进度记录
        """
        progress = GenerationProgress.objects.create(
            user=self.user,
            generation_type="batch",
            status="processing",
            total_items=total_items,
            completed_items=0,
            failed_items=0,
        )
        self.progress = progress
        self.result.progress_id = progress.id
        return progress

    def _update_progress(self, completed: int = 0, failed: int = 0):
        """更新进度"""
        if self.progress:
            self.progress.update_progress(completed=completed, failed=failed)

    def _mark_progress_completed(self):
        """标记进度完成"""
        if self.progress:
            status = "completed" if self.result.failed_count == 0 else "failed"
            self.progress.status = status
            self.progress.completed_at = timezone.now()
            self.progress.save()

    def execute_batch_delete(
        self, model_class, item_ids: List[int], id_field: str = "id"
    ) -> BatchOperationResult:
        """
        执行批量删除

        Args:
            model_class: 模型类
            item_ids: 要删除的项目ID列表
            id_field: ID字段名

        Returns:
            BatchOperationResult: 操作结果
        """
        self._create_progress(len(item_ids))

        with transaction.atomic():
            for item_id in item_ids:
                try:
                    # 查找对象
                    filter_kwargs = {id_field: item_id}
                    obj = model_class.objects.get(**filter_kwargs)

                    # 删除对象
                    obj.delete()

                    self.result.add_success(item_id)
                    self._update_progress(completed=1)

                except model_class.DoesNotExist:
                    self.result.add_error(
                        item_id,
                        f"{model_class.__name__} 不存在",
                        error_code="NOT_FOUND",
                    )
                    self._update_progress(failed=1)

                except Exception as e:
                    logger.exception(f"批量删除失败: {item_id}")
                    self.result.add_error(
                        item_id,
                        str(e),
                        error_code="DELETE_ERROR",
                    )
                    self._update_progress(failed=1)

        self.result.mark_completed()
        self._mark_progress_completed()

        return self.result

    def execute_batch_operation(
        self,
        items: List,
        operation_func: Callable,
        error_code: str = "OPERATION_ERROR",
    ) -> BatchOperationResult:
        """
        执行通用批量操作

        Args:
            items: 要操作的项目列表
            operation_func: 操作函数，接收单个项目作为参数
            error_code: 错误代码

        Returns:
            BatchOperationResult: 操作结果
        """
        self._create_progress(len(items))

        for item in items:
            try:
                operation_func(item)
                self.result.add_success(item.id)
                self._update_progress(completed=1)

            except Exception as e:
                logger.exception(f"批量操作失败: {item.id}")
                self.result.add_error(
                    item.id,
                    str(e),
                    error_code=error_code,
                )
                self._update_progress(failed=1)

        self.result.mark_completed()
        self._mark_progress_completed()

        return self.result


class ShotBatchOperationService(BatchOperationService):
    """
    镜头批量操作服务 (Story 11.5.1)

    专门针对镜头的批量操作，包含:
    - 批量重新生成
    - 批量移动
    - 批量更新造型
    """

    def batch_regenerate(
        self,
        shot_ids: List[int],
        regenerate_image: bool = True,
        regenerate_audio: bool = True,
        override_params: Optional[Dict[str, Any]] = None,
    ) -> BatchOperationResult:
        """
        批量重新生成镜头 (Story 11.5.1)

        Args:
            shot_ids: 镜头ID列表
            regenerate_image: 是否重新生成图像
            regenerate_audio: 是否重新生成音频
            override_params: 覆盖参数

        Returns:
            BatchOperationResult: 操作结果
        """
        from .tasks import regenerate_shot_content

        self._create_progress(len(shot_ids))

        shots = Shot.objects.filter(id__in=shot_ids)

        for shot in shots:
            try:
                # 确定 regenerate_type
                if regenerate_image and regenerate_audio:
                    regenerate_type = "both"
                elif regenerate_image:
                    regenerate_type = "image"
                elif regenerate_audio:
                    regenerate_type = "audio"
                else:
                    raise ValueError("至少需要选择重新生成图像或音频")

                # 提取 custom_prompt (如果有)
                custom_prompt = (
                    override_params.get("image_prompt")
                    if override_params
                    else None
                )

                # 启动异步任务
                task = regenerate_shot_content.delay(
                    shot_id=shot.id,
                    regenerate_type=regenerate_type,
                    custom_prompt=custom_prompt,
                )

                self.result.add_success(shot.id)
                self._update_progress(completed=1)

            except Exception as e:
                logger.exception(f"批量重新生成失败: {shot.id}")
                self.result.add_error(
                    shot.id,
                    str(e),
                    error_code="REGENERATE_ERROR",
                )
                self._update_progress(failed=1)

        self.result.mark_completed()
        self._mark_progress_completed()

        return self.result

    def batch_move(
        self,
        shot_ids: List[int],
        target_scene_id: int,
        update_sort_order: bool = True,
    ) -> BatchOperationResult:
        """
        批量移动镜头到其他场景 (Story 11.5.1)

        Args:
            shot_ids: 镜头ID列表
            target_scene_id: 目标场景ID
            update_sort_order: 是否更新排序

        Returns:
            BatchOperationResult: 操作结果
        """
        from .models import ScriptScene

        self._create_progress(len(shot_ids))

        # 验证目标场景存在
        try:
            target_scene = ScriptScene.objects.get(id=target_scene_id)
        except ScriptScene.DoesNotExist:
            self.result.add_error(
                None,
                f"目标场景 {target_scene_id} 不存在",
                error_code="TARGET_SCENE_NOT_FOUND",
            )
            self.result.mark_completed()
            self._mark_progress_completed()
            return self.result

        shots = Shot.objects.filter(id__in=shot_ids).select_related("scene")

        with transaction.atomic():
            max_sort_order = 0
            if update_sort_order:
                # 获取目标场景当前最大排序值
                max_sort_order = (
                    Shot.objects.filter(scene_id=target_scene_id)
                    .order_by("-sort_order")
                    .values_list("sort_order", flat=True)
                    .first() or 0
                )

            for index, shot in enumerate(shots):
                try:
                    # 记录原场景
                    original_scene_id = shot.scene_id

                    # 更新场景
                    shot.scene = target_scene

                    # 更新排序
                    if update_sort_order:
                        shot.sort_order = max_sort_order + index + 1

                    # 重新计算镜头序号
                    shot.shot_number = target_scene.shot_count + index + 1

                    shot.save(update_fields=["scene", "shot_number", "sort_order"])

                    # 更新旧场景的镜头计数
                    if original_scene_id != target_scene_id:
                        ScriptScene.objects.filter(id=original_scene_id).update(
                            shot_count=models.F("shot_count") - 1
                        )

                    self.result.add_success(shot.id)
                    self._update_progress(completed=1)

                except Exception as e:
                    logger.exception(f"批量移动失败: {shot.id}")
                    self.result.add_error(
                        shot.id,
                        str(e),
                        error_code="MOVE_ERROR",
                    )
                    self._update_progress(failed=1)

            # 更新目标场景的镜头计数
            if self.result.success_count > 0:
                target_scene.shot_count += self.result.success_count
                target_scene.save(update_fields=["shot_count"])

        self.result.mark_completed()
        self._mark_progress_completed()

        return self.result

    def batch_update_character(
        self,
        shot_ids: List[int],
        character_pose_id: Optional[int],
    ) -> BatchOperationResult:
        """
        批量更新镜头的角色造型 (Story 11.5.1)

        Args:
            shot_ids: 镜头ID列表
            character_pose_id: 角色造型ID (None表示清除)

        Returns:
            BatchOperationResult: 操作结果
        """
        from .models import CharacterPose

        self._create_progress(len(shot_ids))

        # 验证角色造型存在 (如果指定)
        if character_pose_id:
            try:
                CharacterPose.objects.get(id=character_pose_id)
            except CharacterPose.DoesNotExist:
                self.result.add_error(
                    None,
                    f"角色造型 {character_pose_id} 不存在",
                    error_code="POSE_NOT_FOUND",
                )
                self.result.mark_completed()
                self._mark_progress_completed()
                return self.result

        shots = Shot.objects.filter(id__in=shot_ids)

        with transaction.atomic():
            for shot in shots:
                try:
                    shot.character_pose_id = character_pose_id
                    shot.save(update_fields=["character_pose"])

                    self.result.add_success(shot.id)
                    self._update_progress(completed=1)

                except Exception as e:
                    logger.exception(f"批量更新角色失败: {shot.id}")
                    self.result.add_error(
                        shot.id,
                        str(e),
                        error_code="UPDATE_CHARACTER_ERROR",
                    )
                    self._update_progress(failed=1)

        self.result.mark_completed()
        self._mark_progress_completed()

        return self.result
