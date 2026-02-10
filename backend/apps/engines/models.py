# Engines Models - 引擎配置与监控模型

from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

# ==================== 引擎配置模型 ====================


class EngineConfig(models.Model):
    """
    引擎配置模型

    管理三种 AI 引擎类型的配置：
    - LLM (大语言模型)
    - Image (图像生成)
    - TTS (语音合成)

    支持主引擎和备份引擎的配置，以及自动 Fallback 策略。
    """

    ENGINE_TYPES = [
        ("llm", _("LLM文本生成")),
        ("image", _("图像生成")),
        ("tts", _("语音合成")),
    ]

    HEALTH_STATUS_CHOICES = [
        ("online", _("在线")),
        ("offline", _("离线")),
        ("error", _("异常")),
        ("unknown", _("未知")),
    ]

    # 允许的提供商列表 (通过验证方法强制执行)
    # LLM 提供商
    LLM_PROVIDERS = ["ollama", "openai", "anthropic", "glm", "deepseek"]

    # Image 提供商
    IMAGE_PROVIDERS = ["comfyui", "dalle", "stable-diffusion", "midjourney"]

    # TTS 提供商
    TTS_PROVIDERS = ["edge-tts", "elevenlabs", "azure-tts", "google-tts"]

    # 基础配置
    engine_type = models.CharField(
        max_length=10,
        choices=ENGINE_TYPES,
        unique=True,
        verbose_name=_("引擎类型"),
        help_text=_("引擎类型 (每种类型只能有一个配置)"),
    )

    name = models.CharField(
        max_length=255, verbose_name=_("配置名称"), help_text=_("引擎配置的显示名称")
    )

    description = models.TextField(
        blank=True, verbose_name=_("描述"), help_text=_("引擎配置的详细说明")
    )

    # 主引擎配置
    primary_provider = models.CharField(
        max_length=50,
        verbose_name=_("主引擎提供商"),
        help_text=_("主引擎提供商 (如: ollama, openai)"),
    )

    primary_config = models.JSONField(
        default=dict,
        verbose_name=_("主引擎配置"),
        help_text=_(
            "主引擎配置参数 (JSON格式)\n"
            'LLM示例: {"base_url": "http://localhost:11434", '
            '"model": "llama2:7b", "temperature": 0.7}\n'
            'Image示例: {"base_url": "http://localhost:8188", '
            '"workflow": "..."}\n'
            'TTS示例: {"voice": "zh-CN-XiaoxiaoNeural", '
            '"rate": "+0%"}'
        ),
    )

    # 备份引擎配置
    fallback_provider = models.CharField(
        max_length=50,
        blank=True,
        verbose_name=_("备份引擎提供商"),
        help_text=_("备份引擎提供商 (可选)"),
    )

    fallback_config = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_("备份引擎配置"),
        help_text=_("备份引擎配置参数 (JSON格式)"),
    )

    # Fallback 策略
    fallback_threshold = models.IntegerField(
        default=3, verbose_name=_("失败阈值"), help_text=_("连续失败多少次后切换到备份引擎")
    )

    fallback_timeout = models.IntegerField(
        default=30, verbose_name=_("超时时间(秒)"), help_text=_("请求超时时间 (秒)")
    )

    auto_fallback = models.BooleanField(
        default=True, verbose_name=_("自动Fallback"), help_text=_("是否自动启用Fallback切换")
    )

    # 状态管理
    is_active = models.BooleanField(default=True, verbose_name=_("是否启用"))

    current_provider = models.CharField(
        max_length=50, blank=True, verbose_name=_("当前引擎"), help_text=_("当前使用的引擎提供商")
    )

    health_status = models.CharField(
        max_length=20, default="unknown", choices=HEALTH_STATUS_CHOICES, verbose_name=_("健康状态")
    )

    last_health_check = models.DateTimeField(auto_now=True, verbose_name=_("最后检查时间"))

    # 统计信息
    total_requests = models.IntegerField(default=0, verbose_name=_("总请求数"))

    success_count = models.IntegerField(default=0, verbose_name=_("成功次数"))

    failure_count = models.IntegerField(default=0, verbose_name=_("失败次数"))

    avg_response_time = models.FloatField(default=0.0, verbose_name=_("平均响应时间(ms)"))

    # 成本追踪
    total_cost = models.FloatField(
        default=0.0, verbose_name=_("实际花费($)"), help_text=_("实际花费的金额 (美元)")
    )

    saved_cost = models.FloatField(
        default=0.0, verbose_name=_("节省金额($)"), help_text=_("使用本地引擎节省的金额 (美元)")
    )

    # 时间戳
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("创建时间"))

    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("更新时间"))

    class Meta:
        verbose_name = _("引擎配置")
        verbose_name_plural = _("引擎配置")
        ordering = ["engine_type"]

    def __str__(self):
        return f"{self.get_engine_type_display()} - {self.primary_provider}"

    def clean(self):
        """
        验证配置

        验证:
        1. 主引擎和备份引擎不能相同
        2. 主引擎配置不能为空
        3. 提供商必须在允许的列表中
        """
        super().clean()

        # 主引擎和备份引擎不能相同
        if self.fallback_provider and self.primary_provider == self.fallback_provider:
            raise ValidationError({"fallback_provider": _("备份引擎不能与主引擎相同")})

        # 验证主引擎配置不为空
        if not self.primary_config:
            raise ValidationError({"primary_config": _("主引擎配置不能为空")})

        # 验证提供商是否在允许的列表中
        allowed_providers = self._get_allowed_providers()
        if self.primary_provider not in allowed_providers:
            raise ValidationError(
                {
                    "primary_provider": _(
                        "不支持的提供商: %(provider)s。允许的提供商: %(providers)s"
                    )
                    % {"provider": self.primary_provider, "providers": ", ".join(allowed_providers)}
                }
            )

        if self.fallback_provider and self.fallback_provider not in allowed_providers:
            raise ValidationError(
                {
                    "fallback_provider": _(
                        "不支持的提供商: %(provider)s。允许的提供商: %(providers)s"
                    )
                    % {
                        "provider": self.fallback_provider,
                        "providers": ", ".join(allowed_providers),
                    }
                }
            )

    def _get_allowed_providers(self):
        """根据引擎类型获取允许的提供商列表"""
        providers_map = {
            "llm": self.LLM_PROVIDERS,
            "image": self.IMAGE_PROVIDERS,
            "tts": self.TTS_PROVIDERS,
        }
        return providers_map.get(self.engine_type, [])

    def get_active_provider(self):
        """
        获取当前应使用的引擎

        Returns:
            str: 当前应使用的引擎提供商
        """
        if not self.auto_fallback:
            return self.primary_provider

        # 如果当前引擎在线，继续使用
        if self.health_status == "online" and self.current_provider:
            return self.current_provider

        # 否则使用主引擎
        return self.primary_provider

    def should_fallback(self):
        """
        判断是否需要切换到备份引擎

        Returns:
            bool: 是否需要切换
        """
        if not self.auto_fallback:
            return False

        if not self.fallback_provider:
            return False

        # 连续失败次数达到阈值
        # 使用模运算来追踪"连续"失败（简化实现）
        # 实际应用中可能需要更复杂的逻辑
        return self.failure_count > 0 and self.failure_count % self.fallback_threshold == 0

    def calculate_success_rate(self):
        """
        计算成功率

        Returns:
            float: 成功率百分比 (0-100)
        """
        if self.total_requests == 0:
            return 0.0
        return (self.success_count / self.total_requests) * 100

    def record_success(self, response_time: float, cost: float = 0.0, saved: float = 0.0):
        """
        记录成功请求

        Args:
            response_time: 响应时间 (毫秒)
            cost: 实际花费 (美元)
            saved: 节省金额 (美元)
        """
        self.total_requests += 1
        self.success_count += 1
        self.total_cost += cost
        self.saved_cost += saved

        # 更新平均响应时间 (加权平均)
        if self.total_requests == 1:
            self.avg_response_time = response_time
        else:
            alpha = 0.1  # 平滑因子
            self.avg_response_time = alpha * response_time + (1 - alpha) * self.avg_response_time

        self.save(
            update_fields=[
                "total_requests",
                "success_count",
                "total_cost",
                "saved_cost",
                "avg_response_time",
            ]
        )

    def record_failure(self):
        """记录失败请求"""
        self.total_requests += 1
        self.failure_count += 1
        self.save(update_fields=["total_requests", "failure_count"])


