"""
Pipeline适配器单元测试
目标: 90%+覆盖率

测试范围:
- RewriteStageAdapter
- StoryboardStageAdapter
- ImageGenerationStageAdapter
- CameraMovementStageAdapter
- VideoGenerationStageAdapter

使用pytest-asyncio进行异步测试
"""
import pytest
from unittest.mock import Mock, MagicMock, patch, AsyncMock
from asgiref.sync import sync_to_async
from apps.projects.tests.factories import ProjectFactory, ProjectStageFactory
from apps.projects.pipeline_adapters import (
    RewriteStageAdapter,
    StoryboardStageAdapter,
    ImageGenerationStageAdapter,
    CameraMovementStageAdapter,
    VideoGenerationStageAdapter
)
from core.pipeline.base import PipelineContext, StageResult
from apps.projects.models import Project, ProjectStage


@pytest.mark.django_db
class TestRewriteStageAdapter:
    """RewriteStageAdapter测试"""

    @pytest.fixture
    def adapter(self):
        return RewriteStageAdapter()

    @pytest.fixture
    async def project(self):
        # 使用sync_to_async包装ProjectFactory
        from asgiref.sync import sync_to_async
        return await sync_to_async(ProjectFactory)(
            original_topic="宁静的小镇，年轻的画家"
        )

    @pytest.fixture
    async def context(self, project):
        return PipelineContext(project_id=str(project.id))

    @pytest.mark.asyncio
    async def test_validate_success(self, adapter, context):
        """测试验证成功"""
        result = await adapter.validate(context)
        assert result == True

    @pytest.mark.asyncio
    async def test_validate_failure_no_topic(self, adapter, project):
        """测试验证失败：无原始主题"""
        project.original_topic = ""
        await sync_to_async(project.save)()

        context = PipelineContext(project_id=str(project.id))
        result = await adapter.validate(context)
        assert result == False

    @pytest.mark.asyncio
    async def test_validate_failure_project_not_exists(self, adapter):
        """测试验证失败：项目不存在"""
        context = PipelineContext(project_id="00000000-0000-0000-0000-000000000000")
        result = await adapter.validate(context)
        assert result == False

    @patch('apps.projects.pipeline_adapters.LLMStageProcessor')
    @pytest.mark.asyncio
    async def test_process_success(self, mock_processor_class, adapter, context, project):
        """测试处理成功"""
        # Mock processor
        mock_processor = Mock()
        mock_processor.process_stream.return_value = [
            {'type': 'token', 'full_text': '改写后的文本'},
            {'type': 'done', 'full_text': '改写后的文本'}
        ]
        mock_processor_class.return_value = mock_processor

        # 创建新adapter实例以使用mock
        adapter = RewriteStageAdapter()

        result = await adapter.process(context)

        assert result.success == True
        assert 'rewritten_text' in result.data
        assert result.data['rewritten_text'] == '改写后的文本'

    @pytest.mark.asyncio
    @patch('apps.projects.pipeline_adapters.LLMStageProcessor')
    async def test_process_failure_error_chunk(self, mock_processor_class, context):
        """测试处理失败：错误chunk"""
        mock_processor = Mock()
        mock_processor.process_stream.return_value = [
            {'type': 'error', 'error': '测试错误'}
        ]
        mock_processor_class.return_value = mock_processor

        adapter = RewriteStageAdapter()

        with pytest.raises(Exception, match='测试错误'):
            await adapter.process(context)

    @pytest.mark.asyncio
    async def test_on_failure(self, adapter, project, context):
        """测试失败处理"""
        # 先创建stage
        stage = await sync_to_async(ProjectStage.objects.get_or_create)(
            project=project,
            stage_type='rewrite',
            defaults={'status': 'pending'}
        )

        error = Exception("测试错误")
        await adapter.on_failure(context, error)

        # 刷新并验证
        stage = await sync_to_async(ProjectStage.objects.get)(project=project, stage_type='rewrite')
        assert stage.status == 'failed'
        assert '测试错误' in stage.error_message


