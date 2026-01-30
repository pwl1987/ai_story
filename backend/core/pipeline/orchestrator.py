"""
Pipeline编排器
负责协调各个阶段的执行
"""

import asyncio
import logging
from typing import Awaitable, Callable, List, Optional

from .base import PipelineContext, StageProcessor, StageResult, ValidationError

logger = logging.getLogger(__name__)

# 进度回调类型定义
ProgressCallback = Callable[[str, float, str], Awaitable[None]]


class ProjectPipeline:
    """
    项目工作流编排器
    遵循开闭原则: 可扩展阶段,无需修改核心逻辑
    """

    def __init__(
        self, stages: List[StageProcessor], progress_callback: Optional[ProgressCallback] = None
    ):
        """
        初始化Pipeline

        Args:
            stages: 阶段处理器列表
            progress_callback: 进度回调函数 (可选)
                签名: async def callback(stage_name: str, progress: float, status: str)
        """
        self.stages = stages
        self.progress_callback = progress_callback

    async def execute(self, project_id: str) -> PipelineContext:
        """
        执行完整的项目工作流

        Args:
            project_id: 项目ID

        Returns:
            PipelineContext: 包含所有结果的上下文
        """

        context = PipelineContext(project_id=project_id)
        total_stages = len(self.stages)

        logger.info(f"开始执行项目工作流: {project_id}, 共{total_stages}个阶段")

        for index, stage in enumerate(self.stages):
            progress = index / total_stages
            logger.info(f"执行阶段: {stage.stage_name} ({index + 1}/{total_stages})")

            # 通知阶段开始
            await self._notify_progress(stage.stage_name, progress, "started")

            try:
                # 1. 验证阶段
                if not await stage.validate(context):
                    raise ValidationError(f"阶段 {stage.stage_name} 验证失败")

                # 2. 执行阶段
                result = await stage.process(context)

                # 3. 处理结果
                if result.success:
                    context.add_result(stage.stage_name, result.data)
                    await stage.on_success(context, result)
                    logger.info(f"阶段 {stage.stage_name} 执行成功")

                    # 通知阶段完成
                    progress = (index + 1) / total_stages
                    await self._notify_progress(stage.stage_name, progress, "completed")
                else:
                    # 4. 处理失败
                    if result.can_retry:
                        logger.warning(f"阶段 {stage.stage_name} 执行失败,尝试重试")
                        result = await self._retry_stage(stage, context, index)

                    if not result.success:
                        logger.error(f"阶段 {stage.stage_name} 执行失败: {result.error}")
                        await self._notify_progress(stage.stage_name, progress, "failed")
                        break  # 停止工作流

            except Exception as e:
                logger.exception(f"阶段 {stage.stage_name} 发生异常")
                await stage.on_failure(context, e)
                await self._notify_progress(stage.stage_name, progress, "failed")
                break

        return context

    async def _retry_stage(
        self,
        stage: StageProcessor,
        context: PipelineContext,
        stage_index: int,
        max_retries: int = 3,
    ) -> StageResult:
        """
        重试阶段
        使用指数退避策略

        Args:
            stage: 阶段处理器
            context: 工作流上下文
            stage_index: 阶段索引
            max_retries: 最大重试次数

        Returns:
            StageResult: 最终结果
        """

        for attempt in range(max_retries):
            # 指数退避: 1s, 2s, 4s
            await asyncio.sleep(2**attempt)

            logger.info(f"重试阶段 {stage.stage_name}, 第 {attempt + 1}/{max_retries} 次")

            # 通知重试进度
            progress = stage_index / len(self.stages)
            await self._notify_progress(
                stage.stage_name, progress, f"retrying_{attempt + 1}"
            )

            result = await stage.process(context)

            if result.success:
                logger.info(f"阶段 {stage.stage_name} 重试成功")
                return result

        logger.error(f"阶段 {stage.stage_name} 重试失败,已达最大重试次数")
        return result

    async def _notify_progress(self, stage_name: str, progress: float, status: str):
        """
        通知进度更新

        Args:
            stage_name: 阶段名称
            progress: 进度百分比 (0.0-1.0)
            status: 状态 ('started', 'completed', 'failed', 'retrying_N')
        """
        if self.progress_callback:
            try:
                await self.progress_callback(stage_name, progress, status)
            except Exception as e:
                logger.error(f"进度回调失败: {e}")

    async def execute_stage(self, project_id: str, stage_name: str) -> StageResult:
        """
        执行单个阶段

        Args:
            project_id: 项目ID
            stage_name: 阶段名称

        Returns:
            StageResult: 阶段结果
        """

        # 查找阶段
        stage = next((s for s in self.stages if s.stage_name == stage_name), None)

        if not stage:
            return StageResult(success=False, error=f"未找到阶段: {stage_name}", can_retry=False)

        context = PipelineContext(project_id=project_id)

        # 验证
        if not await stage.validate(context):
            return StageResult(success=False, error=f"阶段 {stage_name} 验证失败", can_retry=False)

        # 执行
        return await stage.process(context)