# ==================== 健康检查日志 ====================


class EngineHealthLog(models.Model):
    """
    引擎健康检查日志

    记录每次健康检查的详细信息。
    """

    STATUS_CHOICES = [
        ("online", _("在线")),
        ("offline", _("离线")),
        ("error", _("异常")),
    ]

    engine = models.ForeignKey(
        EngineConfig,
        on_delete=models.CASCADE,
        related_name="health_logs",
        verbose_name=_("引擎配置"),
    )

    # 检查结果
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, verbose_name=_("状态"))

    response_time = models.FloatField(
        null=True, blank=True, verbose_name=_("响应时间(ms)"), help_text=_("响应时间 (毫秒)")
    )

    # 错误信息
    error_message = models.TextField(blank=True, verbose_name=_("错误信息"))

    error_code = models.CharField(max_length=50, blank=True, verbose_name=_("错误代码"))

    # 时间戳
    checked_at = models.DateTimeField(auto_now_add=True, verbose_name=_("检查时间"))

    class Meta:
        verbose_name = _("引擎健康日志")
        verbose_name_plural = _("引擎健康日志")
        ordering = ["-checked_at"]
        indexes = [
            models.Index(fields=["engine", "-checked_at"]),
        ]

    def __str__(self):
        return f"{self.engine.engine_type} - {self.get_status_display()} @ {self.checked_at}"


