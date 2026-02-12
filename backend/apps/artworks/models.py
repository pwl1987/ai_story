"""
漫剧生产系统 - 数据模型

遵循SOLID原则:
- 单一职责: 每个模型只负责一个领域实体
- 开闭原则: 通过AbstractBase类支持扩展
- 依赖倒置: 依赖抽象的配置层而非具体实现

层次结构:
Artwork (作品)
  └── Chapter (章节)
      └── ScriptScene (剧本场景)
          └── Shot (镜头)

PhysicalScene (物理场景模板) ← ScriptScene继承

CharacterProfile (角色档案)
  ├── CharacterPose (角色造型)
  └── CharacterVoiceConfig (音色配置)

ItemProfile (物品档案)
"""

import json
import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator, MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

# 引擎选择常量 (全局)
ENGINE_CHOICES = [
    ("ollama", _("Ollama (本地LLM)")),
    ("openai", _("OpenAI")),
    ("claude", _("Claude")),
    ("comfyui", _("ComfyUI (本地图像)")),
    ("dalle", _("DALL-E")),
    ("sd", _("Stable Diffusion API")),
    ("edge", _("Edge-TTS (本地语音)")),
    ("elevenlabs", _("ElevenLabs")),
    ("baidu", _("百度TTS")),
]


class TimeStampedModel(models.Model):
    """时间戳抽象基类"""

    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("创建时间"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("更新时间"))

    class Meta:
        abstract = True


class EngineConfigModel(models.Model):
    """引擎配置抽象基类"""

    class Meta:
        abstract = True


# ========================================
# 核心结构: Artwork → Chapter → ScriptScene → Shot
# ========================================


class Artwork(TimeStampedModel, EngineConfigModel):
    """
    作品 (Artwork)

    漫剧生产系统的顶层实体,代表一部完整的小说/剧本作品

    职责:
    - 存储作品元数据
    - 引擎策略配置
    - 统计信息追踪
    """

    ARTWORK_TYPE_CHOICES = [
        ("novel", _("小说")),
        ("script", _("剧本")),
        ("webnovel", _("网络小说")),
        ("comic", _("漫画脚本")),
    ]

    # 基本信息
    title = models.CharField(max_length=500, verbose_name=_("作品标题"))
    author = models.CharField(max_length=200, blank=True, verbose_name=_("作者"))
    artwork_type = models.CharField(
        max_length=20, choices=ARTWORK_TYPE_CHOICES, default="novel", verbose_name=_("作品类型")
    )

    # 源文件
    source_file = models.FileField(
        upload_to="artworks/sources/",
        blank=True,
        null=True,
        validators=[FileExtensionValidator(allowed_extensions=["txt", "md", "pdf", "docx"])],
        verbose_name=_("源文件"),
    )

    # AI分析结果
    story_overview = models.TextField(blank=True, verbose_name=_("故事概要"))
    total_chapters = models.IntegerField(default=0, verbose_name=_("总章节数"))
    total_scenes = models.IntegerField(default=0, verbose_name=_("总场景数"))
    total_shots = models.IntegerField(default=0, verbose_name=_("总镜头数"))

    # 引擎配置 (继承自EngineConfigModel)
    preferred_llm_engine = models.CharField(
        max_length=50, choices=ENGINE_CHOICES, default="ollama", verbose_name=_("首选LLM引擎")
    )
    preferred_image_engine = models.CharField(
        max_length=50, choices=ENGINE_CHOICES, default="comfyui", verbose_name=_("首选图像引擎")
    )
    preferred_tts_engine = models.CharField(
        max_length=50, choices=ENGINE_CHOICES, default="edge", verbose_name=_("首选TTS引擎")
    )

    # 状态
    is_parsed = models.BooleanField(default=False, verbose_name=_("已解析"))
    parsing_status = models.CharField(max_length=50, default="pending", verbose_name=_("解析状态"))

    class Meta:
        db_table = "artworks"
        verbose_name = _("作品")
        verbose_name_plural = _("作品")
        ordering = ["-created_at"]

    def __str__(self):
        return self.title

    @property
    def progress_percentage(self):
        """计算完成进度"""
        if self.total_chapters == 0:
            return 0
        completed = self.chapters.filter(is_completed=True).count()
        return round((completed / self.total_chapters) * 100, 2)


class Chapter(TimeStampedModel):
    """
    章节 (Chapter)

    作品的章节划分,代表叙事的独立单元

    职责:
    - 存储章节文本内容
    - 章节元数据管理
    - 关联所有剧本场景
    """

    artwork = models.ForeignKey(
        Artwork, on_delete=models.CASCADE, related_name="chapters", verbose_name=_("所属作品")
    )

    # 章节信息
    chapter_number = models.IntegerField(verbose_name=_("章节序号"))
    title = models.CharField(max_length=500, verbose_name=_("章节标题"))
    original_text = models.TextField(verbose_name=_("原文内容"))

    # AI分析
    plot_summary = models.TextField(blank=True, verbose_name=_("情节摘要"))
    character_mentions = models.JSONField(default=list, verbose_name=_("出场角色"))
    scene_count = models.IntegerField(default=0, verbose_name=_("场景数"))

    # 状态
    is_completed = models.BooleanField(default=False, verbose_name=_("已完成"))

    class Meta:
        db_table = "chapters"
        verbose_name = _("章节")
        verbose_name_plural = _("章节")
        ordering = ["artwork", "chapter_number"]
        unique_together = [["artwork", "chapter_number"]]

    def __str__(self):
        return f"第{self.chapter_number}章: {self.title}"


