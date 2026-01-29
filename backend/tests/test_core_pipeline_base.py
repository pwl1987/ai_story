"""
core.pipeline.base 单元测试

测试Pipeline工作流基础抽象：责任链模式和数据结构
"""

import pytest

from core.pipeline.base import (
    PipelineContext,
    ProcessingError,
    StageProcessor,
    StageResult,
    ValidationError,
)


@pytest.mark.unit
class TestPipelineContext:
    """测试PipelineContext上下文类"""

    def test_create_context_with_project_id(self):
        """测试创建包含project_id的上下文"""
        context = PipelineContext(project_id="test-project-123")

        assert context.project_id == "test-project-123"
        assert context.results == {}
        assert context.metadata == {}

    def test_create_context_with_initial_data(self):
        """测试创建包含初始数据的上下文"""
        context = PipelineContext(
            project_id="test-project-123",
            results={"stage1": {"data": "value1"}},
            metadata={"start_time": "2024-01-01"},
        )

        assert context.results["stage1"] == {"data": "value1"}
        assert context.metadata["start_time"] == "2024-01-01"

    def test_add_result(self):
        """测试添加阶段结果"""
        context = PipelineContext(project_id="test-project")

        context.add_result("rewrite", {"text": "Rewritten content"})

        assert context.results["rewrite"] == {"text": "Rewritten content"}

    def test_add_multiple_results(self):
        """测试添加多个阶段结果"""
        context = PipelineContext(project_id="test-project")

        context.add_result("stage1", {"data": "value1"})
        context.add_result("stage2", {"data": "value2"})
        context.add_result("stage3", {"data": "value3"})

        assert len(context.results) == 3
        assert context.results["stage1"] == {"data": "value1"}
        assert context.results["stage2"] == {"data": "value2"}
        assert context.results["stage3"] == {"data": "value3"}

    def test_get_result_existing(self):
        """测试获取存在的阶段结果"""
        context = PipelineContext(project_id="test-project")
        context.add_result("rewrite", {"text": "content"})

        result = context.get_result("rewrite")

        assert result == {"text": "content"}

    def test_get_result_non_existent(self):
        """测试获取不存在的阶段结果返回None"""
        context = PipelineContext(project_id="test-project")

        result = context.get_result("non_existent_stage")

        assert result is None

    def test_add_and_get_metadata(self):
        """测试添加和获取元数据"""
        context = PipelineContext(project_id="test-project")

        context.add_metadata("total_tokens", 1000)
        context.add_metadata("model", "gpt-4")

        assert context.get_metadata("total_tokens") == 1000
        assert context.get_metadata("model") == "gpt-4"

    def test_get_non_existent_metadata(self):
        """测试获取不存在的元数据返回None"""
        context = PipelineContext(project_id="test-project")

        result = context.get_metadata("non_existent_key")

        assert result is None


@pytest.mark.unit
class TestStageResult:
    """测试StageResult结果类"""

    def test_create_success_result(self):
        """测试创建成功结果"""
        result = StageResult(success=True, data={"output": "value"})

        assert result.success is True
        assert result.data == {"output": "value"}
        assert result.error is None
        assert result.can_retry is True

    def test_create_error_result(self):
        """测试创建错误结果"""
        result = StageResult(success=False, error="Processing failed", can_retry=True)

        assert result.success is False
        assert result.error == "Processing failed"
        assert result.can_retry is True
        assert result.data == {}

    def test_create_no_retry_result(self):
        """测试创建不可重试的结果"""
        result = StageResult(success=False, error="Critical error", can_retry=False)

        assert result.can_retry is False

    def test_create_result_with_all_fields(self):
        """测试创建包含所有字段的结果"""
        result = StageResult(success=True, data={"key": "value"}, error=None, can_retry=False)

        assert result.success is True
        assert result.data == {"key": "value"}
        assert result.can_retry is False


