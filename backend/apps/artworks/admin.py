"""
漫剧生产系统 - Django Admin配置

遵循Django Admin最佳实践:
- 使用list_display优化列表页展示
- 使用search_fields添加搜索功能
- 使用list_filter添加过滤器
- 使用inline优化关联模型管理
- 使用actions批量操作
"""

from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from .models import (
    Artwork,
    Chapter,
    CharacterPose,
    CharacterProfile,
    CharacterVoiceConfig,
    EngineConfiguration,
    ItemProfile,
    PhysicalScene,
    ScriptScene,
    Shot,
)

# ========================================
# Inline Admins
# ========================================


class ChapterInline(admin.TabularInline):
    """章节内联"""

    model = Chapter
    fields = ["chapter_number", "title", "scene_count", "is_completed"]
    extra = 0
    show_change_link = True


class CharacterInline(admin.TabularInline):
    """角色内联"""

    model = CharacterProfile
    fields = ["name", "display_name", "appearance_count", "importance_rank"]
    extra = 0
    show_change_link = True


class SceneInline(admin.TabularInline):
    """场景内联"""

    model = ScriptScene
    fields = ["scene_number", "scene_name", "shot_count", "is_completed"]
    extra = 0
    show_change_link = True


class ShotInline(admin.TabularInline):
    """镜头内联"""

    model = Shot
    fields = ["shot_number", "shot_type", "content", "duration", "is_generated"]
    extra = 0


class PoseInline(admin.StackedInline):
    """角色造型内联"""

    model = CharacterPose
    fields = ["pose_name", "pose_type", "pose_image", "is_default", "usage_count"]
    extra = 0


class VoiceConfigInline(admin.StackedInline):
    """音色配置内联"""

    model = CharacterVoiceConfig
    fields = ["tts_engine", "voice_id", "pitch", "speed", "volume"]
    extra = 0
    can_delete = False


# ========================================
# Model Admins
# ========================================


@admin.register(Artwork)
class ArtworkAdmin(admin.ModelAdmin):
    """作品管理"""

    list_display = [
        "title",
        "author",
        "artwork_type",
        "total_chapters",
        "total_scenes",
        "total_shots",
        "progress_badge",
        "is_parsed",
        "created_at",
    ]
    list_filter = ["artwork_type", "is_parsed", "created_at"]
    search_fields = ["title", "author", "story_overview"]
    readonly_fields = ["created_at", "updated_at", "progress_percentage"]

    fieldsets = (
        (_("基本信息"), {"fields": ("title", "author", "artwork_type", "source_file")}),
        (_("AI分析"), {"fields": ("story_overview", "is_parsed", "parsing_status")}),
        (
            _("统计信息"),
            {"fields": ("total_chapters", "total_scenes", "total_shots", "progress_percentage")},
        ),
        (
            _("引擎配置"),
            {"fields": ("preferred_llm_engine", "preferred_image_engine", "preferred_tts_engine")},
        ),
        (_("时间信息"), {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )

    inlines = [ChapterInline, CharacterInline]

    def progress_badge(self, obj):
        """进度徽章"""
        percentage = obj.progress_percentage
        color = "red" if percentage < 30 else "orange" if percentage < 70 else "green"
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}%</span>', color, percentage
        )

    progress_badge.short_description = _("进度")