class PhysicalScene(TimeStampedModel):
    """
    物理场景 (PhysicalScene)

    可复用的环境类型模板,例如"实验室"、"家庭"、"街道"

    职责:
    - 定义场景模板属性
    - 提供默认配置(光照、氛围)
    - 支持场景资产复用
    """

    CATEGORY_CHOICES = [
        ("indoor", _("室内")),
        ("outdoor", _("室外")),
        ("abstract", _("抽象")),
    ]

    # 基本信息
    category = models.CharField(
        max_length=50, choices=CATEGORY_CHOICES, default="indoor", verbose_name=_("场景类别")
    )
    name = models.CharField(max_length=200, verbose_name=_("场景名称"))

    # 默认属性 (可被ScriptScene覆盖)
    default_lighting = models.CharField(max_length=50, blank=True, verbose_name=_("默认光照"))
    default_atmosphere = models.CharField(max_length=50, blank=True, verbose_name=_("默认氛围"))

    # 视觉资产
    background_image = models.ImageField(
        upload_to="physical_scenes/", blank=True, verbose_name=_("背景图片")
    )

    # AI生成配置
    prompt_template = models.TextField(blank=True, verbose_name=_("提示词模板"))

    # 系统模板标识
    is_system_template = models.BooleanField(default=False, verbose_name=_("系统模板"))
    usage_count = models.IntegerField(default=0, verbose_name=_("使用次数"))

    class Meta:
        db_table = "physical_scenes"
        verbose_name = _("物理场景")
        verbose_name_plural = _("物理场景")
        ordering = ["-usage_count", "name"]

    def __str__(self):
        return self.name

    def increment_usage(self):
        """增加使用计数"""
        self.usage_count += 1
        self.save(update_fields=["usage_count"])


class ScriptScene(TimeStampedModel):
    """
    剧本场景 (ScriptScene)

    具体的故事场景实例,继承PhysicalScene的属性

    职责:
    - 表示具体的叙事场景
    - 覆盖物理场景的默认属性
    - 管理首尾帧用于转场
    """

    chapter = models.ForeignKey(
        Chapter, on_delete=models.CASCADE, related_name="scenes", verbose_name=_("所属章节")
    )

    physical_scene = models.ForeignKey(
        PhysicalScene,
        on_delete=models.SET_NULL,
        null=True,
        related_name="script_scenes",
        verbose_name=_("物理场景模板"),
    )

    # 场景信息
    scene_number = models.IntegerField(verbose_name=_("场景序号"))
    scene_name = models.CharField(max_length=200, verbose_name=_("场景名称"))
    description = models.TextField(verbose_name=_("场景描述"))

    # 覆盖物理场景的默认属性
    atmosphere = models.CharField(max_length=50, blank=True, verbose_name=_("氛围"))
    time_of_day = models.CharField(max_length=50, blank=True, verbose_name=_("时间"))
    weather = models.CharField(max_length=50, blank=True, verbose_name=_("天气"))

    # 首尾帧 (用于转场)
    head_frame = models.ImageField(upload_to="scenes/heads/", blank=True, verbose_name=_("首帧"))
    tail_frame = models.ImageField(upload_to="scenes/tails/", blank=True, verbose_name=_("尾帧"))

    # 转场配置
    transition_to_next = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="transition_from_prev",
        verbose_name=_("转场目标"),
    )
    TRANSITION_TYPE_CHOICES = [
        ("fade", _("淡入淡出")),
        ("dissolve", _("溶解")),
        ("wipe", _("擦除")),
        ("cut", _("切镜")),
    ]
    transition_type = models.CharField(
        max_length=20, choices=TRANSITION_TYPE_CHOICES, blank=True, verbose_name=_("转场类型")
    )
    transition_duration = models.FloatField(default=1.5, verbose_name=_("转场时长(秒)"))

    # 状态
    shot_count = models.IntegerField(default=0, verbose_name=_("镜头数"))
    is_completed = models.BooleanField(default=False, verbose_name=_("已完成"))

    class Meta:
        db_table = "script_scenes"
        verbose_name = _("剧本场景")
        verbose_name_plural = _("剧本场景")
        ordering = ["chapter", "scene_number"]
        unique_together = [["chapter", "scene_number"]]

    def __str__(self):
        return f"{self.chapter.title} - {self.scene_name}"

    def clean(self):
        """
        验证业务逻辑 (Story 11.2.1)

        验证:
        - 设置转场类型时必须指定转场目标场景
        - 转场时长必须在 0-10 秒之间
        """
        from django.core.exceptions import ValidationError

        super().clean()

        # 验证转场配置
        if self.transition_type and not self.transition_to_next:
            raise ValidationError({"transition_to_next": _("设置转场类型时必须指定转场目标场景")})

        # 验证转场时长
        if self.transition_duration is not None:
            if not (0 <= self.transition_duration <= 10):
                raise ValidationError({"transition_duration": _("转场时长必须在0-10秒之间")})


