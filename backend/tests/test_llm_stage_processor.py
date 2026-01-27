"""
apps.content.processors.llm_stage 单元测试

测试LLM阶段处理器：文案改写、分镜生成、运镜生成
"""

import pytest
from unittest.mock import Mock, MagicMock, patch, call
from apps.content.processors.llm_stage import LLMStageProcessor
from apps.projects.models import Project, ProjectStage
from core.pipeline.base import PipelineContext, StageResult


@pytest.mark.unit
class TestLLMStageProcessorInit:
    """测试LLMStageProcessor初始化"""

    def test_init_with_valid_stage_types(self):
        """测试使用有效阶段类型初始化"""
        valid_stages = ['rewrite', 'storyboard', 'camera_movement']

        for stage_type in valid_stages:
            processor = LLMStageProcessor(stage_type=stage_type)
            assert processor.stage_type == stage_type

    def test_init_with_invalid_stage_type(self):
        """测试使用无效阶段类型初始化也能工作"""
        # 处理器不限制阶段类型，灵活设计
        processor = LLMStageProcessor(stage_type='custom_stage')
        assert processor.stage_type == 'custom_stage'


@pytest.mark.unit
class TestLLMStageProcessorValidate:
    """测试validate方法"""

    @pytest.fixture
    def processor(self):
        """创建处理器实例"""
        return LLMStageProcessor(stage_type='rewrite')

    @pytest.fixture
    def project_with_template(self, db):
        """创建带有提示词模板的项目"""
        from django.contrib.auth import get_user_model
        from apps.prompts.models import PromptTemplateSet, PromptTemplate
        from apps.models.models import ModelProvider

        User = get_user_model()

        # 创建用户
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com'
        )

        # 创建模型提供商
        provider = ModelProvider.objects.create(
            name='Test Provider',
            provider_type='llm',
            api_url='https://api.test.com',
            api_key='test-key',
            model_name='test-model',
            is_active=True
        )

        # 创建提示词集
        template_set = PromptTemplateSet.objects.create(
            name='Test Set',
            is_default=True,
            created_by=user  # 添加必需的用户
        )

        # 创建提示词模板
        template = PromptTemplate.objects.create(
            template_set=template_set,
            stage_type='rewrite',
            template_content='Test prompt: {{ raw_text }}',
            model_provider=provider,
            is_active=True
        )

        # 创建项目
        project = Project.objects.create(
            name='测试项目',
            description='测试描述',
            original_topic='原始主题',
            user=user,
            prompt_template_set=template_set
        )

        return project

    def test_validate_rewrite_stage_with_template(self, processor, project_with_template):
        """测试rewrite阶段验证 - 有提示词模板"""
        context = PipelineContext(project_id=str(project_with_template.id))
        result = processor.validate(context)
        assert result is True

    def test_validate_without_template_fails(self, processor, test_project):
        """测试没有提示词模板时验证失败"""
        context = PipelineContext(project_id=str(test_project.id))
        result = processor.validate(context)
        assert result is False

    def test_validate_nonexistent_project(self, processor):
        """测试不存在的项目验证失败"""
        context = PipelineContext(project_id='nonexistent-id')
        result = processor.validate(context)
        assert result is False


