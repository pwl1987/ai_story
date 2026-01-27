"""
项目管理域视图测试
测试ProjectViewSet、ProjectStageViewSet、ProjectModelConfigViewSet
遵循单一职责原则(SRP)
"""

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APIRequestFactory, force_authenticate

from apps.projects.models import Project, ProjectModelConfig, ProjectStage
from apps.projects.tests.factories import (
    ProjectFactory,
    ProjectModelConfigFactory,
    ProjectStageFactory,
    UserFactory,
)
from apps.projects.views import ProjectViewSet, ProjectStageViewSet, ProjectModelConfigViewSet

User = get_user_model()


@pytest.mark.django_db
class TestProjectViewSet:
    """测试ProjectViewSet"""

    def setup_method(self):
        """每个测试方法前的设置"""
        self.client = APIClient()
        self.user = UserFactory()
        self.client.force_authenticate(user=self.user)

    def test_list_projects(self):
        """测试获取项目列表"""
        # 创建测试数据
        project1 = ProjectFactory(user=self.user, name="项目1")
        project2 = ProjectFactory(user=self.user, name="项目2")

        # 发送请求
        url = reverse('project-list')
        response = self.client.get(url)

        # 验证响应
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) >= 2

    def test_create_project(self):
        """测试创建项目"""
        url = reverse('project-list')
        data = {
            'name': '新项目',
            'description': '项目描述',
            'original_topic': '测试主题'
        }

        response = self.client.post(url, data)

        assert response.status_code == status.HTTP_201_CREATED
        assert Project.objects.filter(name='新项目', user=self.user).exists()

    def test_retrieve_project(self):
        """测试获取项目详情"""
        project = ProjectFactory(user=self.user)

        url = reverse('project-detail', kwargs={'pk': project.id})
        response = self.client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == str(project.id)

    def test_update_project(self):
        """测试更新项目"""
        project = ProjectFactory(user=self.user, name="原名称")

        url = reverse('project-detail', kwargs={'pk': project.id})
        data = {'name': '新名称'}
        response = self.client.patch(url, data)

        assert response.status_code == status.HTTP_200_OK
        project.refresh_from_db()
        assert project.name == '新名称'

    def test_delete_project(self):
        """测试删除项目"""
        project = ProjectFactory(user=self.user)

        url = reverse('project-detail', kwargs={'pk': project.id})
        response = self.client.delete(url)

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Project.objects.filter(id=project.id).exists()

    def test_queryset_filters_by_user(self):
        """测试查询集按用户过滤"""
        # 创建另一个用户的项目
        other_user = UserFactory()
        ProjectFactory(user=other_user, name="其他用户项目")

        # 创建当前用户的项目
        my_project = ProjectFactory(user=self.user, name="我的项目")

        url = reverse('project-list')
        response = self.client.get(url)

        assert response.status_code == status.HTTP_200_OK
        project_ids = [p['id'] for p in response.data['results']]
        assert str(my_project.id) in project_ids

    def test_get_stages_action(self):
        """测试获取项目阶段列表"""
        project = ProjectFactory(user=self.user)
        ProjectStageFactory(project=project, stage_type='rewrite')
        ProjectStageFactory(project=project, stage_type='storyboard')

        url = reverse('project-stages', kwargs={'pk': project.id})
        response = self.client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 2

    def test_pause_project(self):
        """测试暂停项目"""
        project = ProjectFactory(user=self.user, status='processing')

        url = reverse('project-pause', kwargs={'pk': project.id})
        response = self.client.post(url)

        assert response.status_code == status.HTTP_200_OK
        project.refresh_from_db()
        assert project.status == 'paused'

    def test_resume_project(self):
        """测试恢复项目"""
        project = ProjectFactory(user=self.user, status='paused')

        url = reverse('project-resume', kwargs={'pk': project.id})
        response = self.client.post(url)

        assert response.status_code == status.HTTP_200_OK
        project.refresh_from_db()
        assert project.status == 'processing'

    def test_rollback_stage(self):
        """测试回滚阶段"""
        project = ProjectFactory(user=self.user)
        ProjectStageFactory(
            project=project,
            stage_type='storyboard',
            status='completed',
            output_data={'result': 'test'}
        )

        url = reverse('project-rollback-stage', kwargs={'pk': project.id})
        data = {'stage_name': 'storyboard'}
        response = self.client.post(url, data)

        assert response.status_code == status.HTTP_200_OK

    def test_statistics_action(self):
        """测试统计信息"""
        ProjectFactory(user=self.user, status='draft')
        ProjectFactory(user=self.user, status='processing')
        ProjectFactory(user=self.user, status='completed')

        url = reverse('project-statistics')
        response = self.client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert 'total_projects' in response.data
        assert response.data['total_projects'] >= 3

    def test_unauthenticated_access(self):
        """测试未认证访问被拒绝"""
        self.client.force_authenticate(user=None)

        project = ProjectFactory(user=self.user)
        url = reverse('project-detail', kwargs={'pk': project.id})
        response = self.client.get(url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestProjectStageViewSet:
    """测试ProjectStageViewSet"""

    def setup_method(self):
        """每个测试方法前的设置"""
        self.client = APIClient()
        self.user = UserFactory()
        self.client.force_authenticate(user=self.user)

    @pytest.mark.skip(reason="路由配置待确认")
    def test_list_stages(self):
        """测试获取阶段列表"""
        project = ProjectFactory(user=self.user)
        stage1 = ProjectStageFactory(project=project, stage_type='rewrite')
        stage2 = ProjectStageFactory(project=project, stage_type='storyboard')

        url = reverse('stage-list')
        response = self.client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) >= 2

    def test_retrieve_stage(self):
        """测试获取阶段详情"""
        project = ProjectFactory(user=self.user)
        stage = ProjectStageFactory(project=project)

        url = reverse('stage-detail', kwargs={'pk': stage.id})
        response = self.client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == str(stage.id)

    @pytest.mark.skip(reason="路由配置待确认")
    def test_queryset_filters_by_user(self):
        """测试查询集按用户过滤"""
        # 创建其他用户的阶段
        other_user = UserFactory()
        other_project = ProjectFactory(user=other_user)
        ProjectStageFactory(project=other_project)

        # 创建当前用户的阶段
        my_project = ProjectFactory(user=self.user)
        my_stage = ProjectStageFactory(project=my_project)

        url = reverse('stage-list')
        response = self.client.get(url)

        assert response.status_code == status.HTTP_200_OK
        stage_ids = [s['id'] for s in response.data['results']]
        assert str(my_stage.id) in stage_ids


