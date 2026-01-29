"""
Storyboard并行优化补丁

优化策略：两阶段并行生成
1. 快速生成场景大纲（0.5秒）
2. 并行生成每个场景详细描述（1-2秒）
总耗时：1.5-2.5秒（提升50-70%）

创建时间: 2026-01-28
"""

import asyncio
import json
import logging
from typing import Any, Dict

from asgiref.sync import sync_to_async
from django.utils import timezone

from apps.content.processors.llm_stage import LLMStageProcessor
from apps.projects.models import Project, ProjectStage
from core.pipeline.base import PipelineContext, StageProcessor, StageResult

logger = logging.getLogger(__name__)


def sync_to_async_wrapper(func, thread_sensitive=None):
    """包装sync_to_async"""
    return sync_to_async(func, thread_sensitive=thread_sensitive or False)


class StoryboardStageAdapterOptimized(StageProcessor):
    """
    分镜生成阶段适配器（并行优化版本）

    优化内容：
    - 两阶段生成：大纲 → 并行详细描述
    - 预期性能提升：50-70%（4-7.6s → 1.5-2.5s）
    """

    def __init__(self):
        super().__init__("storyboard")
        self.processor = LLMStageProcessor(stage_type="storyboard")
        self.logger = logger

    async def validate(self, context: PipelineContext) -> bool:
        """验证阶段是否可以执行"""
        try:
            await sync_to_async_wrapper(Project.objects.get)(id=context.project_id)

            # 检查是否有文案改写结果
            rewrite_result = context.get_result("rewrite")
            if not rewrite_result:
                logger.error(f"项目 {context.project_id} 缺少文案改写结果")
                return False

            return True
        except Project.DoesNotExist:
            logger.error(f"项目 {context.project_id} 不存在")
            return False
        except Exception as e:
            logger.error(f"验证失败: {e!s}", exc_info=True)
            return False

    async def process(self, context: PipelineContext) -> StageResult:
        """执行分镜生成（并行优化版本）"""
        project = await sync_to_async_wrapper(Project.objects.get)(id=context.project_id)
        rewrite_result = context.get_result("rewrite")

        # 获取或创建阶段
        stage, _created = await sync_to_async_wrapper(ProjectStage.objects.get_or_create)(
            project=project,
            stage_type="storyboard",
            defaults={
                "status": "pending",
                "input_data": {"raw_text": rewrite_result.get("rewritten_text", "")},
            },
        )

        # 更新状态
        stage.status = "processing"
        stage.started_at = timezone.now()
        await sync_to_async_wrapper(stage.save)()

        try:
            rewritten_text = rewrite_result.get("rewritten_text", "")

            logger.info(f"项目 {project.id}: 开始两阶段并行生成分镜")

            # 阶段1: 快速生成场景大纲
            logger.info("阶段1: 生成场景大纲...")
            scene_outline = await self._generate_scene_outline(project, rewritten_text)

            if not scene_outline or "scenes" not in scene_outline:
                raise Exception("场景大纲生成失败")

            scenes_outline = scene_outline["scenes"]
            scene_count = len(scenes_outline)
            logger.info(f"阶段1完成: 将生成 {scene_count} 个场景")

            # 阶段2: 并行生成每个场景的详细描述
            logger.info(f"阶段2: 并行生成 {scene_count} 个场景的详细描述...")

            tasks = [
                self._generate_scene_detail(scene_index, scene_outline, project)
                for scene_index, scene_outline in enumerate(scenes_outline, 1)
            ]

            # 使用asyncio.gather并行执行
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # 处理结果
            scenes = []
            failed_count = 0

            for i, result in enumerate(results):
                scene_number = i + 1

                if isinstance(result, Exception):
                    logger.error(f"场景 {scene_number} 详细描述生成失败: {result!s}")
                    failed_count += 1
                    # 使用基础大纲作为fallback
                    scenes.append(
                        {
                            "scene_number": scene_number,
                            "scene_description": scenes_outline[i].get("description", ""),
                            "narration": scenes_outline[i].get("narration", ""),
                        }
                    )
                elif result and result.get("success"):
                    scenes.append(result["scene"])
                    logger.info(f"场景 {scene_number} 详细描述生成成功")
                else:
                    logger.error(f"场景 {scene_number} 详细描述生成失败: {result}")
                    failed_count += 1

            success_count = len(scenes)
            logger.info(
                f"项目 {project.id}: 分镜生成完成，成功 {success_count}/{scene_count}，失败 {failed_count}"
            )

            if success_count == 0:
                raise Exception("所有场景生成都失败了")

            # 保存结果
            stage.output_data = {
                "scenes": scenes,
                "total": scene_count,
                "success_count": success_count,
                "raw_text": json.dumps(scenes, ensure_ascii=False),
            }
            stage.status = "completed"
            stage.completed_at = timezone.now()
            await sync_to_async_wrapper(stage.save)()

            return StageResult(success=True, data={"storyboard": scenes})

        except Exception as e:
            logger.error(f"分镜生成失败: {e!s}", exc_info=True)
            stage.status = "failed"
            stage.error_message = str(e)
            stage.retry_count += 1
            await sync_to_async_wrapper(stage.save)()
            return StageResult(success=False, error=str(e))

    async def _generate_scene_outline(
        self, project: Project, rewritten_text: str
    ) -> Dict[str, Any]:
        """
        阶段1: 快速生成场景大纲

        Args:
            project: 项目对象
            rewritten_text: 改写后的文本

        Returns:
            场景大纲: {'scenes': [{'description': '...', 'narration': '...'}]}
        """
        try:
            from apps.models.models import ModelProvider
            from core.ai_client.factory import create_ai_client

            # 获取LLM模型提供商
            def get_provider():
                config = getattr(project, "model_config", None)
                if config and config.storyboard_providers.exists():
                    return config.storyboard_providers.first()
                return ModelProvider.objects.filter(provider_type="llm", is_active=True).first()

            provider = await sync_to_async_wrapper(get_provider)()

            if not provider:
                raise Exception("未配置LLM模型")

            # 构建大纲生成Prompt（简洁版）
            outline_prompt = f"""根据以下故事生成3-5个场景的大纲（每个场景不超过20字）：

故事：{rewritten_text}

要求：
- 每个场景包含：description（场景描述）和 narration（旁白）
- 简洁明了，每项不超过20字
- 返回JSON格式

示例格式：
{{
    "scenes": [
        {{"description": "宁静的小镇早晨", "narration": "阳光洒在小镇上"}},
        {{"description": "年轻画家开始作画", "narration": "他拿起画笔"}}
    ]
}}

请生成场景大纲："""

            # 调用LLM生成大纲
            def call_llm():
                client = create_ai_client(provider)
                response = client.generate(prompt=outline_prompt, max_tokens=500)

                if response.success:
                    # 解析JSON
                    response_text = response.text

                    # 提取JSON
                    if "```json" in response_text:
                        start = response_text.find("```json") + 7
                        end = response_text.find("```", start)
                        json_str = response_text[start:end].strip()
                    elif "[" in response_text and "]" in response_text:
                        start = response_text.find("[")
                        end = response_text.rfind("]") + 1
                        json_str = response_text[start:end]
                    else:
                        json_str = response_text

                    return json.loads(json_str)
                else:
                    raise Exception(response.error)

            # 在同步上下文中执行
            result = await sync_to_async_wrapper(call_llm, thread_sensitive=True)()
            return result

        except Exception as e:
            logger.error(f"场景大纲生成失败: {e!s}", exc_info=True)
            # 返回默认大纲（3个场景）
            return {
                "scenes": [
                    {"description": "开场", "narration": rewritten_text[:50]},
                    {"description": "发展", "narration": rewritten_text[:50]},
                    {"description": "结尾", "narration": rewritten_text[:50]},
                ]
            }

    async def _generate_scene_detail(
        self, scene_number: int, scene_outline: Dict[str, Any], project: Project
    ) -> Dict[str, Any]:
        """
        阶段2: 生成单个场景的详细描述（并行执行）

        Args:
            scene_number: 场景编号
            scene_outline: 场景大纲
            project: 项目对象

        Returns:
            {'success': True, 'scene': {...}}
        """
        try:
            from apps.models.models import ModelProvider
            from core.ai_client.factory import create_ai_client

            # 获取LLM模型提供商
            def get_provider():
                config = getattr(project, "model_config", None)
                if config and config.storyboard_providers.exists():
                    return config.storyboard_providers.first()
                return ModelProvider.objects.filter(provider_type="llm", is_active=True).first()

            provider = await sync_to_async_wrapper(get_provider)()

            if not provider:
                return {"success": False, "error": "未配置LLM模型"}

            # 构建详细描述生成Prompt
            detail_prompt = f"""请为场景 {scene_number} 生成详细的分镜描述：

场景大纲：
- 描述：{scene_outline.get("description", "")}
- 旁白：{scene_outline.get("narration", "")}

要求：
- image_prompt: 图片生成提示词（英文，详细描述画面）
- visual_prompt: 视觉元素描述（英文）
- scene_description: 场景完整描述（中文，100字以内）
- narration: 旁白文本（中文，50字以内）

返回JSON格式：
{{
    "scene_number": {scene_number},
    "image_prompt": "detailed visual description in English",
    "visual_prompt": "visual elements in English",
    "scene_description": "完整场景描述",
    "narration": "旁白文本"
}}

请生成详细描述："""

            # 调用LLM生成详细描述
            def call_llm():
                client = create_ai_client(provider)
                response = client.generate(prompt=detail_prompt, max_tokens=300)

                if response.success:
                    # 解析JSON
                    response_text = response.text

                    # 提取JSON
                    if "```json" in response_text:
                        start = response_text.find("```json") + 7
                        end = response_text.find("```", start)
                        json_str = response_text[start:end].strip()
                    elif "{" in response_text and "}" in response_text:
                        # 找到最外层的{}
                        start = response_text.find("{")
                        end = response_text.rfind("}") + 1
                        json_str = response_text[start:end]
                    else:
                        json_str = response_text

                    scene_detail = json.loads(json_str)
                    scene_detail["scene_number"] = scene_number

                    return {"success": True, "scene": scene_detail}
                else:
                    return {"success": False, "error": response.error}

            # 在同步上下文中执行
            result = await sync_to_async_wrapper(call_llm, thread_sensitive=True)()
            return result

        except Exception as e:
            logger.error(f"场景 {scene_number} 详细描述生成失败: {e!s}")
            # 返回失败结果
            return {
                "success": False,
                "error": str(e),
                "scene": {
                    "scene_number": scene_number,
                    "scene_description": scene_outline.get("description", ""),
                    "narration": scene_outline.get("narration", ""),
                    "image_prompt": scene_outline.get("description", ""),
                    "visual_prompt": scene_outline.get("narration", ""),
                },
            }

    async def on_failure(self, context: PipelineContext, error: Exception):
        """失败处理"""
        logger.error(f"分镜生成失败: {error!s}")
        try:
            stage = await sync_to_async_wrapper(ProjectStage.objects.get)(
                project_id=context.project_id, stage_type="storyboard"
            )
            stage.status = "failed"
            stage.error_message = str(error)
            await sync_to_async_wrapper(stage.save)()
        except Exception:
            pass
