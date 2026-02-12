"""
ComfyUI 图像生成服务

职责:
- 封装 ComfyUI 客户端调用
- 提供统一的服务接口
- 处理生成任务和进度追踪
- 支持 Redis 发布进度更新

Epic 10 Story 10.3: ComfyUI 本地图像生成引擎集成
"""

import json
import logging
import uuid
from typing import Any, Callable, Dict, List, Optional

from core.ai_client.comfyui_client import ComfyUIClient
from core.redis.publisher import RedisStreamPublisher

logger = logging.getLogger(__name__)


class ComfyUIService:
    """
    ComfyUI 图像生成服务

    职责:
    - 创建和管理 ComfyUI 客户端实例
    - 处理图像/视频生成请求
    - 通过 Redis 发布进度更新
    - 支持批量生成
    - 错误处理和重试逻辑

    配置:
    - base_url: ComfyUI 服务器地址 (默认: http://localhost:8188)
    - timeout: 超时时间 (默认: 300 秒)
    """

    def __init__(
        self,
        base_url: str = "http://localhost:8188",
        api_key: str = "",
        model_name: str = "sdxl_base",
        timeout: int = 300,
        **kwargs
    ):
        """
        初始化 ComfyUI 服务

        Args:
            base_url: ComfyUI 服务器地址
            api_key: API 密钥 (占位符，ComfyUI 不需要)
            model_name: 模型名称
            timeout: 超时时间
            **kwargs: 其他配置
        """
        self.client = ComfyUIClient(
            api_url=base_url,
            api_key=api_key,
            model_name=model_name,
            timeout=timeout,
            save_images=True,
            **kwargs
        )

    def _get_publisher(self, stream_key: str):
        """获取 Redis 发布器实例"""
        return RedisStreamPublisher(stream_key, "comfyui")

    def generate_image(
        self,
        workflow_json: str,
        progress_id: Optional[str] = None,
        progress_callback: Optional[Callable[[float], None]] = None
    ) -> Dict[str, Any]:
        """
        生成图像

        Args:
            workflow_json: ComfyUI 工作流 JSON 字符串
            progress_id: 进度追踪 ID (用于 Redis 发布)
            progress_callback: 进度回调函数

        Returns:
            Dict[str, Any]: 生成结果
                {
                    "success": bool,
                    "data": [{"url": str}],
                    "metadata": {...},
                    "error": str (如果失败)
                }
        """
        if not progress_id:
            progress_id = str(uuid.uuid4())

        publisher = self._get_publisher(progress_id)

        def wrapped_callback(progress: float):
            """包装的进度回调，同时支持 Redis 发布"""
            # 发布到 Redis
            publisher.publish_stage_update(
                status="processing",
                progress=int(progress),
                message=f"图像生成中... {progress:.1f}%"
            )
            # 调用用户回调
            if progress_callback:
                progress_callback(progress)

        try:
            result = self.client._generate_image(
                prompt=workflow_json,
                progress_callback=wrapped_callback
            )

            # 发布完成状态
            if result.get("success"):
                publisher.publish_done(
                    full_text="",
                    metadata=result.get("metadata", {})
                )
            else:
                publisher.publish_error(error=result.get("error", "未知错误"))

            return result

        except Exception as e:
            logger.error(f"ComfyUI 生成失败: {e}")
            publisher.publish_error(error=str(e))
            return {
                "success": False,
                "error": f"生成失败: {e!s}"
            }

    def generate_video(
        self,
        workflow_json: str,
        progress_id: Optional[str] = None,
        progress_callback: Optional[Callable[[float], None]] = None
    ) -> Dict[str, Any]:
        """
        生成视频

        Args:
            workflow_json: ComfyUI 工作流 JSON 字符串
            progress_id: 进度追踪 ID
            progress_callback: 进度回调函数

        Returns:
            Dict[str, Any]: 生成结果
        """
        if not progress_id:
            progress_id = str(uuid.uuid4())

        publisher = self._get_publisher(progress_id)

        def wrapped_callback(progress: float):
            """包装的进度回调"""
            publisher.publish_stage_update(
                status="processing",
                progress=int(progress),
                message=f"视频生成中... {progress:.1f}%"
            )
            if progress_callback:
                progress_callback(progress)

        try:
            result = self.client._generate_video(
                prompt=workflow_json,
                progress_callback=wrapped_callback
            )

            # 发布完成状态
            if result.get("success"):
                publisher.publish_done(
                    full_text="",
                    metadata=result.get("metadata", {})
                )
            else:
                publisher.publish_error(error=result.get("error", "未知错误"))

            return result

        except Exception as e:
            logger.error(f"ComfyUI 视频生成失败: {e}")
            publisher.publish_error(error=str(e))
            return {
                "success": False,
                "error": f"视频生成失败: {e!s}"
            }

    def batch_generate_images(
        self,
        workflows: List[str],
        progress_id: Optional[str] = None,
        progress_callback: Optional[Callable[[float], None]] = None
    ) -> List[Dict[str, Any]]:
        """
        批量生成图像

        Args:
            workflows: 工作流 JSON 字符串列表
            progress_id: 进度追踪 ID
            progress_callback: 进度回调函数

        Returns:
            List[Dict[str, Any]]: 生成结果列表
        """
        if not progress_id:
            progress_id = str(uuid.uuid4())

        total = len(workflows)
        results = []

        for i, workflow in enumerate(workflows):
            # 计算整体进度
            def combined_callback(progress: float, index=i):
                """合并回调"""
                # 当前任务进度占总进度的权重
                task_progress = (progress / total)
                base_progress = (index / total) * 100
                overall_progress = base_progress + task_progress

                publisher = self._get_publisher(progress_id)
                publisher.publish_progress_detailed(
                    percentage=min(100, overall_progress),
                    current_step=index + 1,
                    total_steps=total,
                    step_name=f"批量生成 {index+1}/{total}"
                )
                if progress_callback:
                    progress_callback(overall_progress)

            result = self.generate_image(
                workflow_json=workflow,
                progress_id=f"{progress_id}_{i}",
                progress_callback=combined_callback
            )
            results.append(result)

        # 发布批量完成
        success_count = sum(1 for r in results if r.get("success"))
        publisher = self._get_publisher(progress_id)
        publisher.publish_done(
            full_text=f"批量生成完成: {success_count}/{total}",
            metadata={
                "total": total,
                "success": success_count,
                "failed": total - success_count
            }
        )

        return results

    def health_check(self) -> Dict[str, Any]:
        """
        健康检查

        Returns:
            Dict[str, Any]: 健康状态
                {
                    "healthy": bool,
                    "latency_ms": int,
                    "error": str (如果失败)
                }
        """
        import time
        start_time = time.time()

        try:
            is_valid = self.client.validate_config()

            latency_ms = int((time.time() - start_time) * 1000)

            return {
                "healthy": is_valid,
                "latency_ms": latency_ms,
                "server_address": self.client.server_address,
                "model": self.client.checkpoint_name
            }

        except Exception as e:
            latency_ms = int((time.time() - start_time) * 1000)
            return {
                "healthy": False,
                "latency_ms": latency_ms,
                "error": str(e)
            }

    def get_available_models(self) -> List[str]:
        """
        获取可用模型列表

        Returns:
            List[str]: 模型名称列表
        """
        # TODO: 实现 ComfyUI 模型列表获取
        # 需要调用 ComfyUI API 获取已安装的检查点
        return [
            "sdxl_base",
            "sd1.5_base",
            "sdxl_turbo"
        ]

    @staticmethod
    def create_character_pose_workflow(
        character_description: str,
        pose_type: str = "full_body",
        style: str = "anime",
        background_color: str = "#FFFFFF"
    ) -> str:
        """
        创建角色造型生成工作流

        Args:
            character_description: 角色描述
            pose_type: 造型类型 (full_body/half_body/bust)
            style: 风格 (anime/realistic/illustration)
            background_color: 背景颜色

        Returns:
            str: 工作流 JSON 字符串
        """
        # TODO: 根据不同造型类型和风格生成工作流
        # 这是一个简化的示例工作流
        workflow = {
            "1": {
                "class_type": "KSampler",
                "inputs": {
                    "seed": 0,
                    "steps": 20,
                    "cfg": 7,
                    "sampler_name": "euler",
                    "scheduler": "normal",
                    "denoise": 1,
                    "model": ["4", 0],
                    "positive": ["6", 0],
                    "negative": ["7", 0],
                    "latent_image": ["5", 0]
                }
            },
            "3": {
                "class_type": "VAEDecode",
                "inputs": {
                    "samples": ["1", 0],
                    "vae": ["4", 2]
                }
            },
            "4": {
                "class_type": "CheckpointLoaderSimple",
                "inputs": {
                    "ckpt_name": "sdxl_base.safetensors"
                }
            },
            "5": {
                "class_type": "EmptyLatentImage",
                "inputs": {
                    "width": 1024,
                    "height": 1536,
                    "batch_size": 1
                }
            },
            "6": {
                "class_type": "CLIPTextEncode",
                "inputs": {
                    "text": f"{character_description}, {style} style, high quality, detailed",
                    "clip": ["4", 1]
                }
            },
            "7": {
                "class_type": "CLIPTextEncode",
                "inputs": {
                    "text": f"low quality, blurry, ugly, distorted, {background_color} background",
                    "clip": ["4", 1]
                }
            }
        }

        return json.dumps(workflow)

    @staticmethod
    def create_scene_background_workflow(
        scene_description: str,
        lighting: str = "natural",
        atmosphere: str = "calm",
        style: str = "anime"
    ) -> str:
        """
        创建场景背景生成工作流

        Args:
            scene_description: 场景描述
            lighting: 光照类型
            atmosphere: 氛围
            style: 风格

        Returns:
            str: 工作流 JSON 字符串
        """
        workflow = {
            "1": {
                "class_type": "KSampler",
                "inputs": {
                    "seed": 0,
                    "steps": 25,
                    "cfg": 7.5,
                    "sampler_name": "dpmpp_2m",
                    "scheduler": "karras",
                    "denoise": 1,
                    "model": ["4", 0],
                    "positive": ["6", 0],
                    "negative": ["7", 0],
                    "latent_image": ["5", 0]
                }
            },
            "3": {
                "class_type": "VAEDecode",
                "inputs": {
                    "samples": ["1", 0],
                    "vae": ["4", 2]
                }
            },
            "4": {
                "class_type": "CheckpointLoaderSimple",
                "inputs": {
                    "ckpt_name": "sdxl_base.safetensors"
                }
            },
            "5": {
                "class_type": "EmptyLatentImage",
                "inputs": {
                    "width": 1920,
                    "height": 1080,
                    "batch_size": 1
                }
            },
            "6": {
                "class_type": "CLIPTextEncode",
                "inputs": {
                    "text": f"{scene_description}, {lighting} lighting, {atmosphere} atmosphere, {style} style, masterpiece, best quality",
                    "clip": ["4", 1]
                }
            },
            "7": {
                "class_type": "CLIPTextEncode",
                "inputs": {
                    "text": "low quality, blurry, ugly, distorted, watermark, text",
                    "clip": ["4", 1]
                }
            }
        }

        return json.dumps(workflow)

    @staticmethod
    def create_manga_panel_workflow(
        panel_description: str,
        characters: List[str],
        speech_bubbles: bool = True,
        sfx: bool = True
    ) -> str:
        """
        创建漫画面板生成工作流

        Args:
            panel_description: 面板描述
            characters: 角色列表
            speech_bubbles: 是否包含对话气泡
            sfx: 是否包含音效文字

        Returns:
            str: 工作流 JSON 字符串
        """
        character_str = ", ".join(characters)
        extras = []
        if speech_bubbles:
            extras.append("speech bubbles")
        if sfx:
            extras.append("sound effects")
        extras_str = ", ".join(extras) if extras else ""

        workflow = {
            "1": {
                "class_type": "KSampler",
                "inputs": {
                    "seed": 0,
                    "steps": 30,
                    "cfg": 8,
                    "sampler_name": "dpmpp_sde",
                    "scheduler": "karras",
                    "denoise": 1,
                    "model": ["4", 0],
                    "positive": ["6", 0],
                    "negative": ["7", 0],
                    "latent_image": ["5", 0]
                }
            },
            "3": {
                "class_type": "VAEDecode",
                "inputs": {
                    "samples": ["1", 0],
                    "vae": ["4", 2]
                }
            },
            "4": {
                "class_type": "CheckpointLoaderSimple",
                "inputs": {
                    "ckpt_name": "sdxl_base.safetensors"
                }
            },
            "5": {
                "class_type": "EmptyLatentImage",
                "inputs": {
                    "width": 1024,
                    "height": 1024,
                    "batch_size": 1
                }
            },
            "6": {
                "class_type": "CLIPTextEncode",
                "inputs": {
                    "text": f"manga panel, {panel_description}, characters: {character_str}, {extras_str}, black and white manga style, high quality, detailed lineart",
                    "clip": ["4", 1]
                }
            },
            "7": {
                "class_type": "CLIPTextEncode",
                "inputs": {
                    "text": "color, photo, realistic, 3d render, blurry, low quality",
                    "clip": ["4", 1]
                }
            }
        }

        return json.dumps(workflow)


# 单例模式，便于导入使用
_service_instance: Optional[ComfyUIService] = None


def get_comfyui_service() -> ComfyUIService:
    """获取 ComfyUI 服务单例"""
    global _service_instance
    if _service_instance is None:
        _service_instance = ComfyUIService()
    return _service_instance
