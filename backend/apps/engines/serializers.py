# Engines Serializers - 引擎配置序列化器

from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from .models import (
    EngineConfig,
    EngineHealthLog,
    EngineUsageLog,
    FallbackEventLog,
)


class EngineConfigSerializer(serializers.ModelSerializer):
    """引擎配置序列化器"""

    engine_type_display = serializers.CharField(source="get_engine_type_display", read_only=True)
    health_status_display = serializers.CharField(
        source="get_health_status_display", read_only=True
    )
    success_rate = serializers.ReadOnlyField()

    class Meta:
        model = EngineConfig
        fields = [
            "id",
            "engine_type",
            "engine_type_display",
            "name",
            "description",
            "primary_provider",
            "primary_config",
            "fallback_provider",
            "fallback_config",
            "fallback_threshold",
            "fallback_timeout",
            "auto_fallback",
            "is_active",
            "current_provider",
            "health_status",
            "health_status_display",
            "last_health_check",
            "total_requests",
            "success_count",
            "failure_count",
            "success_rate",
            "avg_response_time",
            "total_cost",
            "saved_cost",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "health_status",
            "last_health_check",
            "total_requests",
            "success_count",
            "failure_count",
            "avg_response_time",
            "total_cost",
            "saved_cost",
            "created_at",
            "updated_at",
        ]

    def validate(self, data):
        """验证业务逻辑"""
        primary = data.get("primary_provider")
        fallback = data.get("fallback_provider")

        # 主引擎和备份引擎不能相同
        if primary and fallback and primary == fallback:
            raise serializers.ValidationError({"fallback_provider": _("主引擎和备份引擎不能相同")})

        return data


class EngineConfigCreateSerializer(serializers.ModelSerializer):
    """引擎配置创建序列化器（包含更多验证）"""

    class Meta:
        model = EngineConfig
        fields = [
            "engine_type",
            "name",
            "description",
            "primary_provider",
            "primary_config",
            "fallback_provider",
            "fallback_config",
            "fallback_threshold",
            "fallback_timeout",
            "auto_fallback",
            "is_active",
        ]

    def validate_primary_config(self, value):
        """验证主引擎配置"""
        if not isinstance(value, dict):
            raise serializers.ValidationError(_("主引擎配置必须是 JSON 对象"))
        return value

    def validate_fallback_config(self, value):
        """验证备份引擎配置"""
        if not isinstance(value, dict):
            raise serializers.ValidationError(_("备份引擎配置必须是 JSON 对象"))
        return value

    def validate_fallback_threshold(self, value):
        """验证失败阈值"""
        if value < 1 or value > 10:
            raise serializers.ValidationError(_("失败阈值必须在 1-10 之间"))
        return value

    def validate_fallback_timeout(self, value):
        """验证超时时间"""
        if value < 10 or value > 120:
            raise serializers.ValidationError(_("超时时间必须在 10-120 秒之间"))
        return value


class EngineHealthLogSerializer(serializers.ModelSerializer):
    """引擎健康日志序列化器"""

    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = EngineHealthLog
        fields = [
            "id",
            "engine",
            "status",
            "status_display",
            "response_time",
            "error_message",
            "error_code",
            "checked_at",
        ]
        read_only_fields = ["id", "checked_at"]


class EngineUsageLogSerializer(serializers.ModelSerializer):
    """引擎使用日志序列化器"""

    success_display = serializers.SerializerMethodField()
    engine_type = serializers.CharField(source="engine.engine_type", read_only=True)
    provider_display = serializers.CharField(source="get_provider_display", read_only=True)

    class Meta:
        model = EngineUsageLog
        fields = [
            "id",
            "engine",
            "engine_type",
            "provider",
            "provider_display",
            "request_type",
            "success",
            "success_display",
            "response_time",
            "token_count",
            "cost",
            "saved_cost",
            "project_id",
            "shot_id",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]

    def get_success_display(self, obj):
        return "✓" if obj.success else "✗"


class FallbackEventLogSerializer(serializers.ModelSerializer):
    """Fallback 事件日志序列化器"""

    reason_display = serializers.CharField(source="get_reason_display", read_only=True)
    engine_type = serializers.CharField(source="engine.engine_type", read_only=True)

    class Meta:
        model = FallbackEventLog
        fields = [
            "id",
            "engine",
            "engine_type",
            "from_provider",
            "to_provider",
            "reason",
            "reason_display",
            "reason_detail",
            "affected_requests",
            "switched_at",
        ]
        read_only_fields = ["id", "switched_at"]


class EngineStatsSerializer(serializers.Serializer):
    """引擎统计序列化器（自定义统计输出）"""

    engine_type = serializers.CharField()
    engine_name = serializers.CharField()
    total_requests = serializers.IntegerField()
    success_count = serializers.IntegerField()
    failure_count = serializers.IntegerField()
    success_rate = serializers.FloatField()
    avg_response_time = serializers.FloatField()
    total_cost = serializers.FloatField()
    saved_cost = serializers.FloatField()
    today_requests = serializers.IntegerField()
    week_requests = serializers.IntegerField()
    month_requests = serializers.IntegerField()


class HealthCheckTriggerSerializer(serializers.Serializer):
    """健康检查触发序列化器"""

    engine_type = serializers.ChoiceField(
        choices=["llm", "image", "tts", None],
        required=False,
        allow_null=True,
        help_text="指定引擎类型，为空则检查所有",
    )
