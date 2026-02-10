"""
代理管理服务层 - ProxyProvider策略模式实现

Story 9.3: ProxyManager + NoProxyProvider实现
- ProxyProvider抽象基类（策略模式）
- NoProxyProvider直连策略
- HttpProxyProvider代理策略（Story 9.4完成完整逻辑）
- ProxyManager工厂方法（工厂模式）

Story 9.4: HttpProxyProvider完整实现
- 实现get_proxy()返回代理URL
- 实现record_usage()记录使用日志

🔗 相关文档:
==========
- Architecture: _bmad-output/planning-artifacts/architecture-proxy-management.md
- Story File: _bmad-output/implementation-artifacts/9-3-proxy-manager.md

@Author: Epic 9 Team
@Created: 2026-01-31
"""

import logging
from abc import ABC, abstractmethod
from typing import Optional

from django.utils import timezone

from apps.proxy.models import ProxyConfig, ProxyUsageLog

logger = logging.getLogger(__name__)


class ProxyProvider(ABC):
    """
    代理策略抽象基类（策略模式）

    定义代理策略的统一接口，所有代理策略必须实现此抽象类的两个方法：
    - get_proxy(): 获取代理URL
    - record_usage(): 记录代理使用日志

    策略模式优势：
    - 开闭原则：新增代理策略（如Socks5ProxyProvider）无需修改现有代码
    - 里氏替换：所有Provider子类可互相替换
    - 依赖倒置：AI客户端依赖抽象接口，而非具体实现
    """

    @abstractmethod
    def get_proxy(self) -> Optional[str]:
        """
        获取代理URL（httpx格式）

        Returns:
            代理URL字符串（如"https://user:pass@proxy.example.com:8080"）
            None表示直连模式（不使用代理）

        Examples:
            >>> provider.get_proxy()
            "https://user:pass@proxy.example.com:8080"

            >>> provider = NoProxyProvider()
            >>> provider.get_proxy()
            None
        """
        pass

    @abstractmethod
    def record_usage(
        self,
        ai_provider: str,
        endpoint: str,
        success: bool,
        response_time: int,
        error_message: Optional[str] = None,
    ) -> None:
        """
        记录代理使用日志

        Args:
            ai_provider: AI客户端类型（如"OpenAIClient", "ClaudeClient"）
            endpoint: API端点路径（如"/v1/chat/completions"）
            success: 调用是否成功
            response_time: 响应时间（毫秒）
            error_message: 错误信息（失败时）

        Note:
            NoProxyProvider实现为空方法体（直连模式不记录日志）
            HttpProxyProvider实现为创建ProxyUsageLog记录
        """
        pass


class NoProxyProvider(ProxyProvider):
    """
    直连策略（不使用代理）

    用于向后兼容：未设置proxy_id时，AI客户端直连外部API。
    符合Strategy Pattern：零开销策略（get_proxy返回None，record_usage什么都不做）
    """

    def get_proxy(self) -> Optional[str]:
        """返回None，表示直连模式"""
        return None

    def record_usage(
        self,
        ai_provider: str,
        endpoint: str,
        success: bool,
        response_time: int,
        error_message: Optional[str] = None,
    ) -> None:
        """
        空方法体 - 直连模式不记录日志

        性能优化：避免不必要的数据库写入
        """
        pass


