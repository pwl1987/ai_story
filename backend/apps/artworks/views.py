"""
角色资产管理 API ViewSets

遵循DRF最佳实践:
- ViewSet分离
- 权限控制
- 自定义Action
- 批量操作
"""

from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import (
    Artwork,
    CharacterPose,
    CharacterProfile,
    CharacterVoiceConfig,
    GenerationProgress,
    ItemProfile,
    ScriptScene,
    Shot,
    ShotVersion,
)
from .serializers import (
    ArtworkDetailSerializer,
    ArtworkSerializer,
    CharacterPoseSerializer,
    CharacterProfileDetailSerializer,
    CharacterProfileSerializer,
    CharacterVoiceConfigSerializer,
    ItemProfileSerializer,
    RegenerateShotSerializer,
    ScriptSceneDetailSerializer,
    ScriptSceneSerializer,
    ShotDetailSerializer,
    ShotSerializer,
    ShotVersionDetailSerializer,
    ShotVersionSerializer,
)


class ArtworkViewSet(viewsets.ReadOnlyModelViewSet):
    """
    作品API ViewSet

    list: 获取作品列表
    retrieve: 获取作品详情（包含角色和物品）
    """

    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["artwork_type", "is_parsed"]
    search_fields = ["title", "author", "story_overview"]
    ordering_fields = ["created_at", "title", "total_chapters"]
    ordering = ["-created_at"]

    def get_queryset(self):
        """获取查询集"""
        return Artwork.objects.all()

    def get_serializer_class(self):
        """根据action选择序列化器"""
        if self.action == "retrieve":
            return ArtworkDetailSerializer
        return ArtworkSerializer

    @action(detail=True, methods=["get"])
    def characters(self, request, pk=None):
        """获取作品的所有角色"""
        artwork = self.get_object()
        characters = artwork.characters.all()
        serializer = CharacterProfileSerializer(characters, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["get"])
    def items(self, request, pk=None):
        """获取作品的所有物品"""
        artwork = self.get_object()
        items = artwork.items.all()
        serializer = ItemProfileSerializer(items, many=True)
        return Response(serializer.data)


class CharacterProfileViewSet(viewsets.ModelViewSet):
    """
    角色档案API ViewSet

    list: 获取角色列表
    retrieve: 获取角色详情
    create: 创建新角色
    update: 更新角色信息
    partial_update: 部分更新角色
    destroy: 删除角色
    """

    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["artwork", "importance_rank"]
    search_fields = ["name", "display_name", "description", "personality"]
    ordering_fields = ["importance_rank", "appearance_count", "created_at"]
    ordering = ["artwork", "importance_rank", "-appearance_count"]

    def get_queryset(self):
        """获取查询集"""
        queryset = CharacterProfile.objects.select_related("artwork").prefetch_related(
            "poses", "voice_config"
        )
        artwork_id = self.request.query_params.get("artwork")
        if artwork_id:
            queryset = queryset.filter(artwork_id=artwork_id)
        return queryset

    def get_serializer_class(self):
        """根据action选择序列化器"""
        if self.action in ["retrieve", "update", "partial_update"]:
            return CharacterProfileDetailSerializer
        return CharacterProfileSerializer

    @action(detail=True, methods=["get", "post"])
    def poses(self, request, pk=None):
        """获取或创建角色造型"""
        character = self.get_object()

        if request.method == "GET":
            poses = character.poses.all()
            serializer = CharacterPoseSerializer(poses, many=True)
            return Response(serializer.data)

        elif request.method == "POST":
            serializer = CharacterPoseSerializer(
                data=request.data, context={"character": character}
            )
            if serializer.is_valid():
                serializer.save(character=character)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["get", "put", "patch"])
    def voice_config(self, request, pk=None):
        """获取或更新角色音色配置"""
        character = self.get_object()

        try:
            voice_config = character.voice_config
        except CharacterVoiceConfig.DoesNotExist:
            voice_config = None

        if request.method == "GET":
            if voice_config:
                serializer = CharacterVoiceConfigSerializer(voice_config)
                return Response(serializer.data)
            return Response({"detail": "音色配置不存在"}, status=status.HTTP_404_NOT_FOUND)

        elif request.method in ["PUT", "PATCH"]:
            if voice_config:
                serializer = CharacterVoiceConfigSerializer(
                    voice_config, data=request.data, partial=request.method == "PATCH"
                )
            else:
                serializer = CharacterVoiceConfigSerializer(data=request.data)
                serializer.validated_data["character"] = character

            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=["post"])
    def bulk_delete(self, request):
        """批量删除角色"""
        character_ids = request.data.get("character_ids", [])
        if not character_ids:
            return Response(
                {"detail": "请提供要删除的角色ID列表"}, status=status.HTTP_400_BAD_REQUEST
            )

        count, _ = CharacterProfile.objects.filter(id__in=character_ids).delete()

        return Response({"deleted_count": count})

    @action(detail=False, methods=["post"])
    def bulk_update_tts(self, request):
        """批量更新TTS引擎"""
        character_ids = request.data.get("character_ids", [])
        tts_engine = request.data.get("tts_engine")

        if not character_ids or not tts_engine:
            return Response(
                {"detail": "请提供角色ID列表和TTS引擎"}, status=status.HTTP_400_BAD_REQUEST
            )

        updated = CharacterProfile.objects.filter(id__in=character_ids).update(
            preferred_tts_engine=tts_engine
        )

        return Response({"updated_count": updated})


