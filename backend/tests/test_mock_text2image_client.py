"""
Mock Text2Image客户端单元测试
"""

import pytest

from core.ai_client.mock_text2image_client import MockText2ImageClient


@pytest.mark.django_db
class TestMockText2ImageClient:
    """Mock Text2Image客户端测试"""

    @pytest.fixture
    def client(self):
        """创建Mock客户端实例"""
        return MockText2ImageClient(
            api_url="http://localhost:8000/api/mock/text2image/",
            api_key="mock_key",
            model_name="mock_sdxl",
        )

    def test_initialization(self, client):
        """测试客户端初始化"""
        assert client.api_url == "http://localhost:8000/api/mock/text2image/"
        assert client.api_key == "mock_key"
        assert client.model_name == "mock_sdxl"

    @pytest.mark.asyncio
    async def test_generate_success(self, client):
        """测试图片生成成功场景"""
        response = await client.generate(
            prompt="A peaceful small town at dawn", width=1024, height=1024
        )

        assert response.success is True
        # 修复断言：Mock客户端返回image_urls数组，不是单个image_url
        assert response.data.get("image_urls") is not None
        assert len(response.data["image_urls"]) > 0
        assert response.data["image_urls"][0].startswith(("http://", "https://"))

    @pytest.mark.asyncio
    async def test_generate_different_sizes(self, client):
        """测试不同尺寸的图片生成"""
        # 1024x1024
        response1 = await client.generate(prompt="测试", width=1024, height=1024)
        assert response1.success is True

        # 512x512
        response2 = await client.generate(prompt="测试", width=512, height=512)
        assert response2.success is True

    @pytest.mark.asyncio
    async def test_validate_config(self, client):
        """测试配置验证"""
        result = await client.validate_config()
        assert result is True

    @pytest.mark.asyncio
    async def test_health_check(self, client):
        """测试健康检查"""
        result = await client.health_check()
        assert result is True
