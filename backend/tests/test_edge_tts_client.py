"""
单元测试: Edge-TTS客户端
测试Edge-TTS本地语音合成集成

Epic 10 Story 10.2: Edge-TTS本地语音合成集成
"""

from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import pytest

from core.ai_client.edge_tts_client import EdgeTTSClient


class TestEdgeTTSClient:
    """测试Edge-TTS客户端"""

    @pytest.fixture
    def client(self):
        """创建Edge-TTS客户端实例"""
        return EdgeTTSClient(
            api_url="https://edge-tts.com",
            api_key="edge-tts",
            model_name="zh-CN-XiaoxiaoNeural",
            fallback_to_elevenlabs=False,
        )

    @pytest.fixture
    def client_with_fallback(self):
        """创建带Fallback的Edge-TTS客户端实例"""
        return EdgeTTSClient(
            api_url="https://edge-tts.com",
            api_key="edge-tts",
            model_name="zh-CN-XiaoxiaoNeural",
            fallback_to_elevenlabs=True,
        )

    def test_client_initialization(self, client):
        """测试客户端初始化"""
        assert client.api_url == "https://edge-tts.com"
        assert client.api_key == "edge-tts"
        assert client.model_name == "zh-CN-XiaoxiaoNeural"
        assert client.fallback_to_elevenlabs is False
        assert client.output_dir.exists()

    def test_client_initialization_with_fallback(self, client_with_fallback):
        """测试客户端初始化（带Fallback）"""
        assert client_with_fallback.fallback_to_elevenlabs is True
        # Fallback客户端尚未实现，应该为None
        assert client_with_fallback.fallback_client is None

    @pytest.mark.asyncio
    async def test_list_voices_success(self, client):
        """测试获取音色列表（成功）"""
        # Mock edge_tts.list_voices
        mock_voices = [
            {
                "Name": "Microsoft Server Speech Text to Speech Voice (zh-CN, XiaoxiaoNeural)",
                "Locale": "zh-CN",
                "Gender": "Female",
                "Description": "Chinese female voice",
            },
            {
                "Name": "Microsoft Server Speech Text to Speech Voice (zh-CN, YunxiNeural)",
                "Locale": "zh-CN",
                "Gender": "Male",
                "Description": "Chinese male voice",
            },
        ]

        with patch(
            "core.ai_client.edge_tts_client.edge_tts.list_voices",
            new=AsyncMock(return_value=mock_voices),
        ):
            voices = await client.list_voices()

            assert len(voices) == 2
            # ShortName 格式: "zh-CN-XiaoxiaoNeural"
            assert voices[0]["ShortName"] == "zh-CN-XiaoxiaoNeural"
            assert voices[0]["Locale"] == "zh-CN"
            assert voices[0]["Gender"] == "Female"
            assert voices[1]["ShortName"] == "zh-CN-YunxiNeural"
            assert voices[1]["Gender"] == "Male"

    @pytest.mark.asyncio
    async def test_list_voices_cache(self, client):
        """测试音色列表缓存"""
        mock_voices = [
            {
                "Name": "Microsoft Server Speech Text to Speech Voice (zh-CN, XiaoxiaoNeural)",
                "Locale": "zh-CN",
                "Gender": "Female",
            },
        ]

        with patch(
            "core.ai_client.edge_tts_client.edge_tts.list_voices",
            new=AsyncMock(return_value=mock_voices),
        ) as mock_list:
            # 第一次调用
            voices1 = await client.list_voices()
            # 第二次调用（应该使用缓存）
            voices2 = await client.list_voices()

            assert len(voices1) == len(voices2)
            # 验证只调用了一次 edge_tts.list_voices
            mock_list.assert_called_once()

    @pytest.mark.asyncio
    async def test_list_voices_with_error(self, client):
        """测试获取音色列表（失败）"""
        with patch(
            "core.ai_client.edge_tts_client.edge_tts.list_voices",
            new=AsyncMock(side_effect=Exception("Network error")),
        ):
            voices = await client.list_voices()
            assert voices == []

    @pytest.mark.asyncio
    async def test_get_available_voices(self, client):
        """测试获取可用音色名称列表"""
        mock_voices = [
            {
                "Name": "Microsoft Server Speech Text to Speech Voice (zh-CN, XiaoxiaoNeural)",
                "Locale": "zh-CN",
                "Gender": "Female",
            },
            {
                "Name": "Microsoft Server Speech Text to Speech Voice (en-US, JennyNeural)",
                "Locale": "en-US",
                "Gender": "Female",
            },
        ]

        with patch(
            "core.ai_client.edge_tts_client.edge_tts.list_voices",
            new=AsyncMock(return_value=mock_voices),
        ):
            # 获取所有音色
            all_voices = await client.get_available_voices()
            assert len(all_voices) == 2
            assert "zh-CN-XiaoxiaoNeural" in all_voices
            assert "en-US-JennyNeural" in all_voices

            # 过滤中文音色
            zh_voices = await client.get_available_voices(locale="zh-CN")
            assert len(zh_voices) == 1
            assert zh_voices[0] == "zh-CN-XiaoxiaoNeural"

    @pytest.mark.asyncio
    async def test_validate_config_success(self, client):
        """测试配置验证（成功）"""
        mock_voices = [
            {
                "Name": "Microsoft Server Speech Text to Speech Voice (zh-CN, XiaoxiaoNeural)",
                "Locale": "zh-CN",
            },
        ]

        with patch(
            "core.ai_client.edge_tts_client.edge_tts.list_voices",
            new=AsyncMock(return_value=mock_voices),
        ):
            result = await client.validate_config()
            assert result is True

    @pytest.mark.asyncio
    async def test_validate_config_failure(self, client):
        """测试配置验证（失败）"""
        with patch(
            "core.ai_client.edge_tts_client.edge_tts.list_voices",
            new=AsyncMock(side_effect=Exception("Connection failed")),
        ):
            result = await client.validate_config()
            assert result is False

    @pytest.mark.asyncio
    async def test_health_check_success(self, client):
        """测试健康检查（成功）"""
        mock_voices = [{"Name": "Test Voice", "Locale": "zh-CN"}]

        with patch(
            "core.ai_client.edge_tts_client.edge_tts.list_voices",
            new=AsyncMock(return_value=mock_voices),
        ):
            result = await client.health_check()
            assert result is True

    @pytest.mark.asyncio
    async def test_health_check_failure(self, client):
        """测试健康检查（失败）"""
        with patch(
            "core.ai_client.edge_tts_client.edge_tts.list_voices",
            new=AsyncMock(side_effect=Exception("Service unavailable")),
        ):
            result = await client.health_check()
            assert result is False

    @pytest.mark.asyncio
    async def test_synthesize_speech_success(self, client, tmp_path):
        """测试语音合成成功"""
        # Mock communicate.save_sync
        mock_communicate = Mock()
        mock_communicate.save_sync.return_value = None

        with patch(
            "core.ai_client.edge_tts_client.edge_tts.Communicate", return_value=mock_communicate
        ):
            result = await client._synthesize_speech(
                text="测试语音合成",
                voice="zh-CN-XiaoxiaoNeural",
                rate="+0%",
                volume="+0%",
                pitch="+0Hz",
                output_format="mp3",
            )

            assert result.success is True
            assert result.text.endswith(".mp3")
            assert result.data["voice"] == "zh-CN-XiaoxiaoNeural"
            assert result.data["format"] == "mp3"
            assert result.metadata["provider"] == "edge-tts"

            # 验证 communicate.save_sync 被调用
            mock_communicate.save_sync.assert_called_once()

    @pytest.mark.asyncio
    async def test_synthesize_speech_with_error(self, client):
        """测试语音合成错误处理"""
        with patch(
            "core.ai_client.edge_tts_client.edge_tts.Communicate",
            side_effect=Exception("TTS Error"),
        ):
            result = await client._synthesize_speech(
                text="测试",
                voice="zh-CN-XiaoxiaoNeural",
                rate="+0%",
                volume="+0%",
                pitch="+0Hz",
                output_format="mp3",
            )

            assert result.success is False
            assert "TTS Error" in result.error

    @pytest.mark.asyncio
    async def test_synthesize_speech_with_fallback(self, client_with_fallback):
        """测试Fallback到ElevenLabs"""
        # Mock Edge-TTS失败
        with patch(
            "core.ai_client.edge_tts_client.edge_tts.Communicate",
            side_effect=Exception("Edge-TTS unavailable"),
        ):
            # Mock Fallback成功
            mock_fallback_response = Mock()
            mock_fallback_response.success = True
            mock_fallback_response.text = "/path/to/fallback_audio.mp3"

            with (
                patch.object(
                    client_with_fallback.fallback_client,
                    "_synthesize_speech",
                    new=AsyncMock(return_value=mock_fallback_response),
                )
                if client_with_fallback.fallback_client
                else patch("asyncio.get_event_loop")
            ):
                result = await client_with_fallback._synthesize_speech(
                    text="测试",
                    voice="zh-CN-XiaoxiaoNeural",
                    rate="+0%",
                    volume="+0%",
                    pitch="+0Hz",
                    output_format="mp3",
                )

                # 如果Fallback客户端可用，应该返回Fallback结果
                # 当前Fallback客户端为None，所以会失败
                if client_with_fallback.fallback_client:
                    assert result.success is True
                    assert result.text == "/path/to/fallback_audio.mp3"
                else:
                    assert result.success is False

    @pytest.mark.asyncio
    async def test_generate_with_default_voice(self, client):
        """测试使用默认音色生成语音"""
        mock_communicate = Mock()
        mock_communicate.save_sync.return_value = None

        with patch(
            "core.ai_client.edge_tts_client.edge_tts.Communicate", return_value=mock_communicate
        ):
            # 不指定voice，应该使用默认音色 (model_name)
            result = await client.generate(text="测试")

            assert result.success is True
            # 验证使用的音色是默认音色
            mock_communicate.save_sync.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_with_custom_voice(self, client):
        """测试使用自定义音色生成语音"""
        mock_communicate = Mock()
        mock_communicate.save_sync.return_value = None

        with patch(
            "core.ai_client.edge_tts_client.edge_tts.Communicate", return_value=mock_communicate
        ) as mock_class:
            # 指定自定义音色
            result = await client.generate(text="测试", voice="zh-CN-YunxiNeural")

            assert result.success is True
            # 验证 Communicate 被正确的 voice 参数调用
            mock_class.assert_called_once()
            call_kwargs = mock_class.call_args[1]
            assert call_kwargs["voice"] == "zh-CN-YunxiNeural"

    @pytest.mark.asyncio
    async def test_generate_with_voice_parameters(self, client):
        """测试语音参数调节"""
        mock_communicate = Mock()
        mock_communicate.save_sync.return_value = None

        with patch(
            "core.ai_client.edge_tts_client.edge_tts.Communicate", return_value=mock_communicate
        ) as mock_class:
            result = await client.generate(
                text="测试",
                voice="zh-CN-XiaoxiaoNeural",
                rate="+50%",
                volume="-20%",
                pitch="+10Hz",
            )

            assert result.success is True
            # 验证语音参数被正确传递
            mock_class.assert_called_once()
            call_kwargs = mock_class.call_args[1]
            assert call_kwargs["rate"] == "+50%"
            assert call_kwargs["volume"] == "-20%"
            assert call_kwargs["pitch"] == "+10Hz"