@pytest.mark.unit
class TestLLMStageProcessorProcessStream:
    """测试process_stream方法"""

    @pytest.fixture
    def processor(self):
        """创建处理器实例"""
        return LLMStageProcessor(stage_type='rewrite')

    @pytest.fixture
    def mock_project(self, db):
        """创建模拟项目"""
        from django.contrib.auth import get_user_model
        User = get_user_model()

        user = User.objects.create_user(
            username='testuser',
            email='test@example.com'
        )

        project = Project.objects.create(
            name='测试项目',
            description='测试描述',
            original_topic='原始主题内容',
            user=user
        )
        return project

    @pytest.fixture
    def project_with_stages(self, mock_project):
        """创建带有阶段和提示词模板的项目"""
        from apps.prompts.models import PromptTemplateSet, PromptTemplate
        from apps.models.models import ModelProvider

        # 创建模型提供商
        provider = ModelProvider.objects.create(
            name='Test Provider for Stream',
            provider_type='llm',
            api_url='https://api.test.com',
            api_key='test-key',
            model_name='test-model',
            is_active=True
        )

        # 创建提示词集
        template_set = PromptTemplateSet.objects.create(
            name='Test Set for Stream',
            is_default=True,
            created_by=mock_project.user
        )

        # 创建提示词模板
        template = PromptTemplate.objects.create(
            template_set=template_set,
            stage_type='rewrite',
            template_content='Test prompt: {{ raw_text }}',
            model_provider=provider,
            is_active=True
        )

        # 创建5个阶段
        stages = []
        for stage_type in ['rewrite', 'storyboard', 'image_generation', 'camera_movement', 'video_generation']:
            stage = ProjectStage.objects.create(
                project=mock_project,
                stage_type=stage_type,
                status='pending'
            )
            stages.append(stage)

        # 更新项目的提示词集
        mock_project.prompt_template_set = template_set
        mock_project.save()

        return mock_project

    @patch('core.ai_client.factory.create_ai_client')
    @patch('apps.content.processors.llm_stage.PromptTemplate.objects')
    def test_process_stream_yields_stage_update_first(
        self,
        mock_template_query,
        mock_create_client,
        processor,
        project_with_stages
    ):
        """测试process_stream首先yield stage_update消息"""
        # Mock AI客户端
        mock_client = MagicMock()
        mock_client.generate_stream.return_value = []
        mock_create_client.return_value = mock_client

        # Mock 提示词模板
        mock_template = MagicMock()
        mock_template.template_content = 'Test prompt: {{ raw_text }}'
        mock_template_query.select_related().filter().first.return_value = mock_template

        # 执行流式处理
        chunks = list(processor.process_stream(
            project_id=str(project_with_stages.id),
            input_data={}
        ))

        # 第一个消息应该是 stage_update
        assert len(chunks) > 0
        assert chunks[0]['type'] == 'stage_update'
        assert chunks[0]['stage']['status'] == 'processing'
        assert 'started_at' in chunks[0]['stage']

    @patch('core.ai_client.factory.create_ai_client')
    @patch('apps.content.processors.llm_stage.PromptTemplate.objects')
    def test_process_stream_yields_tokens(
        self,
        mock_template_query,
        mock_create_client,
        processor,
        project_with_stages
    ):
        """测试process_stream yield token消息"""
        # Mock AI客户端 - 返回token流
        mock_client = MagicMock()
        mock_client.generate_stream.return_value = [
            {'type': 'token', 'content': 'Hello', 'full_text': 'Hello'},
            {'type': 'token', 'content': ' World', 'full_text': 'Hello World'},
            {'type': 'done', 'text': 'Hello World'}
        ]
        mock_create_client.return_value = mock_client

        # Mock 提示词模板
        mock_template = MagicMock()
        mock_template.template_content = 'Test prompt: {{ raw_text }}'
        mock_template_query.select_related().filter().first.return_value = mock_template

        # 执行流式处理
        chunks = list(processor.process_stream(
            project_id=str(project_with_stages.id),
            input_data={}
        ))

        # 应该包含 token 消息
        token_chunks = [c for c in chunks if c['type'] == 'token']
        assert len(token_chunks) == 2
        assert token_chunks[0]['content'] == 'Hello'
        assert token_chunks[0]['full_text'] == 'Hello'
        assert token_chunks[1]['content'] == ' World'
        assert token_chunks[1]['full_text'] == 'Hello World'

    @patch('core.ai_client.factory.create_ai_client')
    @patch('apps.content.processors.llm_stage.PromptTemplate.objects')
    def test_process_stream_updates_stage_to_completed(
        self,
        mock_template_query,
        mock_create_client,
        processor,
        project_with_stages
    ):
        """测试process_stream更新阶段状态为completed"""
        # Mock AI客户端
        mock_client = MagicMock()
        mock_client.generate_stream.return_value = [
            {'type': 'done', 'text': 'Final text'}
        ]
        mock_create_client.return_value = mock_client

        # Mock 提示词模板
        mock_template = MagicMock()
        mock_template.template_content = 'Test: {{ raw_text }}'
        mock_template_query.select_related().filter().first.return_value = mock_template

        # 获取初始阶段
        stage = ProjectStage.objects.get(
            project=project_with_stages,
            stage_type='rewrite'
        )
        assert stage.status == 'pending'

        # 执行流式处理
        list(processor.process_stream(
            project_id=str(project_with_stages.id),
            input_data={}
        ))

        # 刷新并验证状态
        stage.refresh_from_db()
        assert stage.status == 'completed'
        assert stage.completed_at is not None
        assert stage.output_data is not None

    @patch('core.ai_client.factory.create_ai_client')
    @patch('apps.content.processors.llm_stage.PromptTemplate.objects')
    def test_process_stream_handles_error(
        self,
        mock_template_query,
        mock_create_client,
        processor,
        project_with_stages
    ):
        """测试process_stream错误处理"""
        # Mock AI客户端抛出异常
        mock_client = MagicMock()
        mock_client.generate_stream.side_effect = Exception("AI API error")
        mock_create_client.return_value = mock_client

        # Mock 提示词模板
        mock_template = MagicMock()
        mock_template.template_content = 'Test: {{ raw_text }}'
        mock_template_query.select_related().filter().first.return_value = mock_template

        # 执行流式处理
        chunks = list(processor.process_stream(
            project_id=str(project_with_stages.id),
            input_data={}
        ))

        # 应该yield error消息
        error_chunks = [c for c in chunks if c['type'] == 'error']
        assert len(error_chunks) == 1
        assert 'AI API error' in error_chunks[0]['error']

        # 验证阶段状态更新为failed
        stage = ProjectStage.objects.get(
            project=project_with_stages,
            stage_type='rewrite'
        )
        assert stage.status == 'failed'
        assert 'AI API error' in stage.error_message


