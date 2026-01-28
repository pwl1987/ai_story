"""
完整工作流性能基准测试
遵循SOLID原则和BMad工作流

测试指标:
1. 总执行时间
2. 每阶段执行时间
3. 内存使用情况
4. 异步vs同步性能对比
"""
import os
import time
from datetime import datetime

# Django setup
import django
import psutil
import pytest

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.base')
django.setup()

from django.contrib.auth import get_user_model

from apps.models.models import ModelProvider
from apps.projects.pipeline_adapters import (
    CameraMovementStageAdapter,
    ImageGenerationStageAdapter,
    RewriteStageAdapter,
    StoryboardStageAdapter,
    VideoGenerationStageAdapter,
)
from apps.projects.tests.factories import ProjectFactory, ProjectStageFactory
from core.pipeline.base import PipelineContext

User = get_user_model()


class PerformanceMetrics:
    """性能指标数据类"""

    def __init__(self):
        self.start_time = None
        self.end_time = None
        self.start_memory = None
        self.end_memory = None
        self.stage_times = {}

    def start(self):
        """开始计时"""
        self.start_time = time.time()
        process = psutil.Process(os.getpid())
        self.start_memory = process.memory_info().rss / 1024 / 1024  # MB

    def stop(self):
        """停止计时"""
        self.end_time = time.time()
        process = psutil.Process(os.getpid())
        self.end_memory = process.memory_info().rss / 1024 / 1024  # MB

    def record_stage(self, stage_name: str, duration: float):
        """记录阶段耗时"""
        self.stage_times[stage_name] = duration

    @property
    def total_time(self):
        """总执行时间(秒)"""
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return 0.0

    @property
    def memory_used(self):
        """内存增长(MB)"""
        if self.start_memory and self.end_memory:
            return self.end_memory - self.start_memory
        return 0.0

    def to_dict(self):
        """转换为字典"""
        return {
            'total_time': round(self.total_time, 2),
            'memory_used_mb': round(self.memory_used, 2),
            'stage_times': {k: round(v, 2) for k, v in self.stage_times.items()},
            'timestamp': datetime.now().isoformat()
        }


@pytest.mark.django_db
@pytest.mark.benchmark
class TestWorkflowPerformance:
    """工作流性能基准测试"""

    @pytest.fixture
    async def benchmark_project(self):
        """创建基准测试项目"""
        # 获取Mock Provider
        mock_llm = ModelProvider.objects.filter(
            provider_type='llm',
            name__contains='Mock'
        ).first()

        if not mock_llm:
            pytest.skip("需要Mock LLM Provider")

        # 创建测试项目
        user, _ = await User.objects.aget_or_create(username='benchmark_user')
        project = ProjectFactory(
            user=user,
            original_topic='性能测试主题' * 10,
            status='draft'
        )

        # 创建所有阶段
        for stage_type in ['rewrite', 'storyboard', 'image_generation', 'camera_movement', 'video_generation']:
            await ProjectStageFactory(
                project=project,
                stage_type=stage_type,
                status='pending'
            )

        return project

    @pytest.mark.asyncio
    async def test_full_workflow_performance(self, benchmark_project):
        """完整工作流性能测试"""
        metrics = PerformanceMetrics()
        metrics.start()

        context = PipelineContext(project_id=str(benchmark_project.id))

        # 依次执行5个阶段
        adapters = [
            ('rewrite', RewriteStageAdapter()),
            ('storyboard', StoryboardStageAdapter()),
            ('image_generation', ImageGenerationStageAdapter()),
            ('camera_movement', CameraMovementStageAdapter()),
            ('video_generation', VideoGenerationStageAdapter())
        ]

        for stage_name, adapter in adapters:
            stage_start = time.time()

            # 验证
            valid = await adapter.validate(context)
            assert valid, f"{stage_name} 验证失败"

            # 执行
            result = await adapter.process(context)
            assert result.success, f"{stage_name} 执行失败: {result.error}"

            stage_time = time.time() - stage_start
            metrics.record_stage(stage_name, stage_time)

            print(f"  ✅ {stage_name}: {stage_time:.2f}秒")

        metrics.stop()

        # 打印性能报告
        print("\n" + "=" * 60)
        print("性能基准测试报告")
        print("=" * 60)
        print(f"总执行时间: {metrics.total_time:.2f}秒")
        print(f"内存增长: {metrics.memory_used:.2f}MB")
        print("\n各阶段耗时:")
        for stage, duration in metrics.stage_times.items():
            print(f"  {stage}: {duration:.2f}秒")
        print("=" * 60)

        # 断言性能指标
        assert metrics.total_time < 60, f"总执行时间过长: {metrics.total_time:.2f}秒"
        assert metrics.memory_used < 200, f"内存占用过大: {metrics.memory_used:.2f}MB"


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
