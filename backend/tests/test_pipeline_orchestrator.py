"""
Pipeline编排器测试
测试ProjectPipeline的工作流编排逻辑
"""

import pytest

from core.pipeline.base import PipelineContext, StageProcessor, StageResult, ValidationError
from core.pipeline.orchestrator import ProjectPipeline


# Mock阶段处理器用于测试
class MockSuccessProcessor(StageProcessor):
    """Mock成功阶段处理器"""

    def __init__(self, stage_name: str):
        super().__init__(stage_name)
        self.validate_called = False
        self.process_called = False

    async def validate(self, context: PipelineContext) -> bool:
        """验证总是返回True"""
        self.validate_called = True
        return True

    async def process(self, context: PipelineContext) -> StageResult:
        """处理返回成功"""
        self.process_called = True
        return StageResult(
            success=True,
            data={'stage': self.stage_name, 'result': 'success'}
        )

    async def on_failure(self, context: PipelineContext, error: Exception):
        """失败处理"""
        pass

    async def on_success(self, context: PipelineContext, result: StageResult):
        """成功处理"""
        context.add_result(self.stage_name, result.data)


class MockFailureProcessor(StageProcessor):
    """Mock失败阶段处理器"""

    def __init__(self, stage_name: str):
        super().__init__(stage_name)

    async def validate(self, context: PipelineContext) -> bool:
        """验证总是返回True"""
        return True

    async def process(self, context: PipelineContext) -> StageResult:
        """处理返回失败"""
        return StageResult(
            success=False,
            error=f'{self.stage_name} failed'
        )

    async def on_failure(self, context: PipelineContext, error: Exception):
        """失败处理"""
        pass


class MockValidationProcessor(StageProcessor):
    """Mock验证失败阶段处理器"""

    def __init__(self, stage_name: str, should_validate: bool = True):
        super().__init__(stage_name)
        self.should_validate = should_validate

    async def validate(self, context: PipelineContext) -> bool:
        """验证返回指定值"""
        return self.should_validate

    async def process(self, context: PipelineContext) -> StageResult:
        """不应该被调用"""
        return StageResult(
            success=True,
            data={'test': 'data'}
        )

    async def on_failure(self, context: PipelineContext, error: Exception):
        """失败处理"""
        pass


@pytest.mark.unit
class TestProjectPipeline:
    """ProjectPipeline测试类"""

    def test_initialization_with_stages(self):
        """测试Pipeline初始化"""
        stages = [
            MockSuccessProcessor('stage1'),
            MockSuccessProcessor('stage2'),
        ]

        pipeline = ProjectPipeline(stages)

        assert pipeline.stages == stages
        assert len(pipeline.stages) == 2

    def test_initialization_with_empty_stages(self):
        """测试空阶段列表初始化"""
        pipeline = ProjectPipeline([])

        assert pipeline.stages == []
        assert len(pipeline.stages) == 0

    @pytest.mark.asyncio
    async def test_execute_success_workflow(self):
        """测试成功执行工作流"""
        stages = [
            MockSuccessProcessor('stage1'),
            MockSuccessProcessor('stage2'),
            MockSuccessProcessor('stage3'),
        ]

        pipeline = ProjectPipeline(stages)
        context = await pipeline.execute('test-project-1')

        # 验证上下文
        assert context.project_id == 'test-project-1'
        assert 'stage1' in context.results
        assert 'stage2' in context.results
        assert 'stage3' in context.results

        # 验证数据
        assert context.results['stage1']['stage'] == 'stage1'
        assert context.results['stage2']['stage'] == 'stage2'
        assert context.results['stage3']['stage'] == 'stage3'

    @pytest.mark.asyncio
    async def test_execute_with_validation_failure(self):
        """测试验证失败时停止工作流"""
        # 创建一个会记录on_failure调用的验证失败处理器
        class MockValidationFailureProcessor(StageProcessor):
            def __init__(self, stage_name: str, should_validate: bool = True):
                super().__init__(stage_name)
                self.should_validate = should_validate
                self.on_failure_called = False

            async def validate(self, context: PipelineContext) -> bool:
                """验证返回指定值"""
                return self.should_validate

            async def process(self, context: PipelineContext) -> StageResult:
                """不应该被调用"""
                return StageResult(
                    success=True,
                    data={'test': 'data'}
                )

            async def on_failure(self, context: PipelineContext, error: Exception):
                """记录on_failure被调用"""
                self.on_failure_called = True
                assert isinstance(error, ValidationError)

        stages = [
            MockSuccessProcessor('stage1'),
            MockValidationFailureProcessor('stage2', should_validate=False),
            MockSuccessProcessor('stage3'),
        ]

        pipeline = ProjectPipeline(stages)

        # 不会抛出异常，orchestrator会捕获并调用on_failure
        context = await pipeline.execute('test-project-1')

        # 验证stage1成功执行
        assert 'stage1' in context.results

        # 验证stage2和stage3未执行（workflow在stage2验证失败时停止）
        assert 'stage2' not in context.results
        assert 'stage3' not in context.results

        # 验证stage2的on_failure被调用
        assert stages[1].on_failure_called

    @pytest.mark.asyncio
    async def test_execute_with_processing_failure(self):
        """测试处理失败时停止工作流"""
        stages = [
            MockSuccessProcessor('stage1'),
            MockFailureProcessor('stage2'),
            MockSuccessProcessor('stage3'),
        ]

        pipeline = ProjectPipeline(stages)
        context = await pipeline.execute('test-project-1')

        # 验证stage1成功
        assert 'stage1' in context.results

        # 验证stage2和stage3未执行
        assert 'stage2' not in context.results
        assert 'stage3' not in context.results

    @pytest.mark.asyncio
    async def test_execute_preserves_context(self):
        """测试执行保留上下文数据"""
        stages = [MockSuccessProcessor('stage1')]

        pipeline = ProjectPipeline(stages)
        context = await pipeline.execute('test-project-1')

        # 验证上下文属性
        assert context.project_id == 'test-project-1'
        assert isinstance(context.results, dict)
        assert isinstance(context.metadata, dict)

    @pytest.mark.asyncio
    async def test_execute_empty_pipeline(self):
        """测试空Pipeline执行"""
        pipeline = ProjectPipeline([])
        context = await pipeline.execute('test-project-1')

        # 验证上下文创建
        assert context.project_id == 'test-project-1'
        assert len(context.results) == 0