class Shot(TimeStampedModel):
    """
    镜头 (Shot)

    最小的叙事单元,代表一个连续的视觉片段

    职责:
    - 存储镜头内容(对话/旁白/动作)
    - 关联角色、场景、物品
    - 配置运镜效果
    """

    scene = models.ForeignKey(
        ScriptScene, on_delete=models.CASCADE, related_name="shots", verbose_name=_("所属场景")
    )

    # 镜头信息
    shot_number = models.IntegerField(verbose_name=_("镜头序号"))
    shot_type = models.CharField(
        max_length=50, verbose_name=_("镜头类型")
    )  # dialogue/narration/action

    # 内容
    content = models.TextField(verbose_name=_("镜头内容"))
    speaker = models.CharField(max_length=200, blank=True, verbose_name=_("说话人"))
    narration = models.TextField(blank=True, verbose_name=_("旁白"))

    # 视觉配置
    camera_movement = models.CharField(max_length=50, blank=True, verbose_name=_("运镜"))
    camera_angle = models.CharField(max_length=50, blank=True, verbose_name=_("镜头角度"))
    duration = models.FloatField(default=3.0, verbose_name=_("时长(秒)"))

    # 生成结果
    generated_image = models.ImageField(
        upload_to="shots/images/", blank=True, verbose_name=_("生成的画面")
    )
    generated_audio = models.FileField(
        upload_to="shots/audio/", blank=True, verbose_name=_("生成的语音")
    )

    # 排序
    sort_order = models.IntegerField(default=0, verbose_name=_("排序"))

    # 状态
    is_generated = models.BooleanField(default=False, verbose_name=_("已生成"))

    # 角色造型关联 (Story 11.2.2)
    character_pose = models.ForeignKey(
        "CharacterPose",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="shots",
        verbose_name=_("角色造型"),
        help_text=_("镜头中使用的角色造型"),
    )

    # 运镜参数 (Story 11.2.2)
    camera_movement_params = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_("运镜参数"),
        help_text=_('运镜详细参数，JSON格式: {"zoom": "1.5x", "pan": "left", "speed": "medium"}'),
    )

    # 构图描述 (Story 11.2.2)
    shot_composition = models.TextField(
        blank=True, verbose_name=_("构图描述"), help_text=_("镜头构图和布局的详细描述")
    )

    # 生成状态追踪 (Story 11.2.2)
    generated_at = models.DateTimeField(null=True, blank=True, verbose_name=_("生成时间"))
    generation_error = models.TextField(blank=True, verbose_name=_("生成错误"))
    generation_retry_count = models.IntegerField(
        default=0, validators=[MinValueValidator(0)], verbose_name=_("重试次数")
    )

    class Meta:
        db_table = "shots"
        verbose_name = _("镜头")
        verbose_name_plural = _("镜头")
        ordering = ["scene", "sort_order", "shot_number"]
        unique_together = [["scene", "shot_number"]]

    def __str__(self):
        return f"镜头{self.shot_number}: {self.content[:30]}"

    def clean(self):
        """
        验证业务逻辑 (Story 11.2.2)

        验证:
        - 运镜参数 JSON 格式
        - 重试次数不能为负数
        """
        super().clean()

        # 验证运镜参数 JSON 格式
        if self.camera_movement_params:
            try:
                json.dumps(self.camera_movement_params)
            except (TypeError, ValueError) as e:
                raise ValidationError(
                    {"camera_movement_params": _("运镜参数格式错误: %(error)s") % {"error": str(e)}}
                )

    @property
    def is_successfully_generated(self):
        """是否成功生成 (Story 11.2.2)"""
        return self.is_generated and self.generation_error == ""


# ========================================
# 角色管理: CharacterProfile → CharacterPose + CharacterVoiceConfig
# ========================================


class CharacterProfile(TimeStampedModel, EngineConfigModel):
    """
    角色档案 (CharacterProfile)

    角色的主档案,管理角色的基本信息和AI分析结果

    职责:
    - 存储角色元数据
    - 统计角色出场次数
    - 关联多套造型和音色配置
    """

    artwork = models.ForeignKey(
        Artwork, on_delete=models.CASCADE, related_name="characters", verbose_name=_("所属作品")
    )

    # 基本信息
    name = models.CharField(max_length=200, verbose_name=_("角色名"))
    display_name = models.CharField(max_length=200, verbose_name=_("显示名"))

    # 统计信息
    appearance_count = models.IntegerField(default=0, verbose_name=_("出场次数"))
    dialogue_count = models.IntegerField(default=0, verbose_name=_("对话数"))

    # AI分析
    description = models.TextField(blank=True, verbose_name=_("角色描述"))
    personality = models.TextField(blank=True, verbose_name=_("性格特点"))

    # 默认立绘
    default_portrait = models.ImageField(
        upload_to="characters/portraits/", blank=True, verbose_name=_("默认立绘")
    )

    # 引擎偏好
    preferred_llm_engine = models.CharField(
        max_length=50, choices=ENGINE_CHOICES, default="ollama", verbose_name=_("首选LLM引擎")
    )
    preferred_tts_engine = models.CharField(
        max_length=50, choices=ENGINE_CHOICES, default="edge", verbose_name=_("首选TTS引擎")
    )
    preferred_image_engine = models.CharField(
        max_length=50, choices=ENGINE_CHOICES, default="comfyui", verbose_name=_("首选图像引擎")
    )

    # 排序
    importance_rank = models.IntegerField(default=0, verbose_name=_("重要性排名"))

    class Meta:
        db_table = "character_profiles"
        verbose_name = _("角色档案")
        verbose_name_plural = _("角色档案")
        ordering = ["artwork", "importance_rank", "-appearance_count"]
        unique_together = [["artwork", "name"]]

    def __str__(self):
        return f"{self.display_name} ({self.artwork.title})"


class CharacterPose(TimeStampedModel):
    """
    角色造型 (CharacterPose)

    同一角色的多套服装/姿态造型

    职责:
    - 管理角色的多套造型
    - AI自动提取造型信息
    - 适配不同场景需求
    """

    POSE_TYPE_CHOICES = [
        ("casual", _("休闲")),
        ("formal", _("正式")),
        ("battle", _("战斗")),
        ("school", _("校园")),
        ("home", _("居家")),
        ("custom", _("自定义")),
    ]

    character = models.ForeignKey(
        CharacterProfile, on_delete=models.CASCADE, related_name="poses", verbose_name=_("所属角色")
    )

    # 造型信息
    pose_name = models.CharField(max_length=200, verbose_name=_("造型名称"))  # "家庭装", "宴会装"
    pose_type = models.CharField(
        max_length=20, choices=POSE_TYPE_CHOICES, default="casual", verbose_name=_("造型类型")
    )

    # 视觉资产
    pose_image = models.ImageField(upload_to="characters/poses/", verbose_name=_("造型图片"))

    # 适用场景
    suitable_for_scenes = models.JSONField(
        default=list, verbose_name=_("适用场景"), help_text=_("场景关键词列表,如['家', '室内']")
    )

    # AI提取信息
    extraction_source = models.CharField(
        max_length=50, blank=True, verbose_name=_("提取来源")
    )  # "AI_extracted", "manual"
    extracted_from_chapter = models.IntegerField(
        null=True, blank=True, verbose_name=_("提取自章节")
    )
    description = models.TextField(blank=True, verbose_name=_("造型描述"))

    # 使用统计
    usage_count = models.IntegerField(default=0, verbose_name=_("使用次数"))
    is_default = models.BooleanField(default=False, verbose_name=_("默认造型"))

    class Meta:
        db_table = "character_poses"
        verbose_name = _("角色造型")
        verbose_name_plural = _("角色造型")
        ordering = ["-is_default", "-usage_count", "pose_name"]

    def __str__(self):
        return f"{self.character.display_name} - {self.pose_name}"

    def increment_usage(self):
        """增加使用计数"""
        self.usage_count += 1
        self.save(update_fields=["usage_count"])


