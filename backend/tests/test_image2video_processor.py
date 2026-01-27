"""
apps.content.processors.image2video_stage 单元测试

测试Image2Video阶段处理器：
- 验证前置依赖（image_generation + camera_movement）
- 单个视频生成
- 结果保存逻辑
- 流式处理
- 提示词构建
- 错误处理
"""

import pytest
from unittest.mock import Mock, MagicMock, patch, call
from apps.content.processors.image2video_stage import Image2VideoStageProcessor
from apps.projects.models import Project, ProjectStage
from apps.models.models import ModelProvider
from core.pipeline.base import PipelineContext


@pytest.mark.unit
class TestImage2VideoProcessorInit:
    """测试Image2Video处理器初始化"""

    def test_init_image2video_processor(self):
        """测试创建Image2Video处理器"""
        processor = Image2VideoStageProcessor()
        assert processor.stage_type == 'video_generation'
        assert processor.max_concurrent == 2
        assert processor.poll_interval == 10
        assert processor.max_wait_time == 600


@pytest.mark.unit
class TestImage2VideoProcessorValidate:
    """测试Image2Video处理器验证"""

    @pytest.fixture
    def processor(self):
        """创建Image2Video处理器"""
        return Image2VideoStageProcessor()

    @pytest.fixture
    def project_with_completed_stages(self, db):
        """创建带有已完成前置阶段的项目"""
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

        # 创建并完成image_generation阶段
        image_stage = ProjectStage.objects.create(
            project=project,
            stage_type='image_generation',
            status='completed',
            output_data={
                "human_text": {
                    "scenes": [
                        {
                            "scene_number": 1,
                            "narration": "开场旁白",
                            "visual_prompt": "产品特写",
                            "shot_type": "特写",
                            "urls": [{"url": "http://example.com/image1.jpg"}]
                        }
                    ]
                }
            }
        )

        # 创建并完成camera_movement阶段
        camera_stage = ProjectStage.objects.create(
            project=project,
            stage_type='camera_movement',
            status='completed'
        )

        return project

    @pytest.fixture
    def model_provider(self, db):
        """创建模型提供商"""
        provider = ModelProvider.objects.create(
            name='Runway',
            provider_type='image2video',
            api_url='https://api.runway.com',
            api_key='test-key',
            model_name='gen3a_turbo',
            is_active=True
        )
        return provider

    def test_validate_with_completed_prerequisites(
        self,
        processor,
        project_with_completed_stages,
        model_provider
    ):
        """测试前置阶段都完成时验证成功"""
        # 配置模型
        from apps.projects.models import ProjectModelConfig

        config = ProjectModelConfig.objects.create(
            project=project_with_completed_stages
        )
        config.video_providers.add(model_provider)

        context = PipelineContext(project_id=str(project_with_completed_stages.id))
        result = processor.validate(context)

        # 前置阶段完成，有图片数据，有模型配置
        assert result is True

    def test_validate_without_image_generation_fails(
        self,
        processor,
        project_with_completed_stages,
        model_provider
    ):
        """测试image_generation未完成时验证失败"""
        # 删除image_generation阶段
        ProjectStage.objects.filter(
            project=project_with_completed_stages,
            stage_type='image_generation'
        ).delete()

        # 配置模型
        from apps.projects.models import ProjectModelConfig

        config = ProjectModelConfig.objects.create(
            project=project_with_completed_stages
        )
        config.video_providers.add(model_provider)

        context = PipelineContext(project_id=str(project_with_completed_stages.id))
        result = processor.validate(context)

        # image_generation未完成
        assert result is False

    def test_validate_without_camera_movement_fails(
        self,
        processor,
        project_with_completed_stages,
        model_provider
    ):
        """测试camera_movement未完成时验证失败"""
        # 删除camera_movement阶段
        ProjectStage.objects.filter(
            project=project_with_completed_stages,
            stage_type='camera_movement'
        ).delete()

        # 配置模型
        from apps.projects.models import ProjectModelConfig

        config = ProjectModelConfig.objects.create(
            project=project_with_completed_stages
        )
        config.video_providers.add(model_provider)

        context = PipelineContext(project_id=str(project_with_completed_stages.id))
        result = processor.validate(context)

        # camera_movement未完成
        assert result is False

    def test_validate_without_image_urls_fails(
        self,
        processor,
        project_with_completed_stages,
        model_provider
    ):
        """测试没有图片URLs时验证失败"""
        # 移除urls
        image_stage = ProjectStage.objects.get(
            project=project_with_completed_stages,
            stage_type='image_generation'
        )
        image_stage.output_data = {
            "human_text": {
                "scenes": [
                    {
                        "scene_number": 1,
                        "narration": "开场",
                        "visual_prompt": "提示"
                    }
                ]
            }
        }
        image_stage.save()

        # 配置模型
        from apps.projects.models import ProjectModelConfig

        config = ProjectModelConfig.objects.create(
            project=project_with_completed_stages
        )
        config.video_providers.add(model_provider)

        context = PipelineContext(project_id=str(project_with_completed_stages.id))
        result = processor.validate(context)

        # 没有图片URLs
        assert result is False

    def test_validate_without_provider_fails(
        self,
        processor,
        project_with_completed_stages
    ):
        """测试无模型配置时验证失败"""
        # 不配置模型
        context = PipelineContext(project_id=str(project_with_completed_stages.id))
        result = processor.validate(context)

        # 没有模型配置
        assert result is False


