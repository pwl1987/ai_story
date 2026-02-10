"""
GLM-4.7 集成测试（同步版本）
运行: uv run pytest apps/models/tests/test_glm_integration.py -v -s
"""

import asyncio
import pytest
from apps.models.models import ModelProvider
from core.ai_client.factory import create_ai_client


@pytest.mark.django_db
class TestGLMIntegration:
    """GLM-4.7 集成测试"""

    def test_glm_provider_exists(self):
        """测试 GLM Provider 是否存在"""
        provider = ModelProvider.objects.filter(name="167778.xyz GLM API").first()
        assert provider is not None, "GLM Provider 不存在"
        assert provider.model_name == "GLM-4.7"
        assert provider.is_active is True
        assert provider.api_url == "https://api.167778.xyz/v1"

    def test_glm_client_creation(self):
        """测试 GLM 客户端创建"""
        provider = ModelProvider.objects.filter(name="167778.xyz GLM API").first()
        assert provider is not None

        client = create_ai_client(provider)
        assert client is not None
        assert client.model_name == "GLM-4.7"
        assert client.api_url == "https://api.167778.xyz/v1"

    def test_glm_api_call(self):
        """测试 GLM API 调用（同步）"""
        provider = ModelProvider.objects.filter(name="167778.xyz GLM API").first()
        assert provider is not None

        client = create_ai_client(provider)

        # 使用 asyncio 运行异步方法
        response = asyncio.run(client.generate("请用一句话介绍人工智能"))

        assert response.success is True, f"API 调用失败: {response.error}"
        assert response.text is not None, "响应内容为 None"

        # 验证内容不为空（可能来自 reasoning_content）
        text = response.text.strip()
        assert len(text) > 0, "响应内容为空"

        print("\n✅ API 调用成功")
        print(f"💬 回复: {text[:200]}")
        print(f"📊 Token 使用: {response.metadata.get('tokens_used', 'N/A')}")

    def test_glm_reasoning_content_support(self):
        """测试 GLM reasoning_content 格式支持"""
        provider = ModelProvider.objects.filter(name="167778.xyz GLM API").first()
        assert provider is not None

        client = create_ai_client(provider)
        response = asyncio.run(client.generate("你好，请介绍一下自己"))

        assert response.success is True

        # 验证客户端正确处理了 reasoning_content
        # (OpenAI 客户端已修改以支持此格式)
        text = response.text.strip()
        assert len(text) > 0, "reasoning_content 提取失败"

        print("\n✅ reasoning_content 支持正常")
        print(f"💬 内容长度: {len(text)} 字符")
        print(f"💬 内容预览: {text[:150]}...")