@pytest.mark.django_db
class TestStoryboardStageAdapter:
    """StoryboardStageAdapter测试"""

    @pytest.fixture
    def adapter(self):
        return StoryboardStageAdapter()

    @pytest.fixture
    async def project(self):
        project = await sync_to_async(ProjectFactory)(original_topic="测试主题")
        # 创建rewrite阶段并完成
        rewrite_stage = await sync_to_async(ProjectStageFactory)(
            project=project,
            stage_type='rewrite',
            status='completed',
            output_data={'raw_text': '改写后的文本'}
        )
        return project

    @pytest.fixture
    async def context(self, project):
        return PipelineContext(project_id=str(project.id))

    @pytest.mark.asyncio
    async def test_validate_success(self, adapter, context):
        """测试验证成功"""
        result = await adapter.validate(context)
        assert result == True

    @pytest.mark.asyncio
    async def test_validate_failure_no_rewrite_output(self, adapter, project):
        """测试验证失败：无rewrite输出"""
        # 删除rewrite阶段
        await sync_to_async(ProjectStage.objects.filter(
        ).delete)()

        context = PipelineContext(project_id=str(project.id))
        result = await adapter.validate(context)
        assert result == False

    @patch('apps.projects.pipeline_adapters.LLMStageProcessor')
    @pytest.mark.asyncio
    async def test_process_success(self, mock_processor_class, adapter, context, project):
        """测试处理成功"""
        mock_processor = Mock()
        storyboard_json = '[{"scene_number": 1, "scene_description": "测试场景"}]'
        mock_processor.process_stream.return_value = [
            {'type': 'token', 'full_text': storyboard_json},
            {'type': 'done', 'full_text': storyboard_json}
        ]
        mock_processor_class.return_value = mock_processor

        adapter = StoryboardStageAdapter()
        result = await adapter.process(context)

        assert result.success == True
        assert 'storyboard' in result.data


@pytest.mark.django_db
class TestImageGenerationStageAdapter:
    """ImageGenerationStageAdapter测试"""

    @pytest.fixture
    def adapter(self):
        return ImageGenerationStageAdapter()

    @pytest.fixture
    async def project(self):
        project = await sync_to_async(ProjectFactory)(original_topic="测试主题")
        # 创建storyboard阶段并完成
        storyboard_stage = await sync_to_async(ProjectStageFactory)(
            project=project,
            stage_type='storyboard',
            status='completed',
            output_data={'storyboard': '[{"scene_number": 1, "scene_description": "测试场景", "image_prompt": "test prompt"}]'}
        )
        return project

    @pytest.fixture
    async def context(self, project):
        return PipelineContext(project_id=str(project.id))

    @pytest.mark.asyncio
    async def test_validate_success(self, adapter, context):
        """测试验证成功"""
        result = await adapter.validate(context)
        assert result == True

    @pytest.mark.asyncio
    async def test_validate_failure_no_storyboard(self, adapter, project):
        """测试验证失败：无storyboard输出"""
        await sync_to_async(ProjectStage.objects.filter(
        ).delete)()

        context = PipelineContext(project_id=str(project.id))
        result = await adapter.validate(context)
        assert result == False

    @patch('apps.projects.pipeline_adapters.Text2ImageStageProcessor')
    @pytest.mark.asyncio
    async def test_process_success(self, mock_processor_class, adapter, context):
        """测试处理成功"""
        mock_processor = Mock()
        mock_processor.process_stream.return_value = [
            {'type': 'progress', 'scene_index': 0, 'progress': 50},
            {'type': 'image', 'scene_index': 0, 'image_url': 'http://example.com/image1.jpg'},
            {'type': 'done', 'total_images': 1}
        ]
        mock_processor_class.return_value = mock_processor

        adapter = ImageGenerationStageAdapter()
        result = await adapter.process(context)

        assert result.success == True
        assert 'images' in result.data


@pytest.mark.django_db
class TestCameraMovementStageAdapter:
    """CameraMovementStageAdapter测试"""

    @pytest.fixture
    def adapter(self):
        return CameraMovementStageAdapter()

    @pytest.fixture
    async def project(self):
        project = await sync_to_async(ProjectFactory)(original_topic="测试主题")
        # 创建image_generation阶段并完成
        image_stage = await sync_to_async(ProjectStageFactory)(
            project=project,
            stage_type='image_generation',
            status='completed',
            output_data={'images': [{'scene_index': 0, 'image_url': 'http://example.com/image1.jpg'}]}
        )
        return project

    @pytest.fixture
    async def context(self, project):
        return PipelineContext(project_id=str(project.id))

    @pytest.mark.asyncio
    async def test_validate_success(self, adapter, context):
        """测试验证成功"""
        result = await adapter.validate(context)
        assert result == True

    @pytest.mark.asyncio
    async def test_validate_failure_no_images(self, adapter, project):
        """测试验证失败：无图片输出"""
        await sync_to_async(ProjectStage.objects.filter(
        ).delete)()

        context = PipelineContext(project_id=str(project.id))
        result = await adapter.validate(context)
        assert result == False

    @patch('apps.projects.pipeline_adapters.LLMStageProcessor')
    @pytest.mark.asyncio
    async def test_process_success(self, mock_processor_class, adapter, context):
        """测试处理成功"""
        mock_processor = Mock()
        mock_processor.process_stream.return_value = [
            {'type': 'token', 'full_text': '{"movement_type": "zoom_in"}'},
            {'type': 'done', 'full_text': '{"movement_type": "zoom_in"}'}
        ]
        mock_processor_class.return_value = mock_processor

        adapter = CameraMovementStageAdapter()
        result = await adapter.process(context)

        assert result.success == True
        assert 'camera_movements' in result.data