@pytest.mark.unit
class TestLLMStageProcessorOnFailure:
    """测试on_failure方法"""

    @pytest.fixture
    def processor(self):
        """创建处理器实例"""
        return LLMStageProcessor(stage_type='rewrite')

    @pytest.fixture
    def project_with_stage(self, db):
        """创建带有阶段的项目"""
        from django.contrib.auth import get_user_model
        User = get_user_model()

        user = User.objects.create_user(
            username='testuser',
            email='test@example.com'
        )

        project = Project.objects.create(
            name='测试项目',
            description='测试描述',
            original_topic='原始主题',
            user=user
        )

        stage = ProjectStage.objects.create(
            project=project,
            stage_type='rewrite',
            status='processing'
        )
        return project

    def test_on_failure_updates_stage_status(self, processor, project_with_stage):
        """测试on_failure更新阶段状态为failed"""
        context = PipelineContext(project_id=str(project_with_stage.id))
        error = Exception("Test error")

        # 调用on_failure
        processor.on_failure(context, error)

        # 验证状态
        stage = ProjectStage.objects.get(
            project=project_with_stage,
            stage_type='rewrite'
        )
        assert stage.status == 'failed'
        assert 'Test error' in stage.error_message


@pytest.mark.unit
class TestLLMStageProcessorHelperMethods:
    """测试辅助方法"""

    @pytest.fixture
    def processor(self):
        """创建处理器实例"""
        return LLMStageProcessor(stage_type='rewrite')

    @pytest.fixture
    def project_with_templates(self, db):
        """创建带有提示词模板的项目"""
        from django.contrib.auth import get_user_model
        from apps.prompts.models import PromptTemplateSet, PromptTemplate
        from apps.models.models import ModelProvider

        User = get_user_model()

        # 创建用户
        user = User.objects.create_user(
            username='testuser2',
            email='test2@example.com'
        )

        # 创建模型提供商
        provider = ModelProvider.objects.create(
            name='Test Provider 2',
            provider_type='llm',
            api_url='https://api.test.com',
            api_key='test-key',
            model_name='test-model',
            is_active=True
        )

        # 创建提示词集
        template_set = PromptTemplateSet.objects.create(
            name='Test Set 2',
            is_default=True,
            created_by=user  # 添加必需的用户
        )

        # 创建提示词模板
        template = PromptTemplate.objects.create(
            template_set=template_set,
            stage_type='rewrite',
            template_content='Test prompt: {{ raw_text }}',
            model_provider=provider,
            is_active=True
        )

        # 创建项目
        project = Project.objects.create(
            name='测试项目2',
            description='测试描述2',
            original_topic='原始主题',
            user=user,
            prompt_template_set=template_set
        )

        return project

    @patch('core.ai_client.factory.create_ai_client')
    def test_get_ai_client_from_template(
        self,
        mock_create_client,
        processor,
        project_with_templates
    ):
        """测试从提示词模板获取AI客户端"""
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        # 调用方法
        client = processor._get_ai_client(project_with_templates)

        # 验证
        assert client is not None
        mock_create_client.assert_called_once()

    def test_build_prompt_renders_template(self, processor, project_with_templates):
        """测试_build_prompt渲染Jinja2模板"""
        input_data = {'raw_text': 'Test input'}

        # 调用方法
        prompt = processor._build_prompt(project_with_templates, input_data)

        # 验证
        assert 'Test input' in prompt
        assert 'Test prompt:' in prompt

    @patch('apps.content.processors.llm_stage.parse_storyboard_json')
    def test_save_result_for_rewrite(
        self,
        mock_parse,
        processor,
        project_with_templates
    ):
        """测试保存rewrite阶段结果"""
        from apps.projects.models import ProjectStage

        # 创建阶段
        stage = ProjectStage.objects.create(
            project=project_with_templates,
            stage_type='rewrite'
        )

        # 调用方法
        result = processor._save_result(
            project=project_with_templates,
            stage=stage,
            generated_text='Generated content',
            prompt_used='Test prompt',
            metadata={}
        )

        # 验证返回值
        assert result['raw_text'] == 'Generated content'
        assert result['human_text'] == ''

    @patch('apps.content.processors.llm_stage.parse_storyboard_json')
    def test_save_result_for_storyboard(
        self,
        mock_parse,
        project_with_templates
    ):
        """测试保存storyboard阶段结果"""
        from apps.projects.models import ProjectStage

        mock_parse.return_value = {'scenes': []}

        # 切换到storyboard处理器
        processor = LLMStageProcessor(stage_type='storyboard')

        # 创建阶段
        stage = ProjectStage.objects.create(
            project=project_with_templates,
            stage_type='storyboard'
        )

        # 调用方法
        result = processor._save_result(
            project=project_with_templates,
            stage=stage,
            generated_text='Generated storyboard',
            prompt_used='Test prompt',
            metadata={}
        )

        # 验证
        assert result['human_text'] == {'scenes': []}
        assert result['raw_text'] == 'Generated storyboard'
        mock_parse.assert_called_once_with('Generated storyboard')

    def test_get_max_tokens(self):
        """测试获取最大token数"""
        # Test rewrite
        processor_rewrite = LLMStageProcessor(stage_type='rewrite')
        assert processor_rewrite._get_max_tokens() == 2000

        # Test storyboard
        processor_storyboard = LLMStageProcessor(stage_type='storyboard')
        assert processor_storyboard._get_max_tokens() == 4000

        # Test camera_movement
        processor_camera = LLMStageProcessor(stage_type='camera_movement')
        assert processor_camera._get_max_tokens() == 1000

        # Test unknown stage type (defaults to 2000)
        processor_unknown = LLMStageProcessor(stage_type='unknown')
        assert processor_unknown._get_max_tokens() == 2000
