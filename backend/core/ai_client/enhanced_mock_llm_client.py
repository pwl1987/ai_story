"""
增强版 Mock LLM 客户端实现
支持失败场景、可配置响应速度、日志记录
"""

import time
import json
import logging
from typing import Dict, Any, Generator, Optional, List
from .base import LLMClient, AIResponse


logger = logging.getLogger(__name__)


class EnhancedMockLLMClient(LLMClient):
    """
    增强版 Mock LLM 客户端

    新增功能:
    1. 可配置响应速度 (simulate_delay)
    2. 失败场景模拟 (simulate_error)
    3. 请求日志记录 (enable_logging)
    4. 可配置响应数据 (custom_response)
    """

    def __init__(
        self,
        api_url: str = "",
        api_key: str = "",
        model_name: str = "enhanced-mock-model",
        stage_type: str = "",
        timeout: int = 30,
        max_tokens: int = 2000,
        temperature: float = 0.7,
        top_p: float = 0.9,
        # 新增参数
        simulate_delay: float = 0.5,  # 模拟延迟（秒）
        simulate_error: Optional[str] = None,  # 模拟错误类型: "timeout", "rate_limit", "server_error"
        enable_logging: bool = True,  # 是否启用日志
        custom_response: Optional[str] = None,  # 自定义响应
        **kwargs
    ):
        """
        初始化增强版Mock客户端

        Args:
            simulate_delay: 模拟API响应延迟（秒），默认0.5秒
            simulate_error: 模拟错误类型
                - "timeout": 模拟超时错误
                - "rate_limit": 模拟限流错误
                - "server_error": 模拟服务器错误
                - None: 正常响应
            enable_logging: 是否记录请求日志
            custom_response: 自定义响应内容（覆盖默认响应）
        """
        super().__init__(api_url, api_key, model_name)
        self.stage_type = stage_type
        self.simulate_delay = simulate_delay
        self.simulate_error = simulate_error
        self.enable_logging = enable_logging
        self.custom_response = custom_response

        # 请求日志
        self.request_log: List[Dict[str, Any]] = []

    # 增强的模拟响应（保留原有模板，添加custom_response支持）
    MOCK_RESPONSES = {
        "rewrite": """经过改写的故事内容：

在一个宁静的小镇上，住着一位年轻的画家。每天清晨，他都会来到河边，用画笔记录下大自然的美丽瞬间。

这个故事讲述了艺术与生活的完美融合，展现了一个追梦者的日常。通过细腻的笔触，我们看到了他对艺术的执着追求。

改写后的内容更加生动，情感更加饱满，适合进行下一步的分镜创作。""",

        "storyboard": """{
  "scenes": [
    {
      "scene_number": 1,
      "narration": "在一个宁静的小镇上，新的一天开始了",
      "visual_prompt": "A peaceful small town at dawn, sunlight on cobblestone streets, warm golden light, cinematic composition, high quality",
      "shot_type": "wide_shot"
    },
    {
      "scene_number": 2,
      "narration": "年轻的画家像往常一样，带着他的画具出门了",
      "visual_prompt": "A young artist walking towards a river, carrying an easel and painting supplies, morning light, artistic atmosphere, detailed",
      "shot_type": "medium_shot"
    },
    {
      "scene_number": 3,
      "narration": "他在河边架起画架，开始捕捉大自然的美丽",
      "visual_prompt": "Artist painting by a beautiful river, easel setup, natural scenery, peaceful atmosphere, professional photography",
      "shot_type": "close_up"
    }
  ]
}""",

        "camera_movement": """{
  "movement_type": "slow_zoom_in",
  "movement_params": {
    "start_scale": 1.0,
    "end_scale": 1.2,
    "duration": 3.0,
    "easing": "ease_in_out"
  },
  "description": "缓慢推进镜头，聚焦主体"
}""",

        "default": """这是一个模拟的 LLM 响应。

在实际使用中，这里会返回根据提示词生成的真实内容。Mock API 主要用于：
1. 开发环境的快速测试
2. 工作流程的验证
3. 前端界面的调试
4. 成本控制（避免频繁调用真实 API）

请在生产环境中配置真实的 LLM 服务。"""
    }

    def _log_request(self, prompt: str, **kwargs):
        """记录请求日志"""
        if not self.enable_logging:
            return

        log_entry = {
            'timestamp': time.time(),
            'model': self.model_name,
            'stage_type': self.stage_type,
            'prompt_length': len(prompt),
            'simulate_delay': self.simulate_delay,
            'simulate_error': self.simulate_error,
            'kwargs': kwargs
        }

        self.request_log.append(log_entry)
        logger.debug(f"MockLLM Request: {log_entry}")

    def _simulate_error_scenario(self) -> AIResponse:
        """模拟错误场景"""
        if self.simulate_error == "timeout":
            return AIResponse(
                success=False,
                text="",
                error="模拟超时错误: API请求超时（超过30秒）",
                metadata={'simulate_timeout': True}
            )

        elif self.simulate_error == "rate_limit":
            return AIResponse(
                success=False,
                text="",
                error="模拟限流错误: API调用频率超限，请稍后重试",
                metadata={'simulate_rate_limit': True, 'retry_after': 60}
            )

        elif self.simulate_error == "server_error":
            return AIResponse(
                success=False,
                text="",
                error="模拟服务器错误: 500 Internal Server Error",
                metadata={'simulate_server_error': True}
            )

        else:
            # 未知错误类型，返回通用错误
            return AIResponse(
                success=False,
                text="",
                error=f"未知错误类型: {self.simulate_error}",
                metadata={'simulate_unknown_error': True}
            )

    async def _generate_text(
        self,
        prompt: str,
        max_tokens: int,
        temperature: float,
        **kwargs
    ) -> AIResponse:
        """
        生成模拟的文本响应（增强版）

        新增功能:
        - 可配置延迟
        - 失败场景模拟
        - 日志记录
        - 自定义响应
        """
        start_time = time.time()

        # 记录请求日志
        self._log_request(prompt, max_tokens=max_tokens, temperature=temperature, **kwargs)

        # 如果配置了错误模拟，返回错误响应
        if self.simulate_error:
            return self._simulate_error_scenario()

        # 模拟可配置的API延迟
        if self.simulate_delay > 0:
            await asyncio.sleep(self.simulate_delay)

        # 使用自定义响应或默认响应
        if self.custom_response:
            response_text = self.custom_response
        else:
            response_text = self._get_mock_response(prompt)

        # 模拟token使用量
        tokens_used = len(response_text) // 4

        latency_ms = int((time.time() - start_time) * 1000)

        return AIResponse(
            success=True,
            text=response_text,
            metadata={
                'tokens_used': tokens_used,
                'latency_ms': latency_ms,
                'model': self.model_name,
                'is_mock': True,
                'simulate_delay': self.simulate_delay
            }
        )

    def generate_stream(
        self,
        prompt: str,
        system_prompt: str = "",
        max_tokens: int = 2000,
        temperature: float = 0.7,
        **kwargs
    ) -> Generator[Dict[str, Any], None, None]:
        """
        流式生成模拟文本（增强版）

        新增功能:
        - 可配置延迟
        - 失败场景模拟
        - 日志记录
        """
        start_time = time.time()

        # 记录请求日志
        self._log_request(
            prompt,
            system_prompt=system_prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            stream=True,
            **kwargs
        )

        # 如果配置了错误模拟，返回错误chunk
        if self.simulate_error:
            error_response = self._simulate_error_scenario()
            yield {
                'type': 'error',
                'error': error_response.error
            }
            return

        # 获取响应文本
        if self.custom_response:
            full_text = self.custom_response
        else:
            full_text = self._get_mock_response(system_prompt or prompt)

        # 模拟可配置的流式延迟
        if self.simulate_delay > 0:
            time.sleep(self.simulate_delay)

        # 分块返回（模拟流式）
        words = full_text.split()
        chunk_size = max(1, len(words) // 5)  # 分成5个chunk

        for i in range(0, len(words), chunk_size):
            chunk_words = words[i:i + chunk_size]
            chunk_text = ' '.join(chunk_words)

            yield {
                'type': 'token',
                'content': chunk_text,
                'full_text': full_text,
                'progress': (i + chunk_size) / len(words) * 100
            }

        # 返回完成信号
        latency_ms = int((time.time() - start_time) * 1000)

        yield {
            'type': 'done',
            'full_text': full_text,
            'metadata': {
                'latency_ms': latency_ms,
                'simulate_delay': self.simulate_delay
            }
        }

    async def validate_config(self) -> bool:
        """
        验证配置（增强版）

        新增功能:
        - 验证simulate_delay是否合理
        - 验证simulate_error是否有效
        """
        # 验证延迟参数
        if self.simulate_delay < 0:
            logger.warning(f"simulate_delay不能为负数: {self.simulate_delay}")
            return False

        if self.simulate_delay > 60:
            logger.warning(f"simulate_delay过大: {self.simulate_delay}秒")

        # 验证错误类型
        valid_errors = [None, "timeout", "rate_limit", "server_error"]
        if self.simulate_error not in valid_errors:
            logger.warning(f"无效的simulate_error: {self.simulate_error}")
            return False

        return True

    def get_request_log(self) -> List[Dict[str, Any]]:
        """获取请求日志"""
        return self.request_log.copy()

    def clear_request_log(self):
        """清空请求日志"""
        self.request_log.clear()

    def set_custom_response(self, response: str):
        """设置自定义响应"""
        self.custom_response = response
        logger.info(f"设置自定义响应: {response[:100]}...")

    def set_simulate_delay(self, delay: float):
        """设置模拟延迟"""
        self.simulate_delay = delay
        logger.info(f"设置模拟延迟: {delay}秒")

    def set_simulate_error(self, error_type: Optional[str]):
        """设置模拟错误类型"""
        self.simulate_error = error_type
        logger.info(f"设置模拟错误: {error_type}")

    def _get_mock_response(self, prompt: str) -> str:
        """获取模拟响应（原有逻辑）"""
        # 根据stage_type返回对应的响应
        if self.stage_type and self.stage_type in self.MOCK_RESPONSES:
            return self.MOCK_RESPONSES[self.stage_type]

        # 根据提示词关键词判断
        prompt_lower = prompt.lower()

        if "分镜" in prompt_lower or "storyboard" in prompt_lower:
            return self.MOCK_RESPONSES["storyboard"]
        elif "运镜" in prompt_lower or "camera" in prompt_lower:
            return self.MOCK_RESPONSES["camera_movement"]
        else:
            return self.MOCK_RESPONSES["default"]


# 导入asyncio（用于sleep）
import asyncio
