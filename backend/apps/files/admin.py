"""
文件管理Admin配置
Epic 6: 文件管理与预览
"""

from django.contrib import admin

from .models import FileQuota, UploadedFile


@admin.register(UploadedFile)
class UploadedFileAdmin(admin.ModelAdmin):
    """上传文件Admin"""

    list_display = [
        "id",
        "original_filename",
        "user",
        "file_type",
        "file_size_human",
        "mime_type",
        "uploaded_at",
        "is_active",
    ]
    list_filter = ["file_type", "uploaded_at", "is_active"]
    search_fields = ["original_filename", "file_hash", "user__username"]
    readonly_fields = [
        "id",
        "file_size",
        "mime_type",
        "file_hash",
        "uploaded_at",
    ]
    date_hierarchy = "uploaded_at"

    fieldsets = (
        ("基本信息", {"fields": ("user", "project", "original_filename", "file")}),
        ("文件属性", {"fields": ("file_type", "file_size", "mime_type", "file_hash")}),
        ("元数据", {"fields": ("uploaded_at", "uploaded_from", "is_active")}),
    )


@admin.register(FileQuota)
class FileQuotaAdmin(admin.ModelAdmin):
    """文件配额Admin"""

    list_display = [
        "user",
        "max_total_size_human",
        "used_total_size_human",
        "usage_percentage",
        "remaining_size_human",
        "used_file_count",
        "max_file_count",
    ]
    list_filter = ["updated_at"]
    search_fields = ["user__username"]
    readonly_fields = ["used_total_size", "used_file_count", "updated_at"]

    def max_total_size_human(self, obj):
        """人类可读的最大容量"""
        return f"{obj.max_total_size / (1024**3):.1f} GB"

    max_total_size_human.short_description = "最大容量"

    def used_total_size_human(self, obj):
        """人类可读的已用容量"""
        return f"{obj.used_total_size / (1024**2):.1f} MB"

    used_total_size_human.short_description = "已用容量"

    def remaining_size_human(self, obj):
        """人类可读的剩余容量"""
        return f"{obj.remaining_size / (1024**3):.1f} GB"

    remaining_size_human.short_description = "剩余容量"