class HttpProxyProvider(ProxyProvider):
    """
    HTTP/HTTPS/SOCKS5代理策略

    通过代理服务器调用AI API，支持：
    - HTTP/HTTPS代理（basic auth）
    - SOCKS5代理（需要httpx[socks]）
    - 密码自动解密
    - 使用日志记录

    Attributes:
        proxy_config: 代理配置实例
        project_id: 项目ID（用于未来日志记录）
    """

    def __init__(self, proxy_config: ProxyConfig, project_id: Optional[int] = None):
        """
        初始化代理Provider

        Args:
            proxy_config: 代理配置实例
            project_id: 项目ID（用于未来日志记录）
        """
        self.proxy_config = proxy_config
        self.project_id = project_id

    def get_proxy(self) -> Optional[str]:
        """
        返回代理URL（httpx格式）

        Returns:
            代理URL字符串（如"https://user:pass@proxy.example.com:8080"）
            None表示解密失败或代理不可用（触发降级）

        Note:
            解密失败时自动降级到直连模式
        """
        try:
            # 调用ProxyConfig.get_proxy_url()（内部处理解密）
            proxy_url = self.proxy_config.get_proxy_url()
            logger.info(f"Using proxy: {self.proxy_config.name}")
            return proxy_url
        except Exception as e:
            # 捕获解密异常（InvalidToken等）
            logger.error(
                f"Failed to decrypt proxy {self.proxy_config.id}: {e}",
                exc_info=True,
            )
            return None  # 触发降级

    def record_usage(
        self,
        ai_provider: str,
        endpoint: str,
        success: bool,
        response_time: int,
        error_message: Optional[str] = None,
    ) -> None:
        """
        记录代理使用日志到数据库

        Args:
            ai_provider: AI客户端类型（如"OpenAIClient"）
            endpoint: API端点路径
            success: 调用是否成功
            response_time: 响应时间（毫秒）
            error_message: 错误信息（失败时）

        Raises:
            ValueError: 参数验证失败（ai_provider、endpoint、response_time）

        Note:
            立即更新last_used_at（无论日志创建成功与否）
        """
        # 验证必要参数
        if not ai_provider:
            raise ValueError("ai_provider cannot be empty")
        if not endpoint:
            raise ValueError("endpoint cannot be empty")
        if response_time < 0:
            raise ValueError("response_time must be non-negative")

        try:
            # 立即更新last_used_at（原子更新）
            self.proxy_config.last_used_at = timezone.now()
            self.proxy_config.save(update_fields=["last_used_at"])

            # 创建使用日志
            ProxyUsageLog.objects.create(
                proxy=self.proxy_config,
                ai_provider=ai_provider,
                endpoint=endpoint,
                response_time_ms=response_time,
                success=success,
                error_message=error_message or "",
            )

        except Exception as e:
            # 记录错误但不抛出异常（不影响AI调用）
            logger.error(f"Failed to record proxy usage: {e}", exc_info=True)


class ProxyManager:
    """
    代理管理工厂（工厂模式）

    根据proxy_id返回相应的ProxyProvider实例：
    - proxy_id=None → NoProxyProvider（直连）
    - proxy_id存在且active/healthy → HttpProxyProvider
    - proxy_id不存在或inactive/unhealthy → NoProxyProvider（降级策略）

    降级策略：
    当代理不可用时，自动降级到直连模式，保证系统可用性。

    Attributes:
        无状态设计：每次调用get_provider()都创建新实例
        线程安全：无共享状态，多线程安全
    """

    @staticmethod
    def get_provider(proxy_id: Optional[int], project_id: Optional[int] = None) -> ProxyProvider:
        """
        获取代理Provider实例

        Args:
            proxy_id: 代理配置ID（None表示直连）
            project_id: 项目ID（用于未来日志记录）

        Returns:
            ProxyProvider实例：
            - NoProxyProvider（proxy_id=None或不存在或不健康）
            - HttpProxyProvider（代理配置有效）

        Raises:
            无异常 - 所有异常都被捕获，返回NoProxyProvider（降级策略）

        Examples:
            >>> # 直连模式
            >>> provider = ProxyManager.get_provider(None)
            >>> assert provider.get_proxy() is None

            >>> >>> # 代理模式
            >>> provider = ProxyManager.get_provider(5, project_id=10)
            >>> proxy_url = provider.get_proxy()
            >>> assert proxy_url == "https://proxy.example.com:8080"

        降级策略：
            1. proxy_id=None → NoProxyProvider
            2. proxy_id不存在 → NoProxyProvider
            3. 代理is_active=False → NoProxyProvider
            4. 代理is_healthy=False → NoProxyProvider
            5. 数据库异常 → NoProxyProvider
        """
        # 直连模式
        if proxy_id is None:
            return NoProxyProvider()

        try:
            # 查询代理配置
            proxy_config = ProxyConfig.objects.get(id=proxy_id)

            # 验证代理状态
            if not proxy_config.is_active or not proxy_config.is_healthy:
                logger.warning(
                    f"Proxy {proxy_id} is inactive or unhealthy, falling back to direct connection"
                )
                return NoProxyProvider()

            # 返回HttpProxyProvider（Story 9.4完整实现）
            return HttpProxyProvider(proxy_config, project_id)

        except ProxyConfig.DoesNotExist:
            logger.warning(f"Proxy {proxy_id} not found, falling back to direct connection")
            return NoProxyProvider()
        except Exception as e:
            # 捕获所有异常，保证系统可用性
            logger.error(f"Failed to load proxy {proxy_id}: {e}")
            return NoProxyProvider()
