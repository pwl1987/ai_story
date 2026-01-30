"""
用户管理Admin配置
"""

from django.contrib import admin

from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    """审计日志Admin

    Epic 8 Story 8.10: 操作日志

    功能:
    - 只读模式，禁止手动添加/修改/删除
    - 显示操作用户、操作类型、模型、对象
    - 支持按用户、操作类型、模型过滤
    """

    list_display = [
        "created_at",
        "user",
        "action",
        "model_name",
        "object_repr",
        "change_message",
    ]
    list_filter = ["action", "model_name", "created_at"]
    search_fields = ["user__username", "object_repr", "change_message", "model_name"]
    readonly_fields = [
        "created_at",
        "user",
        "action",
        "model_name",
        "object_id",
        "object_repr",
        "change_message",
    ]

    def has_add_permission(self, request):
        """禁止手动添加审计日志"""
        return False

    def has_change_permission(self, request, obj=None):
        """禁止修改审计日志"""
        return False

    def has_delete_permission(self, request, obj=None):
        """禁止删除审计日志"""
        return False


class AuditLogMixin:
    """
    Admin Mixin - 自动记录审计日志

    Epic 8 Story 8.10: 操作日志

    使用方法:
    在 ModelAdmin 中继承此 Mixin:

    class MyModelAdmin(AuditLogMixin, admin.ModelAdmin):
        ...
    """

    def save_model(self, request, obj, form, change):
        """保存模型并记录日志"""
        # 调用父类方法保存模型
        super().save_model(request, obj, form, change)

        # 记录审计日志
        from apps.users.models import AuditLog

        if change:
            action = "update"
            message = f"更新了 {obj}"
        else:
            action = "create"
            message = f"创建了 {obj}"

        AuditLog.objects.create(
            user=request.user,
            action=action,
            model_name=obj.__class__.__name__,
            object_id=str(obj.pk),
            object_repr=str(obj),
            change_message=message,
        )

    def delete_model(self, request, obj):
        """删除模型并记录日志"""
        # 记录对象信息（删除前）
        object_repr = str(obj)
        object_id = str(obj.pk)
        model_name = obj.__class__.__name__

        # 调用父类方法删除模型
        super().delete_model(request, obj)

        # 记录审计日志
        from apps.users.models import AuditLog

        AuditLog.objects.create(
            user=request.user,
            action="delete",
            model_name=model_name,
            object_id=object_id,
            object_repr=object_repr,
            change_message=f"删除了 {object_repr}",
        )

    def log_addition(self, request, obj, message):
        """记录添加操作（Django Admin 内部使用）"""
        # 调用父类方法
        return super().log_addition(request, obj, message)

    def log_change(self, request, obj, message):
        """记录修改操作（Django Admin 内部使用）"""
        # 调用父类方法
        return super().log_change(request, obj, message)

    def log_deletion(self, request, obj, object_repr):
        """记录删除操作（Django Admin 内部使用）"""
        # 调用父类方法
        return super().log_deletion(request, obj, object_repr)
