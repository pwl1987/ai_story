"""
单元测试: Pipeline适配器
Story 5.4: 测试5个阶段适配器的功能
"""

from unittest.mock import patch

import pytest
from asgiref.sync import sync_to_async

from apps.projects.models import Project
from apps.projects.pipeline_adapters import (
    CameraMovementStageAdapter,
    ImageGenerationStageAdapter,
    RewriteStageAdapter,
    StoryboardStageAdapter,
    VideoGenerationStageAdapter,
)
from core.pipeline.base import PipelineContext


@pytest.mark.django_db
class TestRewriteStageAdapter:
    """测试文案改写适配器"""

    @pytest.fixture
    def adapter(self):
        return RewriteStageAdapter()

    @pytest.fixture
    def user(self, django_user_model):
        return django_user_model.objects.create_user(
            username='testuser',
            password='testpass123'
        )

    @pytest.fixture
    def project(self, user):
        return Project.objects.create(
            name="测试项目",
            original_topic="AI故事生成测试",
            user=user
        )

    def test_adapter_initialization(self, adapter):
        """测试适配器初始化"""
        assert adapter.stage_name == 'rewrite'
        assert adapter.processor is not None

    @pytest.mark.asyncio
    async def test_validate_with_valid_project(self, adapter, project):
        """测试验证通过"""
        context = PipelineContext(project_id=str(project.id))
        result = await adapter.validate(context)
        assert result is True

    @pytest.mark.asyncio
    async def test_validate_with_invalid_project(self, adapter):
        """测试验证失败（项目不存在）"""
        context = PipelineContext(project_id="invalid-id")
        result = await adapter.validate(context)
        assert result is False

    @pytest.mark.asyncio
    async def test_validate_with_no_topic(self, adapter, user):
        """测试验证失败（缺少主题）"""
        project = await sync_to_async(Project.objects.create)(
            name="空项目",
            original_topic="",
            user=user
        )
        context = PipelineContext(project_id=str(project.id))
        result = await adapter.validate(context)
        assert result is False

    @pytest.mark.asyncio
    async def test_process_success(self, adapter, project):
        """测试处理成功"""
        context = PipelineContext(project_id=str(project.id))

        # Mock processor.process_stream
        with patch.object(adapter.processor, 'process_stream') as mock_stream:
            mock_stream.return_value = [
                {'type': 'token', 'content': '测试', 'full_text': '测试'},
                {'type': 'done', 'full_text': '完整文本'}
            ]

            result = await adapter.process(context)

            assert result.success is True
            assert 'rewritten_text' in result.data

    @pytest.mark.asyncio
    async def test_on_failure(self, adapter, project):
        """测试失败处理"""
        context = PipelineContext(project_id=str(project.id))
        error = Exception("测试错误")

        # 直接调用，不使用mock logger
        await adapter.on_failure(context, error)
        # 如果没有抛出异常就说明成功
        assert True


@pytest.mark.django_db
class TestStoryboardStageAdapter:
    """测试分镜生成适配器"""

    @pytest.fixture
    def adapter(self):
        return StoryboardStageAdapter()

    @pytest.fixture
    def user(self, django_user_model):
        return django_user_model.objects.create_user(
            username='testuser2',
            password='testpass123'
        )

    @pytest.fixture
    def project(self, user):
        return Project.objects.create(
            name="测试项目",
            original_topic="AI故事生成测试",
            user=user
        )

    @pytest.mark.asyncio
    async def test_validate_without_rewrite_result(self, adapter, project):
        """测试验证失败（缺少文案改写结果）"""
        context = PipelineContext(project_id=str(project.id))
        result = await adapter.validate(context)
        assert result is False

    @pytest.mark.asyncio
    async def test_validate_with_rewrite_result(self, adapter, project):
        """测试验证通过"""
        context = PipelineContext(project_id=str(project.id))
        context.add_result('rewrite', {'rewritten_text': '改写后的文案'})
        result = await adapter.validate(context)
        assert result is True


@pytest.mark.django_db
class TestImageGenerationStageAdapter:
    """测试文生图适配器"""

    @pytest.fixture
    def adapter(self):
        return ImageGenerationStageAdapter()

    @pytest.fixture
    def user(self, django_user_model):
        return django_user_model.objects.create_user(
            username='testuser3',
            password='testpass123'
        )

    @pytest.fixture
    def project(self, user):
        return Project.objects.create(
            name="测试项目",
            original_topic="AI故事生成测试",
            user=user
        )

    @pytest.mark.asyncio
    async def test_validate_without_storyboard_result(self, adapter, project):
        """测试验证失败（缺少分镜结果）"""
        context = PipelineContext(project_id=str(project.id))
        result = await adapter.validate(context)
        assert result is False

    @pytest.mark.asyncio
    async def test_validate_with_storyboard_result(self, adapter, project):
        """测试验证通过"""
        context = PipelineContext(project_id=str(project.id))
        context.add_result('storyboard', {'storyboard_text': '分镜内容'})
        result = await adapter.validate(context)
        assert result is True


@pytest.mark.django_db
class TestCameraMovementStageAdapter:
    """测试运镜生成适配器"""

    @pytest.fixture
    def adapter(self):
        return CameraMovementStageAdapter()

    @pytest.fixture
    def user(self, django_user_model):
        return django_user_model.objects.create_user(
            username='testuser4',
            password='testpass123'
        )

    @pytest.fixture
    def project(self, user):
        return Project.objects.create(
            name="测试项目",
            original_topic="AI故事生成测试",
            user=user
        )

    @pytest.mark.asyncio
    async def test_validate_without_storyboard_result(self, adapter, project):
        """测试验证失败（缺少分镜结果）"""
        context = PipelineContext(project_id=str(project.id))
        result = await adapter.validate(context)
        assert result is False

    @pytest.mark.asyncio
    async def test_validate_with_storyboard_result(self, adapter, project):
        """测试验证通过"""
        context = PipelineContext(project_id=str(project.id))
        context.add_result('storyboard', {'storyboard_text': '分镜内容'})
        result = await adapter.validate(context)
        assert result is True


@pytest.mark.django_db
class TestVideoGenerationStageAdapter:
    """测试图生视频适配器"""

    @pytest.fixture
    def adapter(self):
        return VideoGenerationStageAdapter()

    @pytest.fixture
    def user(self, django_user_model):
        return django_user_model.objects.create_user(
            username='testuser5',
            password='testpass123'
        )

    @pytest.fixture
    def project(self, user):
        return Project.objects.create(
            name="测试项目",
            original_topic="AI故事生成测试",
            user=user
        )

    @pytest.mark.asyncio
    async def test_validate_without_image_result(self, adapter, project):
        """测试验证失败（缺少图片结果）"""
        context = PipelineContext(project_id=str(project.id))
        result = await adapter.validate(context)
        assert result is False

    @pytest.mark.asyncio
    async def test_validate_with_image_result(self, adapter, project):
        """测试验证通过"""
        context = PipelineContext(project_id=str(project.id))
        context.add_result('image_generation', {'images': []})
        result = await adapter.validate(context)
        assert result is True
