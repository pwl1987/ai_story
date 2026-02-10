"""
角色资产管理 API Serializers

遵循DRF最佳实践:
- 嵌套序列化器处理关联关系
- 只读字段控制
- 验证逻辑
"""

import json

from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from .models import (
    Artwork,
    CharacterPose,
    CharacterProfile,
    CharacterVoiceConfig,
    GenerationHistory,
    GenerationProgress,
    ItemProfile,
    ScriptScene,
    Shot,
    ShotVersion,
)


class CharacterPoseSerializer(serializers.ModelSerializer):
    """角色造型序列化器"""

    pose_type_display = serializers.CharField(source="get_pose_type_display", read_only=True)
    thumbnail_url = serializers.ImageField(source="pose_image", read_only=True)

    class Meta:
        model = CharacterPose
        fields = [
            "id",
            "pose_name",
            "pose_type",
            "pose_type_display",
            "pose_image",
            "thumbnail_url",
            "suitable_for_scenes",
            "extraction_source",
            "extracted_from_chapter",
            "description",
            "usage_count",
            "is_default",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["usage_count", "created_at", "updated_at"]


class CharacterVoiceConfigSerializer(serializers.ModelSerializer):
    """角色音色配置序列化器"""

    tts_engine_display = serializers.CharField(source="get_tts_engine_display", read_only=True)
    pitch_display = serializers.CharField(source="get_pitch_display", read_only=True)
    speed_display = serializers.CharField(source="get_speed_display", read_only=True)
    volume_display = serializers.CharField(source="get_volume_display", read_only=True)

    class Meta:
        model = CharacterVoiceConfig
        fields = [
            "id",
            "tts_engine",
            "tts_engine_display",
            "voice_id",
            "voice_type",
            "pitch",
            "pitch_display",
            "speed",
            "speed_display",
            "volume",
            "volume_display",
            "emotion_mode",
            "emotion_intensity",
            "emotion_voices",
            "voice_sample_url",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]


class CharacterProfileSerializer(serializers.ModelSerializer):
    """角色档案序列化器"""

    poses = CharacterPoseSerializer(many=True, read_only=True)
    voice_config = CharacterVoiceConfigSerializer(read_only=True)
    portrait_url = serializers.ImageField(source="default_portrait", read_only=True)
    preferred_llm_engine_display = serializers.CharField(
        source="get_preferred_llm_engine_display", read_only=True
    )
    preferred_tts_engine_display = serializers.CharField(
        source="get_preferred_tts_engine_display", read_only=True
    )
    preferred_image_engine_display = serializers.CharField(
        source="get_preferred_image_engine_display", read_only=True
    )

    class Meta:
        model = CharacterProfile
        fields = [
            "id",
            "artwork",
            "name",
            "display_name",
            "description",
            "personality",
            "appearance_count",
            "dialogue_count",
            "default_portrait",
            "portrait_url",
            "importance_rank",
            "preferred_llm_engine",
            "preferred_llm_engine_display",
            "preferred_tts_engine",
            "preferred_tts_engine_display",
            "preferred_image_engine",
            "preferred_image_engine_display",
            "poses",
            "voice_config",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["appearance_count", "dialogue_count", "created_at", "updated_at"]


class CharacterProfileDetailSerializer(CharacterProfileSerializer):
    """角色档案详情序列化器（包含完整信息）"""

    artwork_title = serializers.CharField(source="artwork.title", read_only=True)

    class Meta(CharacterProfileSerializer.Meta):
        fields = CharacterProfileSerializer.Meta.fields + ["artwork_title"]


class ItemProfileSerializer(serializers.ModelSerializer):
    """物品档案序列化器"""

    item_type_display = serializers.CharField(source="get_item_type_display", read_only=True)
    item_image_url = serializers.ImageField(source="item_image", read_only=True)
    character_name = serializers.CharField(
        source="associated_character.display_name", read_only=True, allow_null=True
    )

    class Meta:
        model = ItemProfile
        fields = [
            "id",
            "artwork",
            "name",
            "item_type",
            "item_type_display",
            "description",
            "appearance_context",
            "item_image",
            "item_image_url",
            "usage_count",
            "first_appearance_chapter",
            "associated_character",
            "character_name",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["usage_count", "created_at", "updated_at"]


class ArtworkSerializer(serializers.ModelSerializer):
    """作品序列化器"""

    artwork_type_display = serializers.CharField(source="get_artwork_type_display", read_only=True)
    progress_percentage = serializers.ReadOnlyField()
    character_count = serializers.SerializerMethodField()
    item_count = serializers.SerializerMethodField()

    class Meta:
        model = Artwork
        fields = [
            "id",
            "title",
            "author",
            "artwork_type",
            "artwork_type_display",
            "source_file",
            "story_overview",
            "total_chapters",
            "total_scenes",
            "total_shots",
            "progress_percentage",
            "is_parsed",
            "parsing_status",
            "character_count",
            "item_count",
            "preferred_llm_engine",
            "preferred_image_engine",
            "preferred_tts_engine",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "total_chapters",
            "total_scenes",
            "total_shots",
            "is_parsed",
            "created_at",
            "updated_at",
        ]

    def get_character_count(self, obj):
        """获取角色数量"""
        return obj.characters.count()

    def get_item_count(self, obj):
        """获取物品数量"""
        return obj.items.count()


class ArtworkDetailSerializer(ArtworkSerializer):
    """作品详情序列化器"""

    characters = CharacterProfileSerializer(many=True, read_only=True)
    items = ItemProfileSerializer(many=True, read_only=True)

    class Meta(ArtworkSerializer.Meta):
        fields = ArtworkSerializer.Meta.fields + ["characters", "items"]


class GenerationProgressSerializer(serializers.ModelSerializer):
    """生成进度序列化器 (Story 11.1.4)"""

    generation_type_display = serializers.CharField(
        source="get_generation_type_display", read_only=True
    )
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    progress_percentage = serializers.ReadOnlyField()
    username = serializers.CharField(source="user.username", read_only=True)

    class Meta:
        model = GenerationProgress
        fields = [
            "id",
            "user",
            "username",
            "generation_type",
            "generation_type_display",
            "status",
            "status_display",
            "total_items",
            "completed_items",
            "failed_items",
            "progress_percentage",
            "celery_task_id",
            "error_message",
            "completed_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at", "completed_at"]


class GenerationHistorySerializer(serializers.ModelSerializer):
    """生成历史序列化器 (Story 11.1.4)"""

    generation_type_display = serializers.CharField(
        source="get_generation_type_display", read_only=True
    )
    character_name = serializers.CharField(source="character.display_name", read_only=True)
    rating_display = serializers.SerializerMethodField()

    class Meta:
        model = GenerationHistory
        fields = [
            "id",
            "character",
            "character_name",
            "generation_type",
            "generation_type_display",
            "prompt_params",
            "voice_params",
            "result_url",
            "quality_rating",
            "rating_display",
            "user_feedback",
            "is_used",
            "regeneration_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["regeneration_count", "created_at", "updated_at"]

    def get_rating_display(self, obj):
        """获取评分显示"""
        if obj.quality_rating:
            return f"{'⭐' * obj.quality_rating} ({obj.quality_rating}/5)"
        return "未评分"


class ScriptSceneSerializer(serializers.ModelSerializer):
    """
    剧本场景序列化器 (Story 11.2.1)

    包含首尾帧和转场配置字段
    """

    transition_type_display = serializers.CharField(
        source="get_transition_type_display", read_only=True
    )
    chapter_title = serializers.CharField(source="chapter.title", read_only=True)
    physical_scene_name = serializers.CharField(
        source="physical_scene.name", read_only=True, allow_null=True
    )
    head_frame_url = serializers.ImageField(source="head_frame", read_only=True)
    tail_frame_url = serializers.ImageField(source="tail_frame", read_only=True)

    class Meta:
        model = ScriptScene
        fields = [
            "id",
            "chapter",
            "chapter_title",
            "physical_scene",
            "physical_scene_name",
            "scene_number",
            "scene_name",
            "description",
            "atmosphere",
            "time_of_day",
            "weather",
            "head_frame",
            "head_frame_url",
            "tail_frame",
            "tail_frame_url",
            "transition_to_next",
            "transition_type",
            "transition_type_display",
            "transition_duration",
            "shot_count",
            "is_completed",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["shot_count", "created_at", "updated_at"]

    def validate(self, attrs):
        """
        验证转场配置 (Story 11.2.1)

        规则:
        - 如果设置了 transition_type，必须设置 transition_to_next
        - transition_duration 必须在 0-10 秒之间
        """
        transition_type = attrs.get("transition_type")
        transition_to_next = attrs.get("transition_to_next")
        transition_duration = attrs.get("transition_duration")

        # 验证转场类型和目标
        if transition_type and not transition_to_next:
            raise serializers.ValidationError(
                {"transition_to_next": _("设置转场类型时必须指定转场目标场景")}
            )

        # 验证转场时长
        if transition_duration is not None:
            if not (0 <= transition_duration <= 10):
                raise serializers.ValidationError(
                    {"transition_duration": _("转场时长必须在0-10秒之间")}
                )

        return attrs


class ScriptSceneDetailSerializer(ScriptSceneSerializer):
    """剧本场景详情序列化器（包含关联的镜头列表）"""

    shots = serializers.SerializerMethodField()

    class Meta(ScriptSceneSerializer.Meta):
        fields = ScriptSceneSerializer.Meta.fields + ["shots"]

    def get_shots(self, obj):
        """获取场景的所有镜头"""
        shots = obj.shots.all().order_by("sort_order", "shot_number")
        return ShotSerializer(shots, many=True).data


class ShotSerializer(serializers.ModelSerializer):
    """
    镜头序列化器 (Story 11.2.2)

    包含增强字段：角色造型、运镜参数、构图描述、生成状态追踪
    """

    shot_type_display = serializers.CharField(source="get_shot_type_display", read_only=True)
    scene_name = serializers.CharField(source="scene.scene_name", read_only=True)
    character_pose_name = serializers.CharField(
        source="character_pose.pose_name", read_only=True, allow_null=True
    )
    generated_image_url = serializers.ImageField(source="generated_image", read_only=True)
    generated_audio_url = serializers.FileField(source="generated_audio", read_only=True)
    is_successfully_generated = serializers.ReadOnlyField()

    class Meta:
        model = Shot
        fields = [
            "id",
            "scene",
            "scene_name",
            "shot_number",
            "shot_type",
            "shot_type_display",
            "content",
            "speaker",
            "narration",
            "camera_movement",
            "camera_movement_params",
            "camera_angle",
            "duration",
            "sort_order",
            "character_pose",
            "character_pose_name",
            "shot_composition",
            "generated_image",
            "generated_image_url",
            "generated_audio",
            "generated_audio_url",
            "is_generated",
            "is_successfully_generated",
            "generated_at",
            "generation_error",
            "generation_retry_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "is_generated",
            "is_successfully_generated",
            "generated_at",
            "created_at",
            "updated_at",
        ]
        extra_kwargs = {"generation_retry_count": {"default": 0}}

    def validate_camera_movement_params(self, value):
        """验证运镜参数 JSON 格式 (Story 11.2.2)"""
        if value:
            try:
                json.dumps(value)
            except (TypeError, ValueError) as e:
                raise serializers.ValidationError(
                    _("运镜参数格式错误: %(error)s") % {"error": str(e)}
                )
        return value

    def validate_generation_retry_count(self, value):
        """验证重试次数不能为负数 (Story 11.2.2)"""
        if value < 0:
            raise serializers.ValidationError(_("重试次数不能为负数"))
        return value


class RegenerateShotSerializer(serializers.Serializer):
    """
    重新生成镜头序列化器 (Story 11.2.4)

    验证重新生成请求的参数
    """

    regenerate_image = serializers.BooleanField(default=True, help_text=_("是否重新生成图像"))
    regenerate_audio = serializers.BooleanField(default=True, help_text=_("是否重新生成音频"))
    override_params = serializers.DictField(
        required=False,
        default=dict,
        help_text=_(
            "覆盖参数，可包含: image_prompt, character_pose_id, camera_movement_params, duration 等"
        ),
    )

    def validate(self, attrs):
        """验证参数逻辑"""
        regenerate_image = attrs.get("regenerate_image", True)
        regenerate_audio = attrs.get("regenerate_audio", True)

        if not regenerate_image and not regenerate_audio:
            raise serializers.ValidationError({"regenerate": _("至少需要选择重新生成图像或音频")})

        return attrs


class ShotDetailSerializer(ShotSerializer):
    """镜头详情序列化器（包含完整场景信息）"""

    scene_detail = ScriptSceneSerializer(source="scene", read_only=True)
    character_pose_detail = CharacterPoseSerializer(
        source="character_pose", read_only=True, allow_null=True
    )

    class Meta(ShotSerializer.Meta):
        fields = ShotSerializer.Meta.fields + ["scene_detail", "character_pose_detail"]


class ShotVersionSerializer(serializers.ModelSerializer):
    """
    镜头版本序列化器 (Story 11.5.2)

    包含版本信息和内容快照
    """

    shot_content_preview = serializers.SerializerMethodField()
    username = serializers.CharField(source="created_by.username", read_only=True, allow_null=True)
    is_latest = serializers.ReadOnlyField()
    thumbnail_url = serializers.ImageField(source="thumbnail", read_only=True, allow_null=True)

    class Meta:
        model = ShotVersion
        fields = [
            "id",
            "shot",
            "version_number",
            "change_description",
            "content_snapshot",
            "field_changes",
            "is_auto_created",
            "thumbnail",
            "thumbnail_url",
            "created_by",
            "username",
            "is_latest",
            "shot_content_preview",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at", "is_latest", "shot_content_preview"]

    def get_shot_content_preview(self, obj):
        """获取镜头内容预览"""
        content = obj.content_snapshot.get("content", "")
        return content[:100] + "..." if len(content) > 100 else content


class ShotVersionDetailSerializer(ShotVersionSerializer):
    """镜头版本详情序列化器（包含完整信息）"""

    shot_detail = ShotSerializer(source="shot", read_only=True)

    class Meta(ShotVersionSerializer.Meta):
        fields = ShotVersionSerializer.Meta.fields + ["shot_detail"]