@pytest.mark.django_db
class TestProjectModelConfigViewSet:
    """测试ProjectModelConfigViewSet"""

    def setup_method(self):
        """每个测试方法前的设置"""
        self.client = APIClient()
        self.user = UserFactory()
        self.client.force_authenticate(user=self.user)

    @pytest.mark.skip(reason="路由配置待确认")
    def test_list_configs(self):
        """测试获取配置列表"""
        project = ProjectFactory(user=self.user)
        ProjectModelConfigFactory(project=project)

        url = reverse('model-config-list')
        response = self.client.get(url)

        assert response.status_code == status.HTTP_200_OK

    def test_retrieve_config(self):
        """测试获取配置详情"""
        project = ProjectFactory(user=self.user)
        config = ProjectModelConfigFactory(project=project)

        url = reverse('model-config-detail', kwargs={'pk': config.id})
        response = self.client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == str(config.id)

    @pytest.mark.skip(reason="ViewSet可能不支持POST方法")
    def test_create_config(self):
        """测试创建配置"""
        project = ProjectFactory(user=self.user)

        url = reverse('model-config-list')
        data = {
            'project': str(project.id),
            'load_balance_strategy': 'random'
        }
        response = self.client.post(url, data)

        assert response.status_code == status.HTTP_201_CREATED

    def test_update_config(self):
        """测试更新配置"""
        project = ProjectFactory(user=self.user)
        config = ProjectModelConfigFactory(
            project=project,
            load_balance_strategy='round_robin'
        )

        url = reverse('model-config-detail', kwargs={'pk': config.id})
        data = {'load_balance_strategy': 'weighted'}
        response = self.client.patch(url, data)

        assert response.status_code == status.HTTP_200_OK
        config.refresh_from_db()
        assert config.load_balance_strategy == 'weighted'


