"""
core.ai_client.base 单元测试

测试AI客户端抽象基类和数据结构
"""

import pytest

from core.ai_client.base import (
    AIResponse,
    BaseAIClient,
    Image2VideoClient,
    LLMClient,
    Text2ImageClient,
)


@pytest.mark.unit
class TestAIResponse:
    """测试AIResponse数据类"""

    def test_create_response_with_all_fields(self):
        """测试创建包含所有字段的响应"""
        response = AIResponse(
            success=True,
            text="Generated text",
            data={'key': 'value'},
            metadata={'model': 'gpt-4', 'tokens': 100},
            error=None
        )

        assert response.success is True
        assert response.text == "Generated text"
        assert response.data == {'key': 'value'}
        assert response.metadata == {'model': 'gpt-4', 'tokens': 100}
        assert response.error is None

    def test_create_response_with_minimal_fields(self):
        """测试创建包含最小字段的响应"""
        response = AIResponse(success=True)

        assert response.success is True
        assert response.text == ""
        assert response.data == {}
        assert response.metadata == {}
        assert response.error is None

    def test_create_error_response(self):
        """测试创建错误响应"""
        response = AIResponse(
            success=False,
            error="API call failed"
        )

        assert response.success is False
        assert response.error == "API call failed"

    def test_response_post_init_populates_defaults(self):
        """测试__post_init__方法填充默认值"""
        response = AIResponse(
            success=True,
            text="Test"
        )

        # 验证data和metadata被初始化为空字典
        assert hasattr(response, 'data')
        assert hasattr(response, 'metadata')
        assert response.data == {}
        assert response.metadata == {}


@pytest.mark.unit
class TestBaseAIClient:
    """测试BaseAIClient抽象基类"""

    @pytest.fixture
    def concrete_client(self):
        """创建具体的客户端实现用于测试"""

        class ConcreteAIClient(BaseAIClient):
            async def generate(self, prompt: str, **kwargs):
                return AIResponse(success=True, text=f"Generated: {prompt}")

            async def validate_config(self):
                return bool(self.api_key and self.api_url)

        return ConcreteAIClient(
            api_url="https://api.example.com",
            api_key="test_key",
            model_name="test_model"
        )

    def test_client_initialization(self, concrete_client):
        """测试客户端初始化"""
        assert concrete_client.api_url == "https://api.example.com"
        assert concrete_client.api_key == "test_key"
        assert concrete_client.model_name == "test_model"
        assert concrete_client.config == {}

    def test_client_initialization_with_extra_config(self):
        """测试带额外配置的客户端初始化"""

        class ConcreteAIClient(BaseAIClient):
            async def generate(self, prompt: str, **kwargs):
                return AIResponse(success=True)

            async def validate_config(self):
                return True

        client = ConcreteAIClient(
            api_url="https://api.example.com",
            api_key="test_key",
            model_name="test_model",
            timeout=30,
            max_tokens=2000
        )

        assert client.config['timeout'] == 30
        assert client.config['max_tokens'] == 2000

    @pytest.mark.asyncio
    async def test_health_check_success(self, concrete_client):
        """测试健康检查成功"""
        assert await concrete_client.health_check() is True

    @pytest.mark.asyncio
    async def test_health_check_failure(self):
        """测试健康检查失败"""

        class FailingClient(BaseAIClient):
            async def generate(self, prompt: str, **kwargs):
                return AIResponse(success=True)

            async def validate_config(self):
                return False

        client = FailingClient(
            api_url="https://api.example.com",
            api_key="invalid_key",
            model_name="test_model"
        )

        assert await client.health_check() is False


@pytest.mark.unit
class TestLLMClient:
    """测试LLMClient抽象基类"""

    @pytest.fixture
    def concrete_llm_client(self):
        """创建具体的LLM客户端实现"""

        class ConcreteLLMClient(LLMClient):
            async def _generate_text(self, prompt, max_tokens, temperature, **kwargs):
                return AIResponse(
                    success=True,
                    text=f"LLM generated: {prompt}",
                    metadata={'tokens': max_tokens}
                )

            async def validate_config(self):
                return True

        return ConcreteLLMClient(
            api_url="https://api.openai.com",
            api_key="test_key",
            model_name="gpt-4"
        )

    @pytest.mark.asyncio
    async def test_llm_generate_with_default_params(self, concrete_llm_client):
        """测试LLM生成使用默认参数"""
        response = await concrete_llm_client.generate("Test prompt")

        assert response.success is True
        assert "LLM generated: Test prompt" in response.text

    @pytest.mark.asyncio
    async def test_llm_generate_with_custom_params(self, concrete_llm_client):
        """测试LLM生成使用自定义参数"""
        response = await concrete_llm_client.generate(
            prompt="Test prompt",
            max_tokens=500,
            temperature=0.5
        )

        assert response.success is True
        assert response.metadata['tokens'] == 500


