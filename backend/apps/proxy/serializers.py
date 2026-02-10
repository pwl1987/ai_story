"""
代理配置序列化器
Story 9.8: 前端代理选择器
"""

from rest_framework import serializers

from .models import ProxyConfig


class ProxySelectSerializer(serializers.ModelSerializer):
    """代理选择器序列化器 - 用于前端下拉框"""

    protocol_display = serializers.CharField(source="get_protocol_display", read_only=True)
    status = serializers.SerializerMethodField()

    class Meta:
        model = ProxyConfig
        fields = [
            "id",
            "name",
            "protocol",
            "protocol_display",
            "host",
            "port",
            "is_healthy",
            "status",
        ]
        read_only_fields = ["id", "is_healthy"]

    def get_status(self, obj):
        """获取代理状态文本"""
        if obj.is_healthy:
            return "✓ 健康"
        else:
            return "✗ 不健康"


class TestConnectionSerializer(serializers.Serializer):
    """测试连接响应序列化器"""

    success = serializers.BooleanField()
    ip = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    response_time_ms = serializers.IntegerField(required=False, allow_null=True)
    error = serializers.CharField(required=False, allow_null=True, allow_blank=True)

    class Meta:
        fields = ["success", "ip", "response_time_ms", "error"]