@pytest.mark.unit
class TestStageProcessor:
    """测试StageProcessor抽象基类"""

    @pytest.fixture
    def concrete_processor(self):
        """创建具体的处理器实现用于测试"""

        class ConcreteProcessor(StageProcessor):
            async def validate(self, context):
                # 简单验证：project_id不能为空
                return bool(context.project_id)

            async def on_failure(self, context, error):
                context.add_metadata("error", str(error))

            async def on_success(self, context, result):
                context.add_result(self.stage_name, result.data)

        return ConcreteProcessor("test_stage")

    def test_processor_initialization(self, concrete_processor):
        """测试处理器初始化"""
        assert concrete_processor.stage_name == "test_stage"

    @pytest.mark.asyncio
    async def test_validate_success(self, concrete_processor):
        """测试验证成功"""
        context = PipelineContext(project_id="valid-project")

        result = await concrete_processor.validate(context)

        assert result is True

    @pytest.mark.asyncio
    async def test_validate_failure(self, concrete_processor):
        """测试验证失败"""
        context = PipelineContext(project_id="")

        result = await concrete_processor.validate(context)

        assert result is False

    @pytest.mark.asyncio
    async def test_on_failure_callback(self, concrete_processor):
        """测试失败回调"""
        context = PipelineContext(project_id="test-project")
        error = Exception("Test error")

        await concrete_processor.on_failure(context, error)

        assert context.get_metadata("error") == "Test error"

    @pytest.mark.asyncio
    async def test_on_success_callback(self, concrete_processor):
        """测试成功回调"""
        context = PipelineContext(project_id="test-project")
        result = StageResult(success=True, data={"output": "value"})

        await concrete_processor.on_success(context, result)

        assert context.get_result("test_stage") == {"output": "value"}

    def test_abstract_class_cannot_be_instantiated(self):
        """测试抽象类不能直接实例化"""
        with pytest.raises(TypeError):
            StageProcessor("stage_name")


@pytest.mark.unit
class TestExceptions:
    """测试自定义异常类"""

    def test_validation_error(self):
        """测试ValidationError异常"""
        with pytest.raises(ValidationError) as exc_info:
            raise ValidationError("Validation failed")

        assert str(exc_info.value) == "Validation failed"
        assert isinstance(exc_info.value, Exception)

    def test_processing_error(self):
        """测试ProcessingError异常"""
        with pytest.raises(ProcessingError) as exc_info:
            raise ProcessingError("Processing failed")

        assert str(exc_info.value) == "Processing failed"
        assert isinstance(exc_info.value, Exception)

    def test_exception_inheritance(self):
        """测试异常继承关系"""
        # 验证自定义异常继承自Exception
        assert issubclass(ValidationError, Exception)
        assert issubclass(ProcessingError, Exception)


@pytest.mark.unit
class TestPipelineIntegration:
    """Pipeline集成测试"""

    @pytest.mark.asyncio
    async def test_full_pipeline_workflow(self):
        """测试完整的Pipeline工作流程"""

        # 创建模拟处理器
        class MockProcessor(StageProcessor):
            def __init__(self, stage_name, should_fail=False):
                super().__init__(stage_name)
                self.should_fail = should_fail

            async def validate(self, context):
                return True

            async def on_failure(self, context, error):
                context.add_metadata(f"{self.stage_name}_error", str(error))

            async def on_success(self, context, result):
                context.add_result(self.stage_name, result.data)

        # 创建上下文和处理器链
        context = PipelineContext(project_id="test-project")
        processors = [MockProcessor("stage1"), MockProcessor("stage2"), MockProcessor("stage3")]

        # 执行处理器链
        for processor in processors:
            if await processor.validate(context):
                result = StageResult(success=True, data={"stage": processor.stage_name})
                await processor.on_success(context, result)

        # 验证所有阶段都执行成功
        assert context.get_result("stage1")["stage"] == "stage1"
        assert context.get_result("stage2")["stage"] == "stage2"
        assert context.get_result("stage3")["stage"] == "stage3"

    @pytest.mark.asyncio
    async def test_pipeline_with_failure(self):
        """测试Pipeline失败处理"""

        class FailingProcessor(StageProcessor):
            async def validate(self, context):
                return True

            async def on_failure(self, context, error):
                context.add_metadata("failure_handled", True)

        context = PipelineContext(project_id="test-project")
        processor = FailingProcessor("failing_stage")

        # 模拟失败
        error = Exception("Simulated failure")
        await processor.on_failure(context, error)

        # 验证失败被处理
        assert context.get_metadata("failure_handled") is True
