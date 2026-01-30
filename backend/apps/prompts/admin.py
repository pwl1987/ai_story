"""提示词管理Admin配置"""

from django.contrib import admin

from apps.users.admin import AuditLogMixin
from core.admin_mixins import SystemResourceBadgeMixin

from .models import GlobalVariable, PromptTemplate, PromptTemplateSet


@admin.register(PromptTemplateSet)
class PromptTemplateSetAdmin(SystemResourceBadgeMixin, AuditLogMixin, admin.ModelAdmin):
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

    def save_model(self, request, obj, form, change):
        """
        保存模型

        Epic 8 Story 8.6: 自动设置created_by
        """
        # 如果是新创建的对象，自动设置created_by为当前用户
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

    def has_change_permission(self, request, obj=None):
        """
        检查用户是否有change权限

        Epic 8 Story 8.8: 资源所有权与审计日志

        Args:
            request: HttpRequest对象
            obj: 模型实例（可选）

        Returns:
            bool: True如果有权限，False否则

        权限规则:
        - obj=None: 返回True（显示列表页）
        - obj存在: 创建者或superuser可以编辑
        """
        if obj is None:
            return True

        # superuser可以绕过所有限制
        if request.user.is_superuser:
            return True

        # 创建者可以编辑
        return obj.can_edit(request.user)

    def has_delete_permission(self, request, obj=None):
        """
        检查用户是否有delete权限

        Epic 8 Story 8.8: 资源所有权与审计日志

        Args:
            request: HttpRequest对象
            obj: 模型实例（可选）

        Returns:
            bool: True如果有权限，False否则

        权限规则:
        - obj=None: 返回True（显示列表页）
        - obj存在: 创建者或superuser可以删除
        """
        if obj is None:
            return True

        # superuser可以绕过所有限制
        if request.user.is_superuser:
            return True

        # 创建者可以删除
        return obj.created_by == request.user


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
