"""
角色资产批量生成Celery任务

职责: 执行角色立绘和音色的批量异步生成
遵循单一职责原则(SRP)

Story 11.1.4: 角色资产批量生成
- 批量立绘生成 (基于ComfyUI)
- 批量音色生成 (基于Edge-TTS)
- AI智能推荐造型 (基于Ollama)
- 异步任务处理 (Celery)
- 生成进度追踪 (WebSocket实时更新)
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional

from celery import group
from django.conf import settings
from django.utils import timezone

from config.celery import app
from core.ai_client.comfyui_client import ComfyUIClient
from core.ai_client.edge_tts_client import EdgeTTSClient
from core.ai_client.ollama_client import OllamaClient
from core.redis import RedisStreamPublisher

from .models import (
    CharacterPose,
    CharacterProfile,
    CharacterVoiceConfig,
    GenerationHistory,
    GenerationProgress,
    Shot,
)

logger = logging.getLogger(__name__)


@app.task(
    bind=True,
    max_retries=2,
    default_retry_delay=60,
    acks_late=True,
    soft_time_limit=300,  # 5分钟软超时
    time_limit=600,  # 10分钟硬超时
)
def generate_portrait(
    self,
    character_id: int,
    pose_type: str,
    prompt_params: Dict[str, Any],
    progress_id: Optional[int] = None,
) -> Dict[str, Any]:
    """
    生成单个角色立绘

    Args:
        self: Celery任务实例
        character_id: 角色ID
        pose_type: 造型类型 (casual/formal/battle/school/home/custom)
        prompt_params: 提示词参数
            - prompt: 正向提示词 (JSON workflow或文本)
            - negative_prompt: 负向提示词 (可选)
            - width: 图片宽度 (默认512)
            - height: 图片高度 (默认768)
            - steps: 采样步数 (默认20)
            - seed: 随机种子 (可选)
        progress_id: 进度记录ID

    Returns:
        Dict包含: pose_id, image_url, character_id, pose_type
    """
    task_id = self.request.id
    logger.info(
        f"开始生成角色立绘: character_id={character_id}, pose_type={pose_type}, task_id={task_id}"
    )

    try:
        # 获取角色
        character = CharacterProfile.objects.get(id=character_id)

        # 更新进度
        if progress_id:
            _update_progress(
                progress_id,
                status="processing",
                message=f"正在生成{character.display_name}的{pose_type}造型立绘...",
            )

        # 初始化ComfyUI客户端
        comfyui_client = ComfyUIClient(
            api_url=getattr(settings, "COMFYUI_API_URL", "http://localhost:8188"),
            api_key="",
            model_name=getattr(settings, "COMFYUI_CHECKPOINT", "sdxl_base"),
        )

        # 准备提示词
        prompt = prompt_params.get(
            "prompt", f"anime character portrait of {character.display_name}, {pose_type} style"
        )
        negative_prompt = prompt_params.get("negative_prompt", "low quality, blurry, distorted")
        width = prompt_params.get("width", 512)
        height = prompt_params.get("height", 768)
        steps = prompt_params.get("steps", 20)
        seed = prompt_params.get("seed")

        # 生成图片 (使用同步方式包装异步)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            response = loop.run_until_complete(
                comfyui_client.generate(
                    prompt=prompt,
                    negative_prompt=negative_prompt,
                    width=width,
                    height=height,
                    steps=steps,
                    seed=seed,
                )
            )
        finally:
            loop.close()

        if not response.success:
            raise Exception(f"ComfyUI生成失败: {response.error}")

        # 获取生成的图片URL
        image_url = response.data.get("image_url", response.text)

        # 保存到CharacterPose
        pose = CharacterPose.objects.create(
            character=character,
            pose_name=f"{pose_type}造型",
            pose_type=pose_type,
            pose_image=image_url,
            extraction_source="AI_generated",
            description=f"AI生成的{pose_type}造型立绘",
        )

        logger.info(f"立绘生成成功: pose_id={pose.id}, image_url={image_url}")

        # 更新进度
        if progress_id:
            _update_progress(progress_id, completed_items=1)

        # 记录生成历史
        GenerationHistory.objects.create(
            character=character,
            generation_type="portrait",
            prompt_params={
                "pose_type": pose_type,
                "prompt": prompt,
                "negative_prompt": negative_prompt,
                "width": width,
                "height": height,
                "steps": steps,
                "seed": seed,
            },
            result_url=image_url,
            is_used=True,
        )

        return {
            "pose_id": pose.id,
            "character_id": character_id,
            "character_name": character.display_name,
            "pose_type": pose_type,
            "image_url": image_url,
            "task_id": task_id,
        }

    except Exception as e:
        logger.error(f"立绘生成失败: {e}")

        # 更新进度
        if progress_id:
            _update_progress(progress_id, failed_items=1, error_message=str(e))

        # 重试
        if self.request.retries < self.max_retries:
            raise self.retry(exc=e)

        return {
            "character_id": character_id,
            "pose_type": pose_type,
            "error": str(e),
            "task_id": task_id,
        }


@app.task(
    bind=True,
    max_retries=2,
    default_retry_delay=60,
    acks_late=True,
    soft_time_limit=120,  # 2分钟软超时
    time_limit=180,  # 3分钟硬超时
)
def generate_voice_sample(
    self,
    character_id: int,
    text: str,
    voice_params: Dict[str, Any],
    progress_id: Optional[int] = None,
) -> Dict[str, Any]:
    """
    生成单个角色音色样本

    Args:
        self: Celery任务实例
        character_id: 角色ID
        text: 试听文本
        voice_params: 音色参数
            - voice_name: 音色名称 (默认 zh-CN-XiaoxiaoNeural)
            - rate: 语速 (如 "+0%")
            - volume: 音量 (如 "+0%")
            - pitch: 音调 (如 "+0Hz")
            - output_format: 输出格式 (默认 mp3)
        progress_id: 进度记录ID

    Returns:
        Dict包含: voice_config_id, audio_url, character_id
    """
    task_id = self.request.id
    logger.info(
        f"开始生成角色音色: character_id={character_id}, text={text[:30]}, task_id={task_id}"
    )

    try:
        # 获取角色
        character = CharacterProfile.objects.get(id=character_id)

        # 更新进度
        if progress_id:
            _update_progress(
                progress_id,
                status="processing",
                message=f"正在生成{character.display_name}的音色样本...",
            )

        # 初始化Edge-TTS客户端
        edge_client = EdgeTTSClient(
            api_url="https://edge-tts.com",
            api_key="edge-tts",
            model_name=voice_params.get("voice_name", "zh-CN-XiaoxiaoNeural"),
        )

        # 合成语音
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            response = loop.run_until_complete(
                edge_client.generate(
                    text=text,
                    voice=voice_params.get("voice_name"),
                    rate=voice_params.get("rate", "+0%"),
                    volume=voice_params.get("volume", "+0%"),
                    pitch=voice_params.get("pitch", "+0Hz"),
                    output_format=voice_params.get("output_format", "mp3"),
                )
            )
        finally:
            loop.close()

        if not response.success:
            raise Exception(f"Edge-TTS生成失败: {response.error}")

        # 获取音频文件路径
        audio_file = response.data.get("audio_file", response.text)

        # 保存到CharacterVoiceConfig
        voice_config, created = CharacterVoiceConfig.objects.get_or_create(
            character=character,
            defaults={
                "tts_engine": "edge",
                "voice_id": voice_params.get("voice_name", "zh-CN-XiaoxiaoNeural"),
                "voice_type": "女声"
                if "Xiaoxiao" in voice_params.get("voice_name", "")
                else "男声",
                "voice_sample_url": audio_file,
            },
        )

        if not created:
            voice_config.voice_sample_url = audio_file
            voice_config.save()

        logger.info(f"音色样本生成成功: voice_config_id={voice_config.id}, audio_file={audio_file}")

        # 更新进度
        if progress_id:
            _update_progress(progress_id, completed_items=1)

        # 记录生成历史
        GenerationHistory.objects.create(
            character=character,
            generation_type="voice",
            voice_params=voice_params,
            result_url=audio_file,
            is_used=True,
        )

        return {
            "voice_config_id": voice_config.id,
            "character_id": character_id,
            "character_name": character.display_name,
            "audio_url": audio_file,
            "task_id": task_id,
        }

    except Exception as e:
        logger.error(f"音色样本生成失败: {e}")

        # 更新进度
        if progress_id:
            _update_progress(progress_id, failed_items=1, error_message=str(e))

        # 重试
        if self.request.retries < self.max_retries:
            raise self.retry(exc=e)

        return {
            "character_id": character_id,
            "error": str(e),
            "task_id": task_id,
        }


@app.task
def recommend_poses(scene_description: str) -> List[Dict[str, Any]]:
    """
    AI推荐造型 (基于场景描述分析)

    Args:
        scene_description: 场景描述文本

    Returns:
        List[Dict]: 推荐的造型列表，每个包含:
            - pose_type: 造型类型
            - confidence: 置信度
            - reason: 推荐理由
    """
    logger.info(f"开始AI推荐造型: scene={scene_description[:50]}")

    try:
        # 初始化Ollama客户端
        ollama_client = OllamaClient(
            api_url=getattr(settings, "OLLAMA_API_URL", "http://localhost:11434"),
            api_key="ollama",
            model_name=getattr(settings, "OLLAMA_MODEL", "llama2"),
        )

        # 构建提示词
        prompt = f"""分析以下场景描述，推荐适合的角色造型类型。

