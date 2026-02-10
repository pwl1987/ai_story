"""
AI客户端抽象基类
遵循依赖倒置原则(DIP): 定义抽象接口,具体实现依赖接口
遵循开闭原则(OCP): 对扩展开放,对修改封闭

Story 9.5: 代理降级逻辑实现
- DegradeFailedException: 代理和直连都失败时抛出
- _call_api_with_fallback(): 代理失败时自动降级到直连
"""

import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, Optional

import httpx

logger = logging.getLogger(__name__)


class DegradeFailedError(Exception):
    """
    代理和直连都失败时抛出的异常

    当代理调用失败，降级到直连后直连也失败时抛出此异常。
    异常信息包含两个错误信息，便于诊断问题。

    Example:
        >>> raise DegradeFailedError(
        ...     "PROXY_AND_DIRECT_FAILED: "
        ...     "Proxy failed (ProxyError: Connection timeout), "
        ...     "Direct connection failed (ConnectError: Network unreachable)"
        ... )
    """

    pass


@dataclass
class AIResponse:
    """AI响应统一数据结构"""

    success: bool
    text: str = ""
    data: Dict[str, Any] = None
    metadata: Dict[str, Any] = None
    error: Optional[str] = None

    def __post_init__(self):
        if self.data is None:
            self.data = {}
        if self.metadata is None:
            self.metadata = {}


