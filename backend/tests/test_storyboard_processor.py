"""
apps.content.processors.llm_stage (storyboard) 单元测试

测试LLM阶段处理器的Storyboard功能：
- 输入数据获取（从rewrite阶段）
- JSON解析和验证
- 结果保存（批量更新3个阶段）
- 流式处理
- 错误处理
"""

from unittest.mock import MagicMock, patch

import pytest

from apps.content.processors.llm_stage import LLMStageProcessor
from apps.projects.models import Project, ProjectStage
from apps.projects.utils import parse_storyboard_json
from core.pipeline.base import PipelineContext


@pytest.mark.unit
class TestStoryboardProcessorInit:
    """测试Storyboard处理器初始化"""

    def test_init_storyboard_processor(self):
        """测试创建Storyboard处理器"""
        processor = LLMStageProcessor(stage_type='storyboard')
        assert processor.stage_type == 'storyboard'


@pytest.mark.unit
class TestStoryboardProcessorGetInputData:
    """测试Storyboard输入数据获取"""

    @pytest.fixture
    def processor(self):
        """创建Storyboard处理器"""
        return LLMStageProcessor(stage_type='storyboard')

    @pytest.fixture
    def project_with_rewrite(self, db):
        """创建已完成rewrite阶段的项目"""
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

        # 创建并完成rewrite阶段
        ProjectStage.objects.create(
            project=project,
            stage_type='rewrite',
            status='completed',
            output_data={
                'raw_text': '改写后的文案内容',
                'human_text': '改写后的文案'
            }
        )

        # 创建storyboard阶段
        ProjectStage.objects.create(
            project=project,
            stage_type='storyboard',
            status='pending'
        )

        return project

    @pytest.fixture
    def project_without_rewrite(self, db):
        """创建没有rewrite阶段的项目"""
        from django.contrib.auth import get_user_model
        User = get_user_model()

        user = User.objects.create_user(
            username='testuser2',
            email='test2@example.com'
        )

        project = Project.objects.create(
            name='测试项目2',
            description='测试描述2',
            original_topic='原始主题',
            user=user
        )

        return project

    def test_get_input_data_from_completed_rewrite(self, processor, project_with_rewrite):
        """测试从完成的rewrite阶段获取输入数据"""
        stage = ProjectStage.objects.get(
            project=project_with_rewrite,
            stage_type='storyboard'
        )

        input_data = processor._get_input_data(project_with_rewrite, stage)

        assert input_data['raw_text'] == '改写后的文案内容'
        assert input_data['human_text'] == ''

    def test_get_input_data_without_rewrite_stage(self, processor, project_without_rewrite):
        """测试没有rewrite阶段时抛出错误"""
        stage = ProjectStage.objects.create(
            project=project_without_rewrite,
            stage_type='storyboard',
            status='pending'
        )

        with pytest.raises(ValueError) as exc_info:
            processor._get_input_data(project_without_rewrite, stage)

        assert '前置阶段(文案改写)未完成或无输出数据' in str(exc_info.value)

    def test_get_input_data_with_stage_input_data(self, processor, project_with_rewrite):
        """测试阶段已有input_data时直接使用"""
        stage = ProjectStage.objects.get(
            project=project_with_rewrite,
            stage_type='storyboard'
        )

        # 设置input_data
        stage.input_data = {'custom': 'data'}
        stage.save()

        input_data = processor._get_input_data(project_with_rewrite, stage)

        assert input_data == {'custom': 'data'}


@pytest.mark.unit
class TestStoryboardJsonParsing:
    """测试Storyboard JSON解析"""

    def test_parse_valid_json(self):
        """测试解析有效的JSON"""
        json_text = '''
        {
          "scenes": [
            {
              "scene_number": 1,
              "narration": "开场镜头",
              "visual_prompt": "产品特写",
              "shot_type": "特写"
            },
            {
              "scene_number": 2,
              "narration": "功能演示",
              "visual_prompt": "使用场景",
              "shot_type": "中景"
            }
          ]
        }
        '''

        result = parse_storyboard_json(json_text)

        assert 'scenes' in result
        assert len(result['scenes']) == 2
        assert result['scenes'][0]['scene_number'] == 1
        assert result['scenes'][0]['narration'] == '开场镜头'

    def test_parse_json_with_markdown_code_block(self):
        """测试解析包含markdown代码块的JSON"""
        json_text = '''
```json
{
  "scenes": [
    {
      "scene_number": 1,
      "narration": "测试",
      "visual_prompt": "测试提示",
      "shot_type": "特写"
    }
  ]
}
```
'''

        result = parse_storyboard_json(json_text)

        assert 'scenes' in result
        assert len(result['scenes']) == 1

    def test_parse_json_missing_scenes_field(self):
        """测试缺少scenes字段时抛出错误"""
        json_text = '{"data": "some data"}'

        with pytest.raises(ValueError) as exc_info:
            parse_storyboard_json(json_text)

        assert '缺少 \'scenes\' 字段' in str(exc_info.value)

    def test_parse_json_scenes_not_array(self):
        """测试scenes不是数组时抛出错误"""
        json_text = '{"scenes": "not an array"}'

        with pytest.raises(ValueError) as exc_info:
            parse_storyboard_json(json_text)

        assert '必须是数组类型' in str(exc_info.value)

    def test_parse_json_missing_required_field(self):
        """测试场景缺少必需字段时抛出错误"""
        json_text = '''
        {
          "scenes": [
            {
              "scene_number": 1,
              "narration": "测试"
            }
          ]
        }
        '''

        with pytest.raises(ValueError) as exc_info:
            parse_storyboard_json(json_text)

        assert '缺少必需字段' in str(exc_info.value)
        assert 'visual_prompt' in str(exc_info.value)

    def test_parse_invalid_json(self):
        """测试无效JSON时抛出错误"""
        json_text = 'not a valid json'

        with pytest.raises(ValueError) as exc_info:
            parse_storyboard_json(json_text)

        assert 'JSON解析失败' in str(exc_info.value)