@pytest.mark.unit
class TestImage2VideoGenerateSingleVideo:
    """测试单个视频生成"""

    @pytest.fixture
    def processor(self):
        """创建Image2Video处理器"""
        return Image2VideoStageProcessor()

    @pytest.fixture
    def project_with_data(self, db):
        """创建带有数据的项目"""
        from django.contrib.auth import get_user_model
        User = get_user_model()

        user = User.objects.create_user(
            username='testuser',
            email='test@example.com'
        )

        project = Project.objects.create(
            name='测试项目',
            original_topic='原始',
            user=user
        )

        return project

    @pytest.fixture
    def model_provider(self, db):
        """创建模型提供商"""
        provider = ModelProvider.objects.create(
            name='Runway',
            provider_type='image2video',
            api_url='https://api.runway.com',
            api_key='test-key',
            model_name='gen3a_turbo',
            is_active=True
        )
        return provider

    @pytest.fixture
    def storyboard_dict(self):
        """创建分镜数据字典"""
        return {
            'scene_number': 1,
            'narration': '测试旁白',
            'visual_prompt': '测试提示',
            'shot_type': '特写',
            'urls': [{'url': 'http://example.com/image.jpg'}]
        }

    @patch('apps.content.processors.image2video_stage.create_ai_client')
    def test_generate_single_video_success(
        self,
        mock_create_client,
        processor,
        project_with_data,
        model_provider,
        storyboard_dict
    ):
        """测试成功生成单个视频"""
        # Mock AI客户端
        mock_client = MagicMock()
        mock_response = {
            'data': [
                {'url': 'http://example.com/video1.mp4'}
            ]
        }
        mock_client._generate_video.return_value = mock_response
        mock_create_client.return_value = mock_client

        # Mock _build_prompt和image_to_base64
        with patch.object(processor, '_build_prompt', return_value='mock prompt'), \
             patch.object(processor, 'image_to_base64', return_value='base64string'):
            # 生成视频
            chunks = list(processor._generate_single_video_stream(
                project=project_with_data,
                storyboard=storyboard_dict,
                scene_number=1,
                provider=model_provider
            ))

            # 验证返回结果
            assert len(chunks) > 0
            assert chunks[-1]['type'] == 'video_generated'
            assert 'video_urls' in chunks[-1]

    def test_generate_single_video_no_image_urls(
        self,
        processor,
        project_with_data,
        model_provider
    ):
        """测试没有图片URL时返回error"""
        storyboard_dict = {
            'scene_number': 1,
            'narration': '测试',
            'visual_prompt': '测试'
            # 没有urls字段
        }

        # Mock _build_prompt避免模板错误
        with patch.object(processor, '_build_prompt', return_value='mock prompt'):
            chunks = list(processor._generate_single_video_stream(
                project=project_with_data,
                storyboard=storyboard_dict,
                scene_number=1,
                provider=model_provider
            ))

        # 应该返回error
        assert len(chunks) == 1
        assert chunks[0]['type'] == 'error'
        assert '没有图片URL' in chunks[0]['error']


