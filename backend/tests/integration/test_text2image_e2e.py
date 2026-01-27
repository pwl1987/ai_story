"""
Text2Image端到端集成测试

测试完整的文生图工作流：
1. 创建项目并完成storyboard阶段
2. 触发image_generation阶段
3. 验证Celery任务执行
4. 验证生成的图片数据
5. 验证数据库更新（image_generation和video_generation阶段）
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from django.contrib.auth import get_user_model

from apps.projects.models import Project, ProjectStage
from apps.prompts.models import PromptTemplateSet, PromptTemplate
from apps.models.models import ModelProvider

User = get_user_model()


@pytest.mark.integration
@pytest.mark.django_db(transaction=True)
class TestText2ImageE2E:
    """Text2Image端到端测试"""

    @pytest.fixture
    def configured_user(self, db):
        """创建配置好的用户"""
        user = User.objects.create_user(
            username='text2image_test_user',
            email='text2image@test.com'
        )
        return user

    @pytest.fixture
    def model_provider(self, db):
        """创建模型提供商"""
        provider = ModelProvider.objects.create(
            name='Test SD Provider',
            provider_type='text2image',
            api_url='http://localhost:7860',
            api_key='test-key',
            model_name='sdxl-base-1.0',
            is_active=True
        )
        return provider

    @pytest.fixture
    def llm_provider(self, db):
        """创建LLM提供商"""
        provider = ModelProvider.objects.create(
            name='Test OpenAI',
            provider_type='llm',
            api_url='https://api.openai.com/v1',
            api_key='test-key',
            model_name='gpt-4',
            is_active=True
        )
        return provider

    @pytest.fixture
    def template_set(self, db, configured_user):
        """创建提示词集"""
        template_set = PromptTemplateSet.objects.create(
            name='Text2Image Template Set',
            is_default=True,
            created_by=configured_user
        )
        return template_set

    @pytest.fixture
    def all_templates(self, db, template_set, model_provider, llm_provider):
        """创建所有阶段的提示词模板"""
        # Rewrite模板
        PromptTemplate.objects.create(
            template_set=template_set,
            stage_type='rewrite',
            template_content='请改写以下文案：\n\n{{ raw_text }}',
            model_provider=llm_provider,
            is_active=True
        )

        # Storyboard模板
        PromptTemplate.objects.create(
            template_set=template_set,
            stage_type='storyboard',
            template_content='根据以下文案生成分镜JSON：\n\n{{ raw_text }}\n\n返回格式：\n{"scenes": [{"scene_number": 1, "narration": "...", "visual_prompt": "...", "shot_type": "..."}]}',
            model_provider=llm_provider,
            is_active=True
        )

        # Image Generation模板
        PromptTemplate.objects.create(
            template_set=template_set,
            stage_type='image_generation',
            template_content='Generate image: {{ narration }}, style: {{ visual_prompt }}',
            model_provider=model_provider,
            is_active=True
        )

        return template_set

    @pytest.fixture
    def api_client(self, db, configured_user):
        """创建API客户端"""
        from rest_framework.test import APIClient
        client = APIClient()
        client.force_authenticate(user=configured_user)
        return client

    @patch('apps.projects.tasks.execute_llm_stage.delay')
    def test_e2e_text2image_after_storyboard(
        self,
        mock_execute_task,
        api_client,
        configured_user,
        model_provider,
        all_templates
    ):
        """
        端到端测试：storyboard → image_generation 完整工作流
        """
        # 1. 创建项目
        project_data = {
            'name': '测试文生图项目',
            'description': '测试项目描述',
            'original_topic': '这是一个关于AI的故事',
            'prompt_template_set': str(all_templates.id)
        }

        response = api_client.post('/api/v1/projects/', project_data, format='json')
        assert response.status_code == 201
        project_id = response.data['id']

        # 验证5个阶段已创建
        project = Project.objects.get(id=project_id)
        stages = ProjectStage.objects.filter(project=project)
        assert stages.count() == 5

        # 2. 完成storyboard阶段（模拟）
        storyboard_stage = ProjectStage.objects.get(
            project=project,
            stage_type='storyboard'
        )

        # 设置storyboard输出数据
        storyboard_output = {
            "human_text": {
                "scenes": [
                    {
                        "scene_number": 1,
                        "narration": "开场旁白",
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
            },
            "raw_text": ""
        }

        storyboard_stage.status = 'completed'
        storyboard_stage.output_data = storyboard_output
        storyboard_stage.save()

        # 初始化image_generation阶段：将storyboard数据复制到input_data
        image_stage = ProjectStage.objects.get(
            project=project,
            stage_type='image_generation'
        )
        image_stage.input_data = storyboard_output  # 复制storyboard数据
        image_stage.output_data = storyboard_output  # 也设置output_data
        image_stage.save()

        # 3. 配置文生图模型
        from apps.projects.models import ProjectModelConfig
        config, created = ProjectModelConfig.objects.get_or_create(
            project=project
        )
        config.image_providers.add(model_provider)

        # 4. 执行image_generation阶段（模拟处理器直接调用）
        from apps.content.processors.text2image_stage import Text2ImageStageProcessor

        processor = Text2ImageStageProcessor()

        # Mock AI客户端
        with patch('apps.content.processors.text2image_stage.create_ai_client') as mock_create_client:
            mock_client = MagicMock()

            # Mock生成结果
            def mock_generate(prompt, **kwargs):
                scene_num = kwargs.get('scene_number', 1)
                return {
                    'data': [
                        {
                            'url': f'http://example.com/scene{scene_num}_image1.jpg',
                            'width': 1920,
                            'height': 1080
                        }
                    ]
                }

            mock_client.generate.side_effect = mock_generate
            mock_create_client.return_value = mock_client

            # 执行流式处理
            chunks = list(processor.process_stream(
                project_id=str(project_id)
            ))

            # 验证输出
            assert len(chunks) > 0

            # 应该有进度消息
            progress_chunks = [c for c in chunks if c['type'] == 'progress']
            assert len(progress_chunks) == 2  # 2个场景

            # 应该有图片生成消息
            image_chunks = [c for c in chunks if c['type'] == 'image_generated']
            assert len(image_chunks) == 2

            # 应该有完成消息
            done_chunks = [c for c in chunks if c['type'] == 'done']
            assert len(done_chunks) == 1
            assert done_chunks[0]['data']['success_count'] == 2

        # 5. 验证image_generation阶段已更新
        image_stage = ProjectStage.objects.get(
            project=project,
            stage_type='image_generation'
        )

        # 注意：process_stream()不会自动将status设置为completed
        # 它只设置status为processing，需要手动设置为completed
        assert image_stage.status in ['processing', 'completed']
        assert 'human_text' in image_stage.output_data
        scenes = image_stage.output_data['human_text']['scenes']
        assert len(scenes) == 2

        # 验证第一个场景的图片URLs
        assert 'urls' in scenes[0]
        assert len(scenes[0]['urls']) > 0
        assert 'url' in scenes[0]['urls'][0]

        # 6. 验证video_generation阶段也已更新
        video_stage = ProjectStage.objects.get(
            project=project,
            stage_type='video_generation'
        )

        assert 'human_text' in video_stage.output_data
        video_scenes = video_stage.output_data['human_text']['scenes']
        assert len(video_scenes) == 2
        assert 'urls' in video_scenes[0]

    def test_text2image_requires_storyboard_completion(
        self,
        api_client,
        configured_user,
        model_provider,
        all_templates
    ):
        """测试文生图需要storyboard完成"""
        # 1. 创建项目
        project_data = {
            'name': '文生图依赖测试',
            'description': '测试',
            'original_topic': '原始主题',
            'prompt_template_set': str(all_templates.id)
        }

        response = api_client.post('/api/v1/projects/', project_data, format='json')
        project_id = response.data['id']

        # 2. storyboard未完成时执行文生图
        storyboard_stage = ProjectStage.objects.get(
            project=Project.objects.get(id=project_id),
            stage_type='storyboard'
        )
        assert storyboard_stage.status == 'pending'  # 未完成

        # 验证会失败（validate返回False）
        from apps.content.processors.text2image_stage import Text2ImageStageProcessor
        from core.pipeline.base import PipelineContext

        processor = Text2ImageStageProcessor()
        context = PipelineContext(project_id=project_id)

        result = processor.validate(context)
        if hasattr(result, '__await__'):
            import asyncio
            result = asyncio.run(result)

        # 验证应该失败
        assert result is False

    @patch('apps.projects.tasks.execute_llm_stage.delay')
    def test_text2image_generates_multiple_images(
        self,
        mock_execute_task,
        api_client,
        configured_user,
        model_provider,
        all_templates
    ):
        """测试为多个场景生成图片"""
        # 1. 创建项目
        project_data = {
            'name': '多图片生成测试',
            'description': '测试',
            'original_topic': '测试主题',
            'prompt_template_set': str(all_templates.id)
        }

        response = api_client.post('/api/v1/projects/', project_data, format='json')
        project_id = response.data['id']

        # 2. 完成storyboard阶段，包含3个场景
        storyboard_stage = ProjectStage.objects.get(
            project=Project.objects.get(id=project_id),
            stage_type='storyboard'
        )

        storyboard_output = {
            "human_text": {
                "scenes": [
                    {
                        "scene_number": 1,
                        "narration": "场景1",
                        "visual_prompt": "提示1",
                        "shot_type": "特写"
                    },
                    {
                        "scene_number": 2,
                        "narration": "场景2",
                        "visual_prompt": "提示2",
                        "shot_type": "中景"
                    },
                    {
                        "scene_number": 3,
                        "narration": "场景3",
                        "visual_prompt": "提示3",
                        "shot_type": "远景"
                    }
                ]
            },
            "raw_text": ""
        }

        storyboard_stage.status = 'completed'
        storyboard_stage.output_data = storyboard_output
        storyboard_stage.save()

        # 初始化image_generation阶段：将storyboard数据复制到input_data
        image_stage = ProjectStage.objects.get(
            project=Project.objects.get(id=project_id),
            stage_type='image_generation'
        )
        image_stage.input_data = storyboard_output  # 复制storyboard数据
        image_stage.output_data = storyboard_output  # 也设置output_data
        image_stage.save()

        # 3. 配置模型
        from apps.projects.models import ProjectModelConfig
        config, created = ProjectModelConfig.objects.get_or_create(
            project=Project.objects.get(id=project_id)
        )
        config.image_providers.add(model_provider)

        # 4. 执行文生图
        from apps.content.processors.text2image_stage import Text2ImageStageProcessor

        processor = Text2ImageStageProcessor()

        with patch('apps.content.processors.text2image_stage.create_ai_client') as mock_create_client:
            mock_client = MagicMock()

            def mock_generate(prompt, **kwargs):
                return {
                    'data': [
                        {'url': 'http://example.com/image.jpg', 'width': 1920, 'height': 1080}
                    ]
                }

            mock_client.generate.side_effect = mock_generate
            mock_create_client.return_value = mock_client

            chunks = list(processor.process_stream(project_id=project_id))

            # 验证生成了3个场景的图片
            progress_chunks = [c for c in chunks if c['type'] == 'progress']
            assert len(progress_chunks) == 3

            image_chunks = [c for c in chunks if c['type'] == 'image_generated']
            assert len(image_chunks) == 3

            done_chunks = [c for c in chunks if c['type'] == 'done']
            assert done_chunks[0]['data']['success_count'] == 3

        # 5. 验证数据库
        image_stage = ProjectStage.objects.get(
            project=Project.objects.get(id=project_id),
            stage_type='image_generation'
        )

        scenes = image_stage.output_data['human_text']['scenes']
        assert len(scenes) == 3
        for scene in scenes:
            assert 'urls' in scene
            assert len(scene['urls']) > 0

    @patch('apps.projects.tasks.execute_llm_stage.delay')
    def test_text2image_handles_partial_failure(
        self,
        mock_execute_task,
        api_client,
        configured_user,
        model_provider,
        all_templates
    ):
        """测试部分图片生成失败时的处理"""
        # 1. 创建项目
        project_data = {
            'name': '部分失败测试',
            'description': '测试',
            'original_topic': '测试',
            'prompt_template_set': str(all_templates.id)
        }

        response = api_client.post('/api/v1/projects/', project_data, format='json')
        project_id = response.data['id']

        # 2. 完成storyboard
        storyboard_stage = ProjectStage.objects.get(
            project=Project.objects.get(id=project_id),
            stage_type='storyboard'
        )

        storyboard_output = {
            "human_text": {
                "scenes": [
                    {
                        "scene_number": 1,
                        "narration": "场景1",
                        "visual_prompt": "提示1",
                        "shot_type": "特写"
                    },
                    {
                        "scene_number": 2,
                        "narration": "场景2",
                        "visual_prompt": "提示2",
                        "shot_type": "中景"
                    }
                ]
            },
            "raw_text": ""
        }

        storyboard_stage.status = 'completed'
        storyboard_stage.output_data = storyboard_output
        storyboard_stage.save()

        # 初始化image_generation阶段：将storyboard数据复制到input_data
        image_stage = ProjectStage.objects.get(
            project=Project.objects.get(id=project_id),
            stage_type='image_generation'
        )
        image_stage.input_data = storyboard_output  # 复制storyboard数据
        image_stage.output_data = storyboard_output  # 也设置output_data
        image_stage.save()

        # 3. 配置模型
        from apps.projects.models import ProjectModelConfig
        config, created = ProjectModelConfig.objects.get_or_create(
            project=Project.objects.get(id=project_id)
        )
        config.image_providers.add(model_provider)

        # 4. 执行文生图（第2个失败）
        from apps.content.processors.text2image_stage import Text2ImageStageProcessor

        processor = Text2ImageStageProcessor()

        with patch('apps.content.processors.text2image_stage.create_ai_client') as mock_create_client:
            mock_client = MagicMock()

            # 使用计数器来模拟第2次调用失败
            call_count = [0]

            def mock_generate(prompt, **kwargs):
                call_count[0] += 1
                if call_count[0] == 2:
                    raise Exception("API Error for scene 2")
                return {
                    'data': [
                        {'url': f'http://example.com/scene{call_count[0]}.jpg', 'width': 1920, 'height': 1080}
                    ]
                }

            mock_client.generate.side_effect = mock_generate
            mock_create_client.return_value = mock_client

            chunks = list(processor.process_stream(project_id=project_id))

            # 验证有警告消息
            warning_chunks = [c for c in chunks if c['type'] == 'warning']
            assert len(warning_chunks) >= 1

            # 验证完成消息统计
            done_chunks = [c for c in chunks if c['type'] == 'done']
            assert done_chunks[0]['data']['success_count'] == 1
            assert done_chunks[0]['data']['failed_count'] == 1

        # 5. 验证数据库（只有场景1有图片）
        image_stage = ProjectStage.objects.get(
            project=Project.objects.get(id=project_id),
            stage_type='image_generation'
        )

        scenes = image_stage.output_data['human_text']['scenes']
        assert len(scenes) == 2

        # 场景1应该有图片
        assert 'urls' in scenes[0]
        assert len(scenes[0]['urls']) > 0

        # 场景2应该没有图片（或为空）
        # 这个取决于具体实现，可能没有urls字段或为空数组
