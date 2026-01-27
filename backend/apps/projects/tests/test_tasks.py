"""
项目管理域Celery任务测试
测试execute_llm_stage、execute_text2image_stage、execute_image2video_stage、generate_jianying_draft
遵循单一职责原则(SRP)
"""

import pytest
from celery.exceptions import Retry
from django.contrib.auth import get_user_model
from django.utils import timezone
from unittest.mock import Mock, patch, MagicMock

from apps.projects.models import Project, ProjectStage
from apps.projects.tasks import (
    execute_llm_stage,
    execute_text2image_stage,
    execute_image2video_stage,
    generate_jianying_draft,
)
from apps.projects.tests.factories import (
    ProjectFactory,
    ProjectStageFactory,
    UserFactory,
)

User = get_user_model()


@pytest.mark.django_db
class TestExecuteLLMStage:
    """测试execute_llm_stage任务"""

    def setup_method(self):
        """每个测试方法前的设置"""
        self.user = UserFactory()
        self.project = ProjectFactory(user=self.user, status='draft')

    @pytest.mark.skip(reason="需要完整的AI服务和Redis环境")
    def test_execute_llm_stage_success(self):
        """测试成功执行LLM阶段"""
        # 创建阶段
        stage = ProjectStageFactory(
            project=self.project,
            stage_type='rewrite',
            status='pending'
        )

        # 模拟任务执行
        task = execute_llm_stage
        result = task.apply_async(
            args=[str(self.project.id), 'rewrite', {'topic': 'test'}, self.user.id]
        ).get(timeout=10)

        # 验证结果
        assert result['success'] is True
        assert 'task_id' in result

    def test_execute_llm_stage_project_not_found(self):
        """测试项目不存在"""
        fake_project_id = '00000000-0000-0000-0000-000000000000'

        task = execute_llm_stage
        result = task.apply_async(
            args=[fake_project_id, 'rewrite', {}, self.user.id]
        ).get(timeout=10)

        assert result['success'] is False
        assert 'error' in result

    def test_execute_llm_stage_stage_not_found(self):
        """测试阶段不存在"""
        # 创建项目但不创建阶段

        task = execute_llm_stage
        result = task.apply_async(
            args=[str(self.project.id), 'rewrite', {}, self.user.id]
        ).get(timeout=10)

        assert result['success'] is False


@pytest.mark.django_db
class TestExecuteText2ImageStage:
    """测试execute_text2image_stage任务"""

    def setup_method(self):
        """每个测试方法前的设置"""
        self.user = UserFactory()
        self.project = ProjectFactory(user=self.user)

    @pytest.mark.skip(reason="需要完整的AI服务和Redis环境")
    def test_execute_text2image_stage_success(self):
        """测试成功执行文生图阶段"""
        # 创建阶段
        stage = ProjectStageFactory(
            project=self.project,
            stage_type='image_generation',
            status='pending'
        )

        task = execute_text2image_stage
        result = task.apply_async(
            args=[str(self.project.id), None, self.user.id]
        ).get(timeout=10)

        assert result['success'] is True


@pytest.mark.django_db
class TestExecuteImage2VideoStage:
    """测试execute_image2video_stage任务"""

    def setup_method(self):
        """每个测试方法前的设置"""
        self.user = UserFactory()
        self.project = ProjectFactory(user=self.user)

    @pytest.mark.skip(reason="需要完整的AI服务和Redis环境")
    def test_execute_image2video_stage_success(self):
        """测试成功执行图生视频阶段"""
        # 创建阶段
        stage = ProjectStageFactory(
            project=self.project,
            stage_type='video_generation',
            status='pending'
        )

        task = execute_image2video_stage
        result = task.apply_async(
            args=[str(self.project.id), None, self.user.id]
        ).get(timeout=10)

        assert result['success'] is True


@pytest.mark.django_db
class TestGenerateJianyingDraft:
    """测试generate_jianying_draft任务"""

    def setup_method(self):
        """每个测试方法前的设置"""
        self.user = UserFactory()
        self.project = ProjectFactory(user=self.user)

    @pytest.mark.skip(reason="需要剪映草稿服务")
    def test_generate_jianying_draft_success(self):
        """测试成功生成剪映草稿"""
        # 创建完成的视频生成阶段
        video_stage = ProjectStageFactory(
            project=self.project,
            stage_type='video_generation',
            status='completed',
            output_data={
                'human_text': {
                    'scenes': [
                        {
                            'scene_number': 1,
                            'video_urls': ['video1.mp4']
                        }
                    ]
                }
            }
        )

        task = generate_jianying_draft
        result = task.apply_async(
            args=[str(self.project.id), self.user.id, None]
        ).get(timeout=10)

        assert result['success'] is True
        assert 'draft_path' in result

    def test_generate_jianying_draft_video_stage_not_completed(self):
        """测试视频阶段未完成"""
        # 创建未完成的视频阶段
        ProjectStageFactory(
            project=self.project,
            stage_type='video_generation',
            status='processing'
        )

        task = generate_jianying_draft
        result = task.apply_async(
            args=[str(self.project.id), self.user.id, None]
        ).get(timeout=10)

        assert result['success'] is False

    def test_generate_jianying_draft_project_not_found(self):
        """测试项目不存在"""
        fake_project_id = '00000000-0000-0000-0000-000000000000'

        task = generate_jianying_draft
        result = task.apply_async(
            args=[fake_project_id, self.user.id, None]
        ).get(timeout=10)

        assert result['success'] is False


@pytest.mark.django_db
class TestCeleryTaskIntegration:
    """测试Celery任务集成"""

    def setup_method(self):
        """每个测试方法前的设置"""
        self.user = UserFactory()

    def test_task_signature_exists(self):
        """测试任务签名存在"""
        assert execute_llm_stage is not None
        assert execute_text2image_stage is not None
        assert execute_image2video_stage is not None
        assert generate_jianying_draft is not None

    def test_task_has_correct_attributes(self):
        """测试任务有正确的属性"""
        # 检查任务属性
        assert hasattr(execute_llm_stage, 'max_retries')
        assert hasattr(execute_llm_stage, 'default_retry_delay')
