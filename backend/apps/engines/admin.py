# Engines Admin - 引擎配置管理后台


from django.contrib import admin, messages
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from .models import EngineConfig, EngineHealthLog, EngineUsageLog, FallbackEventLog

# ==================== Health Status Badge ====================


def health_status_badge(status):
    """生成健康状态徽章 HTML"""
    colors = {
        "online": "green",
        "offline": "red",
        "error": "orange",
        "unknown": "gray",
    }
    color = colors.get(status, "gray")
    label = {
        "online": "在线",
        "offline": "离线",
        "error": "异常",
        "unknown": "未知",
    }.get(status, status)

    return format_html('<span style="color: {}; font-weight: bold;">● {}</span>', color, label)


# ==================== EngineConfig Admin ====================


@admin.register(EngineConfig)
class EngineConfigAdmin(admin.ModelAdmin):
    """引擎配置管理"""

    list_display = [
        "engine_type_display",
        "name",
        "primary_provider",
        "health_status_badge",
        "is_active",
        "success_rate",
        "total_requests",
        "saved_cost_display",
    ]

    list_filter = [
        "engine_type",
        "health_status",
        "is_active",
        "auto_fallback",
    ]

    search_fields = [
        "name",
        "primary_provider",
        "fallback_provider",
        "description",
    ]

    readonly_fields = [
        "current_provider",
        "health_status",
        "last_health_check",
        "total_requests",
        "success_count",
        "failure_count",
        "avg_response_time",
        "total_cost",
        "saved_cost",
        "success_rate_display",
        "created_at",
        "updated_at",
    ]

    fieldsets = (
        (
            _("基础配置"),
            {
                "fields": (
                    "engine_type",
                    "name",
                    "description",
                    "is_active",
                )
            },
        ),
        (
            _("主引擎配置"),
            {
                "fields": (
                    "primary_provider",
                    "primary_config",
                )
            },
        ),
        (
            _("备份引擎配置"),
            {
                "fields": (
                    "fallback_provider",
                    "fallback_config",
                    "auto_fallback",
                    "fallback_threshold",
                    "fallback_timeout",
                )
            },
        ),
        (
            _("状态监控"),
            {
                "fields": (
                    "current_provider",
                    "health_status",
                    "last_health_check",
                )
            },
        ),
        (
            _("统计信息"),
            {
                "fields": (
                    "total_requests",
                    "success_count",
                    "failure_count",
                    "avg_response_time",
                    "success_rate_display",
                )
            },
        ),
        (
            _("成本追踪"),
            {
                "fields": (
                    "total_cost",
                    "saved_cost",
                )
            },
        ),
        (
            _("时间信息"),
            {
                "fields": (
                    "created_at",
                    "updated_at",
                )
            },
        ),
    )

    actions = [
        "test_connection_action",
        "reset_stats_action",
        "enable_auto_fallback",
        "disable_auto_fallback",
        "mark_as_online",
        "mark_as_offline",
    ]

    def engine_type_display(self, obj):
        """显示引擎类型图标"""
        icons = {
            "llm": "🤖",
            "image": "🎨",
            "tts": "🔊",
        }
        icon = icons.get(obj.engine_type, "⚙️")
        return f"{icon} {obj.get_engine_type_display()}"

    engine_type_display.short_description = _("引擎类型")
    engine_type_display.admin_order_field = "engine_type"

    def health_status_badge(self, obj):
        """显示健康状态徽章"""
        return health_status_badge(obj.health_status)

    health_status_badge.short_description = _("健康状态")
    health_status_badge.admin_order_field = "health_status"

    def success_rate(self, obj):
        """显示成功率"""
        rate = obj.calculate_success_rate()
        color = "green" if rate >= 90 else "orange" if rate >= 70 else "red"
        # 格式化数字为字符串，避免 SafeString 冲突
        rate_str = f"{rate:.1f}"
        return format_html('<span style="color: {};">{}%</span>', color, rate_str)

    success_rate.short_description = _("成功率")

    def success_rate_display(self, obj):
        """详情页显示成功率"""
        return f"{obj.calculate_success_rate():.2f}%"

    success_rate_display.short_description = _("成功率")

    def saved_cost_display(self, obj):
        """显示节省金额"""
        if obj.saved_cost > 0:
            return format_html(
                '<span style="color: green; font-weight: bold;">${:.2f} 💰</span>', obj.saved_cost
            )
        return "$0.00"

    saved_cost_display.short_description = _("节省金额")
    saved_cost_display.admin_order_field = "saved_cost"

    # ==================== Admin Actions ====================

    def test_connection_action(self, request, queryset):
        """
        测试引擎连接

        注意：这是占位符实现，实际的健康检查逻辑
        将在 Story 11.3.2 中实现。
        """
        count = queryset.count()
        for engine in queryset:
            # 占位符：实际测试逻辑在 Story 11.3.2
            engine.health_status = "unknown"
            engine.save()

        self.message_user(
            request,
            _(f"已启动 {count} 个引擎的连接测试（实际功能在 Story 11.3.2 实现）"),
            messages.SUCCESS,
        )

    test_connection_action.short_description = _("🔌 测试连接")

    def reset_stats_action(self, request, queryset):
        """重置统计信息"""
        count = queryset.update(
            total_requests=0,
            success_count=0,
            failure_count=0,
            avg_response_time=0.0,
            total_cost=0.0,
            saved_cost=0.0,
        )
        self.message_user(request, _(f"已重置 {count} 个引擎的统计信息"), messages.SUCCESS)

    reset_stats_action.short_description = _("🔄 重置统计")

    def enable_auto_fallback(self, request, queryset):
        """启用自动 Fallback"""
        count = queryset.update(auto_fallback=True)
        self.message_user(request, _(f"已为 {count} 个引擎启用自动 Fallback"), messages.SUCCESS)

    enable_auto_fallback.short_description = _("✓ 启用自动Fallback")

    def disable_auto_fallback(self, request, queryset):
        """禁用自动 Fallback"""
        count = queryset.update(auto_fallback=False)
        self.message_user(request, _(f"已为 {count} 个引擎禁用自动 Fallback"), messages.WARNING)

    disable_auto_fallback.short_description = _("✗ 禁用自动Fallback")

    def mark_as_online(self, request, queryset):
        """标记为在线"""
        count = queryset.update(health_status="online")
        self.message_user(request, _(f"已将 {count} 个引擎标记为在线"), messages.SUCCESS)

    mark_as_online.short_description = _("🟢 标记为在线")

    def mark_as_offline(self, request, queryset):
        """标记为离线"""
        count = queryset.update(health_status="offline")
        self.message_user(request, _(f"已将 {count} 个引擎标记为离线"), messages.WARNING)

    mark_as_offline.short_description = _("🔴 标记为离线")


