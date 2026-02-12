"""
工作流序列化器 (Story 12-4 拆分 - workflow.py)

包含 ChapterWorkflow 和 WorkflowEvent 序列化器
"""

from rest_framework import serializers

from apps.artworks.models import ChapterWorkflow, WorkflowEvent


class ChapterWorkflowSerializer(serializers.ModelSerializer):
    """
    章节工作流序列化器 (Story 12-4)

    序列化 ChapterWorkflow 模型，包含状态显示和进度信息
    """

    status_display = serializers.CharField(source="get_status_display", read_only=True)
    current_scene_title = serializers.CharField(source="current_scene.scene_name", read_only=True, allow_null=True)
    chapter_title = serializers.CharField(source="chapter.title", read_only=True)
    elapsed_seconds = serializers.ReadOnlyField()
    is_active = serializers.ReadOnlyField()

    class Meta:
        model = ChapterWorkflow
        fields = [
            "workflow_id",
            "status",
            "status_display",
            "current_scene_title",
            "chapter_title",
            "total_scenes",
            "completed_scenes",
            "progress_percentage",
            "elapsed_seconds",
            "is_active",
            "started_at",
            "completed_at",
            "error_message",
            "celery_task_id",
        ]
        read_only_fields = ["workflow_id", "started_at", "completed_at", "elapsed_seconds", "is_active"]


class WorkflowEventSerializer(serializers.ModelSerializer):
    """
    工作流事件序列化器 (Story 12-4)

    序列化 WorkflowEvent 模型，用于工作流事件历史查询
    """

    event_type_display = serializers.CharField(source="get_event_type_display", read_only=True)
    severity_display = serializers.CharField(source="get_severity_display", read_only=True)
    scene_title = serializers.CharField(source="scene.scene_name", read_only=True, allow_null=True)
    message = serializers.CharField()
    metadata = serializers.JSONField()
    created_at = serializers.DateTimeField(read_only=True)

    class Meta:
        model = WorkflowEvent
        fields = [
            "id",
            "event_type",
            "event_type_display",
            "severity",
            "severity_display",
            "message",
            "metadata",
            "scene_title",
            "created_at",
        ]
        read_only_fields = ["created_at"]