@pytest.mark.unit
class TestText2ImageClient:
    """测试Text2ImageClient抽象基类"""

    @pytest.fixture
    def concrete_image_client(self):
        """创建具体的文生图客户端实现"""

        class ConcreteImageClient(Text2ImageClient):
            async def _generate_image(
                self,
                prompt,
                negative_prompt="",
                width=1024,
                height=1024,
                steps=20,
                **kwargs
            ):
                return AIResponse(
                    success=True,
                    data={
                        'urls': ['https://example.com/image.png'],
                        'images': [{'url': 'https://example.com/image.png'}]
                    }
                )

            async def validate_config(self):
                return True

        return ConcreteImageClient(
            api_url="https://api.stability.ai",
            api_key="test_key",
            model_name="stable-diffusion"
        )

    @pytest.mark.asyncio
    async def test_image_generate_default_params(self, concrete_image_client):
        """测试图片生成使用默认参数"""
        response = await concrete_image_client.generate("A sunset")

        assert response.success is True
        assert 'urls' in response.data
        assert len(response.data['urls']) == 1

    @pytest.mark.asyncio
    async def test_image_generate_custom_params(self, concrete_image_client):
        """测试图片生成使用自定义参数"""
        response = await concrete_image_client.generate(
            prompt="A sunset",
            width=512,
            height=512,
            steps=30
        )

        assert response.success is True


@pytest.mark.unit
class TestImage2VideoClient:
    """测试Image2VideoClient抽象基类"""

    @pytest.fixture
    def concrete_video_client(self):
        """创建具体的图生视频客户端实现"""

        class ConcreteVideoClient(Image2VideoClient):
            async def _generate_video(
                self,
                image_url,
                camera_movement,
                duration,
                fps,
                **kwargs
            ):
                return AIResponse(
                    success=True,
                    data={
                        'url': 'https://example.com/video.mp4',
                        'video': {'duration': duration, 'fps': fps}
                    }
                )

            async def validate_config(self):
                return True

        return ConcreteVideoClient(
            api_url="https://api.runway.ml",
            api_key="test_key",
            model_name="gen2"
        )

    @pytest.mark.asyncio
    async def test_video_generate_default_params(self, concrete_video_client):
        """测试视频生成使用默认参数"""
        response = await concrete_video_client.generate(
            image_url="https://example.com/image.jpg",
            camera_movement={'type': 'zoom'},
            duration=5.0,
            fps=24
        )

        assert response.success is True
        assert response.data['video']['duration'] == 5.0

    @pytest.mark.asyncio
    async def test_video_generate_custom_params(self, concrete_video_client):
        """测试视频生成使用自定义参数"""
        response = await concrete_video_client.generate(
            image_url="https://example.com/image.jpg",
            camera_movement={'type': 'pan'},
            duration=10.0,
            fps=30,
            width=1920,
            height=1080
        )

        assert response.success is True
        assert response.data['video']['fps'] == 30


@pytest.mark.unit
class TestClientInheritance:
    """测试客户端继承关系"""

    def test_llm_client_inherits_from_base(self):
        """验证LLMClient继承自BaseAIClient"""
        assert issubclass(LLMClient, BaseAIClient)

    def test_text2image_client_inherits_from_base(self):
        """验证Text2ImageClient继承自BaseAIClient"""
        assert issubclass(Text2ImageClient, BaseAIClient)

    def test_image2video_client_inherits_from_base(self):
        """验证Image2VideoClient继承自BaseAIClient"""
        assert issubclass(Image2VideoClient, BaseAIClient)

    def test_abstract_methods_prevent_instantiation(self):
        """测试抽象类不能直接实例化"""
        with pytest.raises(TypeError):
            BaseAIClient("url", "key", "model")

        with pytest.raises(TypeError):
            LLMClient("url", "key", "model")

        with pytest.raises(TypeError):
            Text2ImageClient("url", "key", "model")

        with pytest.raises(TypeError):
            Image2VideoClient("url", "key", "model")
