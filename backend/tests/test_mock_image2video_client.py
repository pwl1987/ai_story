"""
Mock Image2Video客户端单元测试
"""

import pytest

from core.ai_client.mock_image2video_client import MockImage2VideoClient


@pytest.mark.django_db
class TestMockImage2VideoClient:
    """Mock Image2Video客户端测试"""

    @pytest.fixture
    def client(self):
        """创建Mock客户端实例"""
        return MockImage2VideoClient(
            api_url="http://localhost:8000/api/mock/image2video/",
            api_key="mock_key",
            model_name="mock_runway",
        )

    def test_initialization(self, client):
        """测试客户端初始化"""
        assert client.api_url == "http://localhost:8000/api/mock/image2video/"
        assert client.api_key == "mock_key"
        assert client.model_name == "mock_runway"

    @pytest.mark.asyncio
    async def test_generate_success(self, client):
        """测试视频生成成功场景"""
        response = await client.generate(
            image_url="http://example.com/image.jpg", camera_movement="缓慢推进镜头", duration=5
        )

        assert response.success is True
        assert response.data.get("url") is not None
        assert response.data["url"].startswith(("http://", "https://"))
        assert response.metadata.get("duration") == 5

    @pytest.mark.asyncio
    async def test_generate_different_durations(self, client):
        """测试不同时长"""
        # 5秒视频
        response1 = await client.generate(
            image_url="http://example.com/image.jpg", camera_movement="推进", duration=5
        )
        assert response1.success is True
        assert response1.metadata.get("duration") == 5

        # 10秒视频
        response2 = await client.generate(
            image_url="http://example.com/image.jpg", camera_movement="平移", duration=10
        )
        assert response2.success is True
        assert response2.metadata.get("duration") == 10

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
