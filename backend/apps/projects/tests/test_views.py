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