class BaseAIClient(ABC):
    """
    AI客户端抽象基类
    所有AI客户端必须实现此接口

    Story 9.5: 代理降级逻辑
    - 支持proxy_provider属性（通过ProxyManager获取）
    - _call_api_with_fallback()实现自动降级逻辑

    Story 9.6: BaseAIClient代理支持
    - 接收proxy_id参数，自动初始化proxy_provider
    - 支持project_id参数用于日志记录
    - 所有子类自动继承代理功能
    """

    def __init__(
        self,
        api_url: str,
        api_key: str,
        model_name: str,
        proxy_id: Optional[int] = None,
        project_id: Optional[int] = None,
        **kwargs,
    ):
        """
        初始化客户端

        Args:
            api_url: API地址
            api_key: API密钥
            model_name: 模型名称
            proxy_id: 代理配置ID（可选，Story 9.6）
            project_id: 项目ID（可选，Story 9.6，用于日志记录）
            **kwargs: 其他配置参数

        Story 9.6: 代理支持
        - 通过ProxyManager.get_provider()初始化proxy_provider
        - 向后兼容：proxy_id默认为None（直连模式）
        """
        self.api_url = api_url
        self.api_key = api_key
        self.model_name = model_name
        self.project_id = project_id
        self.config = kwargs

        # Story 9.6: 初始化proxy_provider（通过ProxyManager）
        from apps.proxy.services import ProxyManager

        self.proxy_provider = ProxyManager.get_provider(proxy_id, project_id)

    @abstractmethod
    async def generate(self, prompt: str, **kwargs) -> AIResponse:
        """
        生成内容

        Args:
            prompt: 输入提示词
            **kwargs: 其他参数

        Returns:
            AIResponse: 统一响应对象
        """
        pass

    @abstractmethod
    async def validate_config(self) -> bool:
        """
        验证配置是否有效

        Returns:
            bool: 配置是否有效
        """
        pass

    async def health_check(self) -> bool:
        """
        健康检查

        Returns:
            bool: 服务是否健康
        """
        try:
            return await self.validate_config()
        except Exception:
            return False

    async def _call_api_with_fallback(
        self,
        endpoint: str,
        method: str = "POST",
        **kwargs,
    ):
        """
        调用API（含自动降级逻辑）- Story 9.5

        降级策略：
        1. 尝试使用代理（如果配置了proxy_provider）
        2. 代理失败时自动降级到直连，重试1次
        3. 记录降级事件到日志（通过proxy_provider.record_usage()）
        4. 直连也失败时抛出DegradeFailedError

        Args:
            endpoint: API端点（如 "/v1/chat/completions"）
            method: HTTP方法（GET/POST/PUT/DELETE）
            **kwargs: 传递给httpx的其他参数

        Returns:
            httpx.Response: API响应对象

        Raises:
            DegradeFailedError: 代理和直连都失败时抛出
            Exception: 其他异常直接抛出（不降级）

        异常降级策略：
        - 降级异常：httpx.ProxyError、httpx.ConnectError、httpx.TimeoutException
        - 不降级异常：httpx.HTTPStatusError（业务错误，应该直接抛出）

        Example:
            >>> # 使用代理
            >>> response = await self._call_api_with_fallback("/v1/chat/completions")
            >>> # 代理失败时自动降级到直连，重试1次
        """
        start_time = time.time()
        proxy_url = None
        proxy_error = None

        # 获取代理URL（如果配置了proxy_provider）
        if self.proxy_provider:
            proxy_url = self.proxy_provider.get_proxy()

        # 构建httpx配置
        config = self._get_httpx_config(proxy_url)

        try:
            # 尝试1：使用代理（如果配置了）
            async with httpx.AsyncClient(**config) as client:
                response = await getattr(client, method.lower())(endpoint, **kwargs)
                response.raise_for_status()

            # 记录成功日志
            response_time = int((time.time() - start_time) * 1000)
            if self.proxy_provider:
                self.proxy_provider.record_usage(
                    ai_provider=self.__class__.__name__,
                    endpoint=endpoint,
                    success=True,
                    response_time=response_time,
                )

            return response

        except (httpx.ProxyError, httpx.ConnectError, httpx.TimeoutException) as e:
            # 代理相关错误，触发降级逻辑
            if proxy_url:
                proxy_error = e
                logger.warning(
                    f"DEGRADED: Proxy failed ({type(e).__name__}), retrying with direct connection"
                )
                # 降级到直连，重试1次
                config = self._get_httpx_config(None)  # 移除代理

                try:
                    async with httpx.AsyncClient(**config) as client:
                        response = await getattr(client, method.lower())(endpoint, **kwargs)
                        response.raise_for_status()

                    # 记录降级成功
                    response_time = int((time.time() - start_time) * 1000)
                    if self.proxy_provider:
                        self.proxy_provider.record_usage(
                            ai_provider=self.__class__.__name__,
                            endpoint=endpoint,
                            success=True,
                            response_time=response_time,
                            error_message=f"DEGRADED: {type(e).__name__}",
                        )

                    return response

                except Exception as fallback_error:
                    # 降级也失败，记录错误并抛出聚合异常
                    response_time = int((time.time() - start_time) * 1000)
                    if self.proxy_provider:
                        self.proxy_provider.record_usage(
                            ai_provider=self.__class__.__name__,
                            endpoint=endpoint,
                            success=False,
                            response_time=response_time,
                            error_message=f"PROXY_AND_DIRECT_FAILED: "
                            f"Proxy failed ({type(proxy_error).__name__}), "
                            f"Direct connection failed ({type(fallback_error).__name__})",
                        )

                    raise DegradeFailedError(
                        f"PROXY_AND_DIRECT_FAILED: "
                        f"Proxy failed ({type(proxy_error).__name__}: {proxy_error}), "
                        f"Direct connection failed ({type(fallback_error).__name__}: {fallback_error})"
                    ) from fallback_error
            else:
                # 没有使用代理，直接抛出原始异常
                raise

        except Exception as e:
            # 其他异常（非代理异常），不降级，直接抛出
            # 记录失败日志
            response_time = int((time.time() - start_time) * 1000)
            if self.proxy_provider:
                self.proxy_provider.record_usage(
                    ai_provider=self.__class__.__name__,
                    endpoint=endpoint,
                    success=False,
                    response_time=response_time,
                    error_message=str(e),
                )
            raise

    def _get_httpx_config(self, proxy_url: Optional[str] = None) -> Dict[str, Any]:
        """
        获取httpx客户端配置 - Story 9.5

        Args:
            proxy_url: 代理URL（可选）

        Returns:
            httpx客户端配置字典

        Note:
            子类可以重写此方法来自定义httpx配置
        """
        config = {
            "timeout": self.config.get("timeout", 60.0),
            "limits": httpx.Limits(max_keepalive_connections=5, max_connections=10),
        }

        if proxy_url:
            config["proxies"] = {"all://": proxy_url}

        return config


