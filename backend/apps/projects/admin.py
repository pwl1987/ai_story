"""项目管理Admin配置"""

from django.contrib import admin

from .models import Project, ProjectModelConfig, ProjectStage, ProjectTemplate


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ["name", "status", "proxy_config", "user", "created_at"]
    list_filter = ["status", "proxy_config", "created_at"]
    search_fields = ["name", "description"]
    fieldsets = (
        ("基本信息", {"fields": ("name", "description", "original_topic")}),
        (
            "配置",
            {"fields": ("prompt_template_set", "proxy_config")},
        ),
        ("状态", {"fields": ("status", "jianying_draft_path")}),
        ("元数据", {"fields": ("user", "created_at", "updated_at", "completed_at")}),
    )
    readonly_fields = ["created_at", "updated_at"]


@admin.register(ProjectStage)
class ProjectStageAdmin(admin.ModelAdmin):
    list_display = ["project", "stage_type", "status", "retry_count", "created_at"]
    list_filter = ["stage_type", "status"]


@admin.register(ProjectModelConfig)
class ProjectModelConfigAdmin(admin.ModelAdmin):
    list_display = ["project", "load_balance_strategy", "created_at"]


@admin.register(ProjectTemplate)
class ProjectTemplateAdmin(admin.ModelAdmin):
    """
    Story 11.4.3: 项目模板Admin配置
    """

    list_display = ["name", "is_system_template", "created_by", "created_at"]
    list_filter = ["is_system_template", "created_at"]
    search_fields = ["name", "description"]
    readonly_fields = ["created_at", "updated_at"]

    fieldsets = (
        ("基本信息", {"fields": ("name", "description")}),
        (
            "模板参数",
            {
                "fields": ("parameters",),
                "description": "模板参数JSON，包含: style, quality, aspect_ratio, llm_provider, image_provider, video_provider 等",
            },
        ),
        ("元数据", {"fields": ("is_system_template", "created_by", "created_at", "updated_at")}),
    )

    def has_delete_permission(self, request, obj=None):
        """
        系统预置模板不允许删除
        """
        if obj and obj.is_system_template:
            return False
        return super().has_delete_permission(request, obj)

    def has_change_permission(self, request, obj=None):
        """
        用户只能修改自己创建的模板，管理员可以修改所有模板
        """
        if obj and obj.is_system_template and not request.user.is_superuser:
            return False
        return super().has_change_permission(request, obj)
