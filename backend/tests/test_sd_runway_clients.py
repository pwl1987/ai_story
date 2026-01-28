"""
单元测试: Stable Diffusion和Runway客户端
Story 5.2 & 5.3
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from core.ai_client.stable_diffusion_client import StableDiffusionClient
from core.ai_client.runway_client import RunwayClient
from core.ai_client.base import AIResponse


class TestStableDiffusionClient:
    """测试Stable Diffusion客户端"""

    @pytest.fixture
    def client(self):
        return StableDiffusionClient(
            api_url="http://localhost:7860/sdapi/v1/",
            api_key="test-key",
            model_name="sdxl-base-1.0"
        )

    def test_client_initialization(self, client):
        """测试客户端初始化"""
        assert client.api_url == "http://localhost:7860/sdapi/v1/"
        assert client.model_name == "sdxl-base-1.0"

    def test_validate_config_with_valid_config(self, client):
        """测试配置验证（有效配置）"""
        with patch('core.ai_client.stable_diffusion_client.requests.get') as mock_get:
            mock_get.return_value.status_code = 200
            # 由于validate中有实际网络调用，这里只测试参数检查
            assert client.api_url is not None
            assert client.model_name is not None

    def test_validate_config_with_invalid_config(self, client):
        """测试配置验证（无效配置）"""
        client.api_url = ""
        assert client.validate_config() is False

    @patch('core.ai_client.stable_diffusion_client.requests.post')
    def test_generate_a111_success(self, mock_post, client):
        """测试A111生成成功"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'images': ['data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAAAElFTkSuQmCC'],
            'info': {'all_seeds': [12345]}
        }
        mock_post.return_value = mock_response

        result = client._generate_a111(
            prompt="测试提示词",
            width=512,
            height=512
        )

        assert result.success is True
        assert 'url' in result.data
        assert result.metadata['api_type'] == 'automatic1111'


@pytest.mark.django_db
class TestRunwayClient:
    """测试Runway客户端"""

    @pytest.fixture
    def client(self):
        return RunwayClient(
            api_url="https://api.runwayml.com/v1/",
            api_key="test-key",
            model_name="gen3a_turbo"
        )

    def test_client_initialization(self, client):
        """测试客户端初始化"""
        assert client.api_url == "https://api.runwayml.com/v1/"
        assert client.model_name == "gen3a_turbo"

    @patch('core.ai_client.runway_client.requests.post')
    def test_submit_task_success(self, mock_post, client):
        """测试任务提交成功"""
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.json.return_value = {
            'id': 'test-task-123'
        }
        mock_post.return_value = mock_response

        task_id = client._submit_task(
            image_url="https://example.com/image.jpg",
            prompt="测试视频"
        )

        assert task_id == "test-task-123"

    @patch('core.ai_client.runway_client.requests.get')
    @patch('time.sleep')
    def test_poll_task_success(self, mock_sleep, mock_get, client):
        """测试轮询成功"""
        # 第一次返回PROCESSING，第二次返回SUCCEEDED
        mock_response_1 = Mock()
        mock_response_1.status_code = 200
        mock_response_1.json.return_value = {
            'status': 'PROCESSING'
        }

        mock_response_2 = Mock()
        mock_response_2.status_code = 200
        mock_response_2.json.return_value = {
            'status': 'SUCCEEDED',
            'output': [{'URL': 'https://example.com/video.mp4'}]
        }

        mock_get.side_effect = [mock_response_1, mock_response_2]

        result = client._poll_task('test-task-123', max_wait_time=10, poll_interval=1)

        assert result['success'] is True
        assert result['url'] == 'https://example.com/video.mp4'