class TestEdgeTTSClientIntegration:
    """集成测试: 需要网络连接到Edge-TTS服务"""

    @pytest.fixture
    def real_client(self):
        """创建真实Edge-TTS客户端"""
        return EdgeTTSClient(
            api_url="https://edge-tts.com",
            api_key="edge-tts",
            model_name="zh-CN-XiaoxiaoNeural",
            fallback_to_elevenlabs=False,
        )

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_real_edge_tts_connection(self, real_client):
        """测试真实Edge-TTS连接（需要网络）"""
        result = await real_client.validate_config()
        # 如果网络不可用，测试会跳过
        if not result:
            pytest.skip("Edge-TTS服务不可用，跳过集成测试")
        assert result is True

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_real_edge_tts_list_voices(self, real_client):
        """测试真实获取音色列表（需要网络）"""
        voices = await real_client.list_voices()
        if not voices:
            pytest.skip("Edge-TTS服务不可用，跳过集成测试")

        assert len(voices) > 0
        # 验证中文音色存在
        zh_voices = [v for v in voices if v.get("Locale", "") == "zh-CN"]
        assert len(zh_voices) > 0

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_real_edge_tts_synthesize(self, real_client):
        """测试真实语音合成（需要网络）"""
        # 先验证连接
        if not await real_client.validate_config():
            pytest.skip("Edge-TTS服务不可用，跳过集成测试")

        result = await real_client.generate(
            text="这是一个测试",
            voice="zh-CN-XiaoxiaoNeural",
            output_format="mp3",
        )

        assert result.success is True
        # 验证音频文件存在
        audio_file = Path(result.text)
        assert audio_file.exists()
        assert audio_file.stat().st_size > 0

        # 清理测试文件
        audio_file.unlink()
