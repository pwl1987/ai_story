"""
Mock客户端完整测试 - 修复版
"""
import pytest

from core.ai_client.mock_image2video_client import MockImage2VideoClient
from core.ai_client.mock_llm_client import MockLLMClient
from core.ai_client.mock_text2image_client import MockText2ImageClient


@pytest.mark.django_db
class TestMockClients:
    """Mock客户端完整测试"""

    @pytest.fixture
    def mock_llm(self):
        return MockLLMClient(api_url='http://mock', api_key='key', model_name='llm')

    @pytest.fixture
    def mock_t2i(self):
        return MockText2ImageClient(api_url='http://mock', api_key='key', model_name='sdxl')

    @pytest.fixture
    def mock_i2v(self):
        return MockImage2VideoClient(api_url='http://mock', api_key='key', model_name='runway')

    # Mock LLM Client 测试
    @pytest.mark.asyncio
    async def test_mock_llm_generate(self, mock_llm):
        """测试Mock LLM生成"""
        response = await mock_llm.generate(prompt='测试')
        assert response.success is True
        assert response.text != ''

    @pytest.mark.asyncio
    async def test_mock_llm_validate(self, mock_llm):
        """测试Mock LLM配置验证"""
        assert await mock_llm.validate_config() is True
        assert await mock_llm.health_check() is True

    # Mock Text2Image Client 测试
    @pytest.mark.asyncio
    async def test_mock_t2i_generate(self, mock_t2i):
        """测试Mock文生图"""
        response = await mock_t2i.generate(prompt='测试')
        assert response.success is True
        assert 'urls' in response.data or 'images' in response.data

    @pytest.mark.asyncio
    async def test_mock_t2i_validate(self, mock_t2i):
        """测试Mock文生图配置验证"""
        assert await mock_t2i.validate_config() is True
        assert await mock_t2i.health_check() is True

    # Mock Image2Video Client 测试
    @pytest.mark.asyncio
    async def test_mock_i2v_generate(self, mock_i2v):
        """测试Mock图生视频"""
        response = await mock_i2v.generate(
            image_url='http://test.jpg',
            camera_movement='推进',
            duration=5
        )
        assert response.success is True
        assert 'video_url' in response.data or 'videos' in response.data

    @pytest.mark.asyncio
    async def test_mock_i2v_validate(self, mock_i2v):
        """测试Mock图生视频配置验证"""
        assert await mock_i2v.validate_config() is True
        assert await mock_i2v.health_check() is True
