"""
core.ai_client.factory 单元测试

测试AI客户端工厂模式的客户端创建逻辑
"""

import pytest

from core.ai_client.factory import _create_mock_client, create_ai_client, create_ai_client_safe
from core.ai_client.mock_image2video_client import MockImage2VideoClient
from core.ai_client.mock_llm_client import MockLLMClient
from core.ai_client.mock_text2image_client import MockText2ImageClient


@pytest.mark.unit
class TestCreateMockClient:
    """测试_create_mock_client函数"""

    @pytest.fixture
    def mock_llm_provider(self):
        """创建Mock LLM Provider对象"""

        class Provider:
            name = "OpenAI"
            executor_class = "core.ai_client.openai_client.OpenAIClient"
            model_name = "gpt-4"

        return Provider()

    @pytest.fixture
    def mock_text2image_provider(self):
        """创建Mock文生图Provider"""

        class Provider:
            name = "Stable Diffusion"
            executor_class = "core.ai_client.text2image_client.Text2ImageClient"
            model_name = "stable-diffusion-v1.5"

        return Provider()

    @pytest.fixture
    def mock_image2video_provider(self):
        """创建Mock图生视频Provider"""

        class Provider:
            name = "Runway"
            executor_class = "core.ai_client.image2video_client.Image2VideoClient"
            model_name = "gen2"

        return Provider()

    def test_create_mock_llm_client(self, mock_llm_provider):
        """测试创建Mock LLM客户端"""
        client = _create_mock_client(mock_llm_provider)

        assert isinstance(client, MockLLMClient)
        assert client.model_name == "gpt-4"
        assert client.api_url == "mock://llm"

    def test_create_mock_text2image_client(self, mock_text2image_provider):
        """测试创建Mock文生图客户端"""
        client = _create_mock_client(mock_text2image_provider)

        assert isinstance(client, MockText2ImageClient)
        assert client.model_name == "stable-diffusion-v1.5"

    def test_create_mock_image2video_client(self, mock_image2video_provider):
        """测试创建Mock图生视频客户端"""
        client = _create_mock_client(mock_image2video_provider)

        assert isinstance(client, MockImage2VideoClient)
        assert client.model_name == "gen2"

    def test_create_mock_client_default_fallback(self):
        """测试无法识别类型时默认使用LLM客户端"""

        class UnknownProvider:
            name = "Unknown"
            executor_class = "some.unknown.Class"
            model_name = "unknown-model"

        client = _create_mock_client(UnknownProvider())

        # 应该fallback到MockLLMClient
        assert isinstance(client, MockLLMClient)
        assert client.model_name == "unknown-model"


@pytest.mark.unit
class TestCreateAIClient:
    """测试create_ai_client函数"""

    @pytest.fixture
    def mock_provider(self):
        """创建Mock Provider对象"""

        class Provider:
            name = "Test Provider"
            executor_class = "core.ai_client.openai_client.OpenAIClient"
            model_name = "gpt-4"
            api_url = "https://api.openai.com"
            api_key = "test_key"
            timeout = 30
            max_tokens = 2000
            temperature = 0.7
            top_p = 1.0
            extra_config = {}

        return Provider()

    def test_create_client_with_mock_enabled(self, mock_provider, monkeypatch):
        """测试启用Mock模式时创建Mock客户端"""
        monkeypatch.setenv("ENABLE_MOCK_AI", "true")

        client = create_ai_client(mock_provider)

        assert isinstance(client, MockLLMClient)
        assert client.model_name == "gpt-4"

    def test_create_client_without_mock_succeeds(self, mock_provider, monkeypatch):
        """测试未启用Mock时工厂函数会成功创建客户端（延迟验证）"""
        # 确保环境变量未设置
        monkeypatch.delenv("ENABLE_MOCK_AI", raising=False)

        # factory函数采用延迟验证设计，会成功创建客户端对象
        # 实际配置验证在validate_config()或调用API时进行
        client = create_ai_client(mock_provider)

        # 验证客户端对象创建成功
        assert client is not None
        assert client.model_name == "gpt-4"

    def test_create_client_with_none_provider_raises_error(self):
        """测试Provider为None时抛出异常"""
        with pytest.raises(ValueError, match="ModelProvider实例不能为空"):
            create_ai_client(None)