class CharacterPoseViewSet(viewsets.ModelViewSet):
    """
    角色造型API ViewSet

    list: 获取造型列表
    retrieve: 获取造型详情
    create: 创建新造型
    update: 更新造型
    partial_update: 部分更新造型
    destroy: 删除造型
    """

    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["character", "pose_type", "is_default"]
    search_fields = ["pose_name", "description"]
    ordering_fields = ["usage_count", "created_at"]
    ordering = ["-is_default", "-usage_count", "pose_name"]

    def get_queryset(self):
        """获取查询集"""
        return CharacterPose.objects.select_related("character")

    def get_serializer_class(self):
        """返回序列化器"""
        return CharacterPoseSerializer

    def perform_create(self, serializer):
        """创建时自动设置character"""
        character_id = self.request.data.get("character")
        if character_id:
            character = get_object_or_404(CharacterProfile, id=character_id)
            serializer.save(character=character)

    @action(detail=True, methods=["post"])
    def set_default(self, request, pk=None):
        """设为默认造型"""
        pose = self.get_object()
        character = pose.character

        # 取消其他默认造型
        CharacterPose.objects.filter(character=character).update(is_default=False)

        # 设置当前为默认
        pose.is_default = True
        pose.save()

        serializer = CharacterPoseSerializer(pose)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def increment_usage(self, request, pk=None):
        """增加使用计数"""
        pose = self.get_object()
        pose.increment_usage()
        serializer = CharacterPoseSerializer(pose)
        return Response(serializer.data)

    @action(detail=False, methods=["post"])
    def bulk_delete(self, request):
        """批量删除造型"""
        pose_ids = request.data.get("pose_ids", [])
        if not pose_ids:
            return Response(
                {"detail": "请提供要删除的造型ID列表"}, status=status.HTTP_400_BAD_REQUEST
            )

        count, _ = CharacterPose.objects.filter(id__in=pose_ids).delete()

        return Response({"deleted_count": count})


class CharacterVoiceConfigViewSet(viewsets.ModelViewSet):
    """
    角色音色配置API ViewSet

    list: 获取音色配置列表
    retrieve: 获取音色配置详情
    create: 创建音色配置
    update: 更新音色配置
    partial_update: 部分更新音色配置
    destroy: 删除音色配置
    """

    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["tts_engine", "pitch", "speed", "volume"]
    ordering_fields = ["created_at"]
    ordering = ["-created_at"]

    def get_queryset(self):
        """获取查询集"""
        return CharacterVoiceConfig.objects.select_related("character")

    def get_serializer_class(self):
        """返回序列化器"""
        return CharacterVoiceConfigSerializer

    @action(detail=True, methods=["post"])
    def preview(self, request, pk=None):
        """生成音色试听样本"""
        voice_config = self.get_object()
        # TODO: 集成TTS生成逻辑
        return Response({"detail": "试听样本生成功能待实现", "voice_config_id": voice_config.id})


