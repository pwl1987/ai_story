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
            api_url='http://localhost:8000/api/mock/image2video/',
            api_key='mock_key',
            model_name='mock_runway'
        )

    def test_initialization(self, client):
        """测试客户端初始化"""
        assert client.api_url == 'http://localhost:8000/api/mock/image2video/'
        assert client.api_key == 'mock_key'
        assert client.model_name == 'mock_runway'

    def test_generate_success(self, client):
        """测试视频生成成功场景"""
        response = client.generate(
            image_url='http://example.com/image.jpg',
            camera_movement='缓慢推进镜头',
            duration=5
        )

        assert response.success is True
        assert response.data.get('video_url') is not None
        assert response.data['video_url'].startswith('http://')
        assert response.data.get('duration') == 5

    def test_generate_different_durations(self, client):
        """测试不同时长"""
        # 5秒视频
        response1 = client.generate(
            image_url='http://example.com/image.jpg',
            camera_movement='推进',
            duration=5
        )
        assert response1.success is True
        assert response1.data['duration'] == 5

        # 10秒视频
        response2 = client.generate(
            image_url='http://example.com/image.jpg',
            camera_movement='平移',
            duration=10
        )
        assert response2.success is True
        assert response2.data['duration'] == 10

    def test_validate_config(self, client):
        """测试配置验证"""
        result = client.validate_config()
        assert result is True

    def test_health_check(self, client):
        """测试健康检查"""
        result = client.health_check()
        assert result is True
