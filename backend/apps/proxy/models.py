"""
Proxy Module - 代理配置管理模块

该模块提供代理配置和使用日志的Django模型，支持HTTP/HTTPS/SOCKS5协议。

📋 实施路线图:
==============
Story 9.0 (✅完成): 创建基础设施文件，添加TODO注释
Story 9.1 (⏳当前): 实现ProxyConfig模型（name, protocol, host, port, username, password_encrypted）
          - Fernet密码加密/解密
          - get_proxy_url()方法
Story 9.2: ⏳ 实现ProxyUsageLog模型（proxy, ai_provider, endpoint, response_time_ms, success）
          - Django Admin只读界面
Story 9.3: ⏳ 实现ProxyManager服务层 + NoProxyProvider
Story 9.4: ⏳ 实现HttpProxyProvider（Strategy Pattern）
Story 9.5: ⏳ 实现代理降级逻辑（ProxyManager + BaseAIClient集成）
Story 9.6: ⏳ AI客户端集成（BaseAIClient代理支持）

🔗 相关文档:
==========
- Architecture: _bmad-output/planning-artifacts/architecture-proxy-management.md
- Epic Breakdown: _bmad-output/planning-artifacts/epics-proxy-management.md
- Story File: _bmad-output/implementation-artifacts/9-1-proxy-config-model.md

@Author: Epic 9 Team
@Created: 2026-01-30
"""

from cryptography.fernet import Fernet
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured, ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class ProxyProtocol(models.TextChoices):
    """代理协议枚举"""

    HTTP = "http", "HTTP"
    HTTPS = "https", "HTTPS"
    SOCKS5 = "socks5", "SOCKS5"


