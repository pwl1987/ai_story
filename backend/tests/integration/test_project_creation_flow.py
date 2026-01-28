"""
项目创建流程集成测试
测试完整的API创建流程和数据验证
"""

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from apps.projects.models import Project, ProjectModelConfig, ProjectStage

User = get_user_model()


@pytest.mark.integration
@pytest.mark.django_db
class TestProjectCreationFlow:
    """项目创建流程集成测试"""

    @pytest.fixture
    def api_client(self, db):
        """API客户端"""
        return APIClient()

    @pytest.fixture
    def test_user(self, db):
        """测试用户"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        return user

    def test_create_project_success(self, api_client, test_user):
        """测试成功创建项目"""
        # 认证用户
        api_client.force_authenticate(user=test_user)

        # 准备项目数据
        project_data = {
            'name': '测试项目',
            'description': '这是一个测试项目',
            'original_topic': 'AI驱动的视频生成'
        }

        # 发送POST请求创建项目
        response = api_client.post('/api/v1/projects/', project_data)

        # 验证响应状态码
        assert response.status_code == 201
        assert response.data['name'] == '测试项目'
        assert response.data['original_topic'] == 'AI驱动的视频生成'
        assert 'id' in response.data

        # 获取项目ID
        project_id = response.data['id']

        # 验证Project数据库记录
        assert Project.objects.filter(id=project_id).exists()
        project = Project.objects.get(id=project_id)
        assert project.name == '测试项目'
        assert project.user == test_user
        assert project.status == 'draft'

    def test_create_project_auto_creates_stages(self, api_client, test_user):
        """测试创建项目时自动创建5个阶段"""
        api_client.force_authenticate(user=test_user)

        project_data = {
            'name': '阶段测试项目',
            'original_topic': '测试阶段自动创建'
        }

        response = api_client.post('/api/v1/projects/', project_data)
        assert response.status_code == 201

        project_id = response.data['id']

        # 验证5个阶段自动创建
        stages = ProjectStage.objects.filter(project_id=project_id)
        assert stages.count() == 5

        # 验证阶段类型
        stage_types = {stage.stage_type for stage in stages}
        expected_types = {'rewrite', 'storyboard', 'image_generation', 'camera_movement', 'video_generation'}
        assert stage_types == expected_types

        # 验证所有阶段初始状态为pending
        for stage in stages:
            assert stage.status == 'pending'
            assert stage.retry_count == 0
            assert stage.max_retries == 3

    def test_create_project_creates_model_config(self, api_client, test_user):
        """测试创建项目时自动创建模型配置"""
        api_client.force_authenticate(user=test_user)

        project_data = {
            'name': '模型配置测试项目',
            'original_topic': '测试模型配置创建'
        }

        response = api_client.post('/api/v1/projects/', project_data)
        assert response.status_code == 201

        project_id = response.data['id']

        # 验证模型配置自动创建
        assert ProjectModelConfig.objects.filter(project_id=project_id).exists()
        config = ProjectModelConfig.objects.get(project_id=project_id)
        assert config.load_balance_strategy == 'weighted'  # 默认策略

    def test_create_project_stage_input_data(self, api_client, test_user):
        """测试阶段输入数据正确初始化"""
        api_client.force_authenticate(user=test_user)

        topic = 'AI视频生成测试主题'
        project_data = {
            'name': '输入数据测试项目',
            'original_topic': topic
        }

        response = api_client.post('/api/v1/projects/', project_data)
        project_id = response.data['id']

        # 验证rewrite和storyboard阶段的input_data包含原始主题
        rewrite_stage = ProjectStage.objects.get(
            project_id=project_id,
            stage_type='rewrite'
        )
        assert rewrite_stage.input_data['raw_text'] == topic
        assert rewrite_stage.input_data['human_text'] == ''

        storyboard_stage = ProjectStage.objects.get(
            project_id=project_id,
            stage_type='storyboard'
        )
        assert storyboard_stage.input_data['raw_text'] == topic
        assert storyboard_stage.input_data['human_text'] == ''

    def test_create_project_missing_required_field(self, api_client, test_user):
        """测试缺少必填字段时返回400错误"""
        api_client.force_authenticate(user=test_user)

        # 缺少original_topic字段
        project_data = {
            'name': '不完整的项目'
        }

        response = api_client.post('/api/v1/projects/', project_data)

        # 应该返回400错误
        assert response.status_code == 400

    def test_create_project_empty_original_topic(self, api_client, test_user):
        """测试原始主题为空时返回验证错误"""
        api_client.force_authenticate(user=test_user)

        project_data = {
            'name': '空主题项目',
            'original_topic': '   '  # 只有空格
        }

        response = api_client.post('/api/v1/projects/', project_data)

        # 应该返回验证错误
        assert response.status_code == 400
        assert 'original_topic' in response.data

    def test_create_project_unauthenticated(self, api_client):
        """测试未认证用户无法创建项目"""
        # 不认证用户

        project_data = {
            'name': '未认证项目',
            'original_topic': '测试'
        }

        response = api_client.post('/api/v1/projects/', project_data)

        # 应该返回401或403
        assert response.status_code in [401, 403]

    def test_create_project_with_description(self, api_client, test_user):
        """测试带描述的项目创建"""
        api_client.force_authenticate(user=test_user)

        project_data = {
            'name': '带描述的项目',
            'description': '这是一个详细的项目描述，用于测试描述字段功能',
            'original_topic': '测试描述字段'
        }

        response = api_client.post('/api/v1/projects/', project_data)

        assert response.status_code == 201
        assert response.data['description'] == '这是一个详细的项目描述，用于测试描述字段功能'

        # 验证数据库中的描述
        project_id = response.data['id']
        project = Project.objects.get(id=project_id)
        assert project.description == '这是一个详细的项目描述，用于测试描述字段功能'

    def test_create_project_default_values(self, api_client, test_user):
        """测试项目创建的默认值"""
        api_client.force_authenticate(user=test_user)

        project_data = {
            'name': '默认值测试项目',
            'original_topic': '测试默认值'
        }

        response = api_client.post('/api/v1/projects/', project_data)
        assert response.status_code == 201

        project_id = response.data['id']
        project = Project.objects.get(id=project_id)

        # 验证默认值
        assert project.status == 'draft'
        assert project.jianying_draft_path == ''
        assert project.created_at is not None
        assert project.updated_at is not None
        assert project.completed_at is None

    def test_create_project_user_isolation(self, api_client, test_user):
        """测试用户隔离：用户只能看到自己的项目"""
        # 创建第一个用户和项目
        api_client.force_authenticate(user=test_user)

        project_data = {
            'name': '用户1的项目',
            'original_topic': '用户1主题'
        }

        response1 = api_client.post('/api/v1/projects/', project_data)
        assert response1.status_code == 201

        # 创建第二个用户
        user2 = User.objects.create_user(
            username='user2',
            email='user2@example.com',
            password='pass123'
        )

        # 使用第二个用户创建项目
        api_client.force_authenticate(user=user2)

        project_data2 = {
            'name': '用户2的项目',
            'original_topic': '用户2主题'
        }

        response2 = api_client.post('/api/v1/projects/', project_data2)
        assert response2.status_code == 201

        # 用户1获取项目列表
        api_client.force_authenticate(user=test_user)
        response = api_client.get('/api/v1/projects/')

        # 应该只返回用户1的项目
        assert response.status_code == 200
        project_names = [p['name'] for p in response.data['results']]
        assert '用户1的项目' in project_names
        assert '用户2的项目' not in project_names
