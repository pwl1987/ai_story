"""
Pipeline阶段适配器
将现有的Celery任务处理器适配到StageProcessor接口
遵循适配器模式(Adapter Pattern)
"""

import logging
from typing import Dict, Any
from django.utils import timezone
from asgiref.sync import async_to_sync, sync_to_async

from core.pipeline.base import (
    StageProcessor,
    PipelineContext,
    StageResult
)
from apps.projects.models import Project, ProjectStage
from apps.content.processors.llm_stage import LLMStageProcessor
from apps.content.processors.text2image_stage import Text2ImageStageProcessor
from apps.content.processors.image2video_stage import Image2VideoStageProcessor

logger = logging.getLogger(__name__)


class RewriteStageAdapter(StageProcessor):
    """
    文案改写阶段适配器
    适配LLMStageProcessor用于Pipeline工作流
    """

    def __init__(self):
        super().__init__('rewrite')
        self.processor = LLMStageProcessor(stage_type='rewrite')
        self.logger = logger

    async def validate(self, context: PipelineContext) -> bool:
        """验证阶段是否可以执行"""
        try:
            project = await sync_to_async(Project.objects.get)(id=context.project_id)

            # 检查是否有原始主题
            if not project.original_topic:
                logger.error(f"项目 {context.project_id} 缺少原始主题")
                return False

            return True
        except Project.DoesNotExist:
            logger.error(f"项目 {context.project_id} 不存在")
            return False
        except Exception as e:
            logger.error(f"验证失败: {str(e)}", exc_info=True)
            return False

    async def process(self, context: PipelineContext) -> StageResult:
        """执行文案改写"""
        project = await sync_to_async(Project.objects.get)(id=context.project_id)

        # 获取或创建阶段
        stage, created = await sync_to_async(ProjectStage.objects.get_or_create)(
            project=project,
            stage_type='rewrite',
            defaults={
                'status': 'pending',
                'input_data': {'raw_text': project.original_topic}
            }
        )

        # 更新状态
        stage.status = 'processing'
        stage.started_at = timezone.now()
        await sync_to_async(stage.save)()

        try:
            # 使用sync_to_async包装同步处理器的调用
            def run_sync_processor():
                """在同步上下文中运行LLM处理器"""
                full_text = ""
                for chunk in self.processor.process_stream(
                    project_id=project.id,
                    input_data={'raw_text': project.original_topic}
                ):
                    chunk_type = chunk.get('type')

                    if chunk_type == 'token':
                        full_text = chunk.get('full_text', full_text)

                    elif chunk_type == 'done':
                        # 保存结果
                        stage.output_data = {'raw_text': full_text}
                        stage.status = 'completed'
                        stage.completed_at = timezone.now()
                        stage.save()

                        return StageResult(
                            success=True,
                            data={'rewritten_text': full_text}
                        )

                    elif chunk_type == 'error':
                        raise Exception(chunk.get('error', '未知错误'))

                return StageResult(success=False, error='处理未完成')

            # 在同步上下文中执行处理器
            result = await sync_to_async(run_sync_processor, thread_sensitive=True)()
            return result

        except Exception as e:
            stage.status = 'failed'
            stage.error_message = str(e)
            stage.retry_count += 1
            await sync_to_async(stage.save)()
            return StageResult(success=False, error=str(e))

    async def on_failure(self, context: PipelineContext, error: Exception):
        """失败处理"""
        logger.error(f"文案改写失败: {str(error)}")
        try:
            stage = await sync_to_async(ProjectStage.objects.get)(
                project_id=context.project_id,
                stage_type='rewrite'
            )
            stage.status = 'failed'
            stage.error_message = str(error)
            await sync_to_async(stage.save)()
        except Exception:
            pass


