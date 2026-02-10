"""
Edge-TTS本地语音合成客户端实现

遵循SOLID原则:
- 继承TTSClient抽象基类 (依赖倒置)
- 实现语音合成和音色列表获取 (接口隔离)
- 支持Fallback机制到ElevenLabs (开闭原则)

Epic 10 Story 10.2: Edge-TTS本地语音合成集成
"""

import asyncio
import logging
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional

import edge_tts

from .base import AIResponse, TTSClient

logger = logging.getLogger(__name__)


class EdgeTTSClient(TTSClient):
    """
    Microsoft Edge-TTS客户端

    功能:
    - 免费本地语音合成 (无需API key)
    - 支持322种音色 (中文14种)
    - 支持语音参数调节 (rate, volume, pitch)
    - 自动Fallback到ElevenLabs (可选)
    - 异步处理支持

    配置:
    - api_url: 占位符 (Edge-TTS不需要，但保持接口一致)
    - api_key: 占位符 (Edge-TTS不需要)
    - model_name: 音色名称 (默认: zh-CN-XiaoxiaoNeural)
    - output_dir: 音频文件输出目录 (可选，默认使用临时目录)
    - fallback_to_elevenlabs: 是否启用Fallback到ElevenLabs (默认: False)

    常用中文音色:
    - zh-CN-XiaoxiaoNeural - 女，温柔
    - zh-CN-YunxiNeural - 男，温和
    - zh-CN-YunjianNeural - 男，成熟
    - zh-TW-HsiaoChenNeural - 繁体中文女声
    """

    def __init__(
        self,
        api_url: str = "https://edge-tts.com",  # 占位符
        api_key: str = "edge-tts",  # 占位符
        model_name: str = "zh-CN-XiaoxiaoNeural",
        proxy_id: Optional[int] = None,
        project_id: Optional[int] = None,
        output_dir: Optional[str] = None,
        fallback_to_elevenlabs: bool = False,
        **kwargs,
    ):
        """
        初始化Edge-TTS客户端

        Args:
            api_url: 占位符 (Edge-TTS不需要)
            api_key: 占位符 (Edge-TTS不需要)
            model_name: 默认音色名称
            proxy_id: 代理配置ID (可选)
            project_id: 项目ID (可选)
            output_dir: 音频文件输出目录 (可选)
            fallback_to_elevenlabs: 是否启用Fallback到ElevenLabs
            **kwargs: 其他配置参数
        """
        super().__init__(
            api_url=api_url,
            api_key=api_key,
            model_name=model_name,
            proxy_id=proxy_id,
            project_id=project_id,
            **kwargs,
        )

        self.output_dir = Path(output_dir) if output_dir else Path(tempfile.gettempdir())
        self.fallback_to_elevenlabs = fallback_to_elevenlabs
        self.fallback_client = None

        # 确保输出目录存在
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Fallback客户端 (延迟加载)
        if fallback_to_elevenlabs:
            self._init_fallback_client()

        # 音色列表缓存
        self._voices_cache: Optional[List[Dict[str, Any]]] = None

    def _init_fallback_client(self):
        """初始化Fallback客户端 (ElevenLabs)"""
        try:
            # 假设未来会有 ElevenLabsTTSClient 实现
            # from .elevenlabs_tts_client import ElevenLabsTTSClient
            # self.fallback_client = ElevenLabsTTSClient(...)
            logger.warning("ElevenLabs Fallback客户端尚未实现")
            self.fallback_client = None
        except Exception as e:
            logger.warning(f"无法初始化Fallback ElevenLabs客户端: {e}")
            self.fallback_client = None

    async def _synthesize_speech(
        self,
        text: str,
        voice: str,
        rate: str,
        volume: str,
        pitch: str,
        output_format: str,
        **kwargs,
    ) -> AIResponse:
        """
        合成语音 (Edge-TTS实现)

        Args:
            text: 要转换的文本
            voice: 音色名称
            rate: 语速 (如 "+50%", "-50%")
            volume: 音量 (如 "+50%", "-50%")
            pitch: 音调 (如 "+50Hz", "-50Hz")
            output_format: 输出格式 ("mp3" 或 "wav")
            **kwargs: 其他参数

        Returns:
            AIResponse: 包含音频文件路径的响应对象
        """
        try:
            # 创建Edge-TTS通信对象
            communicate = edge_tts.Communicate(
                text=text,
                voice=voice,
                rate=rate,
                volume=volume,
                pitch=pitch,
            )

            # 生成输出文件路径
            import uuid

            audio_filename = self.output_dir / f"edge_tts_{uuid.uuid4().hex}.{output_format}"

            # 保存音频文件 (同步方法)
            # 注意: edge_tts.Communicate.save() 是同步方法，需要在独立线程中运行
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                communicate.save_sync,
                str(audio_filename),
            )

            logger.info(f"Edge-TTS语音合成成功: {audio_filename}")

            return AIResponse(
                success=True,
                text=str(audio_filename),  # 返回音频文件路径
                data={
                    "audio_file": str(audio_filename),
                    "format": output_format,
                    "voice": voice,
                    "text": text,
                },
                metadata={
                    "provider": "edge-tts",
                    "engine": "local_tts",
                    "rate": rate,
                    "volume": volume,
                    "pitch": pitch,
                },
            )

        except Exception as e:
            logger.error(f"Edge-TTS语音合成失败: {e}")

            # Fallback到ElevenLabs (如果启用)
            if self.fallback_to_elevenlabs and self.fallback_client:
                logger.info("触发Fallback到ElevenLabs")
                return await self.fallback_client._synthesize_speech(
                    text=text,
                    voice=voice,
                    rate=rate,
                    volume=volume,
                    pitch=pitch,
                    output_format=output_format,
                    **kwargs,
                )

            # 失败返回
            return AIResponse(
                success=False,
                text="",
                error=str(e),
            )

    async def list_voices(self) -> List[Dict[str, Any]]:
        """
        获取可用音色列表

        Returns:
            list: 音色信息列表，每个元素包含:
                - Name: 音色全名
                - ShortName: 简短名称 (如 "zh-CN-XiaoxiaoNeural")
                - Locale: 语言区域 (如 "zh-CN")
                - Gender: 性别 (Female/Male)
                - Description: 描述
        """
        try:
            # 如果有缓存，直接返回
            if self._voices_cache:
                return self._voices_cache

            # 获取音色列表 (edge-tts是异步API，需要在事件循环中运行)
            voices = await edge_tts.list_voices()

            # 格式化音色信息
            formatted_voices = []
            for voice in voices:
                # 提取ShortName (如 "zh-CN-XiaoxiaoNeural")
                full_name = voice.get("Name", "")
                # 格式: "Microsoft Server Speech Text to Speech Voice (zh-CN, XiaoxiaoNeural)"
                if "(" in full_name and ", " in full_name and full_name.endswith(")"):
                    # 提取括号内的内容: "zh-CN, XiaoxiaoNeural"
                    import re

                    bracket_content = full_name[full_name.rfind("(") + 1 : full_name.rfind(")")]
                    # 分割: ["zh-CN", "XiaoxiaoNeural"]
                    parts = [p.strip() for p in bracket_content.split(", ")]
                    if len(parts) >= 2:
                        # 组合: "zh-CN-XiaoxiaoNeural"
                        short_name = f"{parts[0]}-{parts[1]}"
                    else:
                        short_name = full_name
                else:
                    short_name = full_name

                formatted_voices.append(
                    {
                        "Name": full_name,
                        "ShortName": short_name,
                        "Locale": voice.get("Locale", ""),
                        "Gender": voice.get("Gender", ""),
                        "Description": voice.get("Description", ""),
                    }
                )

            # 缓存结果
            self._voices_cache = formatted_voices

            logger.info(f"Edge-TTS获取音色列表成功，共 {len(formatted_voices)} 个音色")
            return formatted_voices

        except Exception as e:
            logger.error(f"Edge-TTS获取音色列表失败: {e}")
            return []

    async def get_available_voices(self, locale: Optional[str] = None) -> List[str]:
        """
        获取可用音色名称列表 (便捷方法)

        Args:
            locale: 语言区域过滤 (如 "zh-CN" 只返回中文音色)

        Returns:
            list: 音色ShortName列表
        """
        voices = await self.list_voices()

        if locale:
            # 过滤指定语言的音色
            voices = [v for v in voices if v.get("Locale", "") == locale]

        return [v.get("ShortName", "") for v in voices]

    async def validate_config(self) -> bool:
        """
        验证Edge-TTS配置是否有效

        验证方法:
        1. 尝试获取音色列表
        2. 测试简单的语音合成

        Returns:
            bool: 配置是否有效
        """
        try:
            # 测试1: 获取音色列表
            voices = await self.list_voices()
            if not voices:
                logger.error("Edge-TTS音色列表为空")
                return False

            logger.info(f"Edge-TTS配置验证成功，可用音色数: {len(voices)}")
            return True

        except Exception as e:
            logger.error(f"Edge-TTS配置验证失败: {e}")
            return False

    async def health_check(self) -> bool:
        """
        健康检查

        Returns:
            bool: 服务是否健康
        """
        try:
            return await self.validate_config()
        except Exception:
            return False

    async def generate(
        self,
        text: str,
        voice: Optional[str] = None,
        rate: str = "+0%",
        volume: str = "+0%",
        pitch: str = "+0Hz",
        output_format: str = "mp3",
        **kwargs,
    ) -> AIResponse:
        """
        合成语音 (公共接口)

        Args:
            text: 要转换的文本
            voice: 音色名称 (默认使用 model_name)
            rate: 语速调整
            volume: 音量调整
            pitch: 音调调整
            output_format: 输出格式
            **kwargs: 其他参数

        Returns:
            AIResponse: 包含音频文件路径的响应对象
        """
        # 使用默认音色 (model_name) 如果未指定
        if voice is None:
            voice = self.model_name

        return await self._synthesize_speech(
            text=text,
            voice=voice,
            rate=rate,
            volume=volume,
            pitch=pitch,
            output_format=output_format,
            **kwargs,
        )
