"""
角色序列化器 (Story 12-4 拆分 - character.py)

包含角色相关的序列化器
"""

from rest_framework import serializers
from django.utils.translation import gettext_lazy as _

from apps.artworks.models import (
    CharacterPose,
    CharacterProfile,
    CharacterVoiceConfig,
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


class CharacterVoiceConfigSerializer(serializers.ModelSerializer):
    """角色音色配置序列化器"""
    
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


class CharacterProfileSerializer(serializers.ModelSerializer):
    """角色档案序列化器"""
    
    poses = CharacterPoseSerializer(many=True, read_only=True)
    voice_config = CharacterVoiceConfigSerializer(read_only=True)
    portrait_url = serializers.ImageField(source="default_portrait", read_only=True)
    
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


class CharacterProfileDetailSerializer(CharacterProfileSerializer):
    """角色档案详情序列化器（包含完整信息）"""

    profile = CharacterProfileSerializer(read_only=True)
    artwork_title = serializers.CharField(source="artwork.title", read_only=True)

    class Meta:
        model = CharacterProfile
        fields = CharacterProfileSerializer.Meta.fields + ["artwork_title", "profile"]


class RegenerateShotSerializer(serializers.Serializer):
    """
    重新生成镜头序列化器 (Story 11.2.4)

    验证重新生成请求的参数
    """

    regenerate_image = serializers.BooleanField(default=True, help_text=_("是否重新生成图像"))
    regenerate_audio = serializers.BooleanField(default=True, help_text=_("是否重新生成音频"))
    override_params = serializers.DictField(
        required=False,
        default={},
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
