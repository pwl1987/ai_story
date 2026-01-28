"""
Anthropic Claude LLM客户端实现
支持Claude 3 Opus/Sonnet/Haiku模型
支持流式和非流式生成
"""

import json
import time
from typing import Any, Dict, Generator

import requests

from .base import AIResponse, LLMClient


class ClaudeClient(LLMClient):
    """
    Anthropic Claude客户端实现
    支持Claude 3 Opus/Sonnet/Haiku模型
    支持流式和非流式生成
    """

    def _generate_text(
        self,
        prompt: str,
        max_tokens: int = None,
        temperature: float = None,
        system_prompt: str = "",
        **kwargs
    ) -> AIResponse:
        """
        生成文本(非流式)

        Args:
            prompt: 用户提示词
            max_tokens: 最大token数
            temperature: 温度参数
            system_prompt: 系统提示词
            **kwargs: 其他参数

        Returns:
            AIResponse: 生成结果
        """

        start_time = time.time()

        # Claude API使用x-api-key头
        headers = {
            'x-api-key': self.api_key,
            'Content-Type': 'application/json',
            'anthropic-version': '2023-06-01'
        }

        # Claude API请求格式
        payload = {
            'model': self.model_name,
            'max_tokens': max_tokens or self.config.get("max_tokens", 4096),
            'temperature': temperature or self.config.get("temperature", 0.7),
            'messages': [
                {'role': 'user', 'content': prompt}
            ]
        }

        # 添加系统提示词（如果有）
        if system_prompt:
            payload['system'] = system_prompt

        # 添加其他参数
        payload.update(kwargs)

        try:
            timeout = self.config.get('timeout', 60)

            # Claude API端点
            api_url = self.api_url if self.api_url else 'https://api.anthropic.com/v1/messages'

            response = requests.post(
                f'{api_url}',
                headers=headers,
                json=payload,
                timeout=timeout
            )

            if response.status_code == 200:
                result = response.json()
                latency_ms = int((time.time() - start_time) * 1000)

                # 提取文本内容
                content = result.get('content', [])
                text = ''
                if content and len(content) > 0:
                    # Claude返回的content是一个数组，第一个元素的text字段包含文本
                    text = content[0].get('text', '')

                return AIResponse(
                    success=True,
                    text=text,
                    metadata={
                        'tokens_used': result.get('usage', {}).get('input_tokens', 0) + result.get('usage', {}).get('output_tokens', 0),
                        'input_tokens': result.get('usage', {}).get('input_tokens', 0),
                        'output_tokens': result.get('usage', {}).get('output_tokens', 0),
                        'latency_ms': latency_ms,
                        'model': self.model_name,
                        'stop_reason': result.get('stop_reason')
                    }
                )
            else:
                return AIResponse(
                    success=False,
                    error=f'Claude API请求失败: {response.status_code} - {response.text}'
                )

        except requests.RequestException as e:
            return AIResponse(
                success=False,
                error=f'网络请求错误: {e!s}'
            )
        except Exception as e:
            return AIResponse(
                success=False,
                error=f'未知错误: {e!s}'
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
        流式生成文本

        Args:
            prompt: 用户提示词
            system_prompt: 系统提示词
            max_tokens: 最大token数
            temperature: 温度参数
            **kwargs: 其他参数

        Yields:
            Dict包含: type (token/done/error), content, metadata
        """

        # Claude API使用x-api-key头
        headers = {
            'x-api-key': self.api_key,
            'Content-Type': 'application/json',
            'anthropic-version': '2023-06-01'
        }

        # Claude API请求格式
        payload = {
            'model': self.model_name,
            'max_tokens': max_tokens,
            'temperature': temperature,
            'messages': [
                {'role': 'user', 'content': prompt}
            ],
            'stream': True
        }

        # 添加系统提示词（如果有）
        if system_prompt:
            payload['system'] = system_prompt

        # 添加其他参数
        payload.update(kwargs)

        start_time = time.time()
        full_text = ""

        try:
            timeout = self.config.get('timeout', 300)
            api_url = self.api_url if self.api_url else 'https://api.anthropic.com/v1/messages'

            response = requests.post(
                api_url,
                headers=headers,
                json=payload,
                timeout=timeout,
                stream=True
            )

            if response.status_code != 200:
                yield {
                    'type': 'error',
                    'error': f'Claude API请求失败: {response.status_code} - {response.text}'
                }
                return

            # 读取SSE流
            buffer = ''
            for chunk_bytes in response.iter_content(chunk_size=1024):
                if not chunk_bytes:
                    continue

                buffer += chunk_bytes.decode('utf-8')

                # 按行分割
                while '\n' in buffer:
                    line, buffer = buffer.split('\n', 1)
                    line = line.strip()

                    if not line or line == 'data: [DONE]':
                        continue

                    if line.startswith('data: '):
                        try:
                            json_str = line[6:]  # 移除 'data: ' 前缀
                            chunk = json.loads(json_str)

                            # Claude流式响应格式
                            if chunk.get('type') == 'content_block_delta':
                                # 提取token
                                delta = chunk.get('delta', {})
                                content = delta.get('text', '')
                                if content:
                                    full_text += content
                                    yield {
                                        'type': 'token',
                                        'content': content,
                                        'full_text': full_text
                                    }

                            elif chunk.get('type') == 'message_stop':
                                # 计算延迟
                                latency_ms = int((time.time() - start_time) * 1000)

                                yield {
                                    'type': 'done',
                                    'full_text': full_text,
                                    'metadata': {
                                        'latency_ms': latency_ms,
                                        'model': self.model_name,
                                        'stop_reason': chunk.get('message', {}).get('stop_reason')
                                    }
                                }

                        except json.JSONDecodeError:
                            continue

        except requests.RequestException as e:
            yield {
                'type': 'error',
                'error': f'网络请求错误: {e!s}'
            }
        except Exception as e:
            yield {
                'type': 'error',
                'error': f'未知错误: {e!s}'
            }

    def validate_config(self) -> bool:
        """
        验证配置

        Returns:
            bool: 配置是否有效
        """
        if not self.api_key or not self.model_name:
            return False

        # 简单的连通性测试
        try:
            headers = {
                'x-api-key': self.api_key,
                'Content-Type': 'application/json',
                'anthropic-version': '2023-06-01'
            }

            # 使用最小化的请求测试连通性
            api_url = self.api_url if self.api_url else 'https://api.anthropic.com/v1/messages'

            # 发送一个小请求验证API key
            response = requests.post(
                api_url,
                headers=headers,
                json={
                    'model': self.model_name,
                    'max_tokens': 1,
                    'messages': [{'role': 'user', 'content': 'test'}]
                },
                timeout=10
            )

            # 200 (成功) 或 400 (参数错误但API可达) 或 401 (认证问题但API可达)
            return response.status_code in [200, 400, 401]

        except Exception:
            return False

    async def generate(
        self,
        prompt: str,
        max_tokens: int = 2000,
        temperature: float = 0.7,
        **kwargs
    ) -> AIResponse:
        """
        异步生成文本（非流式）

        Args:
            prompt: 输入提示词
            max_tokens: 最大token数
            temperature: 温度参数
            **kwargs: 其他参数

        Returns:
            AIResponse: 生成结果
        """
        # 同步调用
        return self._generate_text(
            prompt=prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            **kwargs
        )
