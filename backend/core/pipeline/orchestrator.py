"""
Pipeline编排器
负责协调各个阶段的执行
"""

import asyncio
import logging
from typing import List

from .base import PipelineContext, StageProcessor, StageResult, ValidationError

logger = logging.getLogger(__name__)


class ProjectPipeline:
    """
    项目工作流编排器
    遵循开闭原则: 可扩展阶段,无需修改核心逻辑
    """

    def __init__(self, stages: List[StageProcessor]):
        """
        初始化Pipeline

        Args:
            stages: 阶段处理器列表
        """
        self.stages = stages

    async def execute(self, project_id: str) -> PipelineContext:
        """
        执行完整的项目工作流

        Args:
            project_id: 项目ID

        Returns:
            PipelineContext: 包含所有结果的上下文
        """

        context = PipelineContext(project_id=project_id)

        logger.info(f"开始执行项目工作流: {project_id}")

        for stage in self.stages:
            logger.info(f"执行阶段: {stage.stage_name}")

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
                else:
                    # 4. 处理失败
                    if result.can_retry:
                        logger.warning(f"阶段 {stage.stage_name} 执行失败,尝试重试")
                        result = await self._retry_stage(stage, context)

                    if not result.success:
                        logger.error(f"阶段 {stage.stage_name} 执行失败: {result.error}")
                        break  # 停止工作流

            except Exception as e:
                logger.exception(f"阶段 {stage.stage_name} 发生异常")
                await stage.on_failure(context, e)
                break

        return context

    async def _retry_stage(
        self, stage: StageProcessor, context: PipelineContext, max_retries: int = 3
    ) -> StageResult:
        """
        重试阶段
        使用指数退避策略

        Args:
            stage: 阶段处理器
            context: 工作流上下文
            max_retries: 最大重试次数

        Returns:
            StageResult: 最终结果
        """

        for attempt in range(max_retries):
            # 指数退避: 1s, 2s, 4s
            await asyncio.sleep(2**attempt)

            logger.info(f"重试阶段 {stage.stage_name}, 第 {attempt + 1}/{max_retries} 次")

            result = await stage.process(context)

            if result.success:
                logger.info(f"阶段 {stage.stage_name} 重试成功")
                return result

        logger.error(f"阶段 {stage.stage_name} 重试失败,已达最大重试次数")
        return result

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