class CharacterVoiceConfig(TimeStampedModel):
    """
    角色音色配置 (CharacterVoiceConfig)

    为每个角色配置专属的TTS音色参数

    职责:
    - TTS引擎选择
    - 音色参数调优
    - 情感音色映射
    """

    TTS_ENGINE_CHOICES = [
        ("edge", _("Edge-TTS (本地)")),
        ("elevenlabs", _("ElevenLabs")),
        ("baidu", _("百度TTS")),
        ("azure", _("Azure TTS")),
    ]

    EMOTION_CHOICES = [
        ("neutral", _("中性")),
        ("happy", _("开心")),
        ("sad", _("悲伤")),
        ("angry", _("愤怒")),
        ("excited", _("兴奋")),
        ("calm", _("平静")),
    ]

    character = models.OneToOneField(
        CharacterProfile,
        on_delete=models.CASCADE,
        related_name="voice_config",
        verbose_name=_("所属角色"),
    )

    # TTS引擎
    tts_engine = models.CharField(
        max_length=20, choices=TTS_ENGINE_CHOICES, default="edge", verbose_name=_("TTS引擎")
    )
    voice_id = models.CharField(max_length=100, blank=True, verbose_name=_("音色ID"))

    # 音色参数
    voice_type = models.CharField(max_length=100, blank=True, verbose_name=_("音色类型"))
    PITCH_CHOICES = [
        ("very_low", _("极低")),
        ("low", _("低")),
        ("normal", _("正常")),
        ("high", _("高")),
        ("very_high", _("极高")),
    ]
    pitch = models.CharField(
        max_length=20, choices=PITCH_CHOICES, default="normal", verbose_name=_("音调")
    )
    SPEED_CHOICES = [
        ("very_slow", _("极慢")),
        ("slow", _("慢")),
        ("normal", _("正常")),
        ("fast", _("快")),
        ("very_fast", _("极快")),
    ]
    speed = models.CharField(
        max_length=20, choices=SPEED_CHOICES, default="normal", verbose_name=_("语速")
    )
    VOLUME_CHOICES = [
        ("very_soft", _("极小")),
        ("soft", _("小")),
        ("normal", _("正常")),
        ("loud", _("大")),
        ("very_loud", _("极大")),
    ]
    volume = models.CharField(
        max_length=20, choices=VOLUME_CHOICES, default="normal", verbose_name=_("音量")
    )

    # 情感配置
    emotion_mode = models.CharField(max_length=50, blank=True, verbose_name=_("情感模式"))
    emotion_intensity = models.CharField(
        max_length=20, default="medium", verbose_name=_("情感强度")
    )

    # 情感音色映射
    # 格式: {"happy": "voice_id_1", "sad": "voice_id_2", ...}
    emotion_voices = models.JSONField(default=dict, verbose_name=_("情感音色映射"), blank=True)

    # 试听样本
    voice_sample_url = models.URLField(blank=True, verbose_name=_("试听样本URL"))

    class Meta:
        db_table = "character_voice_configs"
        verbose_name = _("角色音色配置")
        verbose_name_plural = _("角色音色配置")

    def __str__(self):
        return f"{self.character.display_name} - {self.tts_engine}"


# ========================================
# 物品管理: ItemProfile
# ========================================


class ItemProfile(TimeStampedModel):
    """
    物品档案 (ItemProfile)

    故事中出现的物品、道具、武器的管理

    职责:
    - 提取物品信息
    - 生成物品图片
    - 追踪物品使用
    """

    ITEM_TYPE_CHOICES = [
        ("prop", _("道具")),
        ("weapon", _("武器")),
        ("vehicle", _("载具")),
        ("tool", _("工具")),
        ("accessory", _("饰品")),
        ("other", _("其他")),
    ]

    artwork = models.ForeignKey(
        Artwork, on_delete=models.CASCADE, related_name="items", verbose_name=_("所属作品")
    )

    # 基本信息
    name = models.CharField(max_length=200, verbose_name=_("物品名称"))
    item_type = models.CharField(
        max_length=20, choices=ITEM_TYPE_CHOICES, default="prop", verbose_name=_("物品类型")
    )

    # AI分析
    description = models.TextField(blank=True, verbose_name=_("物品描述"))
    appearance_context = models.TextField(blank=True, verbose_name=_("出现场景"))

    # 视觉资产
    item_image = models.ImageField(upload_to="items/", blank=True, verbose_name=_("物品图片"))

    # 统计
    usage_count = models.IntegerField(default=0, verbose_name=_("使用次数"))
    first_appearance_chapter = models.IntegerField(
        null=True, blank=True, verbose_name=_("首次出现章节")
    )

    # 关联角色 (可选)
    associated_character = models.ForeignKey(
        CharacterProfile,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="items",
        verbose_name=_("关联角色"),
    )

    class Meta:
        db_table = "item_profiles"
        verbose_name = _("物品档案")
        verbose_name_plural = _("物品档案")
        ordering = ["-usage_count", "name"]

    def __str__(self):
        return f"{self.name} ({self.artwork.title})"

    def increment_usage(self):
        """增加使用计数"""
        self.usage_count += 1
        self.save(update_fields=["usage_count"])


# ========================================
# 引擎全局配置
# ========================================


