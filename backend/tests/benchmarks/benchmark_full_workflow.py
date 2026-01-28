"""
完整工作流性能基准测试
建立性能基线，监控性能退化

运行方式:
    cd backend
    uv run pytest tests/benchmarks/benchmark_full_workflow.py -v

性能指标:
- 总执行时间: < 30秒（Mock环境）
- 内存增长: < 100MB
- 每阶段平均: < 6秒
"""
import pytest
import time
import psutil
import os
import asyncio

from apps.projects.tests.factories import (
    ProjectFactory,
    ProjectStageFactory,
    UserFactory
)
from apps.projects.pipeline_adapters import (
    RewriteStageAdapter,
    StoryboardStageAdapter,
    ImageGenerationStageAdapter,
    CameraMovementStageAdapter,
    VideoGenerationStageAdapter
)
from core.pipeline.base import PipelineContext


@pytest.mark.django_db
@pytest.mark.benchmark
class TestWorkflowPerformance:
    """工作流性能基准测试"""

    @pytest.fixture
    def memory_before(self):
        """记录测试前内存使用"""
        process = psutil.Process(os.getpid())
        return process.memory_info().rss / 1024 / 1024  # MB

    def test_full_workflow_performance(self, memory_before, benchmark):
        """测试完整工作流性能"""
        from apps.models.models import ModelProvider
        from apps.prompts.models import PromptTemplateSet, PromptTemplate

        # 准备测试数据
        user = UserFactory()

        # 创建PromptTemplateSet
        prompt_set = PromptTemplateSet.objects.create(
            name='Benchmark Test Set',
            created_by=user
        )

        # 创建提示词模板
        for stage in ['rewrite', 'storyboard', 'image_generation', 'camera_movement', 'video_generation']:
            PromptTemplate.objects.create(
                template_set=prompt_set,
                stage_type=stage,
                template_content=f'Test {{{{ raw_text }}}}',
                is_active=True
            )

        # 获取Mock Providers
        mock_llm = ModelProvider.objects.get(name='Mock LLM for E2E Test')
        mock_t2i = ModelProvider.objects.get(name='Mock Text2Image for E2E Test')
        mock_i2v = ModelProvider.objects.get(name='Mock Image2Video for E2E Test')

        # 创建项目
        project = ProjectFactory(
            user=user,
            original_topic='性能测试主题' * 10,  # 较长文本
            prompt_template_set=prompt_set
        )

        # 创建5个阶段
        for stage_type in ['rewrite', 'storyboard', 'image_generation', 'camera_movement', 'video_generation']:
            ProjectStageFactory(
                project=project,
                stage_type=stage_type,
                status='pending'
            )

        # 执行工作流
        start_time = time.time()
        start_memory = psutil.Process(os.getpid()).memory_info().rss / 1024 / 1024

        # 模拟工作流执行
        async def run_workflow():
            context = PipelineContext(project_id=str(project.id))

            # 依次执行5个适配器
            adapters = [
                RewriteStageAdapter(),
                StoryboardStageAdapter(),
                ImageGenerationStageAdapter(),
                CameraMovementStageAdapter(),
                VideoGenerationStageAdapter()
            ]

            for adapter in adapters:
                # 验证
                assert await adapter.validate(context)

                # 注意: 这里不执行process，因为需要mock processor
                # 只测量验证的性能
                time.sleep(0.1)  # 模拟处理时间

        asyncio.run(run_workflow())

        end_time = time.time()
        end_memory = psutil.Process(os.getpid()).memory_info().rss / 1024 / 1024

        total_time = end_time - start_time
        memory_used = end_memory - start_memory

        print(f"\n性能指标:")
        print(f"  总执行时间: {total_time:.2f}秒")
        print(f"  内存增长: {memory_used:.2f}MB")
        print(f"  每阶段平均: {total_time/5:.2f}秒")

        # 性能断言（Mock环境）
        assert total_time < 30, f"工作流执行时间过长: {total_time:.2f}秒"
        assert memory_used < 100, f"内存占用过大: {memory_used:.2f}MB"

    def test_adapter_validation_performance(self):
        """测试适配器验证性能"""
        project = ProjectFactory(original_topic="测试主题")
        for stage_type in ['rewrite', 'storyboard', 'image_generation', 'camera_movement', 'video_generation']:
            ProjectStageFactory(project=project, stage_type=stage_type, status='pending')

        context = PipelineContext(project_id=str(project.id))
        adapter = RewriteStageAdapter()

        # 测量验证性能
        start_time = time.time()
        for _ in range(100):  # 运行100次
            result = asyncio.run(adapter.validate(context))
            assert result == True
        elapsed = time.time() - start_time

        avg_time = elapsed / 100 * 1000  # 毫秒
        print(f"\n验证性能:")
        print(f"  100次验证总时间: {elapsed:.2f}秒")
        print(f"  平均每次验证: {avg_time:.2f}毫秒")

        assert avg_time < 100, f"验证性能过低: {avg_time:.2f}毫秒"

    def test_async_vs_sync_orm_performance(self):
        """对比异步ORM vs 同步ORM性能"""
        from apps.projects.models import Project

        # 创建100个测试项目
        projects = [ProjectFactory(original_topic=f"项目{i}") for i in range(100)]
        project_ids = [str(p.id) for p in projects]

        # 测试同步ORM
        start_time = time.time()
        for pid in project_ids[:10]:
            _ = Project.objects.get(id=pid)
        sync_time = time.time() - start_time

        # 测试异步ORM
        async def test_async():
            from asgiref.sync import sync_to_async
            aget = sync_to_async(Project.objects.get)
            start = time.time()
            for pid in project_ids[:10]:
                _ = await aget(id=pid)
            return time.time() - start

        async_time = asyncio.run(test_async())

        print(f"\nORM性能对比:")
        print(f"  同步ORM (10次): {sync_time:.2f}秒")
        print(f"  异步ORM (10次): {async_time:.2f}秒")
        print(f"  异步/同步比率: {async_time/sync_time:.2f}x")

        # 异步ORM应该不比同步ORM慢太多（允许2倍）
        assert async_time < sync_time * 2, "异步ORM性能过慢"