class StoryboardStageAdapter(StageProcessor):
    """
    分镜生成阶段适配器
    适配LLMStageProcessor用于Pipeline工作流
    """

    def __init__(self):
        super().__init__('storyboard')
        self.processor = LLMStageProcessor(stage_type='storyboard')
        self.logger = logger

    async def validate(self, context: PipelineContext) -> bool:
        """验证阶段是否可以执行"""
        try:
            project = await sync_to_async(Project.objects.get)(id=context.project_id)

            # 检查是否有文案改写结果
            rewrite_result = context.get_result('rewrite')
            if not rewrite_result:
                logger.error(f"项目 {context.project_id} 缺少文案改写结果")
                return False

            return True
        except Project.DoesNotExist:
            logger.error(f"项目 {context.project_id} 不存在")
            return False

    async def process(self, context: PipelineContext) -> StageResult:
        """执行分镜生成"""
        project = await sync_to_async(Project.objects.get)(id=context.project_id)
        rewrite_result = context.get_result('rewrite')

        # 获取或创建阶段
        stage, created = await sync_to_async(ProjectStage.objects.get_or_create)(
            project=project,
            stage_type='storyboard',
            defaults={
                'status': 'pending',
                'input_data': {'raw_text': rewrite_result.get('rewritten_text', '')}
            }
        )

        # 更新状态
        stage.status = 'processing'
        stage.started_at = timezone.now()
        await sync_to_async(stage.save)()

        try:
            # 使用sync_to_async包装同步处理器的调用
            def run_sync_processor():
                """在同步上下文中运行LLM处理器"""
                full_text = ""
                for chunk in self.processor.process_stream(
                    project_id=project.id,
                    input_data={'raw_text': rewrite_result.get('rewritten_text', '')}
                ):
                    chunk_type = chunk.get('type')

                    if chunk_type == 'token':
                        full_text = chunk.get('full_text', full_text)

                    elif chunk_type == 'done':
                        # 保存结果
                        stage.output_data = {'raw_text': full_text}
                        stage.status = 'completed'
                        stage.completed_at = timezone.now()
                        stage.save()

                        return StageResult(
                            success=True,
                            data={'storyboard_text': full_text}
                        )

                    elif chunk_type == 'error':
                        raise Exception(chunk.get('error', '未知错误'))

                return StageResult(success=False, error='处理未完成')

            # 在同步上下文中执行处理器
            result = await sync_to_async(run_sync_processor, thread_sensitive=True)()
            return result

        except Exception as e:
            stage.status = 'failed'
            stage.error_message = str(e)
            stage.retry_count += 1
            await sync_to_async(stage.save)()
            return StageResult(success=False, error=str(e))

    async def on_failure(self, context: PipelineContext, error: Exception):
        """失败处理"""
        logger.error(f"分镜生成失败: {str(error)}")
        try:
            stage = await sync_to_async(ProjectStage.objects.get)(
                project_id=context.project_id,
                stage_type='storyboard'
            )
            stage.status = 'failed'
            stage.error_message = str(error)
            await sync_to_async(stage.save)()
        except Exception:
            pass


class ImageGenerationStageAdapter(StageProcessor):
    """
    文生图阶段适配器
    适配Text2ImageStageProcessor用于Pipeline工作流
    """

    def __init__(self):
        super().__init__('image_generation')
        self.processor = Text2ImageStageProcessor()
        self.logger = logger

    async def validate(self, context: PipelineContext) -> bool:
        """验证阶段是否可以执行"""
        try:
            # 检查是否有分镜结果
            storyboard_result = context.get_result('storyboard')
            if not storyboard_result:
                logger.error(f"项目 {context.project_id} 缺少分镜结果")
                return False

            return True
        except Exception as e:
            logger.error(f"验证失败: {str(e)}", exc_info=True)
            return False

    async def process(self, context: PipelineContext) -> StageResult:
        """执行文生图"""
        project = await sync_to_async(Project.objects.get)(id=context.project_id)

        # 获取或创建阶段
        stage, created = await sync_to_async(ProjectStage.objects.get_or_create)(
            project=project,
            stage_type='image_generation',
            defaults={'status': 'pending'}
        )

        # 更新状态
        stage.status = 'processing'
        stage.started_at = timezone.now()
        await sync_to_async(stage.save)()

        try:
            # 调用文生图处理器（使用sync_to_async包装同步方法）
            result = await sync_to_async(self.processor.process)(project_id=project.id)

            if result.get('success'):
                stage.output_data = {'images': result.get('images', [])}
                stage.status = 'completed'
                stage.completed_at = timezone.now()
                await sync_to_async(stage.save)()

                return StageResult(
                    success=True,
                    data={'images': result.get('images', [])}
                )
            else:
                raise Exception(result.get('error', '文生图失败'))

        except Exception as e:
            stage.status = 'failed'
            stage.error_message = str(e)
            stage.retry_count += 1
            await sync_to_async(stage.save)()
            return StageResult(success=False, error=str(e))

    async def on_failure(self, context: PipelineContext, error: Exception):
        """失败处理"""
        logger.error(f"文生图失败: {str(error)}")
        try:
            stage = await sync_to_async(ProjectStage.objects.get)(
                project_id=context.project_id,
                stage_type='image_generation'
            )
            stage.status = 'failed'
            stage.error_message = str(error)
            await sync_to_async(stage.save)()
        except Exception:
            pass