class EngineConfiguration(TimeStampedModel):
    """
    引擎全局配置 (EngineConfiguration)

    系统级别的AI引擎配置,支持Fallback机制

    职责:
    - 配置主引擎和备份引擎
    - 存储API密钥和端点
    - 测试引擎可用性
    """

    ENGINE_TYPE_CHOICES = [
        ("llm", _("LLM引擎")),
        ("image", _("图像引擎")),
        ("tts", _("TTS引擎")),
    ]

    PROVIDER_CHOICES = [
        ("ollama", _("Ollama")),
        ("openai", _("OpenAI")),
        ("claude", _("Claude")),
        ("comfyui", _("ComfyUI")),
        ("dalle", _("DALL-E")),
        ("sd", _("Stable Diffusion")),
        ("edge", _("Edge-TTS")),
        ("elevenlabs", _("ElevenLabs")),
        ("baidu", _("百度TTS")),
    ]

    engine_type = models.CharField(
        max_length=10, choices=ENGINE_TYPE_CHOICES, verbose_name=_("引擎类型")
    )
    provider = models.CharField(max_length=20, choices=PROVIDER_CHOICES, verbose_name=_("提供商"))
    is_primary = models.BooleanField(default=True, verbose_name=_("主引擎"))

    # 连接配置
    base_url = models.URLField(blank=True, verbose_name=_("基础URL"))
    api_key = models.CharField(max_length=500, blank=True, verbose_name=_("API密钥"))
    model_name = models.CharField(max_length=100, blank=True, verbose_name=_("模型名称"))

    # 参数配置 (JSON格式)
    config_params = models.JSONField(default=dict, verbose_name=_("配置参数"))

    # 健康检查
    is_healthy = models.BooleanField(default=False, verbose_name=_("健康"))
    last_check_at = models.DateTimeField(null=True, blank=True, verbose_name=_("最后检查时间"))
    error_message = models.TextField(blank=True, verbose_name=_("错误信息"))

    class Meta:
        db_table = "engine_configurations"
        verbose_name = _("引擎配置")
        verbose_name_plural = _("引擎配置")
        unique_together = [["engine_type", "provider", "is_primary"]]

    def __str__(self):
        is_primary = "主" if self.is_primary else "备"
        return f"{self.get_engine_type_display()} - {self.get_provider_display()} ({is_primary})"


# ========================================
# 角色资产生成管理 (Story 11.1.4)
# ========================================


class GenerationProgress(TimeStampedModel):
    """
    生成进度追踪 (GenerationProgress)

    职责:
    - 追踪批量生成任务的进度
    - 记录成功/失败数量
    - 关联Celery任务ID
    - 支持WebSocket实时通知

    Story 11.1.4: 角色资产批量生成
    """

    STATUS_CHOICES = [
        ("pending", _("等待中")),
        ("processing", _("处理中")),
        ("completed", _("已完成")),
        ("failed", _("失败")),
        ("cancelled", _("已取消")),
    ]

    GENERATION_TYPE_CHOICES = [
        ("portrait", _("立绘生成")),
        ("voice", _("音色生成")),
        ("batch", _("批量生成")),
        ("pose_recommendation", _("造型推荐")),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="generation_progress",
        verbose_name=_("用户"),
    )
    generation_type = models.CharField(
        max_length=50, choices=GENERATION_TYPE_CHOICES, verbose_name=_("生成类型")
    )
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="pending", verbose_name=_("状态")
    )

    # 进度统计
    total_items = models.IntegerField(default=0, verbose_name=_("总项目数"))
    completed_items = models.IntegerField(default=0, verbose_name=_("完成项目数"))
    failed_items = models.IntegerField(default=0, verbose_name=_("失败项目数"))

    # Celery任务关联
    celery_task_id = models.CharField(max_length=255, blank=True, verbose_name=_("Celery任务ID"))
    error_message = models.TextField(blank=True, verbose_name=_("错误信息"))

    # 时间戳
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name=_("完成时间"))

    class Meta:
        db_table = "generation_progress"
        verbose_name = _("生成进度")
        verbose_name_plural = _("生成进度")
        ordering = ["-created_at"]

    def __str__(self):
        return (
            f"{self.get_generation_type_display()} - "
            f"{self.get_status_display()} "
            f"({self.completed_items}/{self.total_items})"
        )

    @property
    def progress_percentage(self) -> float:
        """计算进度百分比"""
        if self.total_items == 0:
            return 0.0
        return (self.completed_items / self.total_items) * 100

    def update_progress(self, completed: int = 0, failed: int = 0, status: str = None) -> None:
        """更新进度"""
        if completed:
            self.completed_items += completed
        if failed:
            self.failed_items += failed
        if status:
            self.status = status
        if self.completed_items + self.failed_items >= self.total_items and self.total_items > 0:
            self.status = "completed"
            self.completed_at = timezone.now()
        self.save()


class GenerationHistory(TimeStampedModel):
    """
    生成历史记录 (GenerationHistory)

    职责:
    - 记录每次生成的参数和结果
    - 支持用户质量评分
    - 支持重新生成
    - 记录最佳参数推荐

    Story 11.1.4: 角色资产批量生成
    """

    GENERATION_TYPE_CHOICES = [
        ("portrait", _("立绘")),
        ("voice", _("音色")),
        ("pose_recommendation", _("造型推荐")),
    ]

    character = models.ForeignKey(
        CharacterProfile,
        on_delete=models.CASCADE,
        related_name="generation_history",
        verbose_name=_("角色"),
    )
    generation_type = models.CharField(
        max_length=50, choices=GENERATION_TYPE_CHOICES, verbose_name=_("生成类型")
    )

    # 生成参数
    prompt_params = models.JSONField(default=dict, verbose_name=_("提示词参数"), blank=True)
    voice_params = models.JSONField(default=dict, verbose_name=_("音色参数"), blank=True)

    # 生成结果
    result_url = models.URLField(blank=True, verbose_name=_("结果URL"))

    # 质量评分
    quality_rating = models.IntegerField(
        null=True, blank=True, verbose_name=_("质量评分"), help_text=_("1-5星")
    )
    user_feedback = models.TextField(blank=True, verbose_name=_("用户反馈"))

    # 统计
    is_used = models.BooleanField(default=False, verbose_name=_("是否被采用"))
    regeneration_count = models.IntegerField(default=0, verbose_name=_("重新生成次数"))

    class Meta:
        db_table = "generation_history"
        verbose_name = _("生成历史")
        verbose_name_plural = _("生成历史")
        ordering = ["-created_at"]

    def __str__(self):
        rating_display = f"⭐{self.quality_rating}" if self.quality_rating else "未评分"
        return (
            f"{self.character.display_name} - "
            f"{self.get_generation_type_display()} - {rating_display}"
        )

    def rate(self, rating: int, feedback: str = "") -> None:
        """评分"""
        if 1 <= rating <= 5:
            self.quality_rating = rating
            self.user_feedback = feedback
            self.save()

    def mark_as_used(self) -> None:
        """标记为已采用"""
        self.is_used = True
        self.save()

    def increment_regeneration_count(self) -> None:
        """增加重新生成次数"""
        self.regeneration_count += 1
        self.save()


