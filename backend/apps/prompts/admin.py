"""提示词管理Admin配置"""

from django.contrib import admin

from .models import GlobalVariable, PromptTemplate, PromptTemplateSet


@admin.register(PromptTemplateSet)
class PromptTemplateSetAdmin(admin.ModelAdmin):
    list_display = [
        "system_resource_badge",
        "name",
        "is_active",
        "is_default",
        "created_by",
        "created_at",
    ]
    list_filter = ["is_active", "is_default", "is_system_default"]
    search_fields = ["name", "description"]
    readonly_fields = ["created_by"]

    def system_resource_badge(self, obj):
        """
        显示系统资源标记

        Epic 8 Story 8.6: 系统资源视觉标记

        Returns:
            str: HTML格式的标记
        """
        from django.utils.html import format_html

        if obj.is_system_default:
            return format_html('<span style="color: #D4AF37; font-weight: bold;">🌟 系统级</span>')
        return format_html('<span style="color: #808080;">👤 用户级</span>')

    system_resource_badge.short_description = "资源类型"

    def save_model(self, request, obj, form, change):
        """
        保存模型

        Epic 8 Story 8.6: 自动设置created_by
        """
        # 如果是新创建的对象，自动设置created_by为当前用户
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(PromptTemplate)
class PromptTemplateAdmin(admin.ModelAdmin):
    list_display = ["template_set", "stage_type", "version", "is_active", "created_at"]
    list_filter = ["stage_type", "is_active"]
    search_fields = ["template_content"]


@admin.register(GlobalVariable)
class GlobalVariableAdmin(admin.ModelAdmin):
    list_display = [
        "key",
        "variable_type",
        "scope",
        "group",
        "is_active",
        "created_by",
        "created_at",
    ]
    list_filter = ["variable_type", "scope", "group", "is_active"]
    search_fields = ["key", "description", "value"]
    readonly_fields = ["created_at", "updated_at"]
    fieldsets = (
        ("基本信息", {"fields": ("key", "value", "variable_type", "description")}),
        ("作用域和分组", {"fields": ("scope", "group", "is_active")}),
        (
            "元数据",
            {"fields": ("created_by", "created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )
