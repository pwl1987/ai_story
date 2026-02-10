"""
角色资产批量生成API视图

Story 11.1.4: 角色资产批量生成
- 批量立绘生成API
- 批量音色生成API
- 生成进度查询API
- 质量评分API
"""

import logging

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import CharacterProfile, GenerationHistory, GenerationProgress
from .serializers import (
    GenerationHistorySerializer,
    GenerationProgressSerializer,
)
from .tasks import batch_generate_assets, recommend_poses

logger = logging.getLogger(__name__)


class BatchGenerationViewSet(viewsets.ViewSet):
    """
    批量生成API ViewSet

    端点:
    - POST /api/v1/artworks/batch-generation/ - 启动批量生成
    - GET /api/v1/artworks/batch-generation/progress/?task_id=xxx - 查询进度
    - POST /api/v1/artworks/batch-generation/recommend_poses/ - AI推荐造型
    - POST /api/v1/artworks/batch-generation/rate/ - 评分生成结果
    - GET /api/v1/artworks/batch-generation/history/ - 获取生成历史
    """

    permission_classes = [IsAuthenticated]

    def create(self, request) -> Response:
        """
        启动批量生成任务

        请求体:
        {
            "character_ids": [1, 2, 3],
            "portrait_config": {
                "pose_type": "casual",
                "prompt_params": {
                    "prompt": "anime style character portrait",
                    "negative_prompt": "low quality",
                    "width": 512,
                    "height": 768,
                    "steps": 20
                }
            },
            "voice_config": {
                "text": "你好，我是测试语音。",
                "voice_params": {
                    "voice_name": "zh-CN-XiaoxiaoNeural",
                    "rate": "+0%",
                    "volume": "+0%",
                    "pitch": "+0Hz"
                }
            }
        }
        """
        character_ids = request.data.get("character_ids", [])
        portrait_config = request.data.get("portrait_config", {})
        voice_config = request.data.get("voice_config", {})

        # 验证
        if not character_ids:
            raise ValidationError({"character_ids": "请选择要生成的角色"})

        # 验证角色存在
        characters = CharacterProfile.objects.filter(id__in=character_ids)
        if characters.count() != len(character_ids):
            raise ValidationError({"character_ids": "部分角色不存在"})

        # 构建生成配置
        generation_config = {
            "portrait": portrait_config,
            "voice": voice_config,
        }

        # 启动Celery任务
        result = batch_generate_assets.delay(
            character_ids=character_ids,
            generation_config=generation_config,
            user_id=request.user.id,
        )

        logger.info(f"启动批量生成任务: task_id={result.id}, character_ids={character_ids}")

        return Response(
            {
                "task_id": result.id,
                "progress_id": result.result["progress_id"],
                "total_items": result.result["total_items"],
                "status": "processing",
                "message": result.result["message"],
            },
            status=status.HTTP_202_ACCEPTED,
        )

    @action(detail=False, methods=["get"], url_path="progress")
    def progress(self, request) -> Response:
        """
        查询生成进度

        查询参数:
        - task_id: Celery任务ID (可选)
        - progress_id: 进度记录ID (可选)

        返回:
        {
            "status": "processing",
            "total_items": 6,
            "completed_items": 3,
            "failed_items": 0,
            "progress_percentage": 50.0,
            "error_message": ""
        }
        """
        task_id = request.query_params.get("task_id")
        progress_id = request.query_params.get("progress_id")

        if not task_id and not progress_id:
            raise ValidationError({"detail": "请提供task_id或progress_id"})

        # 查询进度记录
        if progress_id:
            try:
                progress = GenerationProgress.objects.get(id=progress_id)
            except GenerationProgress.DoesNotExist:
                raise ValidationError({"progress_id": "进度记录不存在"})
        else:
            # 通过task_id查询
            progress = GenerationProgress.objects.filter(celery_task_id=task_id).first()
            if not progress:
                raise ValidationError({"task_id": "任务不存在"})

        # 检查权限
        if progress.user != request.user:
            return Response({"detail": "无权访问此进度"}, status=status.HTTP_403_FORBIDDEN)

        # 序列化结果
        serializer = GenerationProgressSerializer(progress)

        return Response(serializer.data)

    @action(detail=False, methods=["post"], url_path="recommend-poses")
    def recommend_poses(self, request) -> Response:
        """
        AI推荐造型 (基于场景描述)

        请求体:
        {
            "scene_description": "纳米中心实验室，科学家们正在讨论实验结果"
        }

        返回:
        [
            {
                "pose_type": "formal",
                "confidence": 0.9,
                "reason": "实验室场景适合正式装"
            }
        ]
        """
        scene_description = request.data.get("scene_description", "")

        if not scene_description:
            raise ValidationError({"scene_description": "请提供场景描述"})

        # 调用推荐任务
        task = recommend_poses.delay(scene_description)

        # 等待结果 (同步方式，实际应该用异步)
        result = task.get(timeout=30)

        return Response(
            {
                "scene_description": scene_description,
                "recommendations": result,
            }
        )

    @action(detail=False, methods=["post"], url_path="rate")
    def rate(self, request) -> Response:
        """
        评分生成结果

        请求体:
        {
            "history_id": 1,
            "rating": 5,
            "feedback": "质量很好"
        }
        """
        history_id = request.data.get("history_id")
        rating = request.data.get("rating")
        feedback = request.data.get("feedback", "")

        if not history_id or rating is None:
            raise ValidationError({"detail": "请提供history_id和rating"})

        if not 1 <= rating <= 5:
            raise ValidationError({"rating": "评分必须在1-5之间"})

        try:
            history = GenerationHistory.objects.get(id=history_id)

            # 检查权限
            if history.character.artwork.created_by != request.user:
                return Response({"detail": "无权评分此记录"}, status=status.HTTP_403_FORBIDDEN)

            # 评分
            history.rate(rating, feedback)

            logger.info(f"用户评分: history_id={history_id}, rating={rating}")

            return Response(
                {
                    "status": "rated",
                    "history_id": history_id,
                    "rating": rating,
                }
            )

        except GenerationHistory.DoesNotExist:
            raise ValidationError({"history_id": "历史记录不存在"})

    @action(detail=False, methods=["get"], url_path="history")
    def history(self, request) -> Response:
        """
        获取生成历史

        查询参数:
        - character_id: 角色ID (可选)
        - generation_type: 生成类型 (可选)

        返回:
        [
            {
                "id": 1,
                "character": 1,
                "generation_type": "portrait",
                "result_url": "...",
                "quality_rating": 5,
                "created_at": "2026-02-09T16:00:00Z"
            }
        ]
        """
        character_id = request.query_params.get("character_id")
        generation_type = request.query_params.get("generation_type")

        # 构建查询
        queryset = GenerationHistory.objects.all()

        if character_id:
            queryset = queryset.filter(character_id=character_id)

        if generation_type:
            queryset = queryset.filter(generation_type=generation_type)

        # 排序
        queryset = queryset.order_by("-created_at")

        # 分页
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = GenerationHistorySerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = GenerationHistorySerializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["post"], url_path="regenerate")
    def regenerate(self, request) -> Response:
        """
        重新生成 (基于历史记录)

        请求体:
        {
            "history_id": 1
        }
        """
        history_id = request.data.get("history_id")

        if not history_id:
            raise ValidationError({"history_id": "请提供history_id"})

        try:
            history = GenerationHistory.objects.get(id=history_id)

            # 检查权限
            if history.character.artwork.created_by != request.user:
                return Response({"detail": "无权重新生成此记录"}, status=status.HTTP_403_FORBIDDEN)

            # 增加重新生成次数
            history.increment_regeneration_count()

            # 根据类型重新生成
            if history.generation_type == "portrait":
                # 重新生成立绘
                from .tasks import generate_portrait

                task = generate_portrait.delay(
                    character_id=history.character.id,
                    pose_type=history.prompt_params.get("pose_type", "casual"),
                    prompt_params=history.prompt_params,
                )
            elif history.generation_type == "voice":
                # 重新生成音色
                from .tasks import generate_voice_sample

                task = generate_voice_sample.delay(
                    character_id=history.character.id,
                    text="你好，这是重新生成的音色。",
                    voice_params=history.voice_params,
                )
            else:
                raise ValidationError({"generation_type": "不支持的生成类型"})

            logger.info(f"重新生成: history_id={history_id}, task_id={task.id}")

            return Response(
                {
                    "task_id": task.id,
                    "message": "重新生成任务已启动",
                }
            )

        except GenerationHistory.DoesNotExist:
            raise ValidationError({"history_id": "历史记录不存在"})

    @action(detail=False, methods=["post"], url_path="cancel")
    def cancel(self, request) -> Response:
        """
        取消批量生成任务

        请求体:
        {
            "task_id": "xxx-xxx-xxx"
        }
        """
        task_id = request.data.get("task_id")

        if not task_id:
            raise ValidationError({"task_id": "请提供task_id"})

        try:
            from celery.result import AsyncResult

            # 获取任务
            task = AsyncResult(task_id)

            if task.state not in ["PENDING", "PROGRESS"]:
                return Response(
                    {
                        "message": f"任务状态为 {task.state}，无法取消",
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # 取消任务
            task.revoke(terminate=True)

            # 更新进度记录
            progress = GenerationProgress.objects.filter(celery_task_id=task_id).first()
            if progress:
                progress.status = "cancelled"
                progress.save()

            logger.info(f"取消批量生成任务: task_id={task_id}")

            return Response(
                {
                    "message": "任务已取消",
                    "task_id": task_id,
                }
            )

        except Exception as e:
            logger.error(f"取消任务失败: {e}")
            return Response(
                {
                    "message": f"取消任务失败: {e!s}",
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
