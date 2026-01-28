"""
Mock AI客户端单元测试

测试所有Mock客户端的行为和响应格式
"""


import pytest

from core.ai_client.factory import create_ai_client
from core.ai_client.mock_image2video_client import MockImage2VideoClient
from core.ai_client.mock_llm_client import MockLLMClient
from core.ai_client.mock_text2image_client import MockText2ImageClient


@pytest.mark.unit
class TestMockLLMClient:
    """MockLLMClient单元测试"""

    @pytest.fixture
    def mock_llm_client(self):
        """创建MockLLMClient实例"""
        return MockLLMClient(
            api_url='mock://llm',
            api_key='mock_key',
            model_name='mock-llm'
        )

    @pytest.mark.asyncio
    async def test_generate_rewrite_response(self, mock_llm_client):
        """测试生成改写响应"""
        response = await mock_llm_client.generate(
            prompt="请改写这个故事",
            max_tokens=2000,
            temperature=0.7
        )

        assert response.success is True
        assert len(response.text) > 0
        assert '改写' in response.text
        assert response.metadata['is_mock'] is True
        assert response.metadata['model'] == 'mock-llm'
        assert 'latency_ms' in response.metadata

    @pytest.mark.asyncio
    async def test_generate_storyboard_response(self, mock_llm_client):
        """测试生成分镜响应"""
        response = await mock_llm_client.generate(
            prompt="生成分镜",
            max_tokens=2000
        )

        assert response.success is True
        assert '[' in response.text  # JSON格式
        assert 'scene_number' in response.text

    @pytest.mark.asyncio
    async def test_generate_camera_movement_response(self, mock_llm_client):
        """测试生成运镜响应"""
        response = await mock_llm_client.generate(
            prompt="设计运镜",
            max_tokens=1000
        )

        assert response.success is True
        assert 'movement_type' in response.text

    @pytest.mark.asyncio
    async def test_generate_default_response(self, mock_llm_client):
        """测试生成默认响应"""
        response = await mock_llm_client.generate(
            prompt="随机内容"
        )

        assert response.success is True
        assert '模拟的 LLM 响应' in response.text

    @pytest.mark.asyncio
    async def test_validate_config(self, mock_llm_client):
        """测试配置验证"""
        assert await mock_llm_client.validate_config() is True

    @pytest.mark.asyncio
    async def test_health_check(self, mock_llm_client):
        """测试健康检查"""
        assert await mock_llm_client.health_check() is True

    def test_generate_stream(self, mock_llm_client):
        """测试流式生成"""
        chunks = list(mock_llm_client.generate_stream(
            prompt="请改写这个故事"
        ))

        assert len(chunks) > 0

        # 检查token类型
        token_chunks = [c for c in chunks if c['type'] == 'token']
        assert len(token_chunks) > 0

        # 检查完成信号
        done_chunks = [c for c in chunks if c['type'] == 'done']
        assert len(done_chunks) == 1

        # 验证完整文本
        full_text = done_chunks[0]['full_text']
        assert len(full_text) > 0


@pytest.mark.unit
class TestMockText2ImageClient:
    """MockText2ImageClient单元测试"""

    @pytest.fixture
    def mock_image_client(self):
        """创建MockText2ImageClient实例"""
        return MockText2ImageClient(
            api_url='mock://text2image',
            api_key='mock_key',
            model_name='mock-text2image'
        )

    @pytest.mark.unit
    def test_generate_single_image(self, mock_image_client):
        """测试生成单张图片"""
        response = mock_image_client.generate(
            prompt="A beautiful sunset",
            width=1024,
            height=1024
        )

        assert response.success is True
        assert 'urls' in response.data
        assert len(response.data['urls']) == 1
        assert 'https://picsum.photos' in response.data['urls'][0]
        assert response.metadata['is_mock'] is True

    @pytest.mark.unit
    def test_generate_multiple_images(self, mock_image_client):
        """测试生成多张图片"""
        response = mock_image_client.generate(
            prompt="Test prompt",
            sample_count=3
        )

        assert response.success is True
        assert len(response.data['urls']) == 3
        assert len(response.data['images']) == 3

        # 验证每张图片都有必要字段
        for img_data in response.data['images']:
            assert 'url' in img_data
            assert 'width' in img_data
            assert 'height' in img_data
            assert img_data['format'] == 'jpeg'

    @pytest.mark.asyncio
    async def test_validate_config(self, mock_image_client):
        """测试配置验证"""
        assert await mock_image_client.validate_config() is True

    @pytest.mark.asyncio
    async def test_health_check(self, mock_image_client):
        """测试健康检查"""
        assert await mock_image_client.health_check() is True