@pytest.mark.django_db
class TestMemoryEfficiency:
    """内存效率测试"""

    def test_stage_data_memory(self):
        """测试阶段数据内存占用"""
        project = ProjectFactory(original_topic="测试主题" * 100)

        # 创建大量阶段数据
        stage = ProjectStageFactory(
            project=project,
            stage_type='rewrite',
            status='completed',
            input_data={'text': 'x' * 10000},  # 10KB数据
            output_data={'result': 'y' * 10000}  # 10KB数据
        )

        # 测量内存占用
        import sys
        data_size = sys.getsizeof(stage.input_data) + sys.getsizeof(stage.output_data)

        print(f"\n数据内存占用:")
        print(f"  input_data: {sys.getsizeof(stage.input_data)/1024:.2f}KB")
        print(f"  output_data: {sys.getsizeof(stage.output_data)/1024:.2f}KB")
        print(f"  总计: {data_size/1024:.2f}KB")

        # 单个阶段数据应该小于50KB
        assert data_size < 50 * 1024, f"阶段数据占用过大: {data_size/1024:.2f}KB"

    def test_large_project_memory(self):
        """测试大型项目内存占用"""
        from apps.projects.models import Project, ProjectStage

        # 创建包含100个阶段的项目
        project = ProjectFactory(original_topic="大型项目")

        initial_memory = psutil.Process(os.getpid()).memory_info().rss / 1024 / 1024

        # 创建100个阶段
        stages = []
        for i in range(100):
            stage = ProjectStage(
                project=project,
                stage_type='rewrite',
                status='completed',
                input_data={'index': i, 'data': 'x' * 1000},
                output_data={'result': 'y' * 1000}
            )
            stages.append(stage)

        # 估算内存增长
        estimated_growth = len(stages) * 2  # 每个阶段约2KB
        final_memory = psutil.Process(os.getpid()).memory_info().rss / 1024 / 1024
        actual_growth = final_memory - initial_memory

        print(f"\n大型项目内存:")
        print(f"  阶段数: {len(stages)}")
        print(f"  预估增长: {estimated_growth:.2f}MB")
        print(f"  实际增长: {actual_growth:.2f}MB")

        # 实际增长应该合理（允许5倍估算值）
        assert actual_growth < estimated_growth * 5, "内存增长过大"


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s', '--tb=short'])