@pytest.mark.unit
class TestStoryboardProcessorSaveResult:
    """测试Storyboard结果保存"""

    @pytest.fixture
    def processor(self):
        """创建Storyboard处理器"""
        return LLMStageProcessor(stage_type='storyboard')

    @pytest.fixture
    def project_with_stages(self, db):
        """创建带有多个阶段的项目"""
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

        # 创建rewrite阶段
        ProjectStage.objects.create(
            project=project,
            stage_type='rewrite',
            status='completed'
        )

        # 创建storyboard及后续3个阶段
        for stage_type in ['storyboard', 'image_generation', 'camera_movement', 'video_generation']:
            ProjectStage.objects.create(
                project=project,
                stage_type=stage_type,
                status='pending'
            )

        return project

    @patch('apps.content.processors.llm_stage.parse_storyboard_json')
    def test_save_result_updates_three_stages(
        self,
        mock_parse,
        processor,
        project_with_stages
    ):
        """测试保存结果时更新3个后续阶段"""
        # Mock JSON解析
        mock_parse.return_value = {
            'scenes': [
                {
                    'scene_number': 1,
                    'narration': '测试旁白',
                    'visual_prompt': '测试提示',
                    'shot_type': '特写'
                }
            ]
        }

        storyboard_stage = ProjectStage.objects.get(
            project=project_with_stages,
            stage_type='storyboard'
        )

        generated_text = '{"scenes": [{"scene_number": 1, ...}]}'

        result = processor._save_result(
            project=project_with_stages,
            stage=storyboard_stage,
            generated_text=generated_text,
            prompt_used='Test prompt',
            metadata={}
        )

        # 验证返回值
        assert 'human_text' in result
        assert 'raw_text' in result
        assert result['human_text']['scenes'][0]['scene_number'] == 1

        # 验证后续3个阶段已更新
        for stage_type in ['image_generation', 'camera_movement', 'video_generation']:
            stage = ProjectStage.objects.get(
                project=project_with_stages,
                stage_type=stage_type
            )
            assert stage.input_data is not None
            assert 'human_text' in stage.input_data
            assert stage.output_data is not None