class ItemProfileViewSet(viewsets.ModelViewSet):
    """
    物品档案API ViewSet

    list: 获取物品列表
    retrieve: 获取物品详情
    create: 创建新物品
    update: 更新物品
    partial_update: 部分更新物品
    destroy: 删除物品
    """

    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["artwork", "item_type", "associated_character"]
    search_fields = ["name", "description", "appearance_context"]
    ordering_fields = ["usage_count", "created_at"]
    ordering = ["-usage_count", "name"]

    def get_queryset(self):
        """获取查询集"""
        return ItemProfile.objects.select_related("artwork", "associated_character")

    def get_serializer_class(self):
        """返回序列化器"""
        return ItemProfileSerializer

    @action(detail=True, methods=["post"])
    def increment_usage(self, request, pk=None):
        """增加使用计数"""
        item = self.get_object()
        item.increment_usage()
        serializer = ItemProfileSerializer(item)
        return Response(serializer.data)


class ScriptSceneViewSet(viewsets.ModelViewSet):
    """
    剧本场景API ViewSet (Story 11.2.1)

    list: 获取场景列表
    retrieve: 获取场景详情（包含镜头列表）
    create: 创建新场景
    update: 更新场景信息
    partial_update: 部分更新场景
    destroy: 删除场景
    """

    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["chapter", "physical_scene", "is_completed"]
    search_fields = ["scene_name", "description"]
    ordering_fields = ["scene_number", "created_at"]
    ordering = ["chapter", "scene_number"]

    def get_queryset(self):
        """获取查询集"""
        return ScriptScene.objects.select_related("chapter", "physical_scene").prefetch_related(
            "shots"
        )

    def get_serializer_class(self):
        """根据action选择序列化器"""
        if self.action in ["retrieve", "update", "partial_update"]:
            return ScriptSceneDetailSerializer
        return ScriptSceneSerializer

    @action(detail=False, methods=["post"])
    def bulk_update_transition(self, request):
        """
        批量更新转场配置 (Story 11.2.1)

        请求参数:
        - scene_ids: list[int] - 场景ID列表
        - transition_type: str - 转场类型
        - transition_duration: float - 转场时长(秒)

        返回:
        - 更新统计
        """
        from .services import BatchOperationService

        scene_ids = request.data.get("scene_ids", [])
        transition_type = request.data.get("transition_type")
        transition_duration = request.data.get("transition_duration")

        if not scene_ids:
            return Response({"detail": "请提供场景ID列表"}, status=status.HTTP_400_BAD_REQUEST)

        # 使用批量操作服务
        service = BatchOperationService(
            operation_type="bulk_update_transition", user=request.user
        )

        scenes = ScriptScene.objects.filter(id__in=scene_ids)

        def update_scene(scene):
            scene.transition_type = transition_type
            scene.transition_duration = transition_duration
            scene.save(update_fields=["transition_type", "transition_duration"])

        result = service.execute_batch_operation(
            items=scenes,
            operation_func=update_scene,
            error_code="UPDATE_TRANSITION_ERROR",
        )

        return Response(result.to_dict())

    @action(detail=False, methods=["post"])
    def bulk_delete_enhanced(self, request):
        """
        批量删除场景 (增强版 - Story 11.5.1)

        请求参数:
        - scene_ids: list[int] - 场景ID列表

        返回:
        - 操作结果 (包含成功/失败统计、详细错误信息、进度追踪ID)
        """
        from .services import BatchOperationService

        scene_ids = request.data.get("scene_ids", [])
        if not scene_ids:
            return Response(
                {"detail": "请提供场景ID列表"}, status=status.HTTP_400_BAD_REQUEST
            )

        service = BatchOperationService(operation_type="bulk_delete", user=request.user)
        result = service.execute_batch_delete(
            model_class=ScriptScene, item_ids=scene_ids
        )

        return Response(result.to_dict())


