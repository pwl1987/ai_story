"""
Pipeline阶段适配器
将现有的Celery任务处理器适配到StageProcessor接口
遵循适配器模式(Adapter Pattern)
"""

import asyncio
import logging
import os
from typing import Dict, Any, List
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

# 检测是否在测试环境中
TEST_ENVIRONMENT = os.environ.get('PYTEST_CURRENT_TEST') is not None


def sync_to_async_wrapper(func, thread_sensitive=None):
    """
    包装sync_to_async,在测试环境中禁用thread_sensitive以避免SQLite锁问题
    """
    if thread_sensitive is None:
        thread_sensitive = not TEST_ENVIRONMENT  # 测试环境中使用False
    return sync_to_async(func, thread_sensitive=thread_sensitive)


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
            project = await sync_to_async_wrapper(Project.objects.get)(id=context.project_id)

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
        project = await sync_to_async_wrapper(Project.objects.get)(id=context.project_id)

        # 获取或创建阶段
        stage, created = await sync_to_async_wrapper(ProjectStage.objects.get_or_create)(
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
        await sync_to_async_wrapper(stage.save)()

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
            result = await sync_to_async_wrapper(run_sync_processor, thread_sensitive=True)()
            return result

        except Exception as e:
            stage.status = 'failed'
            stage.error_message = str(e)
            stage.retry_count += 1
            await sync_to_async_wrapper(stage.save)()
            return StageResult(success=False, error=str(e))

    async def on_failure(self, context: PipelineContext, error: Exception):
        """失败处理"""
        logger.error(f"文案改写失败: {str(error)}")
        try:
            stage = await sync_to_async_wrapper(ProjectStage.objects.get)(
                project_id=context.project_id,
                stage_type='rewrite'
            )
            stage.status = 'failed'
            stage.error_message = str(error)
            await sync_to_async_wrapper(stage.save)()
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
            project = await sync_to_async_wrapper(Project.objects.get)(id=context.project_id)

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
        project = await sync_to_async_wrapper(Project.objects.get)(id=context.project_id)
        rewrite_result = context.get_result('rewrite')

        # 获取或创建阶段
        stage, created = await sync_to_async_wrapper(ProjectStage.objects.get_or_create)(
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
        await sync_to_async_wrapper(stage.save)()

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
            result = await sync_to_async_wrapper(run_sync_processor, thread_sensitive=True)()
            return result

        except Exception as e:
            stage.status = 'failed'
            stage.error_message = str(e)
            stage.retry_count += 1
            await sync_to_async_wrapper(stage.save)()
            return StageResult(success=False, error=str(e))

    async def on_failure(self, context: PipelineContext, error: Exception):
        """失败处理"""
        logger.error(f"分镜生成失败: {str(error)}")
        try:
            stage = await sync_to_async_wrapper(ProjectStage.objects.get)(
                project_id=context.project_id,
                stage_type='storyboard'
            )
            stage.status = 'failed'
            stage.error_message = str(error)
            await sync_to_async_wrapper(stage.save)()
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
        """执行文生图（并行处理优化）"""
        project = await sync_to_async_wrapper(Project.objects.get)(id=context.project_id)

        # 获取或创建阶段
        stage, created = await sync_to_async_wrapper(ProjectStage.objects.get_or_create)(
            project=project,
            stage_type='image_generation',
            defaults={'status': 'pending'}
        )

        # 更新状态
        stage.status = 'processing'
        stage.started_at = timezone.now()
        await sync_to_async_wrapper(stage.save)()

        try:
            # 获取storyboard阶段的输出数据
            storyboard_result = context.get_result('storyboard')
            if not storyboard_result:
                raise Exception('缺少storyboard阶段结果')

            # 提取分镜数据（兼容多种数据结构）
            scenes = []

            # 尝试从不同路径提取分镜数据
            if 'human_text' in storyboard_result and 'scenes' in storyboard_result['human_text']:
                # 结构1: {'human_text': {'scenes': [...]}}
                scenes = storyboard_result['human_text']['scenes']
            elif 'storyboard' in storyboard_result:
                # 结构2: {'storyboard': [...]} 或 {'storyboard': '[...]'}
                storyboard_data = storyboard_result['storyboard']
                if isinstance(storyboard_data, str):
                    # JSON字符串，需要解析
                    import json
                    scenes = json.loads(storyboard_data)
                elif isinstance(storyboard_data, list):
                    # 已经是列表
                    scenes = storyboard_data
                else:
                    raise Exception(f'不支持的storyboard数据类型: {type(storyboard_data)}')
            elif isinstance(storyboard_result, list):
                # 结构3: 直接是列表
                scenes = storyboard_result
            else:
                raise Exception(f'无法识别的storyboard数据结构: {list(storyboard_result.keys())}')

            if not scenes:
                raise Exception('没有找到分镜数据')

            logger.info(f"项目 {project.id}: 开始并行生成 {len(scenes)} 张图片")

            # 并行处理每个场景的图片生成
            tasks = [
                self._generate_scene_image(scene['scene_number'], scene, project)
                for scene in scenes
            ]

            # 使用asyncio.gather并行执行，return_exceptions=True确保部分失败不影响其他任务
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # 处理结果
            images = []
            failed_count = 0

            for i, result in enumerate(results):
                scene_number = scenes[i]['scene_number']

                if isinstance(result, Exception):
                    logger.error(f"场景 {scene_number} 图片生成失败: {str(result)}")
                    failed_count += 1
                elif result and result.get('success'):
                    images.append(result.get('image_url'))
                    logger.info(f"场景 {scene_number} 图片生成成功: {result.get('image_url')}")
                else:
                    logger.error(f"场景 {scene_number} 图片生成失败: {result}")
                    failed_count += 1

            success_count = len(images)
            logger.info(f"项目 {project.id}: 图片生成完成，成功 {success_count}/{len(scenes)}，失败 {failed_count}")

            if success_count == 0:
                raise Exception('所有图片生成都失败了')

            # 保存结果
            stage.output_data = {'images': images, 'total': len(scenes), 'success_count': success_count}
            stage.status = 'completed'
            stage.completed_at = timezone.now()
            await sync_to_async_wrapper(stage.save)()

            return StageResult(
                success=True,
                data={'images': images, 'total': len(scenes), 'success_count': success_count}
            )

        except Exception as e:
            logger.error(f"文生图处理失败: {str(e)}", exc_info=True)
            stage.status = 'failed'
            stage.error_message = str(e)
            stage.retry_count += 1
            await sync_to_async_wrapper(stage.save)()
            return StageResult(success=False, error=str(e))

    async def _generate_scene_image(self, scene_number: int, scene: Dict[str, Any], project: Project) -> Dict[str, Any]:
        """
        为单个场景生成图片（异步版本）

        Args:
            scene_number: 场景编号
            scene: 场景数据（包含image_prompt等）
            project: 项目对象

        Returns:
            字典: {'success': True, 'image_url': 'http://...'} 或 {'success': False, 'error': '...'}
        """
        try:
            from core.ai_client.factory import create_ai_client
            from apps.models.models import ModelProvider

            # 获取文生图模型提供商
            def get_provider():
                # Project与ProjectModelConfig是OneToOne关系，related_name='model_config'
                config = getattr(project, 'model_config', None)
                if config and config.image_providers.exists():
                    return config.image_providers.first()
                return ModelProvider.objects.filter(provider_type='text2image', is_active=True).first()

            provider = await sync_to_async_wrapper(get_provider)()

            if not provider:
                return {'success': False, 'error': '未配置文生图模型'}

            # 构建提示词
            prompt = scene.get('image_prompt', scene.get('scene_description', ''))

            if not prompt:
                return {'success': False, 'error': '缺少提示词'}

            # 创建AI客户端并生成图片
            def create_client():
                return create_ai_client(provider)

            client = await sync_to_async_wrapper(create_client)()

            # 调用generate（同步方法，不需要await）
            # Text2ImageClient的generate是同步方法，返回AIResponse对象
            response = client.generate(
                prompt=prompt,
                width=1024,
                height=1024
            )

            if response.success:
                image_url = response.data.get('image_url')
                logger.info(f"场景 {scene_number} 图片生成成功: {image_url}")
                return {'success': True, 'image_url': image_url}
            else:
                error_msg = response.error or '未知错误'
                logger.error(f"场景 {scene_number} AI调用失败: {error_msg}")
                return {'success': False, 'error': error_msg}

        except Exception as e:
            logger.error(f"场景 {scene_number} 图片生成异常: {str(e)}", exc_info=True)
            return {'success': False, 'error': str(e)}

    async def on_failure(self, context: PipelineContext, error: Exception):
        """失败处理"""
        logger.error(f"文生图失败: {str(error)}")
        try:
            stage = await sync_to_async_wrapper(ProjectStage.objects.get)(
                project_id=context.project_id,
                stage_type='image_generation'
            )
            stage.status = 'failed'
            stage.error_message = str(error)
            await sync_to_async_wrapper(stage.save)()
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
        """执行运镜生成（并行处理优化）"""
        project = await sync_to_async_wrapper(Project.objects.get)(id=context.project_id)

        # 获取或创建阶段
        stage, created = await sync_to_async_wrapper(ProjectStage.objects.get_or_create)(
            project=project,
            stage_type='camera_movement',
            defaults={'status': 'pending'}
        )

        # 更新状态
        stage.status = 'processing'
        stage.started_at = timezone.now()
        await sync_to_async_wrapper(stage.save)()

        try:
            # 获取storyboard阶段的输出数据
            storyboard_result = context.get_result('storyboard')
            if not storyboard_result:
                raise Exception('缺少storyboard阶段结果')

            # 提取分镜数据（兼容多种数据结构）
            scenes = []

            # 尝试从不同路径提取分镜数据
            if 'human_text' in storyboard_result and 'scenes' in storyboard_result['human_text']:
                # 结构1: {'human_text': {'scenes': [...]}}
                scenes = storyboard_result['human_text']['scenes']
            elif 'storyboard' in storyboard_result:
                # 结构2: {'storyboard': [...]} 或 {'storyboard': '[...]'}
                storyboard_data = storyboard_result['storyboard']
                if isinstance(storyboard_data, str):
                    # JSON字符串，需要解析
                    import json
                    scenes = json.loads(storyboard_data)
                elif isinstance(storyboard_data, list):
                    # 已经是列表
                    scenes = storyboard_data
                else:
                    raise Exception(f'不支持的storyboard数据类型: {type(storyboard_data)}')
            elif 'storyboard_text' in storyboard_result:
                # 结构4: {'storyboard_text': [...]}  (测试中使用的结构)
                storyboard_text = storyboard_result['storyboard_text']
                if isinstance(storyboard_text, list):
                    scenes = storyboard_text
                else:
                    # 如果是文本，尝试解析为JSON
                    try:
                        import json
                        scenes = json.loads(storyboard_text)
                    except:
                        # 解析失败，创建单个场景
                        scenes = [{'scene_number': 1, 'scene_description': storyboard_text}]
            elif isinstance(storyboard_result, list):
                # 结构3: 直接是列表
                scenes = storyboard_result
            else:
                raise Exception(f'无法识别的storyboard数据结构: {list(storyboard_result.keys())}')

            if not scenes:
                raise Exception('没有找到分镜数据')

            logger.info(f"项目 {project.id}: 开始并行生成 {len(scenes)} 个场景的运镜参数")

            # 并行处理每个场景的运镜生成
            tasks = [
                self._generate_camera_movement(scene['scene_number'], scene, project)
                for scene in scenes
            ]

            # 使用asyncio.gather并行执行，return_exceptions=True确保部分失败不影响其他任务
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # 处理结果
            camera_movements = []
            failed_count = 0

            for i, result in enumerate(results):
                scene_number = scenes[i]['scene_number']

                if isinstance(result, Exception):
                    logger.error(f"场景 {scene_number} 运镜生成失败: {str(result)}")
                    failed_count += 1
                elif result and result.get('success'):
                    camera_movements.append(result)
                    logger.info(f"场景 {scene_number} 运镜生成成功")
                else:
                    logger.error(f"场景 {scene_number} 运镜生成失败: {result}")
                    failed_count += 1

            success_count = len(camera_movements)
            logger.info(f"项目 {project.id}: 运镜生成完成，成功 {success_count}/{len(scenes)}，失败 {failed_count}")

            if success_count == 0:
                raise Exception('所有运镜生成都失败了')

            # 为了向后兼容，也生成camera_movement_text（JSON字符串）
            import json
            camera_movement_text = json.dumps(camera_movements, ensure_ascii=False)

            # 保存结果
            stage.output_data = {
                'camera_movements': camera_movements,
                'camera_movement_text': camera_movement_text,  # 向后兼容
                'total': len(scenes),
                'success_count': success_count
            }
            stage.status = 'completed'
            stage.completed_at = timezone.now()
            await sync_to_async_wrapper(stage.save)()

            return StageResult(
                success=True,
                data={
                    'camera_movements': camera_movements,
                    'camera_movement_text': camera_movement_text,  # 向后兼容
                    'total': len(scenes),
                    'success_count': success_count
                }
            )

        except Exception as e:
            logger.error(f"运镜生成处理失败: {str(e)}", exc_info=True)
            stage.status = 'failed'
            stage.error_message = str(e)
            stage.retry_count += 1
            await sync_to_async_wrapper(stage.save)()
            return StageResult(success=False, error=str(e))

    async def _generate_camera_movement(self, scene_number: int, scene: Dict[str, Any], project: Project) -> Dict[str, Any]:
        """
        为单个场景生成运镜参数（异步版本）

        Args:
            scene_number: 场景编号
            scene: 场景数据（包含scene_description等）
            project: 项目对象

        Returns:
            字典: {'success': True, 'movement_type': '...', 'movement_params': {...}} 或 {'success': False, 'error': '...'}
        """
        try:
            from core.ai_client.factory import create_ai_client
            from apps.models.models import ModelProvider

            # 获取LLM模型提供商
            def get_provider():
                # Project与ProjectModelConfig是OneToOne关系，related_name='model_config'
                config = getattr(project, 'model_config', None)
                if config and config.camera_providers.exists():
                    return config.camera_providers.first()
                return ModelProvider.objects.filter(provider_type='llm', is_active=True).first()

            provider = await sync_to_async_wrapper(get_provider)()

            if not provider:
                return {'success': False, 'error': '未配置LLM模型'}

            # 构建场景描述
            scene_description = scene.get('scene_description', scene.get('description', ''))

            if not scene_description:
                return {'success': False, 'error': '缺少场景描述'}

            # 构建运镜生成提示词
            prompt = f"""
根据以下场景描述生成运镜参数:

场景描述: {scene_description}

请返回JSON格式的运镜参数，包含以下字段:
{{
  "movement_type": "slow_zoom_in",
  "movement_params": {{
    "start_scale": 1.0,
    "end_scale": 1.2,
    "duration": 3.0
  }}
}}

可选的运镜类型: slow_zoom_in, slow_zoom_out, pan_left, pan_right, tilt_up, tilt_down, static
"""

            # 创建AI客户端并生成运镜参数
            def create_client():
                return create_ai_client(provider)

            client = await sync_to_async_wrapper(create_client)()

            # 调用generate（LLMClient是异步方法，需要await）
            response = await client.generate(
                prompt=prompt,
                max_tokens=500,
                temperature=0.7
            )

            if response.success:
                import json
                try:
                    # 尝试解析JSON响应
                    movement_data = json.loads(response.text)

                    # 验证必要字段
                    if 'movement_type' not in movement_data:
                        # 如果解析失败或缺少字段，使用默认值
                        movement_data = {
                            'movement_type': 'static',
                            'movement_params': {
                                'start_scale': 1.0,
                                'end_scale': 1.0,
                                'duration': 3.0
                            }
                        }

                    return {
                        'success': True,
                        'scene_number': scene_number,
                        'movement_type': movement_data['movement_type'],
                        'movement_params': movement_data.get('movement_params', {})
                    }
                except (json.JSONDecodeError, KeyError):
                    # JSON解析失败，返回默认运镜
                    return {
                        'success': True,
                        'scene_number': scene_number,
                        'movement_type': 'static',
                        'movement_params': {
                            'start_scale': 1.0,
                            'end_scale': 1.0,
                            'duration': 3.0
                        }
                    }
            else:
                error_msg = response.error or '未知错误'
                logger.error(f"场景 {scene_number} AI调用失败: {error_msg}")
                return {'success': False, 'error': error_msg}

        except Exception as e:
            logger.error(f"场景 {scene_number} 运镜生成异常: {str(e)}", exc_info=True)
            return {'success': False, 'error': str(e)}

    async def on_failure(self, context: PipelineContext, error: Exception):
        """失败处理"""
        logger.error(f"运镜生成失败: {str(error)}")
        try:
            stage = await sync_to_async_wrapper(ProjectStage.objects.get)(
                project_id=context.project_id,
                stage_type='camera_movement'
            )
            stage.status = 'failed'
            stage.error_message = str(error)
            await sync_to_async_wrapper(stage.save)()
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
        project = await sync_to_async_wrapper(Project.objects.get)(id=context.project_id)

        # 获取或创建阶段
        stage, created = await sync_to_async_wrapper(ProjectStage.objects.get_or_create)(
            project=project,
            stage_type='video_generation',
            defaults={'status': 'pending'}
        )

        # 更新状态
        stage.status = 'processing'
        stage.started_at = timezone.now()
        await sync_to_async_wrapper(stage.save)()

        try:
            # 调用图生视频处理器（使用sync_to_async包装同步方法）
            result = await sync_to_async_wrapper(self.processor.process)(context)

            if result.success:
                stage.output_data = {'videos': result.data.get('videos', [])}
                stage.status = 'completed'
                stage.completed_at = timezone.now()
                await sync_to_async_wrapper(stage.save)()

                return StageResult(
                    success=True,
                    data={'videos': result.data.get('videos', [])}
                )
            else:
                raise Exception(result.error or '图生视频失败')

        except Exception as e:
            stage.status = 'failed'
            stage.error_message = str(e)
            stage.retry_count += 1
            await sync_to_async_wrapper(stage.save)()
            return StageResult(success=False, error=str(e))

    async def on_failure(self, context: PipelineContext, error: Exception):
        """失败处理"""
        logger.error(f"图生视频失败: {str(error)}")
        try:
            stage = await sync_to_async_wrapper(ProjectStage.objects.get)(
                project_id=context.project_id,
                stage_type='video_generation'
            )
            stage.status = 'failed'
            stage.error_message = str(error)
            await sync_to_async_wrapper(stage.save)()
        except Exception:
            pass
