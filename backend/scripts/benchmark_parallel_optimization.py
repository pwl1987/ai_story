#!/usr/bin/env python
"""
性能基准测试 - 验证并行优化效果

测试目标：
- 验证Image Generation并行处理性能提升（预期66%）
- 验证Camera Movement并行处理性能提升（预期64%）
- 验证整体工作流性能提升（预期36-42%）

创建时间: 2026-01-28
"""

import os
import sys
import django
import time
import asyncio

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.base')
sys.path.insert(0, '/home/code/ai_story/backend')
django.setup()

from apps.projects.models import Project, ProjectStage, ProjectModelConfig
from apps.prompts.models import PromptTemplateSet, PromptTemplate
from apps.models.models import ModelProvider
from django.contrib.auth import get_user_model
from apps.projects.tasks import execute_full_pipeline

User = get_user_model()


class PerformanceBenchmark:
    """性能基准测试"""

    def __init__(self):
        self.user = None
        self.mock_llm = None
        self.mock_t2i = None
        self.mock_i2v = None
        self.prompt_set = None

    def setup_test_environment(self):
        """设置测试环境"""
        print("\n" + "="*60)
        print("步骤1: 设置测试环境")
        print("="*60)

        # 获取或创建测试用户
        self.user, _ = User.objects.get_or_create(
            username='benchmark_test_user',
            defaults={'email': 'benchmark@test.com'}
        )
        print(f"✓ 测试用户: {self.user.username}")

        # 获取Mock Providers
        self.mock_llm = ModelProvider.objects.filter(
            name__icontains='Mock LLM',
            provider_type='llm'
        ).first()

        if not self.mock_llm:
            print("❌ 未找到Mock LLM Provider")
            return False
        print(f"✓ Mock LLM: {self.mock_llm.name}")

        self.mock_t2i = ModelProvider.objects.filter(
            provider_type='text2image'
        ).first()

        if not self.mock_t2i:
            print("❌ 未找到Mock Text2Image Provider")
            return False
        print(f"✓ Mock Text2Image: {self.mock_t2i.name}")

        self.mock_i2v = ModelProvider.objects.filter(
            provider_type='image2video'
        ).first()

        if not self.mock_i2v:
            print("❌ 未找到Mock Image2Video Provider")
            return False
        print(f"✓ Mock Image2Video: {self.mock_i2v.name}")

        # 创建PromptTemplateSet
        self.prompt_set = PromptTemplateSet.objects.create(
            name='Benchmark Test Prompt Set',
            created_by=self.user  # 添加created_by字段
        )

        # 创建5个模板
        for stage in ['rewrite', 'storyboard', 'image_generation', 'camera_movement', 'video_generation']:
            PromptTemplate.objects.create(
                template_set=self.prompt_set,
                stage_type=stage,
                template_content=f'Test template for {stage}: {{{{ raw_text }}}}',
                is_active=True
            )

        print(f"✓ PromptTemplateSet已创建，包含5个模板")

        return True

    def create_test_project(self, project_name="Benchmark Test"):
        """创建测试项目"""
        print(f"\n创建测试项目: {project_name}")

        # 创建项目
        project = Project.objects.create(
            name=project_name,
            original_topic='宁静的小镇，年轻的画家正在创作一幅美丽的风景画',
            user=self.user,
            prompt_template_set=self.prompt_set,
            status='draft'
        )
        print(f"✓ 项目创建成功: {project.id}")

        # 创建5个阶段
        for stage_type in ['rewrite', 'storyboard', 'image_generation', 'camera_movement', 'video_generation']:
            ProjectStage.objects.create(
                project=project,
                stage_type=stage_type,
                status='pending'
            )

        print(f"✓ 5个阶段已初始化")

        # 配置模型
        config = ProjectModelConfig.objects.create(project=project)
        config.rewrite_providers.add(self.mock_llm)
        config.storyboard_providers.add(self.mock_llm)
        config.camera_providers.add(self.mock_llm)
        config.image_providers.add(self.mock_t2i)
        config.video_providers.add(self.mock_i2v)

        print(f"✓ 模型配置完成")

        return project

    def run_full_pipeline_benchmark(self, project):
        """运行完整工作流基准测试"""
        print("\n" + "="*60)
        print("步骤2: 运行完整工作流性能测试")
        print("="*60)

        # 启动Celery任务
        start_time = time.time()

        result = execute_full_pipeline.delay(
            project_id=str(project.id),
            user_id=self.user.id
        )

        task_id = result.id
        print(f"✓ Celery任务已启动: {task_id}")

        # 等待任务完成
        max_wait = 300  # 5分钟超时
        check_interval = 1  # 每秒检查一次

        last_progress = -1
        while time.time() - start_time < max_wait:
            # 刷新项目数据
            project.refresh_from_db()

            # 显示进度
            stages = project.stages.all()
            completed_count = sum(1 for s in stages if s.status == 'completed')
            progress = int((completed_count / len(stages)) * 100)

            if progress != last_progress:
                progress_bar = '[' + '█' * (completed_count) + '░' * (5 - completed_count) + ']'
                print(f"\r进度: {progress_bar} {completed_count}/5 阶段完成 ({progress}%)", end='', flush=True)
                last_progress = progress

            # 检查是否完成
            if project.status == 'completed':
                total_time = time.time() - start_time
                print(f"\n\n✓ 工作流完成！总时间: {total_time:.2f}秒")

                # 分析各阶段耗时
                self.analyze_stage_performance(project)

                return total_time

            elif project.status == 'failed':
                print(f"\n\n✗ 工作流失败")
                # 显示失败阶段
                for stage in stages:
                    if stage.status == 'failed':
                        print(f"  失败阶段: {stage.stage_type}")
                        print(f"  错误信息: {stage.error_message}")
                return None

            time.sleep(check_interval)

        print(f"\n\n✗ 超时（{max_wait}秒）")
        return None

    def analyze_stage_performance(self, project):
        """分析各阶段性能"""
        print("\n" + "-"*60)
        print("各阶段性能分析")
        print("-"*60)

        stages = project.stages.all().order_by('started_at')

        for stage in stages:
            if stage.started_at and stage.completed_at:
                duration = (stage.completed_at - stage.started_at).total_seconds()
                status_icon = "✅" if stage.status == 'completed' else "❌"
                print(f"{status_icon} {stage.stage_type:20s}: {duration:6.2f}秒")

        print("-"*60)

    def compare_with_baseline(self, actual_time):
        """与基准对比"""
        print("\n" + "="*60)
        print("性能对比分析")
        print("="*60)

        # 基准时间（优化前）
        baseline_time = 10.91

        # 计算提升
        improvement = ((baseline_time - actual_time) / baseline_time) * 100

        print(f"优化前（基准）: {baseline_time:.2f}秒")
        print(f"优化后（实际）: {actual_time:.2f}秒")
        print(f"性能提升:      {improvement:.1f}%")

        # 预期对比
        print("\n预期对比:")
        print(f"  最低预期（30%）:  {baseline_time * 0.7:.2f}秒")
        print(f"  中等预期（36%）:  {baseline_time * 0.64:.2f}秒")
        print(f"  最高预期（42%）:  {baseline_time * 0.58:.2f}秒")

        # 判断是否达标
        if improvement >= 42:
            print(f"\n🎉 优秀！性能提升达到最高预期！")
        elif improvement >= 36:
            print(f"\n✅ 良好！性能提升达到中等预期")
        elif improvement >= 30:
            print(f"\n✓ 达到最低预期")
        else:
            print(f"\n⚠️ 未达到预期性能提升")

        print("="*60)

        return improvement

    def run_benchmark_suite(self, num_runs=3):
        """运行基准测试套件（多次运行取平均值）"""
        print("\n" + "="*60)
        print(f"性能基准测试套件（{num_runs}次运行）")
        print("="*60)

        times = []

        for i in range(num_runs):
            print(f"\n--- 第 {i+1}/{num_runs} 次运行 ---")

            # 创建测试项目
            project = self.create_test_project(
                project_name=f"Benchmark Test Run {i+1}"
            )

            # 运行测试
            execution_time = self.run_full_pipeline_benchmark(project)

            if execution_time:
                times.append(execution_time)
            else:
                print(f"✗ 第 {i+1} 次运行失败")

            # 清理项目
            project.delete()

        if times:
            avg_time = sum(times) / len(times)
            min_time = min(times)
            max_time = max(times)

            print("\n" + "="*60)
            print("基准测试套件结果")
            print("="*60)
            print(f"运行次数: {len(times)}")
            print(f"平均时间: {avg_time:.2f}秒")
            print(f"最快时间: {min_time:.2f}秒")
            print(f"最慢时间: {max_time:.2f}秒")
            print("="*60)

            return avg_time

        return None


def main():
    """主函数"""
    print("\n" + "="*60)
    print("AI Story Generation - 性能基准测试")
    print("验证并行优化效果")
    print("="*60)

    benchmark = PerformanceBenchmark()

    # 设置测试环境
    if not benchmark.setup_test_environment():
        print("\n❌ 测试环境设置失败")
        return 1

    # 运行基准测试套件（3次取平均）
    avg_time = benchmark.run_benchmark_suite(num_runs=3)

    if avg_time:
        # 与基准对比
        improvement = benchmark.compare_with_baseline(avg_time)

        print(f"\n最终结论:")
        print(f"  平均执行时间: {avg_time:.2f}秒")
        print(f"  性能提升: {improvement:.1f}%")

        if improvement >= 30:
            print(f"\n✅ 性能优化验证成功！")
            return 0
        else:
            print(f"\n⚠️ 性能提升未达到预期")
            return 1
    else:
        print(f"\n❌ 基准测试失败")
        return 1


if __name__ == '__main__':
    sys.exit(main())