class LLMClient(BaseAIClient):
    """
    LLM客户端抽象基类
    用于文案改写、分镜生成、运镜生成等文本生成任务
    """

    async def generate(
        self, prompt: str, max_tokens: int = 2000, temperature: float = 0.7, **kwargs
    ) -> AIResponse:
        """
        生成文本

        Args:
            prompt: 输入提示词
            max_tokens: 最大token数
            temperature: 温度参数
            **kwargs: 其他参数

        Returns:
            AIResponse: 响应对象
        """
        return await self._generate_text(prompt, max_tokens, temperature, **kwargs)

    @abstractmethod
    async def _generate_text(
        self, prompt: str, max_tokens: int, temperature: float, **kwargs
    ) -> AIResponse:
        """具体的文本生成实现"""
        pass


class Text2ImageClient(BaseAIClient):
    """
    文生图客户端抽象基类
    """

    def generate(
        self,
        prompt: str,
        negative_prompt: str = "",
        width: int = 1024,
        height: int = 1024,
        steps: int = 20,
        **kwargs,
    ) -> AIResponse:
        """
        生成图片

        Args:
            prompt: 图片提示词
            negative_prompt: 负面提示词
            width: 宽度
            height: 高度
            steps: 生成步数
            **kwargs: 其他参数

        Returns:
            AIResponse: 包含图片URL的响应对象
        """
        return self._generate_image(prompt, negative_prompt, width, height, steps, **kwargs)

    @abstractmethod
    def _generate_image(
        self, prompt: str, negative_prompt: str, width: int, height: int, steps: int, **kwargs
    ) -> AIResponse:
        """具体的图片生成实现"""
        pass


class Image2VideoClient(BaseAIClient):
    """
    图生视频客户端抽象基类
    """

    async def generate(
        self,
        image_url: str,
        camera_movement: Dict[str, Any],
        duration: float = 3.0,
        fps: int = 24,
        **kwargs,
    ) -> AIResponse:
        """
        生成视频

        Args:
            image_url: 源图片URL
            camera_movement: 运镜参数
            duration: 视频时长
            fps: 帧率
            **kwargs: 其他参数

        Returns:
            AIResponse: 包含视频URL的响应对象
        """
        return await self._generate_video(image_url, camera_movement, duration, fps, **kwargs)

    @abstractmethod
    async def _generate_video(
        self, image_url: str, camera_movement: Dict[str, Any], duration: float, fps: int, **kwargs
    ) -> AIResponse:
        """具体的视频生成实现"""
        pass


class TTSClient(BaseAIClient):
    """
    TTS (Text-to-Speech) 客户端抽象基类
    用于语音合成任务

    Epic 10 Story 10.2: Edge-TTS本地语音合成集成
    """

    async def generate(
        self,
        text: str,
        voice: str = "zh-CN-XiaoxiaoNeural",
        rate: str = "+0%",
        volume: str = "+0%",
        pitch: str = "+0Hz",
        output_format: str = "mp3",
        **kwargs,
    ) -> AIResponse:
        """
        合成语音

        Args:
            text: 要转换的文本
            voice: 音色名称 (如 "zh-CN-XiaoxiaoNeural")
            rate: 语速调整 (如 "+50%", "-50%")
            volume: 音量调整 (如 "+50%", "-50%")
            pitch: 音调调整 (如 "+50Hz", "-50Hz")
            output_format: 输出格式 ("mp3" 或 "wav")
            **kwargs: 其他参数

        Returns:
            AIResponse: 包含音频文件路径或URL的响应对象
        """
        return await self._synthesize_speech(
            text=text,
            voice=voice,
            rate=rate,
            volume=volume,
            pitch=pitch,
            output_format=output_format,
            **kwargs,
        )

    @abstractmethod
    async def _synthesize_speech(
        self,
        text: str,
        voice: str,
        rate: str,
        volume: str,
        pitch: str,
        output_format: str,
        **kwargs,
    ) -> AIResponse:
        """具体的语音合成实现"""
        pass

    @abstractmethod
    async def list_voices(self) -> list:
        """
        获取可用音色列表

        Returns:
            list: 音色信息列表，每个元素包含 name, language, gender 等字段
        """
        pass
