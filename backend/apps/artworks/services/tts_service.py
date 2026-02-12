"""
TTS (Text-to-Speech) 服务模块

职责:
- 封装 Edge-TTS 客户端调用
- 提供统一的语音合成服务接口
- 处理音频生成任务和进度追踪
- 支持 Redis 发布进度更新

Epic 10 Story 10.3: Edge-TTS 本地语音生成引擎集成
"""

import asyncio
import logging
import os
import tempfile
import uuid
from typing import Any, Callable, Dict, List, Optional

from core.ai_client.edge_tts_client import EdgeTTSClient
from core.redis.publisher import RedisStreamPublisher

logger = logging.getLogger(__name__)


class EdgeTTSService:
    """
    Edge-TTS 语音合成服务

    职责:
    - 创建和管理 Edge-TTS 客户端实例
    - 处理语音合成请求
    - 通过 Redis 发布进度更新
    - 支持批量合成
    - 错误处理和重试逻辑

    配置:
    - api_url: Edge-TTS API 地址 (默认使用本地 edge-tts)
    - voice_name: 音色名称 (默认: zh-CN-XiaoxiaoNeural)
    - timeout: 超时时间 (默认: 120 秒)
    """

    # 可用音色列表（中文）
    AVAILABLE_VOICES = {
        "zh-CN-XiaoxiaoNeural": {"gender": "女", "description": "晓晓（温柔女声）"},
        "zh-CN-YunxiNeural": {"gender": "女", "description": "云希（温柔女声）"},
        "zh-CN-YunyangNeural": {"gender": "男", "description": "云扬（温柔男声）"},
        "zh-CN-YunzeNeural": {"gender": "男", "description": "云泽（沉稳男声）"},
        "zh-CN-XiaoyiNeural": {"gender": "女", "description": "晓伊（活泼女声）"},
        "zh-CN-YunjianNeural": {"gender": "男", "description": "云健（明朗男声）"},
    }

    def __init__(
        self,
        api_url: str = "",
        api_key: str = "edge-tts",
        model_name: str = "edge-tts",
        timeout: int = 120,
        **kwargs
    ):
        """
        初始化 Edge-TTS 服务

        Args:
            api_url: API 地址（Edge-TTS 是本地库，此参数占位）
            api_key: API 密钥（占位符）
            model_name: 模型名称（默认 edge-tts）
            timeout: 超时时间
            **kwargs: 其他配置
        """
        self.client = EdgeTTSClient(
            api_url=api_url or "https://edge-tts.com",  # 占位URL
            api_key=api_key,
            model_name=model_name,
            timeout=timeout,
            **kwargs
        )

    def synthesize(
        self,
        text: str,
        voice_name: str = "zh-CN-XiaoxiaoNeural",
        rate: str = "+0%",
        volume: str = "+0%",
        pitch: str = "+0Hz",
        output_format: str = "mp3",
        progress_id: Optional[str] = None,
        progress_callback: Optional[Callable[[float], None]] = None
    ) -> Dict[str, Any]:
        """
        合成语音

        Args:
            text: 要合成的文本
            voice_name: 音色名称
            rate: 语速调整（如 "+0%", "-10%", "+20%"）
            volume: 音量调整（如 "+0%", "+20%", "-10%"）
            pitch: 音调调整（如 "+0Hz", "+2Hz", "-2Hz"）
            output_format: 输出格式（mp3/wav）
            progress_id: 进度追踪 ID（用于 Redis 发布）
            progress_callback: 进度回调函数

        Returns:
            Dict[str, Any]: 合成结果
                {
                    "success": bool,
                    "audio_path": str,
                    "duration_ms": int,
                    "metadata": {...},
                    "error": str (如果失败)
                }
        """
        if not progress_id:
            progress_id = str(uuid.uuid4())

        publisher = RedisStreamPublisher(f"tts_{progress_id}", "synthesize")  # project_id, stage_name

        def wrapped_callback(progress: float):
            """包装的进度回调，同时支持 Redis 发布"""
            # 发布到 Redis
            publisher.publish_stage_update(
                status="processing",
                progress=int(progress),
                message=f"语音合成中... {progress:.1f}%"
            )
            # 调用用户回调
            if progress_callback:
                progress_callback(progress)

        try:
            # 发布开始状态
            publisher.publish_stage_update(
                status="processing",
                progress=0,
                message=f"开始合成语音，文本长度: {len(text)} 字符"
            )

            # 验证音色
            if voice_name not in self.AVAILABLE_VOICES:
                logger.warning(f"未知音色: {voice_name}，使用默认音色")
                voice_name = "zh-CN-XiaoxiaoNeural"

            # 创建临时文件保存音频
            temp_dir = tempfile.gettempdir()
            temp_filename = f"tts_{progress_id}.{output_format}"
            temp_path = os.path.join(temp_dir, temp_filename)

            # 使用同步方式包装异步调用
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            try:
                # 调用 Edge-TTS 客户端
                response = loop.run_until_complete(
                    self.client.generate(
                        text=text,
                        voice=voice_name,
                        rate=rate,
                        volume=volume,
                        pitch=pitch,
                        output_path=temp_path
                    )
                )
            finally:
                loop.close()

            # 发布完成状态
            if response.success:
                publisher.publish_done(
                    full_text=text,
                    metadata={
                        "voice_name": voice_name,
                        "duration_ms": response.data.get("duration_ms", 0),
                        "format": output_format
                    }
                )

                result = {
                    "success": True,
                    "audio_path": response.data.get("audio_file", temp_path),
                    "duration_ms": response.data.get("duration_ms", 0),
                    "metadata": {
                        "voice_name": voice_name,
                        "format": output_format,
                        "text_length": len(text)
                    }
                }
                logger.info(f"语音合成成功: voice={voice_name}, duration={result['duration_ms']}ms")
                return result
            else:
                publisher.publish_error(error=response.error or "未知错误")
                return {
                    "success": False,
                    "error": response.error or "合成失败"
                }

        except Exception as e:
            logger.error(f"语音合成失败: {e}")
            publisher.publish_error(error=str(e))
            return {
                "success": False,
                "error": f"合成失败: {e!s}"
            }
        finally:
            publisher.close()

    def batch_synthesize(
        self,
        texts: List[str],
        voice_name: str = "zh-CN-XiaoxiaoNeural",
        rate: str = "+0%",
        volume: str = "+0%",
        pitch: str = "+0Hz",
        output_format: str = "mp3",
        progress_id: Optional[str] = None,
        progress_callback: Optional[Callable[[float], None]] = None
    ) -> List[Dict[str, Any]]:
        """
        批量合成语音

        Args:
            texts: 要合成的文本列表
            voice_name: 音色名称
            rate: 语速调整
            volume: 音量调整
            pitch: 音调调整
            output_format: 输出格式
            progress_id: 进度追踪 ID
            progress_callback: 进度回调函数

        Returns:
            List[Dict[str, Any]]: 合成结果列表
        """
        if not progress_id:
            progress_id = str(uuid.uuid4())

        total = len(texts)
        results = []

        for i, text in enumerate(texts):
            # 计算整体进度
            def combined_callback(progress: float, index=i, count=total):
                """合并回调"""
                # 当前任务进度占总进度的权重
                task_progress = (progress / count)
                base_progress = (index / count) * 100
                overall_progress = base_progress + task_progress

                publisher = RedisStreamPublisher(f"tts_batch_{progress_id}", "batch")  # project_id, stage_name  # project_id, stage_name
                publisher.publish_progress_detailed(
                    percentage=min(100, overall_progress),
                    current_step=index + 1,
                    total_steps=count,
                    step_name=f"批量合成 {index+1}/{count}"
                )
                if progress_callback:
                    progress_callback(overall_progress)

            result = self.synthesize(
                text=text,
                voice_name=voice_name,
                rate=rate,
                volume=volume,
                pitch=pitch,
                output_format=output_format,
                progress_id=f"{progress_id}_{i}",
                progress_callback=combined_callback
            )
            results.append(result)

        # 发布批量完成
        success_count = sum(1 for r in results if r.get("success"))
        publisher = RedisStreamPublisher(f"tts_batch_{progress_id}", "batch")  # project_id, stage_name
        publisher.publish_done(
            full_text=f"批量合成完成: {success_count}/{total}",
            metadata={
                "total": total,
                "success": success_count,
                "failed": total - success_count
            }
        )
        publisher.close()

        return results

    def get_available_voices(self) -> Dict[str, Dict[str, str]]:
        """
        获取可用音色列表

        Returns:
            Dict[str, Dict[str, str]]: 音色字典
                {
                    "voice_name": {
                        "gender": "女/男",
                        "description": "描述"
                    }
                }
        """
        return self.AVAILABLE_VOICES.copy()

    def get_voice_info(self, voice_name: str) -> Optional[Dict[str, str]]:
        """
        获取音色信息

        Args:
            voice_name: 音色名称

        Returns:
            Optional[Dict[str, str]]: 音色信息，如果不存在返回 None
        """
        return self.AVAILABLE_VOICES.get(voice_name)

    def get_recommended_voice(
        self,
        character_gender: str = "女",
        character_age: str = "adult",
        emotion: str = "neutral"
    ) -> str:
        """
        根据角色特征推荐音色

        Args:
            character_gender: 角色性别（男/女）
            character_age: 角色年龄（child/teen/adult/senior）
            emotion: 情感（neutral/happy/sad/angry/excited）

        Returns:
            str: 推荐的音色名称
        """
        # 根据性别筛选
        if character_gender == "男":
            candidates = [
                "zh-CN-YunyangNeural",
                "zh-CN-YunzeNeural",
                "zh-CN-YunjianNeural"
            ]
        else:
            candidates = [
                "zh-CN-XiaoxiaoNeural",
                "zh-CN-YunxiNeural",
                "zh-CN-XiaoyiNeural"
            ]

        # 根据年龄和情感调整
        if character_age == "child":
            # 儿童优先选择活泼音色
            return candidates[-1] if candidates else "zh-CN-XiaoyiNeural"
        elif character_age == "senior":
            # 老年选择沉稳音色
            return candidates[0] if candidates else "zh-CN-YunzeNeural"
        elif emotion in ["happy", "excited"]:
            # 开心/兴奋选择活泼音色
            return candidates[-1] if candidates else "zh-CN-XiaoyiNeural"
        else:
            # 默认选择第一个
            return candidates[0] if candidates else "zh-CN-XiaoxiaoNeural"

    def health_check(self) -> Dict[str, Any]:
        """
        健康检查

        Returns:
            Dict[str, Any]: 健康状态
                {
                    "healthy": bool,
                    "latency_ms": int,
                    "available_voices": int,
                    "error": str (如果失败)
                }
        """
        import time
        start_time = time.time()

        try:
            # 简单的合成测试
            test_result = self.synthesize(
                text="测试",
                voice_name="zh-CN-XiaoxiaoNeural",
                output_format="mp3"
            )

            latency_ms = int((time.time() - start_time) * 1000)

            return {
                "healthy": test_result.get("success", False),
                "latency_ms": latency_ms,
                "available_voices": len(self.AVAILABLE_VOICES),
                "error": test_result.get("error") if not test_result.get("success") else None
            }

        except Exception as e:
            latency_ms = int((time.time() - start_time) * 1000)
            return {
                "healthy": False,
                "latency_ms": latency_ms,
                "available_voices": len(self.AVAILABLE_VOICES),
                "error": str(e)
            }


# 单例模式，便于导入使用
_service_instance: Optional[EdgeTTSService] = None


def get_tts_service() -> EdgeTTSService:
    """获取 TTS 服务单例"""
    global _service_instance
    if _service_instance is None:
        _service_instance = EdgeTTSService()
    return _service_instance
