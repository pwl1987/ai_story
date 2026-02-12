"""
批量生成序列化器 (Story 11.1.4)

包含 GenerationProgress 和 GenerationHistory 序列化器
"""

from rest_framework import serializers
from django.utils.translation import gettext_lazy as _

from ..models import GenerationProgress, GenerationHistory


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
