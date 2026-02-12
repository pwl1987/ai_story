"""
场景序列化器 (Story 12-4 拆分 - scene.py)

包含剧本场景相关序列化器
"""

from rest_framework import serializers
from django.utils.translation import gettext_lazy as _

from apps.artworks.models import ScriptScene, Shot, ShotVersion


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


class ShotSerializer(serializers.ModelSerializer):
    """镜头序列化器"""

    shot_type_display = serializers.CharField(
        source="get_shot_type_display", read_only=True
    )
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
        read_only_fields = ["is_generated", "generated_at", "created_at", "updated_at"]

    def validate_camera_movement_params(self, value):
        """
        验证运镜参数 (Story 11.2.2)

        确保运镜参数是有效的 JSON 格式
        注意: JSONField 会自动解析字符串，这里只验证已解析的字典结构
        """
        # DRF JSONField 会自动将字符串解析为字典
        # 这里只验证字典内的数值范围
        if value and isinstance(value, dict):
            for key, val in value.items():
                if isinstance(val, (int, float)) and val < 0:
                    raise serializers.ValidationError(
                        _("{key} 的值不能为负数").format(key=key)
                    )

        return value

    def validate_generation_retry_count(self, value):
        """验证重试次数不能为负数 (Story 11.2.2)"""
        if value < 0:
            raise serializers.ValidationError(_("重试次数不能为负数"))
        return value


class ShotDetailSerializer(ShotSerializer):
    """镜头详情序列化器（包含完整场景信息）"""

    scene_detail = ScriptSceneSerializer(source="scene", read_only=True)
    character_pose_detail = serializers.SerializerMethodField()

    class Meta(ShotSerializer.Meta):
        fields = ShotSerializer.Meta.fields + ["scene_detail", "character_pose_detail"]

    def get_character_pose_detail(self, obj):
        """获取角色造型详情"""
        if obj.character_pose:
            from .character import CharacterPoseSerializer
            return CharacterPoseSerializer(obj.character_pose).data
        return None


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
        read_only_fields = [
            "created_at",
            "updated_at",
            "is_latest",
            "shot_content_preview",
        ]

    def get_shot_content_preview(self, obj):
        """获取镜头内容预览"""
        content = obj.content_snapshot.get("content", "")
        return content[:100] + "..." if len(content) > 100 else content


class ShotVersionDetailSerializer(ShotVersionSerializer):
    """镜头版本详情序列化器（包含完整信息）"""

    shot_detail = ShotSerializer(source="shot", read_only=True)

    class Meta(ShotVersionSerializer.Meta):
        fields = ShotVersionSerializer.Meta.fields + ["shot_detail"]


class ScriptSceneDetailSerializer(ScriptSceneSerializer):
    """剧本场景详情序列化器（包含关联的镜头列表）"""

    shots = ShotSerializer(many=True, read_only=True)

    class Meta(ScriptSceneSerializer.Meta):
        fields = ScriptSceneSerializer.Meta.fields + ["shots"]
