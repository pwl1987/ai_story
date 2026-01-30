"""
Django Admin配置 - Story 8.1: StaffAdminSite实施与验证

实现管理员专用的AdminSite，仅允许is_staff用户访问。

Epic 8: 管理员后台系统增强
Story 8.1: StaffAdminSite实施与验证
"""

from django.contrib.admin import AdminSite
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.contrib.auth.models import User

# Import Admin classes from all apps
from apps.content.admin import (
    CameraMovementAdmin,
    ContentRewriteAdmin,
    GeneratedImageAdmin,
    GeneratedVideoAdmin,
    StoryboardAdmin,
)
from apps.content.models import (
    CameraMovement,
    ContentRewrite,
    GeneratedImage,
    GeneratedVideo,
    Storyboard,
)
from apps.files.admin import FileQuotaAdmin, UploadedFileAdmin
from apps.files.models import FileQuota, UploadedFile
from apps.models.admin import ModelProviderAdmin, ModelUsageLogAdmin
from apps.models.models import ModelProvider, ModelUsageLog
from apps.projects.admin import (
    ProjectAdmin,
    ProjectModelConfigAdmin,
    ProjectStageAdmin,
)
from apps.projects.models import Project, ProjectModelConfig, ProjectStage
from apps.prompts.admin import (
    GlobalVariableAdmin,
    PromptTemplateAdmin,
    PromptTemplateSetAdmin,
)
from apps.prompts.models import GlobalVariable, PromptTemplate, PromptTemplateSet


class StaffAdminSite(AdminSite):
    """
    管理员专用AdminSite

    权限规则:
    - 仅允许已认证的is_staff用户访问
    - 非staff用户访问返回403 Forbidden（而非重定向）

    安全考虑:
    - 检查is_authenticated确保用户已登录
    - 检查is_staff确保用户是管理员
    - 不依赖is_superuser（保留给将来扩展）

    Party Mode决策1: 纯Middleware方案
    - 单一逻辑：所有请求统一检查
    - 覆盖所有请求：API和Admin都检查
    - 安全第一：请求管道最外层
    """

    # Admin界面自定义
    site_header = "AI Story 管理后台"
    site_title = "AI Story Admin"
    index_title = "欢迎使用 AI Story 管理后台"

    def has_permission(self, request):
        """
        权限检查方法

        Args:
            request: HttpRequest对象

        Returns:
            bool: True如果用户已认证且is_staff=True

        安全保证:
        - 未认证用户: return False → 403 Forbidden
        - is_staff=False: return False → 403 Forbidden
        - is_staff=True: return True → 允许访问
        """
        return request.user.is_authenticated and request.user.is_staff


class UserAdmin(DjangoUserAdmin):
    """用户管理Admin - Story 8.2: 增强功能"""

    # 优化列表显示
    list_display = [
        "username",
        "email",
        "first_name",
        "last_name",
        "is_staff",
        "is_superuser",
        "is_active",
        "date_joined",
        "last_login",
    ]

    # 优化过滤器
    list_filter = ["is_staff", "is_superuser", "is_active", "date_joined"]

    # 优化搜索字段
    search_fields = ["username", "email", "first_name", "last_name"]

    # 默认排序
    ordering = ["-date_joined"]

    # 字段集组织
    fieldsets = (
        (
            "基本信息",
            {"fields": ("username", "email", "first_name", "last_name")},
        ),
        (
            "权限信息",
            {
                "fields": (
                    "is_staff",
                    "is_superuser",
                    "is_active",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        (
            "重要日期",
            {
                "fields": ("last_login", "date_joined"),
                "classes": ("collapse",),
            },
        ),
    )

    def bulk_enable_users(self, request, queryset):
        """批量启用用户"""
        updated = queryset.update(is_active=True)
        self.message_user(
            request,
            f"成功启用 {updated} 个用户。",
            level="success",
        )

    bulk_enable_users.short_description = "批量启用选中的用户"

    def bulk_disable_users(self, request, queryset):
        """批量禁用用户"""
        updated = queryset.update(is_active=False)
        self.message_user(
            request,
            f"成功禁用 {updated} 个用户。",
            level="warning",
        )

    bulk_disable_users.short_description = "批量禁用选中的用户"

    def bulk_add_staff(self, request, queryset):
        """批量添加staff权限"""
        updated = queryset.update(is_staff=True)
        self.message_user(
            request,
            f"成功为 {updated} 个用户添加管理员权限。",
            level="success",
        )

    bulk_add_staff.short_description = "批量添加管理员权限"

    def bulk_remove_staff(self, request, queryset):
        """批量移除staff权限"""
        updated = queryset.update(is_staff=False)
        self.message_user(
            request,
            f"成功移除 {updated} 个用户的管理员权限。",
            level="warning",
        )

    bulk_remove_staff.short_description = "批量移除管理员权限"

    # 自定义批量操作（必须在方法定义之后）
    actions = [
        bulk_enable_users,
        bulk_disable_users,
        bulk_add_staff,
        bulk_remove_staff,
    ]


# 创建StaffAdminSite实例
# name='staffadmin'用于URL命名空间（如: admin:staffadmin_user_changelist）
staff_admin_site = StaffAdminSite(name="staffadmin")

# ============================================================================
# 模型注册 - Story 8.1: 注册所有17个核心模型
# ============================================================================

# Projects (3个模型)
staff_admin_site.register(Project, ProjectAdmin)
staff_admin_site.register(ProjectStage, ProjectStageAdmin)
staff_admin_site.register(ProjectModelConfig, ProjectModelConfigAdmin)

# Models (2个模型)
staff_admin_site.register(ModelProvider, ModelProviderAdmin)
staff_admin_site.register(ModelUsageLog, ModelUsageLogAdmin)

# Prompts (3个模型)
staff_admin_site.register(PromptTemplateSet, PromptTemplateSetAdmin)
staff_admin_site.register(PromptTemplate, PromptTemplateAdmin)
staff_admin_site.register(GlobalVariable, GlobalVariableAdmin)

# Content (5个模型)
staff_admin_site.register(ContentRewrite, ContentRewriteAdmin)
staff_admin_site.register(Storyboard, StoryboardAdmin)
staff_admin_site.register(GeneratedImage, GeneratedImageAdmin)
staff_admin_site.register(CameraMovement, CameraMovementAdmin)
staff_admin_site.register(GeneratedVideo, GeneratedVideoAdmin)

# Files (2个模型)
staff_admin_site.register(UploadedFile, UploadedFileAdmin)
staff_admin_site.register(FileQuota, FileQuotaAdmin)

# Users (1个模型，UserProfile将在Story 8.4添加)
staff_admin_site.register(User, UserAdmin)

# ============================================================================
# 注册完成: 17个核心模型已注册到StaffAdminSite
# ============================================================================