class ShotViewSet(viewsets.ModelViewSet):
    """
    镜头API ViewSet (Story 11.2.2)

    list: 获取镜头列表
    retrieve: 获取镜头详情
    create: 创建新镜头
    update: 更新镜头信息
    partial_update: 部分更新镜头
    destroy: 删除镜头
    """

    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["scene", "shot_type", "is_generated", "character_pose"]
    search_fields = ["content", "speaker", "narration"]
    ordering_fields = ["shot_number", "sort_order", "duration"]
    ordering = ["scene", "sort_order", "shot_number"]

    def get_queryset(self):
        """获取查询集"""
        return Shot.objects.select_related(
            "scene", "scene__chapter", "character_pose", "character_pose__character"
        )

    def get_serializer_class(self):
        """根据action选择序列化器"""
        if self.action in ["retrieve", "update", "partial_update"]:
            return ShotDetailSerializer
        return ShotSerializer

    @action(detail=False, methods=["post"])
    def bulk_update_sort(self, request):
        """批量更新镜头排序 (Story 11.2.3)"""
        shot_orders = request.data.get("shot_orders", [])

        if not shot_orders:
            return Response({"detail": "请提供镜头排序数据"}, status=status.HTTP_400_BAD_REQUEST)

        updated_shots = []
        for item in shot_orders:
            try:
                shot = Shot.objects.get(id=item["id"])
                shot.sort_order = item["sort_order"]
                shot.save(update_fields=["sort_order"])
                updated_shots.append(shot)
            except Shot.DoesNotExist:
                continue

        serializer = ShotSerializer(updated_shots, many=True)
        return Response({"updated_count": len(updated_shots), "updated_shots": serializer.data})

    @action(detail=False, methods=["post"])
    def bulk_delete(self, request):
        """批量删除镜头 (Story 11.2.3)"""
        shot_ids = request.data.get("shot_ids", [])
        if not shot_ids:
            return Response(
                {"detail": "请提供要删除的镜头ID列表"}, status=status.HTTP_400_BAD_REQUEST
            )

        count, _ = Shot.objects.filter(id__in=shot_ids).delete()

        return Response({"deleted_count": count})

    @action(detail=False, methods=["post"])
    def bulk_update_pose(self, request):
        """批量更新角色造型 (Story 11.2.3)"""
        shot_ids = request.data.get("shot_ids", [])
        pose_id = request.data.get("pose_id")

        if not shot_ids:
            return Response({"detail": "请提供镜头ID列表"}, status=status.HTTP_400_BAD_REQUEST)

        updated = Shot.objects.filter(id__in=shot_ids).update(character_pose_id=pose_id)

        # 返回更新后的镜头列表
        updated_shots = Shot.objects.filter(id__in=shot_ids)
        serializer = ShotSerializer(updated_shots, many=True)

        return Response({"updated_count": updated, "updated_shots": serializer.data})

    @action(detail=False, methods=["post"])
    def bulk_regenerate(self, request):
        """
        批量重新生成镜头 (Story 11.5.1)

        请求参数:
        - shot_ids: list[int] - 镜头ID列表
        - regenerate_image: boolean (是否重新生成图像，默认True)
        - regenerate_audio: boolean (是否重新生成音频，默认True)
        - override_params: dict (覆盖参数，可选)

        返回:
        - 操作结果 (包含成功/失败统计、详细错误信息、进度追踪ID)
        """
        from .services import ShotBatchOperationService

        shot_ids = request.data.get("shot_ids", [])
        if not shot_ids:
            return Response(
                {"detail": "请提供镜头ID列表"}, status=status.HTTP_400_BAD_REQUEST
            )

        regenerate_image = request.data.get("regenerate_image", True)
        regenerate_audio = request.data.get("regenerate_audio", True)
        override_params = request.data.get("override_params")

        # 验证至少选择一种重新生成类型
        if not regenerate_image and not regenerate_audio:
            return Response(
                {"detail": "至少需要选择重新生成图像或音频"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # 执行批量重新生成
        service = ShotBatchOperationService(
            operation_type="bulk_regenerate", user=request.user
        )
        result = service.batch_regenerate(
            shot_ids=shot_ids,
            regenerate_image=regenerate_image,
            regenerate_audio=regenerate_audio,
            override_params=override_params,
        )

        return Response(result.to_dict())

    @action(detail=False, methods=["post"])
    def bulk_move(self, request):
        """
        批量移动镜头到其他场景 (Story 11.5.1)

        请求参数:
        - shot_ids: list[int] - 镜头ID列表
        - target_scene_id: int - 目标场景ID
        - update_sort_order: boolean (是否更新排序，默认True)

        返回:
        - 操作结果 (包含成功/失败统计、详细错误信息、进度追踪ID)
        """
        from .services import ShotBatchOperationService

        shot_ids = request.data.get("shot_ids", [])
        target_scene_id = request.data.get("target_scene_id")
        update_sort_order = request.data.get("update_sort_order", True)

        if not shot_ids:
            return Response(
                {"detail": "请提供镜头ID列表"}, status=status.HTTP_400_BAD_REQUEST
            )

        if not target_scene_id:
            return Response(
                {"detail": "请提供目标场景ID"}, status=status.HTTP_400_BAD_REQUEST
            )

        # 执行批量移动
        service = ShotBatchOperationService(operation_type="bulk_move", user=request.user)
        result = service.batch_move(
            shot_ids=shot_ids,
            target_scene_id=target_scene_id,
            update_sort_order=update_sort_order,
        )

        return Response(result.to_dict())

    @action(detail=False, methods=["post"])
    def bulk_delete_enhanced(self, request):
        """
        批量删除镜头 (增强版 - Story 11.5.1)

        请求参数:
        - shot_ids: list[int] - 镜头ID列表

        返回:
        - 操作结果 (包含成功/失败统计、详细错误信息、进度追踪ID)
        """
        from .services import ShotBatchOperationService

        shot_ids = request.data.get("shot_ids", [])
        if not shot_ids:
            return Response(
                {"detail": "请提供镜头ID列表"}, status=status.HTTP_400_BAD_REQUEST
            )

        # 执行批量删除
        service = ShotBatchOperationService(operation_type="bulk_delete", user=request.user)
        result = service.execute_batch_delete(model_class=Shot, item_ids=shot_ids)

        return Response(result.to_dict())

    @action(detail=False, methods=["post"])
    def bulk_update_character(self, request):
        """
        批量更新镜头的角色造型 (增强版 - Story 11.5.1)

        请求参数:
        - shot_ids: list[int] - 镜头ID列表
        - character_pose_id: int | null - 角色造型ID (null表示清除)

        返回:
        - 操作结果 (包含成功/失败统计、详细错误信息、进度追踪ID)
        """
        from .services import ShotBatchOperationService

        shot_ids = request.data.get("shot_ids", [])
        character_pose_id = request.data.get("character_pose_id")

        if not shot_ids:
            return Response(
                {"detail": "请提供镜头ID列表"}, status=status.HTTP_400_BAD_REQUEST
            )

        # 执行批量更新
        service = ShotBatchOperationService(
            operation_type="bulk_update_character", user=request.user
        )
        result = service.batch_update_character(
            shot_ids=shot_ids, character_pose_id=character_pose_id
        )

        return Response(result.to_dict())

    @action(detail=True, methods=["post"])
    def regenerate(self, request, pk=None):
        """
        重新生成镜头内容 (Story 11.2.4)

        请求参数:
        - regenerate_image: boolean (是否重新生成图像，默认True)
        - regenerate_audio: boolean (是否重新生成音频，默认True)
        - override_params: dict (覆盖参数，可选)
        """
        from .tasks import regenerate_shot_content

        shot = self.get_object()

        # 使用序列化器验证参数
        serializer = RegenerateShotSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        regenerate_image = serializer.validated_data.get("regenerate_image", True)
        regenerate_audio = serializer.validated_data.get("regenerate_audio", True)
        override_params = serializer.validated_data.get("override_params", {})

        # 确定 regenerate_type (兼容现有任务)
        if regenerate_image and regenerate_audio:
            regenerate_type = "both"
        elif regenerate_image:
            regenerate_type = "image"
        elif regenerate_audio:
            regenerate_type = "audio"
        else:
            # 这不应该发生，因为序列化器已经验证过
            return Response(
                {"detail": "至少需要选择重新生成图像或音频"}, status=status.HTTP_400_BAD_REQUEST
            )

        # 提取 custom_prompt (如果有)
        custom_prompt = override_params.get("image_prompt") or override_params.get("custom_prompt")

        # 启动异步任务
        task = regenerate_shot_content.delay(
            shot_id=shot.id, regenerate_type=regenerate_type, custom_prompt=custom_prompt
        )

        return Response(
            {
                "task_id": task.id,
                "shot_id": shot.id,
                "regenerate_type": regenerate_type,
                "status": "processing",
                "message": "重新生成任务已启动",
            },
            status=status.HTTP_202_ACCEPTED,
        )


class GenerationProgressViewSet(viewsets.ReadOnlyModelViewSet):
    """
    批量操作进度追踪 ViewSet (Story 11.5.1)

    list: 获取用户的进度列表
    retrieve: 获取进度详情
    """

    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["status", "generation_type"]
    ordering_fields = ["created_at", "completed_at"]
    ordering = ["-created_at"]

    def get_queryset(self):
        """获取当前用户的进度记录"""
        return GenerationProgress.objects.filter(user=self.request.user)

    def get_serializer_class(self):
        """返回序列化器"""
        from .serializers import GenerationProgressSerializer
        return GenerationProgressSerializer


class ShotVersionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    镜头版本管理 ViewSet (Story 11.5.2)

    list: 获取镜头的版本列表
    retrieve: 获取版本详情
    """

    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["is_auto_created"]
    ordering_fields = ["version_number", "created_at"]
    ordering = ["-version_number"]

    def get_queryset(self):
        """获取查询集"""
        # 支持按 shot_id 过滤
        shot_id = self.request.query_params.get("shot_id")
        queryset = ShotVersion.objects.select_related("shot", "created_by").prefetch_related(
            "shot__scene"
        )
        if shot_id:
            queryset = queryset.filter(shot_id=shot_id)
        return queryset

    def get_serializer_class(self):
        """根据action选择序列化器"""
        if self.action in ["retrieve", "compare"]:
            return ShotVersionDetailSerializer
        return ShotVersionSerializer

    @action(detail=True, methods=["post"])
    def restore(self, request, pk=None):
        """
        恢复到指定版本 (Story 11.5.2)

        将版本快照的内容恢复到镜头
        """
        version = self.get_object()

        try:
            version.restore()
            serializer = ShotSerializer(version.shot)
            return Response(
                {
                    "detail": f"已恢复到版本 {version.version_number}",
                    "shot": serializer.data,
                }
            )
        except Exception as e:
            return Response(
                {"detail": f"恢复失败: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

    @action(detail=True, methods=["get"])
    def compare(self, request, pk=None):
        """
        与其他版本对比 (Story 11.5.2)

        请求参数:
        - compare_version_id: 要对比的版本ID

        返回:
        - 版本差异信息
        """
        version = self.get_object()
        compare_version_id = request.query_params.get("compare_version_id")

        if not compare_version_id:
            return Response(
                {"detail": "请提供要对比的版本ID (compare_version_id)"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            compare_version = ShotVersion.objects.get(id=compare_version_id, shot=version.shot)
        except ShotVersion.DoesNotExist:
            return Response(
                {"detail": "指定的对比版本不存在"},
                status=status.HTTP_404_NOT_FOUND,
            )

        differences = version.compare_with(compare_version)

        return Response(
            {
                "current_version": ShotVersionDetailSerializer(version).data,
                "compare_version": ShotVersionDetailSerializer(compare_version).data,
                "differences": differences,
            }
        )

    @action(detail=False, methods=["post"])
    def create_snapshot(self, request):
        """
        手动创建版本快照 (Story 11.5.2)

        请求参数:
        - shot_id: 镜头ID
        - change_description: 修改说明 (可选)

        返回:
        - 创建的版本信息
        """
        shot_id = request.data.get("shot_id")
        change_description = request.data.get("change_description", "")

        if not shot_id:
            return Response(
                {"detail": "请提供镜头ID (shot_id)"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            shot = Shot.objects.get(id=shot_id)
        except Shot.DoesNotExist:
            return Response(
                {"detail": "指定的镜头不存在"},
                status=status.HTTP_404_NOT_FOUND,
            )

        version = ShotVersion.create_version(
            shot=shot,
            change_description=change_description or "手动创建快照",
            is_auto_created=False,
            user=request.user,
        )

        serializer = ShotVersionSerializer(version)
        return Response(
            {
                "detail": "版本快照创建成功",
                "version": serializer.data,
            },
            status=status.HTTP_201_CREATED,
        )