@pytest.mark.unit
class TestMockImage2VideoClient:
    """MockImage2VideoClient单元测试"""

    @pytest.fixture
    def mock_video_client(self):
        """创建MockImage2VideoClient实例"""
        return MockImage2VideoClient(
            api_url='mock://image2video',
            api_key='mock_key',
            model_name='mock-image2video'
        )

    @pytest.mark.asyncio
    async def test_generate_video(self, mock_video_client):
        """测试生成视频"""
        response = await mock_video_client.generate(
            image_url="https://example.com/image.jpg",
            camera_movement={
                'movement_type': 'slow_zoom_in',
                'duration': 3.0
            },
            duration=5.0,
            fps=24
        )

        assert response.success is True
        assert 'url' in response.data
        assert 'video' in response.data
        assert response.data['video']['duration'] == 5.0
        assert response.data['video']['fps'] == 24
        assert response.metadata['is_mock'] is True

    @pytest.mark.asyncio
    async def test_validate_config(self, mock_video_client):
        """测试配置验证"""
        assert await mock_video_client.validate_config() is True

    @pytest.mark.asyncio
    async def test_health_check(self, mock_video_client):
        """测试健康检查"""
        assert await mock_video_client.health_check() is True


@pytest.mark.unit
class TestFactoryMockIntegration:
    """工厂模式Mock集成测试"""

    @pytest.fixture
    def mock_provider(self):
        """创建Mock ModelProvider对象"""
        class MockProvider:
            name = "Test Provider"
            executor_class = "core.ai_client.openai_client.OpenAIClient"
            model_name = "gpt-4"
            api_url = "https://api.openai.com"
            api_key = "test_key"

        return MockProvider()

    @pytest.fixture
    def mock_text2image_provider(self):
        """创建Mock文生图provider"""
        class MockProvider:
            name = "Stable Diffusion"
            executor_class = "core.ai_client.text2image_client.Text2ImageClient"
            model_name = "stable-diffusion-v1.5"
            api_url = "https://api.stability.ai"
            api_key = "test_key"

        return MockProvider()

    @pytest.fixture
    def mock_image2video_provider(self):
        """创建Mock图生视频provider"""
        class MockProvider:
            name = "Runway"
            executor_class = "core.ai_client.image2video_client.Image2VideoClient"
            model_name = "gen2"
            api_url = "https://api.runway.ml"
            api_key = "test_key"

        return MockProvider()

    def test_create_mock_llm_client(self, mock_provider, monkeypatch):
        """测试创建Mock LLM客户端"""
        # 设置环境变量启用Mock
        monkeypatch.setenv('ENABLE_MOCK_AI', 'true')

        client = create_ai_client(mock_provider)

        assert isinstance(client, MockLLMClient)
        assert client.model_name == 'gpt-4'

    def test_create_mock_text2image_client(self, mock_text2image_provider, monkeypatch):
        """测试创建Mock文生图客户端"""
        monkeypatch.setenv('ENABLE_MOCK_AI', 'true')

        client = create_ai_client(mock_text2image_provider)

        assert isinstance(client, MockText2ImageClient)

    def test_create_mock_image2video_client(self, mock_image2video_provider, monkeypatch):
        """测试创建Mock图生视频客户端"""
        monkeypatch.setenv('ENABLE_MOCK_AI', 'true')

        client = create_ai_client(mock_image2video_provider)

        assert isinstance(client, MockImage2VideoClient)

    def test_create_mock_client_without_env_var(self, mock_provider):
        """测试未设置环境变量时不使用Mock"""
        import os
        # 确保环境变量未设置
        os.environ.pop('ENABLE_MOCK_AI', None)

        # 由于没有真实的API密钥，这里应该抛出异常
        # 或者返回真实的客户端（如果配置正确）
        with pytest.raises(Exception):
            create_ai_client(mock_provider)