# ==================== EngineHealthLog Admin ====================


@admin.register(EngineHealthLog)
class EngineHealthLogAdmin(admin.ModelAdmin):
    """引擎健康检查日志"""

    list_display = [
        "engine_display",
        "status_badge",
        "response_time_display",
        "error_code",
        "checked_at",
    ]

    list_filter = [
        "status",
        "engine__engine_type",
        "error_code",
    ]

    search_fields = [
        "error_message",
        "error_code",
    ]

    readonly_fields = [
        "engine",
        "status",
        "response_time",
        "error_message",
        "error_code",
        "checked_at",
    ]

    date_hierarchy = "checked_at"

    def engine_display(self, obj):
        """显示引擎"""
        return f"{obj.engine.engine_type} - {obj.engine.name}"

    engine_display.short_description = _("引擎")

    def status_badge(self, obj):
        """显示状态徽章"""
        return health_status_badge(obj.status)

    status_badge.short_description = _("状态")

    def response_time_display(self, obj):
        """显示响应时间"""
        if obj.response_time:
            return f"{obj.response_time:.0f} ms"
        return "-"

    response_time_display.short_description = _("响应时间")

    def has_add_permission(self, request):
        """禁用手动添加"""
        return False

    def has_change_permission(self, request, obj=None):
        """禁用手动修改"""
        return False


# ==================== EngineUsageLog Admin ====================


@admin.register(EngineUsageLog)
class EngineUsageLogAdmin(admin.ModelAdmin):
    """引擎使用日志"""

    list_display = [
        "engine_display",
        "provider",
        "request_type",
        "success_badge",
        "response_time_display",
        "cost_display",
        "created_at",
    ]

    list_filter = [
        "success",
        "request_type",
        "engine__engine_type",
        "provider",
    ]

    search_fields = [
        "project_id",
        "shot_id",
    ]

    readonly_fields = [
        "engine",
        "provider",
        "request_type",
        "success",
        "response_time",
        "token_count",
        "cost",
        "saved_cost",
        "project_id",
        "shot_id",
        "created_at",
    ]

    date_hierarchy = "created_at"

    def engine_display(self, obj):
        """显示引擎"""
        return f"{obj.engine.engine_type}"

    engine_display.short_description = _("引擎")

    def success_badge(self, obj):
        """显示成功状态"""
        icon = "✓" if obj.success else "✗"
        color = "green" if obj.success else "red"
        return format_html('<span style="color: {}; font-weight: bold;">{}</span>', color, icon)

    success_badge.short_description = _("状态")

    def response_time_display(self, obj):
        """显示响应时间"""
        return f"{obj.response_time:.0f} ms"

    response_time_display.short_description = _("响应时间")

    def cost_display(self, obj):
        """显示成本"""
        parts = []
        if obj.cost > 0:
            parts.append(f"${obj.cost:.4f}")
        if obj.saved_cost > 0:
            parts.append(f"(省 ${obj.saved_cost:.4f})")
        return " ".join(parts) if parts else "-"

    cost_display.short_description = _("成本")

    def has_add_permission(self, request):
        """禁用手动添加"""
        return False

    def has_change_permission(self, request, obj=None):
        """禁用手动修改"""
        return False


# ==================== FallbackEventLog Admin ====================


@admin.register(FallbackEventLog)
class FallbackEventLogAdmin(admin.ModelAdmin):
    """Fallback 事件日志"""

    list_display = [
        "engine_display",
        "switch_display",
        "reason_badge",
        "affected_requests",
        "occurred_at",
    ]

    list_filter = [
        "reason",
        "engine__engine_type",
    ]

    search_fields = [
        "reason_detail",
    ]

    readonly_fields = [
        "engine",
        "from_provider",
        "to_provider",
        "reason",
        "reason_detail",
        "affected_requests",
        "occurred_at",
    ]

    date_hierarchy = "occurred_at"

    def engine_display(self, obj):
        """显示引擎"""
        return f"{obj.engine.engine_type}"

    engine_display.short_description = _("引擎")

    def switch_display(self, obj):
        """显示切换路径"""
        return format_html("{} → {}", obj.from_provider, obj.to_provider)

    switch_display.short_description = _("切换路径")

    def reason_badge(self, obj):
        """显示原因徽章"""
        colors = {
            "timeout": "orange",
            "failure": "red",
            "manual": "blue",
            "error": "red",
        }
        color = colors.get(obj.reason, "gray")
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>', color, obj.get_reason_display()
        )

    reason_badge.short_description = _("原因")

    def has_add_permission(self, request):
        """禁用手动添加"""
        return False

    def has_change_permission(self, request, obj=None):
        """禁用手动修改"""
        return False