场景描述: {scene_description}

可选造型类型:
- casual: 休闲装 (适合日常、居家场景)
- formal: 正式装 (适合宴会、会议场景)
- battle: 战斗装 (适合战斗、冲突场景)
- school: 校服 (适合校园场景)
- home: 居家服 (适合家庭场景)
- custom: 自定义 (其他特殊场景)

请以JSON格式返回推荐结果，格式如下:
[
    {{"pose_type": "casual", "confidence": 0.9, "reason": "场景描述了日常对话"}},
    {{"pose_type": "formal", "confidence": 0.7, "reason": "可能需要正式场合"}}
]"""

        # 调用Ollama
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            response = loop.run_until_complete(ollama_client.generate(prompt, max_tokens=500))
        finally:
            loop.close()

        if not response.success:
            logger.error(f"Ollama推荐失败: {response.error}")
            return []

        # 解析结果 (简单解析，实际应该更严格)
        import json
        import re

        result_text = response.text
        # 尝试提取JSON
        json_match = re.search(r"\[.*?\]", result_text, re.DOTALL)
        if json_match:
            try:
                recommendations = json.loads(json_match.group())
                logger.info(f"AI推荐造型成功: {len(recommendations)}个推荐")
                return recommendations
            except json.JSONDecodeError:
                pass

        # 默认推荐
        return [{"pose_type": "casual", "confidence": 0.8, "reason": "默认推荐休闲造型"}]

    except Exception as e:
        logger.error(f"AI推荐造型失败: {e}")
        return [{"pose_type": "casual", "confidence": 0.5, "reason": "推荐失败，使用默认"}]


@app.task
def batch_generate_assets(
    character_ids: List[int],
    generation_config: Dict[str, Any],
    user_id: int,
) -> Dict[str, Any]:
    """
    批量生成角色资产 (立绘+音色)

    Args:
        character_ids: 角色ID列表
        generation_config: 生成配置
            - portrait: 立绘配置 (pose_type, prompt_params)
            - voice: 音色配置 (text, voice_params)
        user_id: 用户ID

    Returns:
        Dict包含: task_id, progress_id, total_items, status
    """
    logger.info(f"开始批量生成角色资产: character_ids={character_ids}, config={generation_config}")

    # 创建进度记录
    progress = GenerationProgress.objects.create(
        user_id=user_id,
        generation_type="batch",
        total_items=len(character_ids) * 2,  # 立绘+音色
        status="processing",
    )

    portrait_config = generation_config.get("portrait", {})
    voice_config = generation_config.get("voice", {})

    # 准备任务
    portrait_tasks = [
        generate_portrait.s(
            character_id=cid,
            pose_type=portrait_config.get("pose_type", "casual"),
            prompt_params=portrait_config.get("prompt_params", {}),
            progress_id=progress.id,
        )
        for cid in character_ids
    ]

    voice_tasks = [
        generate_voice_sample.s(
            character_id=cid,
            text=voice_config.get("text", "你好，我是测试语音。"),
            voice_params=voice_config.get("voice_params", {}),
            progress_id=progress.id,
        )
        for cid in character_ids
    ]

    # 并发执行所有任务
    job = group(portrait_tasks + voice_tasks)

    # 保存Celery任务ID
    result = job.apply_async()
    progress.celery_task_id = result.id
    progress.save()

    logger.info(f"批量生成任务已启动: progress_id={progress.id}, task_id={result.id}")

    return {
        "progress_id": progress.id,
        "task_id": result.id,
        "total_items": progress.total_items,
        "status": "processing",
        "message": f"已启动{len(character_ids)}个角色的批量生成任务",
    }


@app.task
def notify_generation_complete(result: Dict[str, Any], progress_id: int) -> None:
    """
    通知生成完成

    Args:
        result: 生成结果
        progress_id: 进度记录ID
    """
    try:
        progress = GenerationProgress.objects.get(id=progress_id)
        progress.status = "completed"
        progress.completed_at = timezone.now()
        progress.save()

        # 通过Redis发布通知
        publisher = RedisStreamPublisher(f"generation_{progress_id}", "complete")
        publisher.publish_stage_update(
            status="completed",
            progress=100,
            message="批量生成完成",
            data=result,
        )

        logger.info(f"批量生成完成通知已发送: progress_id={progress_id}")

    except Exception as e:
        logger.error(f"发送完成通知失败: {e}")


def _update_progress(
    progress_id: int,
    status: Optional[str] = None,
    completed_items: int = 0,
    failed_items: int = 0,
    error_message: str = "",
    message: str = "",
) -> None:
    """
    更新生成进度

    Args:
        progress_id: 进度记录ID
        status: 状态
        completed_items: 完成数量
        failed_items: 失败数量
        error_message: 错误消息
        message: 通知消息
    """
    try:
        progress = GenerationProgress.objects.get(id=progress_id)

        if status:
            progress.status = status

        if completed_items:
            progress.completed_items += completed_items

        if failed_items:
            progress.failed_items += failed_items

        if error_message:
            progress.error_message = error_message

        progress.save()

        # 发布进度更新
        if message:
            publisher = RedisStreamPublisher(f"generation_{progress_id}", "progress")
            publisher.publish_stage_update(
                status=progress.status,
                progress=progress.progress_percentage,
                message=message,
            )

    except Exception as e:
        logger.error(f"更新进度失败: {e}")


@app.task(
    bind=True,
    max_retries=2,
    default_retry_delay=60,
    acks_late=True,
    soft_time_limit=300,  # 5分钟软超时
    time_limit=600,  # 10分钟硬超时
)
def regenerate_shot_content(
    self,
    shot_id: int,
    regenerate_type: str = "both",
    custom_prompt: Optional[str] = None,
) -> Dict[str, Any]:
    """
    重新生成镜头内容 (Story 11.2.4)

    Args:
        self: Celery任务实例
        shot_id: 镜头ID
        regenerate_type: 重新生成类型 ('image' | 'audio' | 'both')
        custom_prompt: 可选的自定义提示词

    Returns:
        Dict包含: shot_id, regenerate_type, image_url, audio_url, task_id
    """
    task_id = self.request.id
    logger.info(
        f"开始重新生成镜头: shot_id={shot_id}, regenerate_type={regenerate_type}, task_id={task_id}"
    )

    try:
        # 获取镜头
        shot = Shot.objects.get(id=shot_id)

        # 更新重试次数和状态
        shot.generation_retry_count += 1
        shot.is_generated = False
        shot.generation_error = ""
        shot.save(update_fields=["generation_retry_count", "is_generated", "generation_error"])

        # 初始化Redis发布器
        publisher = RedisStreamPublisher(f"shot_{shot_id}", "regenerate")

        # 发布开始消息
        publisher.publish_stage_update(
            status="processing", progress=0, message="开始重新生成镜头..."
        )

        # 初始化结果
        result = {
            "shot_id": shot_id,
            "regenerate_type": regenerate_type,
            "task_id": task_id,
        }

        # 重新生成图片
        if regenerate_type in ["image", "both"]:
            publisher.publish_stage_update(
                status="processing", progress=10, message="正在生成图像..."
            )

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            try:
                # TODO: 实现图片生成逻辑
                # 这里应该调用 ComfyUI 或其他图像生成服务
                # 示例: image_url = await image_service.generate(prompt)
                pass
            finally:
                loop.close()

            # result['image_url'] = generated_image_url

        # 重新生成音频
        if regenerate_type in ["audio", "both"]:
            publisher.publish_stage_update(
                status="processing", progress=60, message="正在生成音频..."
            )

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            try:
                # TODO: 实现音频生成逻辑
                # 这里应该调用 Edge-TTS 或其他语音合成服务
                # 示例: audio_url = await tts_service.generate(text, voice)
                pass
            finally:
                loop.close()

            # result['audio_url'] = generated_audio_url

        # 更新生成状态
        shot.is_generated = True
        shot.generation_error = ""
        shot.generated_at = timezone.now()
        shot.save(update_fields=["is_generated", "generation_error", "generated_at"])

        logger.info(f"镜头重新生成成功: shot_id={shot_id}")

        # 通过Redis发布完成通知
        publisher.publish_stage_update(status="completed", progress=100, message="镜头重新生成完成")

        # 关闭Redis连接
        publisher.close()

        return result

    except Shot.DoesNotExist:
        error_msg = f"镜头不存在: shot_id={shot_id}"
        logger.error(error_msg)

        return {
            "shot_id": shot_id,
            "error": error_msg,
            "task_id": task_id,
        }

    except Exception as e:
        logger.error(f"镜头重新生成失败: {e}")

        # 发布错误消息
        try:
            publisher = RedisStreamPublisher(f"shot_{shot_id}", "regenerate")
            publisher.publish_error(error=str(e), retry_count=self.request.retries)
            publisher.close()
        except Exception as pub_error:
            logger.error(f"发布错误消息失败: {pub_error}")

        # 更新错误信息
        try:
            shot = Shot.objects.get(id=shot_id)
            shot.generation_error = str(e)
            shot.save(update_fields=["generation_error"])
        except Shot.DoesNotExist:
            pass

        # 重试
        if self.request.retries < self.max_retries:
            raise self.retry(exc=e)

        return {
            "shot_id": shot_id,
            "regenerate_type": regenerate_type,
            "error": str(e),
            "task_id": task_id,
        }
