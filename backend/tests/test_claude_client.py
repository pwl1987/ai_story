"""
单元测试: Claude客户端
测试Anthropic Claude API集成
"""

from unittest.mock import Mock, patch

import pytest

from core.ai_client.claude_client import ClaudeClient


class TestClaudeClient:
    """测试Claude客户端"""

    @pytest.fixture
    def client(self):
        """创建Claude客户端实例"""
        return ClaudeClient(
            api_url="https://api.anthropic.com/v1/messages",
            api_key="test-api-key",
            model_name="claude-3-opus-20240229"
        )

    def test_client_initialization(self, client):
        """测试客户端初始化"""
        assert client.api_url == "https://api.anthropic.com/v1/messages"
        assert client.api_key == "test-api-key"
        assert client.model_name == "claude-3-opus-20240229"

    def test_validate_config_with_valid_config(self, client):
        """测试配置验证（有效配置）"""
        with patch('core.ai_client.claude_client.requests.post') as mock_post:
            mock_post.return_value.status_code = 200
            assert client.validate_config() is True

    def test_validate_config_with_invalid_config(self, client):
        """测试配置验证（无效配置）"""
        client.api_key = ""
        assert client.validate_config() is False

    def test_generate_text_success(self, client):
        """测试文本生成成功"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'content': [
                {
                    'text': '这是生成的文本'
                }
            ],
            'usage': {
                'input_tokens': 10,
                'output_tokens': 20
            },
            'stop_reason': 'end_turn'
        }

        with patch('core.ai_client.claude_client.requests.post') as mock_post:
            mock_post.return_value = mock_response

            result = client._generate_text("测试提示词")

            assert result.success is True
            assert result.text == "这是生成的文本"
            assert result.metadata['input_tokens'] == 10
            assert result.metadata['output_tokens'] == 20
            assert result.metadata['stop_reason'] == 'end_turn'

    def test_generate_text_with_api_error(self, client):
        """测试API错误处理"""
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"

        with patch('core.ai_client.claude_client.requests.post') as mock_post:
            mock_post.return_value = mock_response

            result = client._generate_text("测试提示词")

            assert result.success is False
            assert "401" in result.error

    def test_generate_text_with_network_error(self, client):
        """测试网络错误处理"""
        with patch('core.ai_client.claude_client.requests.post') as mock_post:
            mock_post.side_effect = Exception("Network error")

            result = client._generate_text("测试提示词")

            assert result.success is False
            assert "Network error" in result.error

    def test_generate_text_with_system_prompt(self, client):
        """测试带系统提示词的文本生成"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'content': [{'text': '生成的文本'}],
            'usage': {'input_tokens': 15, 'output_tokens': 20},
            'stop_reason': 'end_turn'
        }

        with patch('core.ai_client.claude_client.requests.post') as mock_post:
            mock_post.return_value = mock_response

            result = client._generate_text(
                "用户提示词",
                system_prompt="系统提示词"
            )

            assert result.success is True
            # 验证payload包含system字段
            call_args = mock_post.call_args
            payload = call_args[1]['json']
            assert 'system' in payload
            assert payload['system'] == "系统提示词"

    def test_generate_stream_success(self, client):
        """测试流式生成成功"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.iter_content.return_value = [
            b'data: {"type": "content_block_delta", "delta": {"text": "Hello"}}\n\n',
            b'data: {"type": "content_block_delta", "delta": {"text": " world"}}\n\n',
            b'data: {"type": "message_stop"}\n\n'
        ]

        with patch('core.ai_client.claude_client.requests.post') as mock_post:
            mock_post.return_value = mock_response

            chunks = list(client.generate_stream("测试提示词"))

            assert len(chunks) > 0
            assert chunks[0]['type'] == 'token'
            assert chunks[0]['content'] == "Hello"
            assert 'done' in [c['type'] for c in chunks]

    def test_generate_stream_with_error(self, client):
        """测试流式生成错误处理"""
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"

        with patch('core.ai_client.claude_client.requests.post') as mock_post:
            mock_post.return_value = mock_response

            chunks = list(client.generate_stream("测试提示词"))

            assert len(chunks) == 1
            assert chunks[0]['type'] == 'error'

    def test_generate_with_custom_parameters(self, client):
        """测试自定义参数"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'content': [{'text': '生成的文本'}],
            'usage': {'input_tokens': 10, 'output_tokens': 20},
            'stop_reason': 'end_turn'
        }

        with patch('core.ai_client.claude_client.requests.post') as mock_post:
            mock_post.return_value = mock_response

            result = client._generate_text(
                "测试提示词",
                max_tokens=1000,
                temperature=0.5,
                top_p=0.9
            )

            assert result.success is True
            # 验证自定义参数被传递
            call_args = mock_post.call_args
            payload = call_args[1]['json']
            assert payload['max_tokens'] == 1000
            assert payload['temperature'] == 0.5
            assert payload['top_p'] == 0.9

    def test_async_generate(self, client):
        """测试异步生成接口"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'content': [{'text': '异步生成的文本'}],
            'usage': {'input_tokens': 10, 'output_tokens': 20},
            'stop_reason': 'end_turn'
        }

        with patch('core.ai_client.claude_client.requests.post') as mock_post:
            mock_post.return_value = mock_response

            import asyncio
            result = asyncio.run(client.generate("测试提示词"))

            assert result.success is True
            assert result.text == "异步生成的文本"