@pytest.mark.django_db
class TestVideoGenerationStageAdapter:
    """VideoGenerationStageAdapter测试"""

    @pytest.fixture
    def adapter(self):
        return VideoGenerationStageAdapter()

    @pytest.fixture
    async def project(self):
        project = await sync_to_async(ProjectFactory)(original_topic="测试主题")
        # 创建前置阶段
        camera_stage = await sync_to_async(ProjectStageFactory)(
            project=project,
            stage_type='camera_movement',
            status='completed',
            output_data={'camera_movements': [{'scene_index': 0, 'movement_type': 'zoom_in'}]}
        )
        image_stage = await sync_to_async(ProjectStageFactory)(
            project=project,
            stage_type='image_generation',
            status='completed',
            output_data={'images': [{'scene_index': 0, 'image_url': 'http://example.com/image1.jpg'}]}
        )
        return project

    @pytest.fixture
    async def context(self, project):
        return PipelineContext(project_id=str(project.id))

    @pytest.mark.asyncio
    async def test_validate_success(self, adapter, context):
        """测试验证成功"""
        result = await adapter.validate(context)
        assert result == True

    @pytest.mark.asyncio
    async def test_validate_failure_no_camera_movement(self, adapter, project):
        """测试验证失败：无运镜输出"""
        await sync_to_async(ProjectStage.objects.filter(
        ).delete)()

        context = PipelineContext(project_id=str(project.id))
        result = await adapter.validate(context)
        assert result == False

    @pytest.mark.asyncio
    async def test_validate_failure_no_images(self, adapter, project):
        """测试验证失败：无图片"""
        await sync_to_async(ProjectStage.objects.filter(
        ).delete)()

        context = PipelineContext(project_id=str(project.id))
        result = await adapter.validate(context)
        assert result == False

    @patch('apps.projects.pipeline_adapters.Image2VideoStageProcessor')
    @pytest.mark.asyncio
    async def test_process_success(self, mock_processor_class, adapter, context):
        """测试处理成功"""
        mock_processor = Mock()
        mock_processor.process_stream.return_value = [
            {'type': 'progress', 'scene_index': 0, 'progress': 50},
            {'type': 'video', 'scene_index': 0, 'video_url': 'http://example.com/video1.mp4'},
            {'type': 'done', 'total_videos': 1}
        ]
        mock_processor_class.return_value = mock_processor

        adapter = VideoGenerationStageAdapter()
        result = await adapter.process(context)

        assert result.success == True
        assert 'videos' in result.data


@pytest.mark.django_db
class TestAdapterIntegration:
    """适配器集成测试"""

    @pytest.mark.asyncio
    async def test_adapter_chain_execution(self):
        """测试适配器链式执行"""
        # 创建项目
        project = await sync_to_async(ProjectFactory)(original_topic="宁静的小镇，年轻的画家")

        # 创建所有阶段
        for stage_type in ['rewrite', 'storyboard', 'image_generation', 'camera_movement', 'video_generation']:
            ProjectStageFactory(project=project, stage_type=stage_type, status='pending')

        context = PipelineContext(project_id=str(project.id))

        # 测试rewrite适配器验证
        rewrite_adapter = RewriteStageAdapter()
        assert await rewrite_adapter.validate(context) == True

    @pytest.mark.asyncio
    async def test_adapter_error_handling(self):
        """测试适配器错误处理"""
        project = await sync_to_async(ProjectFactory)(original_topic="测试主题")
        ProjectStageFactory(project=project, stage_type='rewrite', status='pending')

        context = PipelineContext(project_id=str(project.id))
        adapter = RewriteStageAdapter()

        # 测试on_failure
        error = Exception("测试错误")
        await adapter.on_failure(context, error)

        stage = await sync_to_async(ProjectStage.objects.get)(project=project, stage_type='rewrite')
        assert stage.status == 'failed'
        assert '测试错误' in stage.error_message