class ProxyConfig(models.Model):
    """
    代理配置模型

    存储HTTP/HTTPS/SOCKS5代理配置，支持用户名/密码认证。
    密码使用Fernet对称加密存储。

    Attributes:
        name: 代理名称（唯一标识）
        protocol: 代理协议（http/https/socks5）
        host: 代理主机地址
        port: 代理端口（1-65535）
        username: 代理认证用户名（可选）
        password: 代理认证密码（明文，仅用于输入，保存后清空）
        password_encrypted: 加密后的密码（BinaryField）
        is_active: 代理是否激活（默认True）
        is_healthy: 代理是否健康（默认True，由健康检查任务更新）
        priority: 代理优先级（数字越小优先级越高，默认0）
        last_used_at: 最后使用时间（自动更新）
        created_at: 创建时间
        updated_at: 更新时间
    """

    # 基本配置
    name = models.CharField(
        max_length=200, unique=True, verbose_name="代理名称", help_text="代理的唯一标识名称"
    )

    protocol = models.CharField(
        max_length=10,
        choices=ProxyProtocol.choices,
        default=ProxyProtocol.HTTP,
        verbose_name="代理协议",
        help_text="支持的协议: HTTP, HTTPS, SOCKS5",
    )

    host = models.CharField(
        max_length=255, verbose_name="代理主机", help_text="代理服务器地址（域名或IP）"
    )

    port = models.IntegerField(
        validators=[
            MinValueValidator(1, message="端口号必须大于等于1"),
            MaxValueValidator(65535, message="端口号必须小于等于65535"),
        ],
        verbose_name="代理端口",
        help_text="代理服务器端口（1-65535）",
    )

    # 认证信息
    username = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        verbose_name="用户名",
        help_text="代理认证用户名（可选）",
    )

    # 明文密码字段 - 仅用于输入，保存后清空
    password = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="密码",
        help_text="代理认证密码（明文，保存后自动加密并清空）",
    )

    # 加密密码字段 - 实际存储的密文
    password_encrypted = models.BinaryField(
        blank=True,
        null=True,
        verbose_name="加密密码",
        help_text="使用Fernet加密后的密码（二进制存储）",
    )

    # 状态字段
    is_active = models.BooleanField(default=True, verbose_name="是否激活", help_text="代理是否可用")

    is_healthy = models.BooleanField(
        default=True, verbose_name="是否健康", help_text="代理健康状态（由健康检查任务更新）"
    )

    # Story 9.10: 健康检查计数器
    consecutive_failures = models.IntegerField(
        default=0,
        verbose_name="连续失败次数",
        help_text="连续健康检查失败次数（>3次标记为不健康）",
    )

    consecutive_successes = models.IntegerField(
        default=0,
        verbose_name="连续成功次数",
        help_text="连续健康检查成功次数（3次恢复为健康）",
    )

    priority = models.IntegerField(
        default=0, verbose_name="优先级", help_text="数字越小优先级越高（0为最高优先级）"
    )

    # 时间戳
    last_used_at = models.DateTimeField(
        blank=True, null=True, verbose_name="最后使用时间", help_text="最后一次使用此代理的时间"
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")

    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    class Meta:
        verbose_name = "代理配置"
        verbose_name_plural = "代理配置"
        ordering = ["priority", "name"]
        indexes = [
            models.Index(fields=["is_active", "is_healthy"], name="proxy_active_healthy_idx"),
            models.Index(fields=["-last_used_at"], name="proxy_last_used_idx"),
            models.Index(fields=["protocol"], name="proxy_protocol_idx"),
        ]

    def __str__(self):
        """代理配置的字符串表示"""
        return f"{self.name} ({self.protocol}://{self.host}:{self.port})"

    def save(self, *args, **kwargs):
        """
        保存代理配置，自动加密密码

        覆盖Django的save()方法，在保存前：
        1. 如果有明文密码，自动加密并存储到password_encrypted
        2. 清空明文password字段（不存储明文）
        """
        if self.password:
            # 加密密码并存储到password_encrypted
            self.password_encrypted = self.encrypt_password(self.password)
            # 清空明文密码字段（不存储明文）
            self.password = None
        super().save(*args, **kwargs)

    def encrypt_password(self, password: str) -> bytes:
        """
        使用Fernet加密密码

        Args:
            password: 明文密码

        Returns:
            加密后的密码（bytes）

        Raises:
            ImproperlyConfigured: 如果PROXY_ENCRYPTION_KEY未设置
        """
        encryption_key = getattr(settings, "PROXY_ENCRYPTION_KEY", None)
        if not encryption_key:
            raise ImproperlyConfigured(
                "代理密码加密需要PROXY_ENCRYPTION_KEY环境变量。"
                "请使用 'uv run python scripts/generate_proxy_key.py' 生成密钥。"
            )

        f = Fernet(
            encryption_key.encode("utf-8") if isinstance(encryption_key, str) else encryption_key
        )
        encrypted = f.encrypt(password.encode("utf-8"))
        return encrypted

    def decrypt_password(self, encrypted: bytes) -> str:
        """
        解密密码

        Args:
            encrypted: 加密的密码（bytes）

        Returns:
            解密后的明文密码（str）

        Raises:
            InvalidToken: 如果解密失败（密钥错误或数据损坏）
        """
        encryption_key = getattr(settings, "PROXY_ENCRYPTION_KEY", None)
        if not encryption_key:
            raise ImproperlyConfigured("代理密码解密需要PROXY_ENCRYPTION_KEY环境变量。")

        f = Fernet(
            encryption_key.encode("utf-8") if isinstance(encryption_key, str) else encryption_key
        )
        decrypted = f.decrypt(encrypted)
        return decrypted.decode("utf-8")

    def get_proxy_url(self) -> str:
        """
        构建代理URL（用于httpx客户端）

        支持的格式：
        - 无认证: "protocol://host:port"
        - 有认证: "protocol://username:password@host:port"

        Returns:
            代理URL字符串

        Examples:
            >>> proxy = ProxyConfig(protocol="https", host="proxy.example.com", port=8080)
            >>> proxy.get_proxy_url()
            "https://proxy.example.com:8080"

            >>> proxy = ProxyConfig(
            ...     protocol="https",
            ...     host="proxy.example.com",
            ...     port=8080,
            ...     username="user",
            ...     password_encrypted=encrypted_password
            ... )
            >>> proxy.get_proxy_url()  # 会自动解密密码
            "https://user:decrypted_password@proxy.example.com:8080"
        """
        # 如果有加密密码，先解密
        password = None
        if self.password_encrypted:
            password = self.decrypt_password(self.password_encrypted)

        # 构建认证部分
        auth = ""
        if self.username and password:
            auth = f"{self.username}:{password}@"
        elif self.username:
            auth = f"{self.username}@"

        # 构建完整URL
        proxy_url = f"{self.protocol}://{auth}{self.host}:{self.port}"
        return proxy_url

    def clean(self):
        """
        验证代理配置的业务规则

        验证项：
        1. 如果有密码，检查PROXY_ENCRYPTION_KEY是否已设置
        2. port范围验证（1-65535）- Django validator已处理，这里重复检查以确保完整性
        3. name唯一性由Django的unique=True自动处理

        Raises:
            ValidationError: 如果验证失败
        """
        # 验证密钥存在性（如果有密码）
        if self.password:
            encryption_key = getattr(settings, "PROXY_ENCRYPTION_KEY", None)
            if not encryption_key:
                raise ValidationError(
                    {
                        "password": "代理密码加密需要PROXY_ENCRYPTION_KEY环境变量。"
                        '请使用 "uv run python scripts/generate_proxy_key.py" 生成密钥。'
                    }
                )

        # 验证port范围（Django validator已处理，这里额外检查）
        if self.port and not (1 <= self.port <= 65535):
            raise ValidationError({"port": "端口号必须在1-65535之间"})

        super().clean()


class ProxyUsageLog(models.Model):
    """
    代理使用日志模型

    记录每次通过代理调用AI API的详细信息，
    包括响应时间、成功状态、错误信息等。

    Attributes:
        proxy: 关联的代理配置（外键）
        ai_provider: AI客户端类型（如'OpenAIClient', 'ClaudeClient'）
        endpoint: API端点路径
        response_time_ms: API响应时间（毫秒）
        success: 调用是否成功
        error_message: 错误信息（失败时记录）
        timestamp: 日志时间戳（自动记录）
    """

    # 外键关联
    proxy = models.ForeignKey(
        ProxyConfig,
        on_delete=models.CASCADE,
        related_name="usage_logs",
        db_index=True,
        verbose_name="代理配置",
        help_text="关联的代理配置",
    )

    # AI调用信息
    ai_provider = models.CharField(
        max_length=50,
        verbose_name="AI提供商",
        help_text="AI客户端类型（如'OpenAIClient', 'ClaudeClient'）",
    )

    endpoint = models.CharField(
        max_length=255,
        verbose_name="API端点",
        help_text="调用的API端点路径",
    )

    response_time_ms = models.PositiveIntegerField(
        verbose_name="响应时间",
        help_text="API响应时间（毫秒）",
    )

    success = models.BooleanField(
        default=True,
        verbose_name="是否成功",
        help_text="调用是否成功",
    )

    error_message = models.TextField(
        blank=True,
        null=True,
        verbose_name="错误信息",
        help_text="失败时的错误信息",
    )

    # 时间戳（自动记录）
    timestamp = models.DateTimeField(
        auto_now_add=True,
        verbose_name="时间戳",
        help_text="日志记录时间（自动生成）",
    )

    class Meta:
        db_table = "proxy_usage_log"
        verbose_name = "代理使用日志"
        verbose_name_plural = "代理使用日志"
        ordering = ["-timestamp"]
        indexes = [
            # 索引1：按代理查询（最常见）
            models.Index(fields=["proxy", "-timestamp"], name="proxy_time_idx"),
            # 索引2：按AI提供商和成功状态筛选
            models.Index(
                fields=["ai_provider", "success", "-timestamp"], name="provider_success_idx"
            ),
        ]

    def __str__(self):
        """日志记录的字符串表示"""
        return f"{self.proxy.name} - {self.ai_provider} - {self.timestamp}"