# ==================== 使用日志 ====================


class EngineUsageLog(models.Model):
    """
    引擎使用日志

    记录每次引擎调用的详细信息，用于成本追踪和分析。
    """

    engine = models.ForeignKey(
        EngineConfig,
        on_delete=models.CASCADE,
        related_name="usage_logs",
        verbose_name=_("引擎配置"),
    )

    # 请求信息
    provider = models.CharField(max_length=50, verbose_name=_("实际使用的提供商"))

    request_type = models.CharField(max_length=20, verbose_name=_("请求类型"))

    success = models.BooleanField(default=True, verbose_name=_("是否成功"))

    # 性能指标
    response_time = models.FloatField(verbose_name=_("响应时间(ms)"))

    token_count = models.IntegerField(null=True, blank=True, verbose_name=_("Token数量"))

    # 成本信息
    cost = models.FloatField(default=0.0, verbose_name=_("实际花费($)"))

    saved_cost = models.FloatField(default=0.0, verbose_name=_("节省金额($)"))

    # 关联信息
    project_id = models.UUIDField(null=True, blank=True, verbose_name=_("项目ID"))

    shot_id = models.UUIDField(null=True, blank=True, verbose_name=_("镜头ID"))

    # 时间戳
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("创建时间"))

    class Meta:
        verbose_name = _("引擎使用日志")
        verbose_name_plural = _("引擎使用日志")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["engine", "-created_at"]),
            models.Index(fields=["success", "-created_at"]),
        ]

    def __str__(self):
        status_icon = "✓" if self.success else "✗"
        return f"{self.engine.engine_type} - {self.provider} - {status_icon}"


# ==================== Fallback 事件日志 ====================


class FallbackEventLog(models.Model):
    """
    Fallback 事件日志

    记录引擎自动切换事件。
    """

    REASON_CHOICES = [
        ("timeout", _("超时")),
        ("failure", _("连续失败")),
        ("manual", _("手动切换")),
        ("error", _("引擎异常")),
    ]

    engine = models.ForeignKey(
        EngineConfig,
        on_delete=models.CASCADE,
        related_name="fallback_logs",
        verbose_name=_("引擎配置"),
    )

    # 切换信息
    from_provider = models.CharField(max_length=50, verbose_name=_("源引擎"))

    to_provider = models.CharField(max_length=50, verbose_name=_("目标引擎"))

    # 切换原因
    reason = models.CharField(max_length=20, choices=REASON_CHOICES, verbose_name=_("切换原因"))

    reason_detail = models.TextField(blank=True, verbose_name=_("原因详情"))

    # 影响范围
    affected_requests = models.IntegerField(default=0, verbose_name=_("影响的请求数"))

    # 时间戳
    occurred_at = models.DateTimeField(auto_now_add=True, verbose_name=_("发生时间"))

    class Meta:
        verbose_name = _("Fallback事件日志")
        verbose_name_plural = _("Fallback事件日志")
        ordering = ["-occurred_at"]

    def __str__(self):
        return f"{self.engine.engine_type}: {self.from_provider} → {self.to_provider}"