# ========================================
# 版本管理 (Story 11.5.2)
# ========================================


class ShotVersion(TimeStampedModel):
    """
    镜头版本快照 (Story 11.5.2)

    职责:
    - 记录镜头的历史版本
    - 支持版本恢复
    - 支持版本对比
    - 自动清理旧版本
    """

    # 关联的镜头
    shot = models.ForeignKey(
        Shot,
        on_delete=models.CASCADE,
        related_name="versions",
        verbose_name=_("所属镜头"),
    )

    # 版本信息
    version_number = models.IntegerField(verbose_name=_("版本号"))
    change_description = models.TextField(
        blank=True, verbose_name=_("修改说明"), help_text=_("描述本次修改的内容")
    )

    # 镜头内容快照 (JSON格式存储完整的镜头数据)
    content_snapshot = models.JSONField(
        default=dict,
        verbose_name=_("内容快照"),
        help_text=_("镜头内容的完整快照"),
    )

    # 字段级别的变更记录
    field_changes = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_("字段变更"),
        help_text=_('记录变更的字段: {"field": {"old": value, "new": value}}'),
    )

    # 自动创建或手动创建
    is_auto_created = models.BooleanField(
        default=True, verbose_name=_("自动创建"), help_text=_("是否由系统自动创建")
    )

    # 创建者
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("创建者"),
    )

    # 预览缩略图
    thumbnail = models.ImageField(
        upload_to="shot_versions/thumbnails/",
        blank=True,
        verbose_name=_("缩略图"),
    )

    class Meta:
        db_table = "shot_versions"
        verbose_name = _("镜头版本")
        verbose_name_plural = _("镜头版本")
        ordering = ["-version_number"]
        unique_together = [["shot", "version_number"]]
        indexes = [
            models.Index(fields=["shot", "-version_number"]),
            models.Index(fields=["-created_at"]),
        ]

    def __str__(self):
        return f"v{self.version_number} - {self.shot.content[:30]}"

    @classmethod
    def create_version(cls, shot, change_description="", is_auto_created=True, user=None):
        """
        创建镜头版本快照 (Story 11.5.2)

        Args:
            shot: 镜头实例
            change_description: 修改说明
            is_auto_created: 是否自动创建
            user: 创建用户

        Returns:
            ShotVersion: 创建的版本实例
        """
        # 获取当前最新版本号
        latest_version = cls.objects.filter(shot=shot).order_by("-version_number").first()
        next_version = (latest_version.version_number + 1) if latest_version else 1

        # 创建内容快照
        content_snapshot = {
            "shot_number": shot.shot_number,
            "shot_type": shot.shot_type,
            "content": shot.content,
            "speaker": shot.speaker,
            "narration": shot.narration,
            "camera_movement": shot.camera_movement,
            "camera_angle": shot.camera_angle,
            "duration": shot.duration,
            "sort_order": shot.sort_order,
            "character_pose_id": shot.character_pose_id,
            "camera_movement_params": shot.camera_movement_params,
            "shot_composition": shot.shot_composition,
        }

        # 如果有生成的图像，复制缩略图
        thumbnail = None
        if shot.generated_image:
            # 这里可以创建缩略图，暂时直接引用
            thumbnail = shot.generated_image.name

        # 创建版本
        version = cls.objects.create(
            shot=shot,
            version_number=next_version,
            change_description=change_description or f"版本 {next_version}",
            content_snapshot=content_snapshot,
            is_auto_created=is_auto_created,
            created_by=user,
            thumbnail=thumbnail,
        )

        # 清理旧版本 (保留最近10个)
        cls.cleanup_old_versions(shot, keep_count=10)

        return version

    @classmethod
    def cleanup_old_versions(cls, shot, keep_count=10):
        """
        清理旧版本，保留指定数量的最近版本 (Story 11.5.2)

        Args:
            shot: 镜头实例
            keep_count: 保留的版本数量

        Returns:
            int: 删除的版本数量
        """
        versions = cls.objects.filter(shot=shot).order_by("-version_number")

        if versions.count() > keep_count:
            # 获取要保留的版本ID
            keep_ids = list(versions[:keep_count].values_list("id", flat=True))
            # 删除其余版本
            excess_count = versions.count() - keep_count
            cls.objects.filter(shot=shot).exclude(id__in=keep_ids).delete()
            return excess_count

        return 0

    def restore(self):
        """
        恢复到当前版本 (Story 11.5.2)

        将版本快照的内容恢复到镜头

        Returns:
            bool: 恢复是否成功
        """
        shot = self.shot
        snapshot = self.content_snapshot

        # 恢复字段
        shot.shot_number = snapshot.get("shot_number", shot.shot_number)
        shot.shot_type = snapshot.get("shot_type", shot.shot_type)
        shot.content = snapshot.get("content", shot.content)
        shot.speaker = snapshot.get("speaker", shot.speaker)
        shot.narration = snapshot.get("narration", shot.narration)
        shot.camera_movement = snapshot.get("camera_movement", shot.camera_movement)
        shot.camera_angle = snapshot.get("camera_angle", shot.camera_angle)
        shot.duration = snapshot.get("duration", shot.duration)
        shot.sort_order = snapshot.get("sort_order", shot.sort_order)
        shot.character_pose_id = snapshot.get("character_pose_id")
        shot.camera_movement_params = snapshot.get("camera_movement_params", {})
        shot.shot_composition = snapshot.get("shot_composition", "")

        shot.save()

        # 创建新版本记录恢复操作
        ShotVersion.create_version(
            shot=shot,
            change_description=f"恢复到版本 {self.version_number}",
            is_auto_created=True,
        )

        return True

    def compare_with(self, other_version):
        """
        与另一个版本对比 (Story 11.5.2)

        Args:
            other_version: 另一个 ShotVersion 实例

        Returns:
            dict: 差异信息
            {
                "field": {
                    "old": "旧值",
                    "new": "新值",
                    "changed": True
                }
            }
        """
        differences = {}
        old_snapshot = other_version.content_snapshot
        new_snapshot = self.content_snapshot

        # 比较所有字段
        for field in old_snapshot:
            if field in new_snapshot:
                old_value = old_snapshot[field]
                new_value = new_snapshot[field]

                if old_value != new_value:
                    differences[field] = {
                        "old": old_value,
                        "new": new_value,
                        "changed": True,
                    }

        return differences

    @property
    def is_latest(self):
        """是否是最新版本"""
        latest_version = (
            ShotVersion.objects.filter(shot=self.shot).order_by("-version_number").first()
        )
        return latest_version and self.version_number == latest_version.version_number


