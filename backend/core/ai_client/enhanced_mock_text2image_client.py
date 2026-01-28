"""
增强版Mock Text2Image客户端
支持可配置延迟、失败场景模拟、日志记录
"""

import time
import logging
from typing import Dict, Any, Generator, Optional, List
from .base import Text2ImageClient, AIResponse


logger = logging.getLogger(__name__)


class EnhancedMockText2ImageClient(Text2ImageClient):
    """
    增强版 Mock Text2Image 客户端

    新增功能:
    1. 可配置响应速度
    2. 失败场景模拟
    3. 请求日志记录
    4. 可配置图片URL
    """

    def __init__(
        self,
        api_url: str = "",
        api_key: str = "",
        model_name: str = "enhanced-mock-image-model",
        # 新增参数
        simulate_delay: float = 1.0,  # 模拟延迟（秒）
        simulate_error: Optional[str] = None,  # 模拟错误类型
        enable_logging: bool = True,
        custom_image_url: Optional[str] = None,  # 自定义图片URL
        **kwargs
    ):
        """
        初始化增强版Mock Text2Image客户端
        """
        super().__init__(api_url, api_key, model_name)
        self.simulate_delay = simulate_delay
        self.simulate_error = simulate_error
        self.enable_logging = enable_logging
        self.custom_image_url = custom_image_url

        # 请求日志
        self.request_log: List[Dict[str, Any]] = []

    def _log_request(self, prompt: str, width: int, height: int, **kwargs):
        """记录请求日志"""
        if not self.enable_logging:
            return

        log_entry = {
            'timestamp': time.time(),
            'model': self.model_name,
            'prompt_length': len(prompt),
            'width': width,
            'height': height,
            'simulate_delay': self.simulate_delay,
            'simulate_error': self.simulate_error
        }

        self.request_log.append(log_entry)
        logger.debug(f"MockText2Image Request: {log_entry}")

    def _simulate_error_scenario(self) -> AIResponse:
        """模拟错误场景"""
        if self.simulate_error == "timeout":
            return AIResponse(
                success=False,
                data={},
                error="模拟超时错误: 图片生成超时（超过60秒）"
            )

        elif self.simulate_error == "rate_limit":
            return AIResponse(
                success=False,
                data={},
                error="模拟限流错误: API调用频率超限"
            )

        elif self.simulate_error == "server_error":
            return AIResponse(
                success=False,
                data={},
                error="模拟服务器错误: 500 Internal Server Error"
            )

        return AIResponse(
            success=False,
            data={},
            error=f"未知错误类型: {self.simulate_error}"
        )

    async def generate(
        self,
        prompt: str,
        width: int = 1024,
        height: int = 1024,
        **kwargs
    ) -> AIResponse:
        """
        生成图片（增强版）
        """
        start_time = time.time()

        # 记录日志
        self._log_request(prompt, width, height, **kwargs)

        # 模拟错误场景
        if self.simulate_error:
            return self._simulate_error_scenario()

        # 模拟延迟
        if self.simulate_delay > 0:
            await asyncio.sleep(self.simulate_delay)

        # 使用自定义URL或生成默认URL
        if self.custom_image_url:
            image_url = self.custom_image_url
        else:
            image_url = f"http://localhost:8000/mock/image/{int(time.time())}.jpg"

        latency_ms = int((time.time() - start_time) * 1000)

        return AIResponse(
            success=True,
            data={
                'image_url': image_url,
                'width': width,
                'height': height
            },
            metadata={
                'latency_ms': latency_ms,
                'model': self.model_name,
                'is_mock': True
            }
        )

    def get_request_log(self) -> List[Dict[str, Any]]:
        """获取请求日志"""
        return self.request_log.copy()

    def set_custom_image_url(self, url: str):
        """设置自定义图片URL"""
        self.custom_image_url = url

    def set_simulate_delay(self, delay: float):
        """设置模拟延迟"""
        self.simulate_delay = delay

    def set_simulate_error(self, error_type: Optional[str]):
        """设置模拟错误类型"""
        self.simulate_error = error_type


import asyncio
