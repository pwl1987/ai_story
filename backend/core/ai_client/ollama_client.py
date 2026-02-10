"""
Ollama本地LLM客户端实现

遵循SOLID原则:
- 继承LLMClient抽象基类 (依赖倒置)
- 实现对话补全和流式响应 (接口隔离)
- 支持Fallback机制 (开闭原则)

Epic 10 Story 10.1: Ollama本地LLM引擎集成
"""

import logging
from typing import AsyncGenerator, Dict, Any, Optional

import httpx
from ollama import Client as OllamaSyncClient

from .base import AIResponse, LLMClient

logger = logging.getLogger(__name__)


class OllamaClient(LLMClient):
    """
    Ollama本地LLM客户端

    功能:
    - 连接本地Ollama服务 (http://localhost:11434)
    - 实现对话补全接口
    - 支持流式和非流式响应
    - 自动Fallback到OpenAI (可选)

    配置:
    - api_url: Ollama服务地址 (默认: http://localhost:11434)
    - api_key: 占位符 (Ollama不需要，但保持接口一致)
    - model_name: 模型名称 (如: llama2:7b, llama3:8b, qwen:7b)
    """

    def __init__(
        self,
        api_url: str = "http://localhost:11434",
        api_key: str = "ollama",  # Ollama不需要API key，但保持接口一致
        model_name: str = "llama2:7b",
        proxy_id: Optional[int] = None,
        project_id: Optional[int] = None,
        fallback_to_openai: bool = True,
        **kwargs,
    ):
        """
        初始化Ollama客户端

        Args:
            api_url: Ollama服务地址
            api_key: 占位符 (Ollama不需要)
            model_name: 模型名称
            proxy_id: 代理配置ID (可选)
            project_id: 项目ID (可选)
            fallback_to_openai: 是否启用Fallback到OpenAI
            **kwargs: 其他配置参数
        """
        super().__init__(
            api_url=api_url,
            api_key=api_key,
            model_name=model_name,
            proxy_id=proxy_id,
            project_id=project_id,
            **kwargs,
        )

        self.fallback_to_openai = fallback_to_openai
        self.fallback_client = None

        # 初始化同步客户端 (用于验证配置)
        self.sync_client = OllamaSyncClient(host=api_url)

        # Fallback客户端 (延迟加载)
        if fallback_to_openai:
            self._init_fallback_client()

    def _init_fallback_client(self):
        """初始化Fallback客户端 (OpenAI)"""
        try:
            from .openai_client import OpenAIClient

            # 使用相同的项目ID和代理配置
            self.fallback_client = OpenAIClient(
                api_url=self.config.get("fallback_api_url", "https://api.openai.com/v1"),
                api_key=self.config.get("fallback_api_key", ""),
                model_name=self.config.get("fallback_model", "gpt-3.5-turbo"),
                proxy_id=None,  # Fallback不使用代理
                project_id=self.project_id,
            )
            logger.info(f"Ollama客户端初始化Fallback到OpenAI: {self.fallback_client.model_name}")
        except Exception as e:
            logger.warning(f"无法初始化Fallback OpenAI客户端: {e}")
            self.fallback_client = None

    async def _generate_text(
        self, prompt: str, max_tokens: int, temperature: float, **kwargs
    ) -> AIResponse:
        """
        生成文本 (非流式)

        Args:
            prompt: 输入提示词
            max_tokens: 最大token数
            temperature: 温度参数
            **kwargs: 其他参数

        Returns:
            AIResponse: 响应对象
        """
        try:
            # 调用Ollama生成API
            response = await self._call_ollama_chat(
                prompt=prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                stream=False,
                **kwargs,
            )

            # 提取响应文本
            text = self._extract_response_text(response)

            return AIResponse(
                success=True,
                text=text,
                data={"model": self.model_name},
                metadata={
                    "provider": "ollama",
                    "engine": "local_llm",
                    "response_time": response.get("total_duration", 0),
                },
            )

        except Exception as e:
            logger.error(f"Ollama生成失败: {e}")

            # Fallback到OpenAI (如果启用)
            if self.fallback_to_openai and self.fallback_client:
                logger.info("触发Fallback到OpenAI")
                return await self.fallback_client.generate(
                    prompt=prompt, max_tokens=max_tokens, temperature=temperature, **kwargs
                )

            # 失败返回
            return AIResponse(success=False, text="", error=str(e))

    async def _generate_text_stream(
        self, prompt: str, max_tokens: int, temperature: float, **kwargs
    ) -> AsyncGenerator[AIResponse, None]:
        """
        生成文本 (流式)

        Args:
            prompt: 输入提示词
            max_tokens: 最大token数
            temperature: 温度参数
            **kwargs: 其他参数

        Yields:
            AIResponse: 流式响应片段
        """
        try:
            # 调用Ollama流式生成API
            async for response_chunk in self._call_ollama_chat_stream(
                prompt=prompt, max_tokens=max_tokens, temperature=temperature, **kwargs
            ):
                yield response_chunk

        except Exception as e:
            logger.error(f"Ollama流式生成失败: {e}")

            # Fallback到OpenAI (如果启用)
            if self.fallback_to_openai and self.fallback_client:
                logger.info("触发Fallback到OpenAI (流式)")
                async for chunk in self.fallback_client.generate_stream(
                    prompt=prompt, max_tokens=max_tokens, temperature=temperature, **kwargs
                ):
                    yield chunk
            else:
                # 失败返回错误响应
                yield AIResponse(success=False, text="", error=str(e))

    async def _call_ollama_chat(
        self, prompt: str, max_tokens: int, temperature: float, stream: bool, **kwargs
    ) -> Dict[str, Any]:
        """
        调用Ollama Chat API

        Args:
            prompt: 提示词
            max_tokens: 最大token数
            temperature: 温度
            stream: 是否流式
            **kwargs: 其他参数

        Returns:
            Dict: Ollama响应
        """
        # 使用httpx直接调用Ollama API
        url = f"{self.api_url}/api/chat"

        payload = {
            "model": self.model_name,
            "messages": [{"role": "user", "content": prompt}],
            "stream": stream,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }

        # 添加其他参数
        if "top_p" in kwargs:
            payload["options"]["top_p"] = kwargs["top_p"]

        timeout = self.config.get("timeout", 120.0)

        # 使用BaseAIClient的代理支持
        response = await self._call_api_with_fallback(
            f"{url}/", method="POST", json=payload, timeout=httpx.Timeout(timeout)
        )

        # 解析响应
        if stream:
            return {"stream": response, "stream": True}
        else:
            return response.json()

    async def _call_ollama_chat_stream(
        self, prompt: str, max_tokens: int, temperature: float, **kwargs
    ) -> AsyncGenerator[AIResponse, None]:
        """
        调用Ollama流式Chat API

        Args:
            prompt: 提示词
            max_tokens: 最大token数
            temperature: 温度
            **kwargs: 其他参数

        Yields:
            AIResponse: 流式响应片段
        """
        url = f"{self.api_url}/api/chat"

        payload = {
            "model": self.model_name,
            "messages": [{"role": "user", "content": prompt}],
            "stream": True,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }

        if "top_p" in kwargs:
            payload["options"]["top_p"] = kwargs["top_p"]

        timeout = self.config.get("timeout", 120.0)

        # 使用BaseAIClient的代理支持
        response = await self._call_api_with_fallback(
            f"{url}/", method="POST", json=payload, timeout=httpx.Timeout(timeout)
        )

        # 解析流式响应
        async for line in response.aiter_lines():
            if line.strip():
                import json

                try:
                    chunk = json.loads(line)
                    if chunk.get("done", False):
                        break

                    if "message" in chunk and "content" in chunk["message"]:
                        yield AIResponse(
                            success=True,
                            text=chunk["message"]["content"],
                            data={"model": self.model_name},
                            metadata={"provider": "ollama", "engine": "local_llm"},
                        )
                except json.JSONDecodeError:
                    logger.warning(f"无法解析流式响应行: {line}")
                    continue

    def _extract_response_text(self, response: Dict[str, Any]) -> str:
        """
        从Ollama响应中提取文本

        Args:
            response: Ollama API响应

        Returns:
            str: 提取的文本
        """
        try:
            if "message" in response:
                return response["message"]["content"]
            elif "response" in response:
                return response["response"]
            else:
                return str(response)
        except Exception as e:
            logger.error(f"提取响应文本失败: {e}, response: {response}")
            return ""

    async def validate_config(self) -> bool:
        """
        验证Ollama配置是否有效

        Returns:
            bool: 配置是否有效
        """
        try:
            # 使用同步客户端测试连接
            models = self.sync_client.list()
            logger.info(
                f"Ollama连接成功，可用模型: {[m.get('name', m.get('id', 'unknown')) for m in models]}"
            )
            return True
        except Exception as e:
            logger.error(f"Ollama配置验证失败: {e}")
            return False

    async def health_check(self) -> bool:
        """
        健康检查

        Returns:
            bool: 服务是否健康
        """
        try:
            # 测试基本连接
            return await self.validate_config()
        except Exception:
            return False
