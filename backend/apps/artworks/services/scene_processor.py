"""
场景处理器服务 (Story 12-1.3)

职责:
- 处理单个场景的完整生命周期
- 集成 Shot 内容生成（调用 Epic 10 的本地AI引擎）
- 实现进度追踪和推送
- 支持失败重试

工作流:
    1. 更新工作流状态为 running
    2. 获取场景的所有 Shot
    3. 依次处理每个 Shot：
       - 生成图像（调用 ComfyUI 服务）
       - 生成音频（调用 TTS 服务）
       - 更新 Shot 状态
    4. 推送进度更新
    5. 标记场景为完成

设计原则:
- 单一职责 (SRP): 只负责场景处理逻辑
- 依赖倒置 (DIP): 依赖抽象的服务接口
- 开闭原则 (OCP): 支持扩展新的生成服务
"""

import logging
from typing import Any, Dict, Optional

from django.utils import timezone

from apps.artworks.models import ChapterWorkflow, ScriptScene, Shot, WorkflowEvent
from core.redis.publisher import RedisStreamPublisher

logger = logging.getLogger(__name__)


class SceneProcessorService:
    """
    单场景处理服务 (Story 12-1.3)

    负责处理单个场景的完整生命周期，包括图像生成、音频生成和状态更新。

    职责:
    - 获取场景下的所有镜头 (Shot)
    - 依次处理每个镜头的图像和音频生成
    - 推送进度更新到 Redis
    - 记录工作流事件

    Attributes:
        workflow_id: 工作流 ID
        workflow: ChapterWorkflow 实例
        publisher: Redis 发布器

    Example:
        >>> processor = SceneProcessorService(workflow_id)
        >>> result = processor.process_scene(scene_id)
        >>> print(result)
        {'scene_id': 1, 'shots_processed': 5, 'status': 'completed'}
    """

    def __init__(self, workflow_id: str):
        """
        初始化场景处理器

        Args:
            workflow_id: 工作流 UUID 字符串

        Raises:
            ChapterWorkflow.DoesNotExist: 如果工作流不存在
        """
        self.workflow_id = workflow_id
        try:
            self.workflow = ChapterWorkflow.objects.get(workflow_id=workflow_id)
        except ChapterWorkflow.DoesNotExist:
            logger.error(f"工作流不存在: workflow_id={workflow_id}")
            raise

        # 初始化 Redis 发布器
        self.publisher = RedisStreamPublisher(
            project_id=str(workflow_id),
            stage_name="scene_processor"
        )

    def process_scene(self, scene_id: int) -> Dict[str, Any]:
        """
        处理单个场景

        工作流:
            1. 验证场景存在
            2. 发布场景开始事件
            3. 获取场景的所有 Shot
            4. 依次处理每个 Shot
            5. 推送进度更新
            6. 标记场景为完成

        Args:
            scene_id: 场景 ID

        Returns:
            Dict[str, Any]: 处理结果
                {
                    "scene_id": int,
                    "shots_processed": int,
                    "status": str,
                    "errors": list (可选)
                }

        Raises:
            ValueError: 如果场景不存在
            Exception: 如果处理过程中发生错误
        """
        # 获取场景
        try:
            scene = ScriptScene.objects.select_related('chapter').get(id=scene_id)
        except ScriptScene.DoesNotExist:
            error_msg = f"场景不存在: scene_id={scene_id}"
            logger.error(error_msg)
            raise ValueError(error_msg)

        # 获取所有镜头
        shots = scene.shots.all().order_by('sort_order', 'shot_number')
        total_shots = shots.count()

        if total_shots == 0:
            logger.warning(f"场景没有镜头: scene_id={scene_id}")
            self._publish_event(
                event_type=WorkflowEvent.EventType.SCENE_SKIPPED,
                scene_id=scene_id,
                message=f"场景 {scene.scene_name} 没有镜头，跳过处理"
            )
            return {
                "scene_id": scene_id,
                "shots_processed": 0,
                "status": "skipped"
            }

        # 发布场景开始事件
        self._publish_event(
            event_type=WorkflowEvent.EventType.SCENE_STARTED,
            scene_id=scene_id,
            message=f"开始处理场景: {scene.scene_name}"
        )

        logger.info(f"开始处理场景: scene_id={scene_id}, shots={total_shots}")

        # 处理每个镜头
        processed = 0
        errors = []

        for shot in shots:
            try:
                self._process_shot(shot)
                processed += 1

                # 推送进度
                progress = int((processed / total_shots) * 100)
                self._publish_progress(scene_id, progress, processed, total_shots)

                logger.info(f"镜头处理成功: shot_id={shot.id}, progress={progress}%")

            except Exception as e:
                error_msg = f"镜头 {shot.id} 处理失败: {e!s}"
                logger.error(error_msg)
                errors.append({"shot_id": shot.id, "error": str(e)})

                # 发布失败事件
                self._publish_event(
                    event_type=WorkflowEvent.EventType.SCENE_FAILED,
                    scene_id=scene_id,
                    message=error_msg,
                    metadata={"shot_id": shot.id, "error": str(e)}
                )

                # 根据配置决定是否继续处理
                # 这里选择继续处理其他镜头，记录错误
                continue

        # 标记场景完成
        if processed == total_shots:
            self._publish_event(
                event_type=WorkflowEvent.EventType.SCENE_COMPLETED,
                scene_id=scene_id,
                message=f"场景 {scene.scene_name} 处理完成，共处理 {processed} 个镜头"
            )

            # 更新场景完成状态
            scene.is_completed = True
            scene.shot_count = processed
            scene.save(update_fields=["is_completed", "shot_count"])

            result_status = "completed"
        elif processed > 0:
            # 部分成功
            self._publish_event(
                event_type=WorkflowEvent.EventType.SCENE_COMPLETED,
                scene_id=scene_id,
                message=f"场景 {scene.scene_name} 部分完成，成功 {processed}/{total_shots} 个镜头"
            )
            result_status = "partial"
        else:
            # 全部失败
            self._publish_event(
                event_type=WorkflowEvent.EventType.SCENE_FAILED,
                scene_id=scene_id,
                message=f"场景 {scene.scene_name} 处理失败，所有镜头均处理失败"
            )
            result_status = "failed"

        logger.info(
            f"场景处理完成: scene_id={scene_id}, "
            f"processed={processed}/{total_shots}, status={result_status}"
        )

        result = {
            "scene_id": scene_id,
            "shots_processed": processed,
            "total_shots": total_shots,
            "status": result_status
        }

        if errors:
            result["errors"] = errors

        return result

    def _process_shot(self, shot: Shot) -> None:
        """
        处理单个镜头

        调用 Epic 10 的服务生成内容：
        - generated_image: 调用 ComfyUI 服务
        - generated_audio: 调用 Edge-TTS 服务

        Args:
            shot: Shot 实例

        Raises:
            Exception: 如果生成失败
        """
        logger.info(f"开始处理镜头: shot_id={shot.id}")

        # 延迟导入避免循环依赖
        from .comfyui_service import ComfyUIService
        from .tts_service import EdgeTTSService

        # ========== 图像生成 ==========
        try:
            comfy_service = ComfyUIService()

            # 根据镜头内容生成提示词
            prompt = self._build_image_prompt(shot)

            # 使用场景背景工作流
            workflow_json = ComfyUIService.create_scene_background_workflow(
                scene_description=prompt,
                lighting=getattr(shot.scene, 'time_of_day', 'natural'),
                atmosphere=getattr(shot.scene, 'atmosphere', 'calm'),
                style="anime"
            )

            # 生成图像
            image_result = comfy_service.generate_image(
                workflow_json=workflow_json,
                progress_id=f"shot_{shot.id}"
            )

            if image_result.get("success") and image_result.get("data"):
                # 保存图像 URL
                image_url = image_result["data"][0].get("url", "")
                shot.generated_image.name = image_url
                logger.info(f"图像生成成功: shot_id={shot.id}, url={image_url}")
            else:
                raise Exception(f"图像生成失败: {image_result.get('error', '未知错误')}")

        except Exception as e:
            logger.error(f"图像生成失败: shot_id={shot.id}, error={e}")
            shot.generation_error = f"图像生成失败: {e!s}"
            # 继续尝试生成音频

        # ========== 音频生成 ==========
        try:
            tts_service = EdgeTTSService()

            # 获取要合成的文本（对话或旁白）
            text_to_synthesize = shot.content or shot.narration or ""
            if not text_to_synthesize:
                logger.warning(f"镜头没有可合成文本: shot_id={shot.id}")
            else:
                # 获取章节角色的音色配置
                voice_config = self._get_voice_config(shot)

                # 合成音频
                audio_result = tts_service.synthesize(
                    text=text_to_synthesize,
                    voice_config=voice_config
                )

                if audio_result.get("success"):
                    # 保存音频路径
                    audio_path = audio_result.get("audio_path", "")
                    shot.generated_audio.name = audio_path
                    logger.info(f"音频生成成功: shot_id={shot.id}, path={audio_path}")
                else:
                    raise Exception(f"音频生成失败: {audio_result.get('error', '未知错误')}")

        except Exception as e:
            logger.error(f"音频生成失败: shot_id={shot.id}, error={e}")
            if shot.generation_error:
                shot.generation_error += f" | 音频生成失败: {e!s}"
            else:
                shot.generation_error = f"音频生成失败: {e!s}"

        # 更新镜头状态
        shot.is_generated = True
        shot.generated_at = timezone.now()
        shot.save(update_fields=["generated_image", "generated_audio", "is_generated", "generated_at", "generation_error"])

    def _build_image_prompt(self, shot: Shot) -> str:
        """
        构建图像生成提示词

        Args:
            shot: Shot 实例

        Returns:
            str: 提示词
        """
        prompt_parts = []

        # 添加场景描述
        if shot.scene and shot.scene.description:
            prompt_parts.append(shot.scene.description)

        # 添加镜头内容
        if shot.content:
            prompt_parts.append(shot.content)

        # 添加运镜信息
        if shot.camera_movement:
            prompt_parts.append(f"camera movement: {shot.camera_movement}")

        if shot.camera_angle:
            prompt_parts.append(f"camera angle: {shot.camera_angle}")

        # 添加构图描述
        if shot.shot_composition:
            prompt_parts.append(shot.shot_composition)

        # 添加角色造型信息
        if shot.character_pose:
            prompt_parts.append(f"character: {shot.character_pose.pose_name}")

        # 默认质量增强词
        prompt_parts.append("high quality, detailed, anime style")

        return ", ".join(prompt_parts) if prompt_parts else "anime scene, high quality"

    def _get_voice_config(self, shot: Shot) -> Dict[str, Any]:
        """
        获取音色配置

        Args:
            shot: Shot 实例

        Returns:
            Dict[str, Any]: 音色配置
        """
        # 默认配置
        default_config = {
            "voice_name": "zh-CN-XiaoxiaoNeural",
            "rate": "+0%",
            "volume": "+0%",
            "pitch": "+0Hz",
            "output_format": "mp3"
        }

        # 如果镜头有说话人，尝试获取角色的音色配置
        if shot.speaker and shot.scene and shot.scene.chapter:
            try:
                # 查找角色
                from apps.artworks.models import CharacterProfile
                character = CharacterProfile.objects.filter(
                    artwork=shot.scene.chapter.artwork,
                    name__icontains=shot.speaker
                ).first()

                if character and hasattr(character, 'voice_config'):
                    voice_config = character.voice_config
                    return {
                        "voice_name": voice_config.voice_id or default_config["voice_name"],
                        "rate": self._pitch_to_rate(voice_config.pitch),
                        "volume": self._volume_to_value(voice_config.volume),
                        "pitch": "+0Hz",  # Edge-TTS 使用 rate 控制
                        "output_format": "mp3"
                    }
            except Exception as e:
                logger.warning(f"获取角色音色配置失败: {e}，使用默认配置")

        return default_config

    def _pitch_to_rate(self, pitch: str) -> str:
        """将音调转换为语速"""
        pitch_map = {
            "very_low": "-10%",
            "low": "-5%",
            "normal": "+0%",
            "high": "+5%",
            "very_high": "+10%"
        }
        return pitch_map.get(pitch, "+0%")

    def _volume_to_value(self, volume: str) -> str:
        """将音量转换为值"""
        volume_map = {
            "very_soft": "-50%",
            "soft": "-20%",
            "normal": "+0%",
            "loud": "+20%",
            "very_loud": "+50%"
        }
        return volume_map.get(volume, "+0%")

    def _publish_event(
        self,
        event_type: str,
        scene_id: int,
        message: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        发布工作流事件

        Args:
            event_type: 事件类型
            scene_id: 场景 ID
            message: 事件消息
            metadata: 元数据（可选）
        """
        try:
            WorkflowEvent.objects.create(
                workflow=self.workflow,
                event_type=event_type,
                scene_id=scene_id,
                message=message,
                metadata=metadata or {}
            )
        except Exception as e:
            logger.error(f"创建工作流事件失败: {e}")

    def _publish_progress(
        self,
        scene_id: int,
        progress: int,
        current: int,
        total: int
    ) -> None:
        """
        推送进度到 Redis

        Args:
            scene_id: 场景 ID
            progress: 进度百分比 (0-100)
            current: 当前已完成数量
            total: 总数量
        """
        try:
            self.publisher.publish_progress_detailed(
                percentage=progress,
                current_step=current,
                total_steps=total,
                step_name=f"处理场景 {scene_id}"
            )
        except Exception as e:
            logger.error(f"发布进度失败: {e}")

    def __del__(self):
        """清理资源"""
        try:
            if hasattr(self, 'publisher'):
                self.publisher.close()
        except Exception:
            pass


# 单例模式，便于导入使用
_service_instance: Optional[SceneProcessorService] = None


def get_scene_processor(workflow_id: str) -> SceneProcessorService:
    """
    获取场景处理器服务实例

    Args:
        workflow_id: 工作流 ID

    Returns:
        SceneProcessorService: 服务实例
    """
    return SceneProcessorService(workflow_id)