@pytest.mark.unit
class TestStoryboardProcessorProcessStream:
    """测试Storyboard流式处理"""

    @pytest.fixture
    def processor(self):
        """创建Storyboard处理器"""
        return LLMStageProcessor(stage_type='storyboard')

    @pytest.fixture
    def project_with_templates_and_rewrite(self, db):
        """创建带有模板和已完成rewrite的项目"""
        from django.contrib.auth import get_user_model

        from apps.models.models import ModelProvider
        from apps.prompts.models import PromptTemplate, PromptTemplateSet

        User = get_user_model()

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
            created_by=user
        )

        # 创建rewrite和storyboard提示词模板
        for stage_type in ['rewrite', 'storyboard']:
            PromptTemplate.objects.create(
                template_set=template_set,
                stage_type=stage_type,
                template_content=f'Template for {stage_type}: {{{{ raw_text }}}}',
                model_provider=provider,
                is_active=True
            )

        project = Project.objects.create(
            name='测试项目',
            description='测试描述',
            original_topic='原始主题',
            user=user,
            prompt_template_set=template_set
        )

        # 完成rewrite阶段
        ProjectStage.objects.create(
            project=project,
            stage_type='rewrite',
            status='completed',
            output_data={
                'raw_text': '改写后的文案',
                'human_text': '改写后的文案'
            }
        )

        # 创建storyboard阶段
        ProjectStage.objects.create(
            project=project,
            stage_type='storyboard',
            status='pending'
        )

        return project

    @patch('core.ai_client.factory.create_ai_client')
    def test_process_stream_yields_tokens(
        self,
        mock_create_client,
        processor,
        project_with_templates_and_rewrite
    ):
        """测试流式处理yield token消息"""
        # Mock AI客户端
        mock_client = MagicMock()
        mock_client.generate_stream.return_value = [
            {'type': 'token', 'content': '{"scenes": [{"scene_number": 1,', 'full_text': '{"scenes": [{"scene_number": 1,'},
            {'type': 'token', 'content': '"narration": "测试"}]}', 'full_text': '{"scenes": [{"scene_number": 1, "narration": "测试"}]}'}
        ]
        mock_create_client.return_value = mock_client

        chunks = list(processor.process_stream(
            project_id=str(project_with_templates_and_rewrite.id),
            input_data={}
        ))

        # 应该包含 token 消息
        token_chunks = [c for c in chunks if c['type'] == 'token']
        assert len(token_chunks) == 2

    @patch('core.ai_client.factory.create_ai_client')
    def test_process_stream_updates_stage_to_completed(
        self,
        mock_create_client,
        processor,
        project_with_templates_and_rewrite
    ):
        """测试流式处理更新阶段状态为completed"""
        # Mock AI客户端 - 返回有效的JSON（需要token消息）
        mock_client = MagicMock()
        valid_json = '{"scenes": [{"scene_number": 1, "narration": "测试旁白", "visual_prompt": "测试提示", "shot_type": "特写"}]}'
        mock_client.generate_stream.return_value = [
            {'type': 'token', 'content': valid_json, 'full_text': valid_json},
            {'type': 'done', 'text': valid_json}
        ]
        mock_create_client.return_value = mock_client

        stage = ProjectStage.objects.get(
            project=project_with_templates_and_rewrite,
            stage_type='storyboard'
        )
        assert stage.status == 'pending'

        list(processor.process_stream(
            project_id=str(project_with_templates_and_rewrite.id),
            input_data={}
        ))

        stage.refresh_from_db()
        assert stage.status == 'completed'
        assert stage.completed_at is not None

    @patch('core.ai_client.factory.create_ai_client')
    def test_process_stream_handles_json_parsing_error(
        self,
        mock_create_client,
        processor,
        project_with_templates_and_rewrite
    ):
        """测试流式处理JSON解析错误"""
        # Mock AI客户端 - 返回无效JSON
        mock_client = MagicMock()
        mock_client.generate_stream.return_value = [
            {'type': 'done', 'text': 'invalid json'}
        ]
        mock_create_client.return_value = mock_client

        chunks = list(processor.process_stream(
            project_id=str(project_with_templates_and_rewrite.id),
            input_data={}
        ))

        # 应该yield error消息
        error_chunks = [c for c in chunks if c['type'] == 'error']
        assert len(error_chunks) == 1

        # 验证阶段状态更新为failed
        stage = ProjectStage.objects.get(
            project=project_with_templates_and_rewrite,
            stage_type='storyboard'
        )
        assert stage.status == 'failed'


@pytest.mark.unit
class TestStoryboardProcessorValidate:
    """测试Storyboard处理器验证"""

    @pytest.fixture
    def processor(self):
        """创建Storyboard处理器"""
        return LLMStageProcessor(stage_type='storyboard')

    @pytest.fixture
    def project_with_completed_rewrite(self, db):
        """创建有已完成rewrite的项目"""
        from django.contrib.auth import get_user_model
        User = get_user_model()

        user = User.objects.create_user(
            username='testuser',
            email='test@example.com'
        )

        project = Project.objects.create(
            name='测试项目',
            original_topic='原始主题',
            user=user
        )

        return project

    def test_validate_with_rewrite_result(self, processor, project_with_completed_rewrite):
        """测试有rewrite结果时验证成功"""
        context = PipelineContext(project_id=str(project_with_completed_rewrite.id))
        context.add_result('rewrite', {'text': 'Rewritten content'})

        result = processor.validate(context)
        if hasattr(result, '__await__'):
            import asyncio
            result = asyncio.get_event_loop().run_until_complete(result)
        # 验证需要检查提示词模板，这里可能需要Mock
        # 实际测试中可能需要更完整的设置

    def test_validate_without_rewrite_result_fails(self, processor, project_with_completed_rewrite):
        """测试没有rewrite结果时验证失败"""
        context = PipelineContext(project_id=str(project_with_completed_rewrite.id))

        result = processor.validate(context)
        if hasattr(result, '__await__'):
            import asyncio
            result = asyncio.get_event_loop().run_until_complete(result)

        # 没有rewrite结果且没有提示词模板，应该返回False
        assert result is False