class CameraMovementStageAdapter(StageProcessor):
    """
    运镜生成阶段适配器
    适配LLMStageProcessor用于Pipeline工作流
    """

    def __init__(self):
        super().__init__('camera_movement')
        self.processor = LLMStageProcessor(stage_type='camera_movement')
        self.logger = logger

    async def validate(self, context: PipelineContext) -> bool:
        """验证阶段是否可以执行"""
        try:
            # 检查是否有分镜结果
            storyboard_result = context.get_result('storyboard')
            if not storyboard_result:
                logger.error(f"项目 {context.project_id} 缺少分镜结果")
                return False

            return True
        except Exception as e:
            logger.error(f"验证失败: {str(e)}", exc_info=True)
            return False

    async def process(self, context: PipelineContext) -> StageResult:
        """执行运镜生成"""
        project = await sync_to_async(Project.objects.get)(id=context.project_id)

        # 获取或创建阶段
        stage, created = await sync_to_async(ProjectStage.objects.get_or_create)(
            project=project,
            stage_type='camera_movement',
            defaults={'status': 'pending'}
        )

        # 更新状态
        stage.status = 'processing'
        stage.started_at = timezone.now()
        await sync_to_async(stage.save)()

        try:
            # 使用sync_to_async包装同步处理器的调用
            def run_sync_processor():
                """在同步上下文中运行LLM处理器"""
                full_text = ""
                storyboard_result = context.get_result('storyboard')

                for chunk in self.processor.process_stream(
                    project_id=project.id,
                    input_data={'raw_text': storyboard_result.get('storyboard_text', '')}
                ):
                    chunk_type = chunk.get('type')

                    if chunk_type == 'token':
                        full_text = chunk.get('full_text', full_text)

                    elif chunk_type == 'done':
                        # 保存结果
                        stage.output_data = {'raw_text': full_text}
                        stage.status = 'completed'
                        stage.completed_at = timezone.now()
                        stage.save()

                        return StageResult(
                            success=True,
                            data={'camera_movement_text': full_text}
                        )

                    elif chunk_type == 'error':
                        raise Exception(chunk.get('error', '未知错误'))

                return StageResult(success=False, error='处理未完成')

            # 在同步上下文中执行处理器
            result = await sync_to_async(run_sync_processor, thread_sensitive=True)()
            return result

        except Exception as e:
            stage.status = 'failed'
            stage.error_message = str(e)
            stage.retry_count += 1
            await sync_to_async(stage.save)()
            return StageResult(success=False, error=str(e))

    async def on_failure(self, context: PipelineContext, error: Exception):
        """失败处理"""
        logger.error(f"运镜生成失败: {str(error)}")
        try:
            stage = await sync_to_async(ProjectStage.objects.get)(
                project_id=context.project_id,
                stage_type='camera_movement'
            )
            stage.status = 'failed'
            stage.error_message = str(error)
            await sync_to_async(stage.save)()
        except Exception:
            pass


class VideoGenerationStageAdapter(StageProcessor):
    """
    图生视频阶段适配器
    适配Image2VideoStageProcessor用于Pipeline工作流
    """

    def __init__(self):
        super().__init__('video_generation')
        self.processor = Image2VideoStageProcessor()
        self.logger = logger

    async def validate(self, context: PipelineContext) -> bool:
        """验证阶段是否可以执行"""
        try:
            # 检查是否有图片生成结果
            image_result = context.get_result('image_generation')
            if not image_result:
                logger.error(f"项目 {context.project_id} 缺少图片生成结果")
                return False

            return True
        except Exception as e:
            logger.error(f"验证失败: {str(e)}", exc_info=True)
            return False

    async def process(self, context: PipelineContext) -> StageResult:
        """执行图生视频"""
        project = await sync_to_async(Project.objects.get)(id=context.project_id)

        # 获取或创建阶段
        stage, created = await sync_to_async(ProjectStage.objects.get_or_create)(
            project=project,
            stage_type='video_generation',
            defaults={'status': 'pending'}
        )

        # 更新状态
        stage.status = 'processing'
        stage.started_at = timezone.now()
        await sync_to_async(stage.save)()

        try:
            # 调用图生视频处理器（已经是StageProcessor，直接传递context）
            result = await self.processor.process(context)

            if result.get('success'):
                stage.output_data = {'videos': result.get('videos', [])}
                stage.status = 'completed'
                stage.completed_at = timezone.now()
                await sync_to_async(stage.save)()

                return StageResult(
                    success=True,
                    data={'videos': result.get('videos', [])}
                )
            else:
                raise Exception(result.get('error', '图生视频失败'))

        except Exception as e:
            stage.status = 'failed'
            stage.error_message = str(e)
            stage.retry_count += 1
            await sync_to_async(stage.save)()
            return StageResult(success=False, error=str(e))

    async def on_failure(self, context: PipelineContext, error: Exception):
        """失败处理"""
        logger.error(f"图生视频失败: {str(error)}")
        try:
            stage = await sync_to_async(ProjectStage.objects.get)(
                project_id=context.project_id,
                stage_type='video_generation'
            )
            stage.status = 'failed'
            stage.error_message = str(error)
            await sync_to_async(stage.save)()
        except Exception:
            pass
