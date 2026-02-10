"""
单元测试: Ollama客户端
测试Ollama本地LLM引擎集成

Epic 10 Story 10.1: Ollama本地LLM引擎集成
"""

from unittest.mock import AsyncMock, Mock, patch

import pytest
import httpx

from core.ai_client.ollama_client import OllamaClient


class TestOllamaClient:
    """测试Ollama客户端"""

    @pytest.fixture
    def client(self):
        """创建Ollama客户端实例"""
        return OllamaClient(
            api_url="http://localhost:11434",
            api_key="ollama",
            model_name="llama2:7b",
            fallback_to_openai=False,
        )

    @pytest.fixture
    def client_with_fallback(self):
        """创建带Fallback的Ollama客户端实例"""
        return OllamaClient(
            api_url="http://localhost:11434",
            api_key="ollama",
            model_name="llama2:7b",
            fallback_to_openai=True,
        )

    def test_client_initialization(self, client):
        """测试客户端初始化"""
        assert client.api_url == "http://localhost:11434"
        assert client.api_key == "ollama"
        assert client.model_name == "llama2:7b"
        assert client.fallback_to_openai is False
        assert client.sync_client is not None

    def test_client_initialization_with_fallback(self, client_with_fallback):
        """测试客户端初始化（带Fallback）"""
        assert client_with_fallback.fallback_to_openai is True
        # Fallback客户端延迟加载，初始化时可能为None
        assert client_with_fallback.sync_client is not None

    @pytest.mark.asyncio
    async def test_validate_config_success(self, client):
        """测试配置验证（成功）"""
        with patch.object(client.sync_client, "list") as mock_list:
            mock_list.return_value = [
                {"name": "llama2:7b"},
                {"name": "llama3:8b"},
            ]
            result = await client.validate_config()
            assert result is True

    @pytest.mark.asyncio
    async def test_validate_config_failure(self, client):
        """测试配置验证（失败）"""
        with patch.object(client.sync_client, "list") as mock_list:
            mock_list.side_effect = Exception("Connection refused")
            result = await client.validate_config()
            assert result is False

    @pytest.mark.asyncio
    async def test_health_check_success(self, client):
        """测试健康检查（成功）"""
        with patch.object(client.sync_client, "list") as mock_list:
            mock_list.return_value = [{"name": "llama2:7b"}]
            result = await client.health_check()
            assert result is True

    @pytest.mark.asyncio
    async def test_health_check_failure(self, client):
        """测试健康检查（失败）"""
        with patch.object(client.sync_client, "list") as mock_list:
            mock_list.side_effect = Exception("Service unavailable")
            result = await client.health_check()
            assert result is False

    @pytest.mark.asyncio
    async def test_generate_text_success(self, client):
        """测试文本生成成功"""
        mock_response = Mock()
        mock_response.json.return_value = {
            "message": {"content": "这是生成的文本"},
            "total_duration": 123456789,
        }

        with patch.object(
            client, "_call_api_with_fallback", new=AsyncMock(return_value=mock_response)
        ):
            result = await client._generate_text(
                prompt="测试提示词", max_tokens=100, temperature=0.7
            )

            assert result.success is True
            assert result.text == "这是生成的文本"
            assert result.data["model"] == "llama2:7b"
            assert result.metadata["provider"] == "ollama"
            assert result.metadata["engine"] == "local_llm"

    @pytest.mark.asyncio
    async def test_generate_text_with_api_error(self, client):
        """测试API错误处理"""
        with patch.object(
            client, "_call_api_with_fallback", new=AsyncMock(side_effect=Exception("API Error"))
        ):
            result = await client._generate_text(
                prompt="测试提示词", max_tokens=100, temperature=0.7
            )

            assert result.success is False
            assert "API Error" in result.error

    @pytest.mark.asyncio
    async def test_generate_text_with_fallback(self, client_with_fallback):
        """测试Fallback到OpenAI"""
        # Mock Ollama失败
        with patch.object(
            client_with_fallback,
            "_call_api_with_fallback",
            new=AsyncMock(side_effect=Exception("Ollama unavailable")),
        ):
            # Mock OpenAI成功
            mock_fallback_response = Mock()
            mock_fallback_response.success = True
            mock_fallback_response.text = "Fallback成功"

            with patch.object(
                client_with_fallback.fallback_client,
                "generate",
                new=AsyncMock(return_value=mock_fallback_response),
            ):
                result = await client_with_fallback._generate_text(
                    prompt="测试提示词", max_tokens=100, temperature=0.7
                )

                # Fallback应该返回OpenAI的结果
                assert result.success is True
                assert result.text == "Fallback成功"
                # 验证Fallback客户端被调用
                client_with_fallback.fallback_client.generate.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_text_stream_success(self, client):
        """测试流式文本生成成功"""

        # 模拟流式响应
        async def mock_aiter_lines():
            yield '{"message": {"content": "Hello"}, "done": false}'
            yield '{"message": {"content": " world"}, "done": false}'
            yield '{"done": true}'

        mock_response = Mock()
        mock_response.aiter_lines = mock_aiter_lines

        with patch.object(
            client, "_call_api_with_fallback", new=AsyncMock(return_value=mock_response)
        ):
            chunks = []
            async for chunk in client._generate_text_stream(
                prompt="测试提示词", max_tokens=100, temperature=0.7
            ):
                chunks.append(chunk)

            assert len(chunks) == 2
            assert chunks[0].success is True
            assert chunks[0].text == "Hello"
            assert chunks[1].text == " world"

    @pytest.mark.asyncio
    async def test_generate_text_stream_with_fallback(self, client_with_fallback):
        """测试流式生成Fallback到OpenAI"""
        # Mock Ollama流式失败
        with patch.object(
            client_with_fallback,
            "_call_api_with_fallback",
            new=AsyncMock(side_effect=Exception("Ollama stream error")),
        ):
            # Mock OpenAI流式成功 - 使用公共接口 generate_stream
            async def mock_fallback_stream(*args, **kwargs):
                yield Mock(success=True, text="Fallback stream")

            with patch.object(
                client_with_fallback.fallback_client,
                "generate_stream",
                side_effect=mock_fallback_stream,
            ):
                chunks = []
                async for chunk in client_with_fallback._generate_text_stream(
                    prompt="测试提示词", max_tokens=100, temperature=0.7
                ):
                    chunks.append(chunk)

                assert len(chunks) == 1
                assert chunks[0].text == "Fallback stream"

    def test_extract_response_text_with_message_field(self, client):
        """测试从响应中提取文本（message字段）"""
        response = {"message": {"content": "测试文本"}}
        text = client._extract_response_text(response)
        assert text == "测试文本"

    def test_extract_response_text_with_response_field(self, client):
        """测试从响应中提取文本（response字段）"""
        response = {"response": "测试文本"}
        text = client._extract_response_text(response)
        assert text == "测试文本"

    def test_extract_response_text_fallback(self, client):
        """测试从响应中提取文本（fallback到str）"""
        response = {"unknown": "data"}
        text = client._extract_response_text(response)
        assert text == str(response)

    def test_extract_response_text_with_error(self, client):
        """测试从响应中提取文本（错误处理）"""
        response = None
        text = client._extract_response_text(response)
        assert text == ""

    @pytest.mark.asyncio
    async def test_call_ollama_chat_payload(self, client):
        """测试Ollama Chat API调用payload"""
        mock_response = Mock()
        mock_response.json.return_value = {"message": {"content": "响应"}}

        with patch.object(
            client, "_call_api_with_fallback", new=AsyncMock(return_value=mock_response)
        ):
            await client._call_ollama_chat(
                prompt="测试", max_tokens=100, temperature=0.7, stream=False, top_p=0.9
            )

            # 验证调用参数
            client._call_api_with_fallback.assert_called_once()
            call_args = client._call_api_with_fallback.call_args
            assert "POST" in call_args[1].values()
            payload = call_args[1]["json"]
            assert payload["model"] == "llama2:7b"
            assert payload["messages"] == [{"role": "user", "content": "测试"}]
            assert payload["stream"] is False
            assert payload["options"]["temperature"] == 0.7
            assert payload["options"]["num_predict"] == 100
            assert payload["options"]["top_p"] == 0.9

    @pytest.mark.asyncio
    async def test_generate_with_custom_parameters(self, client):
        """测试自定义参数传递"""
        mock_response = Mock()
        mock_response.json.return_value = {
            "message": {"content": "生成的文本"},
            "total_duration": 1000000,
        }

        with patch.object(
            client, "_call_api_with_fallback", new=AsyncMock(return_value=mock_response)
        ):
            result = await client._generate_text(
                prompt="测试提示词",
                max_tokens=500,
                temperature=0.5,
                top_p=0.8,
            )

            assert result.success is True
            # 验证参数被正确传递
            client._call_api_with_fallback.assert_called_once()
            call_args = client._call_api_with_fallback.call_args
            payload = call_args[1]["json"]
            assert payload["options"]["temperature"] == 0.5
            assert payload["options"]["num_predict"] == 500
            assert payload["options"]["top_p"] == 0.8


class TestOllamaClientIntegration:
    """集成测试: 需要本地运行Ollama服务"""

    @pytest.fixture
    def real_client(self):
        """创建真实Ollama客户端"""
        return OllamaClient(
            api_url="http://localhost:11434",
            api_key="ollama",
            model_name="llama2:7b",
            fallback_to_openai=False,
        )

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_real_ollama_connection(self, real_client):
        """测试真实Ollama连接（需要Ollama服务运行）"""
        result = await real_client.validate_config()
        # 如果Ollama未运行，测试会跳过
        if not result:
            pytest.skip("Ollama服务未运行，跳过集成测试")
        assert result is True

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_real_ollama_generate(self, real_client):
        """测试真实Ollama生成（需要Ollama服务运行且模型已下载）"""
        # 先验证连接
        if not await real_client.validate_config():
            pytest.skip("Ollama服务未运行，跳过集成测试")

        result = await real_client._generate_text(
            prompt="Say hello", max_tokens=10, temperature=0.7
        )

        assert result.success is True
        assert len(result.text) > 0