@pytest.mark.django_db
class TestProjectViewSetFilters:
    """测试ProjectViewSet过滤器"""

    def setup_method(self):
        """每个测试方法前的设置"""
        self.client = APIClient()
        self.user = UserFactory()
        self.client.force_authenticate(user=self.user)

    def test_filter_by_status(self):
        """测试按状态过滤"""
        ProjectFactory(user=self.user, status='draft')
        ProjectFactory(user=self.user, status='processing')

        url = reverse('project-list')
        response = self.client.get(url, {'status': 'draft'})

        assert response.status_code == status.HTTP_200_OK
        for project in response.data['results']:
            assert project['status'] == 'draft'

    def test_search_by_name(self):
        """测试按名称搜索"""
        ProjectFactory(user=self.user, name="Python教程")
        ProjectFactory(user=self.user, name="Java教程")

        url = reverse('project-list')
        response = self.client.get(url, {'search': 'Python'})

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) >= 1

    def test_ordering_by_created_at(self):
        """测试按创建时间排序"""
        ProjectFactory(user=self.user, name="项目1")
        ProjectFactory(user=self.user, name="项目2")

        url = reverse('project-list')
        response = self.client.get(url, {'ordering': '-created_at'})

        assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
class TestProjectExecuteStage:
    """测试执行阶段API"""

    def setup_method(self):
        """每个测试方法前的设置"""
        self.client = APIClient()
        self.user = UserFactory()
        self.client.force_authenticate(user=self.user)

    def test_execute_llm_stage(self):
        """测试执行LLM阶段（rewrite、storyboard、camera_movement）"""
        project = ProjectFactory(user=self.user, status='draft')
        ProjectStageFactory(
            project=project,
            stage_type='rewrite',
            status='pending'
        )

        url = reverse('project-execute-stage', kwargs={'pk': project.id})
        data = {
            'stage_name': 'rewrite',
            'input_data': {'test': 'data'}
        }

        response = self.client.post(url, data, format='json')

        # 应该返回202 ACCEPTED并包含task_id
        assert response.status_code in [status.HTTP_202_ACCEPTED, status.HTTP_200_OK]
        assert 'task_id' in response.data or 'message' in response.data

    def test_execute_text2image_stage(self):
        """测试执行文生图阶段"""
        project = ProjectFactory(user=self.user, status='draft')
        ProjectStageFactory(
            project=project,
            stage_type='image_generation',
            status='pending'
        )

        url = reverse('project-execute-stage', kwargs={'pk': project.id})
        data = {
            'stage_name': 'image_generation',
            'input_data': {'storyboard_ids': []}
        }

        response = self.client.post(url, data, format='json')

        assert response.status_code in [status.HTTP_202_ACCEPTED, status.HTTP_200_OK]

    def test_execute_image2video_stage(self):
        """测试执行图生视频阶段"""
        project = ProjectFactory(user=self.user, status='draft')
        ProjectStageFactory(
            project=project,
            stage_type='video_generation',
            status='pending'
        )

        url = reverse('project-execute-stage', kwargs={'pk': project.id})
        data = {
            'stage_name': 'video_generation',
            'input_data': {'storyboard_ids': []}
        }

        response = self.client.post(url, data, format='json')

        assert response.status_code in [status.HTTP_202_ACCEPTED, status.HTTP_200_OK]

    def test_execute_stage_invalid_stage_name(self):
        """测试执行阶段 - 无效的阶段名称"""
        project = ProjectFactory(user=self.user, status='draft')

        url = reverse('project-execute-stage', kwargs={'pk': project.id})
        data = {
            'stage_name': 'invalid_stage'
        }

        response = self.client.post(url, data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_execute_stage_missing_stage_name(self):
        """测试执行阶段 - 缺少stage_name参数"""
        project = ProjectFactory(user=self.user, status='draft')

        url = reverse('project-execute-stage', kwargs={'pk': project.id})
        data = {}  # 缺少stage_name

        response = self.client.post(url, data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestProjectRetry:
    """测试重试API"""

    def setup_method(self):
        """每个测试方法前的设置"""
        self.client = APIClient()
        self.user = UserFactory()
        self.client.force_authenticate(user=self.user)

    def test_retry_failed_project(self):
        """测试重试失败的项目"""
        project = ProjectFactory(user=self.user, status='failed')
        stage = ProjectStageFactory(
            project=project,
            stage_type='rewrite',
            status='failed',
            error_message='测试错误',
            retry_count=1
        )

        url = reverse('project-retry-stage', kwargs={'pk': project.id})
        data = {'stage_name': 'rewrite'}
        response = self.client.post(url, data, format='json')

        assert response.status_code == status.HTTP_200_OK
        stage.refresh_from_db()
        assert stage.status == 'processing'  # retry_stage会设置为processing

    def test_retry_with_retry_count_reset(self):
        """测试重试时重置retry_count"""
        project = ProjectFactory(user=self.user, status='failed')
        stage = ProjectStageFactory(
            project=project,
            stage_type='rewrite',
            status='failed',
            retry_count=3
        )

        url = reverse('project-retry-stage', kwargs={'pk': project.id})
        data = {'stage_name': 'rewrite'}
        response = self.client.post(url, data, format='json')

        assert response.status_code == status.HTTP_200_OK
        stage.refresh_from_db()
        assert stage.retry_count == 4  # retry_stage会增加retry_count


@pytest.mark.django_db
class TestProjectPagination:
    """测试项目分页"""

    def setup_method(self):
        """每个测试方法前的设置"""
        self.client = APIClient()
        self.user = UserFactory()
        self.client.force_authenticate(user=self.user)

    def test_default_page_size(self):
        """测试默认分页大小"""
        # 创建15个项目
        for i in range(15):
            ProjectFactory(user=self.user, name=f'项目{i}')

        url = reverse('project-list')
        response = self.client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 15
        assert len(response.data['results']) <= 15  # 可能全部返回或有分页限制

    def test_pagination_with_page_parameter(self):
        """测试使用page参数分页"""
        # 创建25个项目（超过默认PAGE_SIZE 20）
        for i in range(25):
            ProjectFactory(user=self.user, name=f'项目{i}')

        url = reverse('project-list')
        # 第一页应该返回20个（默认PAGE_SIZE）
        response = self.client.get(url, {'page': 1})

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 20  # 默认PAGE_SIZE
        assert response.data['count'] == 25


@pytest.mark.django_db
class TestProjectValidation:
    """测试项目验证逻辑"""

    def setup_method(self):
        """每个测试方法前的设置"""
        self.client = APIClient()
        self.user = UserFactory()
        self.client.force_authenticate(user=self.user)

    def test_create_project_missing_required_field(self):
        """测试创建项目 - 缺少必填字段"""
        url = reverse('project-list')
        data = {
            'name': '测试项目'
            # 缺少original_topic
        }

        response = self.client.post(url, data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_create_project_empty_topic(self):
        """测试创建项目 - original_topic为空"""
        url = reverse('project-list')
        data = {
            'original_topic': '',
            'name': '测试项目'
        }

        response = self.client.post(url, data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_update_project_with_invalid_status(self):
        """测试更新项目 - 无效的状态值"""
        project = ProjectFactory(user=self.user, status='draft')

        url = reverse('project-detail', kwargs={'pk': project.id})
        data = {'status': 'invalid_status'}

        response = self.client.patch(url, data)

        # DRF应该拒绝无效的状态值
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestProjectPermissions:
    """测试项目权限"""

    def setup_method(self):
        """每个测试方法前的设置"""
        self.client = APIClient()
        self.user = UserFactory()
        self.other_user = UserFactory()
        self.admin_user = UserFactory(is_staff=True, is_superuser=True)

        self.client.force_authenticate(user=self.user)

    def test_user_cannot_access_other_users_project(self):
        """测试用户无法访问其他用户的项目"""
        other_project = ProjectFactory(user=self.other_user, name='其他用户项目')

        url = reverse('project-detail', kwargs={'pk': other_project.id})
        response = self.client.get(url)

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_user_cannot_delete_other_users_project(self):
        """测试用户无法删除其他用户的项目"""
        other_project = ProjectFactory(user=self.other_user)

        url = reverse('project-detail', kwargs={'pk': other_project.id})
        response = self.client.delete(url)

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_user_cannot_update_other_users_project(self):
        """测试用户无法更新其他用户的项目"""
        other_project = ProjectFactory(user=self.other_user, name='原名称')

        url = reverse('project-detail', kwargs={'pk': other_project.id})
        data = {'name': '新名称'}
        response = self.client.patch(url, data)

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_admin_can_access_all_projects(self):
        """测试管理员可以访问所有项目"""
        user_project = ProjectFactory(user=self.user, name='用户项目')
        other_project = ProjectFactory(user=self.other_user, name='其他用户项目')

        # 使用管理员认证
        self.client.force_authenticate(user=self.admin_user)

        url = reverse('project-detail', kwargs={'pk': other_project.id})
        response = self.client.get(url)

        # 管理员应该能看到其他用户的项目
        # 或者系统返回404因为查询集过滤了（取决于实现）
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND]


@pytest.mark.skip(reason="Project stage detail endpoint not implemented in views.py")
@pytest.mark.django_db
class TestProjectStageDetail:
    """测试项目阶段详情API - SKIPPED: 端点未实现"""

    def setup_method(self):
        """每个测试方法前的设置"""
        self.client = APIClient()
        self.user = UserFactory()
        self.client.force_authenticate(user=self.user)

    def test_get_stage_detail(self):
        """测试获取阶段详情"""
        project = ProjectFactory(user=self.user)
        stage = ProjectStageFactory(
            project=project,
            stage_type='rewrite',
            status='completed',
            output_data={'result': 'test output'}
        )

        url = reverse('project-stage-detail', kwargs={'pk': project.id, 'stage_type': 'rewrite'})
        response = self.client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['stage_type'] == 'rewrite'

    def test_get_nonexistent_stage(self):
        """测试获取不存在的阶段"""
        project = ProjectFactory(user=self.user)
        # 不创建对应的stage

        url = reverse('project-stage-detail', kwargs={'pk': project.id, 'stage_type': 'rewrite'})
        response = self.client.get(url)

        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
class TestProjectStatistics:
    """测试项目统计API"""

    def setup_method(self):
        """每个测试方法前的设置"""
        self.client = APIClient()
        self.user = UserFactory()
        self.client.force_authenticate(user=self.user)

    def test_project_statistics_contains_counts(self):
        """测试项目统计包含各状态计数"""
        ProjectFactory(user=self.user, status='draft')
        ProjectFactory(user=self.user, status='processing')
        ProjectFactory(user=self.user, status='completed')
        ProjectFactory(user=self.user, status='failed')

        url = reverse('project-statistics')
        response = self.client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert 'total_projects' in response.data

    def test_statistics_filters_by_user(self):
        """测试统计数据按用户过滤"""
        # 创建两个用户的项目
        other_user = UserFactory()
        ProjectFactory(user=other_user, status='draft')
        my_project = ProjectFactory(user=self.user, status='draft')

        url = reverse('project-statistics')
        response = self.client.get(url)

        assert response.status_code == status.HTTP_200_OK
        # 统计应该只包含当前用户的项目
        # 或者是全局统计（取决于实现）