@pytest.mark.unit
class TestCreateAIClientSafe:
    """测试create_ai_client_safe安全版本"""

    @pytest.fixture
    def invalid_provider(self):
        """创建无效Provider对象"""

        class Provider:
            name = "Invalid Provider"
            executor_class = "non.existent.Class"
            model_name = "invalid"

        return Provider()

    def test_create_client_safe_with_invalid_provider(self, invalid_provider, monkeypatch):
        """测试安全版本捕获异常并返回None"""
        monkeypatch.delenv("ENABLE_MOCK_AI", raising=False)

        client = create_ai_client_safe(invalid_provider)

        # 应该捕获异常并返回None
        assert client is None

    def test_create_client_safe_with_none_provider(self):
        """测试安全版本处理None provider"""
        client = create_ai_client_safe(None)

        assert client is None


@pytest.mark.unit
class TestFactoryIntegration:
    """工厂模式集成测试"""

    def test_factory_with_env_var_integration(self, monkeypatch):
        """测试环境变量集成"""
        # 设置环境变量
        monkeypatch.setenv("ENABLE_MOCK_AI", "true")

        class Provider:
            name = "Test"
            executor_class = "core.ai_client.openai_client.OpenAIClient"
            model_name = "gpt-4"

        client = create_ai_client(Provider())

        # 验证创建了Mock客户端
        assert isinstance(client, MockLLMClient)
        assert client.api_url == "mock://llm"

    def test_factory_case_insensitive_env_var(self, monkeypatch):
        """测试环境变量大小写不敏感"""
        # 测试不同的环境变量值
        for env_value in ["true", "True", "TRUE"]:
            monkeypatch.setenv("ENABLE_MOCK_AI", env_value)

            class Provider:
                name = "Test"
                executor_class = "core.ai_client.openai_client.OpenAIClient"
                model_name = "gpt-4"

            client = create_ai_client(Provider())
            assert isinstance(client, MockLLMClient)

    def test_factory_env_var_false(self, monkeypatch):
        """测试环境变量为false时不使用Mock"""
        monkeypatch.setenv("ENABLE_MOCK_AI", "false")

        class Provider:
            name = "Test"
            executor_class = "core.ai_client.openai_client.OpenAIClient"
            model_name = "gpt-4"

        # 应该尝试创建真实客户端（会抛出异常）
        with pytest.raises(Exception):
            create_ai_client(Provider())

    def test_factory_multiple_provider_types(self, monkeypatch):
        """测试工厂支持多种provider类型"""
        monkeypatch.setenv("ENABLE_MOCK_AI", "true")

        # 测试LLM类型
        class LLMProvider:
            name = "OpenAI"
            executor_class = "core.ai_client.openai_client.OpenAIClient"
            model_name = "gpt-4"

        llm_client = create_ai_client(LLMProvider())
        assert isinstance(llm_client, MockLLMClient)

        # 测试文生图类型
        class ImageProvider:
            name = "Stable Diffusion"
            executor_class = "core.ai_client.text2image_client.Text2ImageClient"
            model_name = "sdxl"

        image_client = create_ai_client(ImageProvider())
        assert isinstance(image_client, MockText2ImageClient)

        # 测试图生视频类型
        class VideoProvider:
            name = "Runway"
            executor_class = "core.ai_client.image2video_client.Image2VideoClient"
            model_name = "gen2"

        video_client = create_ai_client(VideoProvider())
        assert isinstance(video_client, MockImage2VideoClient)