# ========================================
# 章节工作流 (Story 12-1.1)
# ========================================


class ChapterWorkflow(TimeStampedModel):
    """
    章节工作流记录 (ChapterWorkflow)

    追踪章节的自动化制作流程状态和进度

    职责:
    - 记录工作流状态 (pending/running/paused/completed/failed)
    - 追踪当前处理场景
    - 计算和更新进度百分比
    - 关联 Celery 异步任务
    - 记录工作流时间戳

    Story 12-1.1: 章节工作流数据模型
    """

    class Status(models.TextChoices):
        """工作流状态枚举"""

        PENDING = "pending"
        RUNNING = "running"
        PAUSED = "paused"
        COMPLETED = "completed"
        FAILED = "failed"

    # 唯一标识符 (用于外部引用)
    workflow_id = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        verbose_name=_("工作流ID"),
        help_text=_("全局唯一的工作流标识符"),
    )

    # 关联章节
    chapter = models.ForeignKey(
        Chapter, on_delete=models.CASCADE, related_name="workflows", verbose_name=_("所属章节")
    )

    # 状态追踪
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PENDING, verbose_name=_("状态")
    )

    # 当前处理进度
    current_scene = models.ForeignKey(
        "ScriptScene",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
        verbose_name=_("当前场景"),
        help_text=_("当前正在处理的场景"),
    )
    progress_percentage = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name=_("进度百分比"),
    )

    # 场景统计
    total_scenes = models.IntegerField(
        default=0, validators=[MinValueValidator(0)], verbose_name=_("总场景数")
    )
    completed_scenes = models.IntegerField(
        default=0, validators=[MinValueValidator(0)], verbose_name=_("已完成场景数")
    )

    # 时间戳（继承自 TimeStampedModel，提供 created_at 和 updated_at）
    started_at = models.DateTimeField(null=True, blank=True, verbose_name=_("开始时间"))
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name=_("完成时间"))

    # 错误处理
    error_message = models.TextField(blank=True, verbose_name=_("错误信息"))

    # Celery 任务关联
    celery_task_id = models.UUIDField(
        null=True,
        blank=True,
        verbose_name=_("Celery任务ID"),
        help_text=_("关联的 Celery 异步任务ID"),
    )

    # 软删除支持 (WARN-003)
    is_deleted = models.BooleanField(
        default=False, verbose_name=_("已删除"), help_text=_("标记为已删除，实现软删除")
    )
    deleted_at = models.DateTimeField(null=True, blank=True, verbose_name=_("删除时间"))

    class Meta:
        db_table = "chapter_workflows"
        verbose_name = _("章节工作流")
        verbose_name_plural = _("章节工作流")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["workflow_id"]),
            models.Index(fields=["chapter", "-created_at"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self):
        return f"{self.chapter.title} - {self.get_status_display()}"

    def start(self) -> "ChapterWorkflow":
        """启动工作流"""
        self.status = self.Status.RUNNING
        self.started_at = timezone.now()
        self.save(update_fields=["status", "started_at"])

        # 记录启动事件
        WorkflowEvent.objects.create(
            workflow=self,
            event_type=WorkflowEvent.EventType.WORKFLOW_STARTED,
            message=_("工作流启动"),
        )

        return self

    def pause(self) -> "ChapterWorkflow":
        """暂停工作流"""
        if self.status != self.Status.RUNNING:
            raise ValueError(_("只有运行中的工作流可以暂停"))
        self.status = self.Status.PAUSED
        self.save(update_fields=["status"])

        WorkflowEvent.objects.create(
            workflow=self,
            event_type=WorkflowEvent.EventType.WORKFLOW_PAUSED,
            message=_("工作流暂停"),
        )

        return self

    def resume(self) -> "ChapterWorkflow":
        """恢复工作流"""
        if self.status != self.Status.PAUSED:
            raise ValueError(_("只有暂停的工作流可以恢复"))
        self.status = self.Status.RUNNING
        self.save(update_fields=["status"])

        WorkflowEvent.objects.create(
            workflow=self,
            event_type=WorkflowEvent.EventType.WORKFLOW_RESUMED,
            message=_("工作流恢复"),
        )

        return self

    def complete(self) -> "ChapterWorkflow":
        """完成工作流"""
        self.status = self.Status.COMPLETED
        self.completed_at = timezone.now()
        self.progress_percentage = 100
        self.save(update_fields=["status", "completed_at", "progress_percentage"])

        WorkflowEvent.objects.create(
            workflow=self,
            event_type=WorkflowEvent.EventType.WORKFLOW_COMPLETED,
            message=_("工作流完成"),
        )

        return self

    def fail(self, error_message: str) -> "ChapterWorkflow":
        """标记工作流失败"""
        self.status = self.Status.FAILED
        self.error_message = error_message
        self.completed_at = timezone.now()
        self.save(update_fields=["status", "error_message", "completed_at"])

        WorkflowEvent.objects.create(
            workflow=self,
            event_type=WorkflowEvent.EventType.WORKFLOW_FAILED,
            message=error_message,
            metadata={"error": error_message},
        )

        return self

    def update_progress(self, current_scene=None):
        """更新处理进度"""
        if current_scene:
            self.current_scene = current_scene

        # 计算进度
        if self.total_scenes > 0:
            self.progress_percentage = int((self.completed_scenes / self.total_scenes) * 100)
        self.save(update_fields=["current_scene", "progress_percentage"])

    @property
    def elapsed_seconds(self):
        """计算已用时长（秒）"""
        if self.started_at:
            end_time = self.completed_at or timezone.now()
            return int((end_time - self.started_at).total_seconds())
        return 0

    @property
    def is_active(self):
        """是否为活动工作流"""
        return (
            self.status in [self.Status.PENDING, self.Status.RUNNING, self.Status.PAUSED]
            and not self.is_deleted
        )

    def soft_delete(self):
        """软删除工作流"""
        if self.is_deleted:
            raise ValueError(_("该工作流已被删除"))
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save(update_fields=["is_deleted", "deleted_at"])

    def recover(self):
        """恢复已软删除的工作流"""
        if not self.is_deleted:
            raise ValueError(_("该工作流未被删除"))
        self.is_deleted = False
        self.deleted_at = None
        self.save(update_fields=["is_deleted", "deleted_at"])

    def hard_delete(self):
        """永久删除工作流（物理删除）"""
        # Django 会级联删除关联的 events
        self.delete()


class WorkflowEvent(TimeStampedModel):
    """
    工作流事件记录 (WorkflowEvent)

    记录工作流执行过程中的所有事件

    职责:
    - 记录工作流生命周期事件 (启动/暂停/恢复/完成/失败)
    - 记录场景处理事件 (场景开始/场景完成/场景跳过)
    - 存储事件元数据 (JSON格式)
    - 支持事件追溯和调试

    Story 12-1.1: 章节工作流数据模型
    """

    class EventType(models.TextChoices):
        """事件类型枚举"""

        # 工作流级别事件
        WORKFLOW_STARTED = "workflow_started"
        WORKFLOW_PAUSED = "workflow_paused"
        WORKFLOW_RESUMED = "workflow_resumed"
        WORKFLOW_COMPLETED = "workflow_completed"
        WORKFLOW_FAILED = "workflow_failed"
        WORKFLOW_CANCELLED = "workflow_cancelled"

        # 场景级别事件
        SCENE_STARTED = "scene_started"
        SCENE_COMPLETED = "scene_completed"
        SCENE_FAILED = "scene_failed"
        SCENE_SKIPPED = "scene_skipped"

        # 系统事件
        TASK_RETRY = "task_retry"
        TASK_TIMEOUT = "task_timeout"

    # 关联工作流
    workflow = models.ForeignKey(
        ChapterWorkflow,
        on_delete=models.CASCADE,
        related_name="events",
        verbose_name=_("所属工作流"),
    )

    # 事件信息
    event_type = models.CharField(
        max_length=50, choices=EventType.choices, verbose_name=_("事件类型")
    )

    # 使用基类的时间字段 (created_at/updated_at)，不额外定义 timestamp
    message = models.TextField(verbose_name=_("事件消息"))

    # 事件元数据 (JSON格式，存储额外上下文)
    metadata = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_("元数据"),
        help_text=_("事件的额外信息，如场景ID、错误详情等"),
    )

    # 关联场景 (可选，用于场景级别事件)
    scene = models.ForeignKey(
        "ScriptScene",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",  # 避免命名冲突
        verbose_name=_("关联场景"),
    )

    # 事件级别 (用于过滤和排序)
    SEVERITY_CHOICES = [
        ("info", _("信息")),
        ("warning", _("警告")),
        ("error", _("错误")),
        ("critical", _("严重")),
    ]
    severity = models.CharField(
        max_length=20, choices=SEVERITY_CHOICES, default="info", verbose_name=_("严重级别")
    )

    # 软删除支持 (WARN-003)
    is_deleted = models.BooleanField(
        default=False, verbose_name=_("已删除"), help_text=_("标记为已删除，实现软删除")
    )
    deleted_at = models.DateTimeField(null=True, blank=True, verbose_name=_("删除时间"))

    class Meta:
        db_table = "workflow_events"
        verbose_name = _("工作流事件")
        verbose_name_plural = _("工作流事件")
        # 使用基类的 created_at，不是自定义 timestamp
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["workflow", "-created_at"]),
            models.Index(fields=["event_type"]),
            models.Index(fields=["severity"]),
            models.Index(fields=["is_deleted"]),  # 软删除查询优化
        ]

    def __str__(self):
        return f"{self.get_event_type_display()}: {self.message[:50]}"

    @classmethod
    def log_scene_started(cls, workflow, scene) -> "WorkflowEvent":
        """记录场景开始"""
        return cls.objects.create(
            workflow=workflow,
            event_type=cls.EventType.SCENE_STARTED,
            message=f"场景开始: {scene.scene_name}",
            scene=scene,
            severity="info",
        )

    @classmethod
    def log_scene_completed(cls, workflow, scene) -> "WorkflowEvent":
        """记录场景完成"""
        return cls.objects.create(
            workflow=workflow,
            event_type=cls.EventType.SCENE_COMPLETED,
            message=f"场景完成: {scene.scene_name}",
            scene=scene,
            severity="info",
        )

    @classmethod
    def log_scene_failed(cls, workflow, scene, error_message: str) -> "WorkflowEvent":
        """记录场景失败"""
        return cls.objects.create(
            workflow=workflow,
            event_type=cls.EventType.SCENE_FAILED,
            message=f"场景失败: {scene.scene_name}",
            scene=scene,
            severity="error",
            metadata={"scene_id": scene.id, "error": error_message},
        )

    def soft_delete(self):
        """软删除事件"""
        if self.is_deleted:
            raise ValueError(_("该事件已被删除"))
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save(update_fields=["is_deleted", "deleted_at"])

    def recover(self):
        """恢复已软删除的事件"""
        if not self.is_deleted:
            raise ValueError(_("该事件未被删除"))
        self.is_deleted = False
        self.deleted_at = None
        self.save(update_fields=["is_deleted", "deleted_at"])

    def hard_delete(self):
        """永久删除事件（物理删除）"""
        self.delete()
