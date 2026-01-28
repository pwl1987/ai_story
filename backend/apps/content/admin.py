"""内容生成Admin配置"""
from django.contrib import admin

from .models import (
    CameraMovement,
    ContentRewrite,
    GeneratedImage,
    GeneratedVideo,
    Storyboard,
)


@admin.register(ContentRewrite)
class ContentRewriteAdmin(admin.ModelAdmin):
    list_display = ['project', 'model_provider', 'created_at']
    search_fields = ['original_text', 'rewritten_text']


@admin.register(Storyboard)
class StoryboardAdmin(admin.ModelAdmin):
    list_display = ['project', 'sequence_number', 'duration_seconds', 'created_at']
    list_filter = ['created_at']
    ordering = ['project', 'sequence_number']


@admin.register(GeneratedImage)
class GeneratedImageAdmin(admin.ModelAdmin):
    list_display = ['storyboard', 'status', 'width', 'height', 'created_at']
    list_filter = ['status', 'created_at']


@admin.register(CameraMovement)
class CameraMovementAdmin(admin.ModelAdmin):
    list_display = ['storyboard', 'movement_type', 'model_provider', 'created_at']
    list_filter = ['movement_type']


@admin.register(GeneratedVideo)
class GeneratedVideoAdmin(admin.ModelAdmin):
    list_display = ['storyboard', 'status', 'duration', 'width', 'height', 'created_at']
    list_filter = ['status', 'created_at']