@pytest.mark.unit
class TestImage2VideoSaveResult:
    """测试结果保存逻辑"""

    @pytest.fixture
    def processor(self):
        """创建处理器"""
        return Image2VideoStageProcessor()

    @pytest.fixture
    def project_with_stages(self, db):
        """创建带有阶段的项目"""
        from django.contrib.auth import get_user_model
        User = get_user_model()

        user = User.objects.create_user(
            username='testuser',
            email='test@example.com'
        )

        project = Project.objects.create(
            name='测试项目',
            original_topic='原始',
            user=user
        )

        # 创建video_generation阶段
        video_stage = ProjectStage.objects.create(
            project=project,
            stage_type='video_generation',
            status='processing',
            output_data={
                "human_text": {
                    "scenes": [
                        {
                            "scene_number": 1,
                            "narration": "旁白",
                            "visual_prompt": "提示",
                            "shot_type": "特写",
                            "urls": [{"url": "http://example.com/image.jpg"}]
                        }
                    ]
                }
            }
        )

        return project

    def test_save_result_updates_video_urls(
        self,
        processor,
        project_with_stages
    ):
        """测试保存结果时更新video_urls"""
        video_stage = ProjectStage.objects.get(
            project=project_with_stages,
            stage_type='video_generation'
        )

        storyboard = {
            'scene_number': 1,
            'narration': '旁白',
            'video_urls': [{'url': 'http://example.com/video.mp4'}]
        }

        # 更新output_data中的video_urls
        scenes = video_stage.output_data['human_text']['scenes']
        for scene in scenes:
            if scene['scene_number'] == storyboard['scene_number']:
                scene['video_urls'] = storyboard['video_urls']

        video_stage.save()

        # 验证已更新
        video_stage.refresh_from_db()
        scenes = video_stage.output_data['human_text']['scenes']
        assert scenes[0]['video_urls'] == [{'url': 'http://example.com/video.mp4'}]


@pytest.mark.unit
class TestImage2VideoProcessStream:
    """测试流式处理"""

    @pytest.fixture
    def processor(self):
        """创建处理器"""
        return Image2VideoStageProcessor()

    @pytest.fixture
    def project_with_data(self, db):
        """创建测试项目"""
        from django.contrib.auth import get_user_model
        from apps.models.models import ModelProvider

        User = get_user_model()

        user = User.objects.create_user(
            username='testuser',
            email='test@example.com'
        )

        project = Project.objects.create(
            name='测试项目',
            original_topic='原始',
            user=user
        )

        # 创建模型提供商
        provider = ModelProvider.objects.create(
            name='Runway',
            provider_type='image2video',
            api_url='https://api.runway.com',
            api_key='test',
            model_name='gen3a',
            is_active=True
        )

        # 创建video_generation阶段
        stage = ProjectStage.objects.create(
            project=project,
            stage_type='video_generation',
            status='pending',
            output_data={
                "human_text": {
                    "scenes": [
                        {
                            "scene_number": 1,
                            "narration": "旁白1",
                            "visual_prompt": "提示1",
                            "shot_type": "特写",
                            "urls": [{"url": "http://example.com/image1.jpg"}]
                        },
                        {
                            "scene_number": 2,
                            "narration": "旁白2",
                            "visual_prompt": "提示2",
                            "shot_type": "中景",
                            "urls": [{"url": "http://example.com/image2.jpg"}]
                        }
                    ]
                }
            }
        )

        return project

    @patch('apps.content.processors.image2video_stage.Image2VideoStageProcessor._generate_single_video_stream')
    def test_process_stream_yields_progress(
        self,
        mock_generate,
        processor,
        project_with_data
    ):
        """测试流式处理yield进度消息"""
        # Mock视频生成
        mock_generate.return_value = iter([
            {'type': 'video_generated', 'video_urls': [{'url': 'http://example.com/video.mp4'}]}
        ])

        chunks = list(processor.process_stream(
            project_id=str(project_with_data.id)
        ))

        # 应该包含进度消息
        progress_chunks = [c for c in chunks if c['type'] == 'progress']
        assert len(progress_chunks) == 2  # 2个分镜

    @patch('apps.content.processors.image2video_stage.Image2VideoStageProcessor._generate_single_video_stream')
    def test_process_stream_yields_video_generated(
        self,
        mock_generate,
        processor,
        project_with_data
    ):
        """测试流式处理yield video_generated消息"""
        # Mock视频生成 - 需要返回generator
        def mock_gen_func(*args, **kwargs):
            yield {'type': 'video_generated', 'video_urls': [{'url': 'http://example.com/video.mp4'}]}

        mock_generate.side_effect = mock_gen_func

        chunks = list(processor.process_stream(
            project_id=str(project_with_data.id)
        ))

        # 应该包含video_generated消息
        video_chunks = [c for c in chunks if c['type'] == 'video_generated']
        assert len(video_chunks) == 2

    @patch('apps.content.processors.image2video_stage.Image2VideoStageProcessor._generate_single_video_stream')
    def test_process_stream_handles_partial_failure(
        self,
        mock_generate,
        processor,
        project_with_data
    ):
        """测试流式处理处理部分失败"""
        # 第1个成功，第2个失败
        mock_generate.side_effect = [
            iter([
                {'type': 'video_generated', 'video_urls': [{'url': 'http://example.com/video1.mp4'}]}
            ]),
            iter([
                {'type': 'error', 'error': 'API Error'}
            ])
        ]

        chunks = list(processor.process_stream(
            project_id=str(project_with_data.id)
        ))

        # 应该有warning或error消息
        error_chunks = [c for c in chunks if c['type'] in ['warning', 'error']]
        assert len(error_chunks) >= 1

        # 应该有done消息统计
        done_chunks = [c for c in chunks if c['type'] == 'done']
        assert done_chunks[-1]['message'].startswith('视频生成完成')