@admin.register(Chapter)
class ChapterAdmin(admin.ModelAdmin):
    """章节管理"""

    list_display = [
        "__str__",
        "artwork",
        "scene_count",
        "plot_summary_preview",
        "is_completed",
        "created_at",
    ]
    list_filter = ["is_completed", "created_at"]
    search_fields = ["title", "plot_summary", "artwork__title"]
    readonly_fields = ["created_at", "updated_at"]

    fieldsets = (
        (_("基本信息"), {"fields": ("artwork", "chapter_number", "title", "original_text")}),
        (_("AI分析"), {"fields": ("plot_summary", "character_mentions", "scene_count")}),
        (_("状态"), {"fields": ("is_completed",)}),
        (_("时间信息"), {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )

    inlines = [SceneInline]

    def plot_summary_preview(self, obj):
        """情节摘要预览"""
        return obj.plot_summary[:100] + "..." if len(obj.plot_summary) > 100 else obj.plot_summary

    plot_summary_preview.short_description = _("情节摘要")


@admin.register(PhysicalScene)
class PhysicalSceneAdmin(admin.ModelAdmin):
    """物理场景管理"""

    list_display = ["name", "category", "is_system_template", "usage_count", "preview_image"]
    list_filter = ["category", "is_system_template"]
    search_fields = ["name", "default_atmosphere", "prompt_template"]
    readonly_fields = ["created_at", "updated_at", "usage_count"]

    fieldsets = (
        (_("基本信息"), {"fields": ("category", "name", "is_system_template")}),
        (_("默认属性"), {"fields": ("default_lighting", "default_atmosphere")}),
        (_("视觉资产"), {"fields": ("background_image", "prompt_template")}),
        (_("统计"), {"fields": ("usage_count",)}),
        (_("时间信息"), {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )

    def preview_image(self, obj):
        """图片预览"""
        if obj.background_image:
            return format_html(
                '<img src="{}" style="max-width: 100px; max-height: 100px;" />',
                obj.background_image.url,
            )
        return _("无图片")

    preview_image.short_description = _("预览")


@admin.register(ScriptScene)
class ScriptSceneAdmin(admin.ModelAdmin):
    """剧本场景管理"""

    list_display = [
        "__str__",
        "physical_scene",
        "atmosphere",
        "time_of_day",
        "shot_count",
        "is_completed",
    ]
    list_filter = ["atmosphere", "time_of_day", "weather", "is_completed"]
    search_fields = ["scene_name", "description", "chapter__title"]
    readonly_fields = ["created_at", "updated_at"]

    fieldsets = (
        (
            _("基本信息"),
            {"fields": ("chapter", "physical_scene", "scene_number", "scene_name", "description")},
        ),
        (_("场景属性"), {"fields": ("atmosphere", "time_of_day", "weather")}),
        (_("首尾帧"), {"fields": ("head_frame", "tail_frame")}),
        (
            _("转场配置"),
            {"fields": ("transition_to_next", "transition_type", "transition_duration")},
        ),
        (_("状态"), {"fields": ("shot_count", "is_completed")}),
        (_("时间信息"), {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )

    inlines = [ShotInline]


@admin.register(Shot)
class ShotAdmin(admin.ModelAdmin):
    """镜头管理"""

    list_display = [
        "__str__",
        "shot_type",
        "speaker",
        "duration",
        "sort_order",
        "is_generated",
        "character_pose",
        "generation_retry_count",
    ]
    list_filter = ["shot_type", "is_generated", "character_pose"]
    search_fields = ["content", "speaker", "narration", "scene__scene_name"]
    readonly_fields = ["created_at", "updated_at", "generated_at"]

    fieldsets = (
        (_("基本信息"), {"fields": ("scene", "shot_number", "shot_type")}),
        (_("内容"), {"fields": ("content", "speaker", "narration")}),
        (
            _("视觉配置"),
            {
                "fields": (
                    "camera_movement",
                    "camera_movement_params",
                    "camera_angle",
                    "duration",
                    "sort_order",
                )
            },
        ),
        (_("构图配置"), {"fields": ("character_pose", "shot_composition")}),
        (
            _("生成结果"),
            {
                "fields": (
                    "generated_image",
                    "generated_audio",
                    "is_generated",
                    "generated_at",
                    "generation_error",
                    "generation_retry_count",
                )
            },
        ),
        (_("时间信息"), {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )


@admin.register(CharacterProfile)
class CharacterProfileAdmin(admin.ModelAdmin):
    """角色档案管理"""

    list_display = [
        "display_name",
        "name",
        "artwork",
        "appearance_count",
        "dialogue_count",
        "importance_rank",
        "portrait_preview",
    ]
    list_filter = ["artwork", "importance_rank"]
    search_fields = ["name", "display_name", "description", "personality"]
    readonly_fields = ["created_at", "updated_at"]

    fieldsets = (
        (_("基本信息"), {"fields": ("artwork", "name", "display_name")}),
        (_("统计信息"), {"fields": ("appearance_count", "dialogue_count", "importance_rank")}),
        (_("AI分析"), {"fields": ("description", "personality")}),
        (_("默认立绘"), {"fields": ("default_portrait",)}),
        (
            _("引擎偏好"),
            {"fields": ("preferred_llm_engine", "preferred_image_engine", "preferred_tts_engine")},
        ),
        (_("时间信息"), {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )

    inlines = [PoseInline, VoiceConfigInline]

    def portrait_preview(self, obj):
        """立绘预览"""
        if obj.default_portrait:
            return format_html(
                '<img src="{}" style="max-width: 80px; max-height: 120px;" />',
                obj.default_portrait.url,
            )
        return _("无立绘")

    portrait_preview.short_description = _("立绘")


@admin.register(CharacterPose)
class CharacterPoseAdmin(admin.ModelAdmin):
    """角色造型管理"""

    list_display = ["__str__", "pose_type", "is_default", "usage_count", "pose_preview"]
    list_filter = ["pose_type", "is_default"]
    search_fields = ["pose_name", "description", "character__display_name"]
    readonly_fields = ["created_at", "updated_at", "usage_count"]

    fieldsets = (
        (_("基本信息"), {"fields": ("character", "pose_name", "pose_type", "is_default")}),
        (_("造型图片"), {"fields": ("pose_image",)}),
        (_("适用场景"), {"fields": ("suitable_for_scenes",)}),
        (
            _("AI提取信息"),
            {"fields": ("extraction_source", "extracted_from_chapter", "description")},
        ),
        (_("统计"), {"fields": ("usage_count",)}),
        (_("时间信息"), {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )

    def pose_preview(self, obj):
        """造型预览"""
        if obj.pose_image:
            return format_html(
                '<img src="{}" style="max-width: 80px; max-height: 120px;" />', obj.pose_image.url
            )
        return _("无图片")

    pose_preview.short_description = _("造型")


@admin.register(CharacterVoiceConfig)
class CharacterVoiceConfigAdmin(admin.ModelAdmin):
    """角色音色配置管理"""

    list_display = ["__str__", "tts_engine", "voice_id", "pitch", "speed", "volume", "emotion_mode"]
    list_filter = ["tts_engine", "pitch", "speed", "volume"]
    search_fields = ["character__display_name", "voice_id", "voice_type"]
    readonly_fields = ["created_at", "updated_at"]

    fieldsets = (
        (_("基本信息"), {"fields": ("character", "tts_engine", "voice_id", "voice_type")}),
        (_("音色参数"), {"fields": ("pitch", "speed", "volume")}),
        (_("情感配置"), {"fields": ("emotion_mode", "emotion_intensity", "emotion_voices")}),
        (_("试听样本"), {"fields": ("voice_sample_url",)}),
        (_("时间信息"), {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )


@admin.register(ItemProfile)
class ItemProfileAdmin(admin.ModelAdmin):
    """物品档案管理"""

    list_display = [
        "name",
        "artwork",
        "item_type",
        "usage_count",
        "associated_character",
        "item_preview",
    ]
    list_filter = ["item_type", "artwork"]
    search_fields = ["name", "description", "appearance_context"]
    readonly_fields = ["created_at", "updated_at", "usage_count"]

    fieldsets = (
        (_("基本信息"), {"fields": ("artwork", "name", "item_type")}),
        (_("AI分析"), {"fields": ("description", "appearance_context")}),
        (_("物品图片"), {"fields": ("item_image",)}),
        (_("关联"), {"fields": ("associated_character", "first_appearance_chapter")}),
        (_("统计"), {"fields": ("usage_count",)}),
        (_("时间信息"), {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )

    def item_preview(self, obj):
        """物品预览"""
        if obj.item_image:
            return format_html(
                '<img src="{}" style="max-width: 80px; max-height: 80px;" />', obj.item_image.url
            )
        return _("无图片")

    item_preview.short_description = _("图片")


@admin.register(EngineConfiguration)
class EngineConfigurationAdmin(admin.ModelAdmin):
    """引擎配置管理"""

    list_display = [
        "__str__",
        "base_url",
        "model_name",
        "is_primary",
        "is_healthy",
        "last_check_at",
    ]
    list_filter = ["engine_type", "provider", "is_primary", "is_healthy"]
    search_fields = ["provider", "model_name", "base_url"]
    readonly_fields = ["created_at", "updated_at", "last_check_at", "is_healthy", "error_message"]

    fieldsets = (
        (_("基本信息"), {"fields": ("engine_type", "provider", "is_primary")}),
        (_("连接配置"), {"fields": ("base_url", "api_key", "model_name")}),
        (_("参数配置"), {"fields": ("config_params",)}),
        (_("健康状态"), {"fields": ("is_healthy", "last_check_at", "error_message")}),
        (_("时间信息"), {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )

    actions = ["test_health"]

    def test_health(self, request, queryset):
        """测试引擎健康状态"""
        # TODO: 实现健康检查逻辑
        self.message_user(request, _("健康检查功能待实现"))

    test_health.short_description = _("测试健康状态")