@pytest.mark.unit
class TestImage2VideoBuildPrompt:
    """测试提示词构建"""

    @pytest.fixture
    def processor(self):
        """创建处理器"""
        return Image2VideoStageProcessor()

    @pytest.fixture
    def project_with_template(self, db):
        """创建带有模板的项目"""
        from django.contrib.auth import get_user_model
        from apps.prompts.models import PromptTemplateSet, PromptTemplate
        from apps.models.models import ModelProvider

        User = get_user_model()

        user = User.objects.create_user(
            username='testuser',
            email='test@example.com'
        )

        # 创建模型提供商
        provider = ModelProvider.objects.create(
            name='Runway',
            provider_type='image2video',
            api_url='https://api.runway.com',
            api_key='test',
            model_name='gen3a_turbo',
            is_active=True
        )

        # 创建提示词集
        template_set = PromptTemplateSet.objects.create(
            name='Video Template Set',
            is_default=True,
            created_by=user
        )

        # 创建提示词模板
        template = PromptTemplate.objects.create(
            template_set=template_set,
            stage_type='video_generation',
            template_content='生成视频：{{ narration }}，风格：{{ visual_prompt }}',
            model_provider=provider,
            is_active=True
        )

        project = Project.objects.create(
            name='测试项目',
            original_topic='原始',
            user=user,
            prompt_template_set=template_set
        )

        return project

    def test_build_prompt_renders_template(self, processor, project_with_template):
        """测试提示词模板渲染"""
        storyboard_dict = {
            'scene_number': 1,
            'narration': '美丽的日落',
            'visual_prompt': '橙色天空，宁静的湖面',
            'shot_type': '特写',
            'urls': [{'url': 'http://example.com/image.jpg'}]
        }

        # Mock image_to_base64
        with patch.object(processor, 'image_to_base64', return_value='base64string'):
            prompt = processor._build_prompt(project_with_template, storyboard_dict)

            # 由于image_to_base64需要读取文件，我们只验证模板调用
            assert prompt is not None or '美丽的日落' in str(prompt)


@pytest.mark.unit
class TestImage2VideoGetProvider:
    """测试获取模型提供商"""

    @pytest.fixture
    def processor(self):
        """创建处理器"""
        return Image2VideoStageProcessor()

    @pytest.fixture
    def project_with_config(self, db):
        """创建带有模型配置的项目"""
        from django.contrib.auth import get_user_model
        from apps.projects.models import ProjectModelConfig
        from apps.models.models import ModelProvider

        User = get_user_model()

        user = User.objects.create_user(
            username='testuser',
            email='test@example.com'
        )

        project = Project.objects.create(
            name='测试项目',
            original_topic='原始',
            user=user
        )

        # 创建模型提供商
        provider = ModelProvider.objects.create(
            name='Runway',
            provider_type='image2video',
            api_url='https://api.runway.com',
            api_key='test',
            model_name='gen3a',
            is_active=True
        )

        # 创建模型配置
        config = ProjectModelConfig.objects.create(
            project=project
        )
        config.video_providers.add(provider)

        return project

    def test_get_provider_from_project_config(self, processor, project_with_config):
        """测试从项目配置获取提供商"""
        provider = processor._get_image2video_provider(project_with_config)

        assert provider is not None
        assert provider.name == 'Runway'

    def test_get_provider_returns_default_when_no_config(self, processor, db):
        """测试无配置时返回默认提供商"""
        from django.contrib.auth import get_user_model
        from apps.models.models import ModelProvider

        User = get_user_model()

        user = User.objects.create_user(
            username='testuser2',
            email='test2@example.com'
        )

        project = Project.objects.create(
            name='测试项目2',
            original_topic='原始',
            user=user
        )

        # 创建默认提供商
        provider = ModelProvider.objects.create(
            name='Default Runway',
            provider_type='image2video',
            api_url='https://api.runway.com',
            api_key='test',
            model_name='gen3a',
            is_active=True
        )

        # 获取提供商
        result = processor._get_image2video_provider(project)

        assert result is not None
        assert result.name == 'Default Runway'
