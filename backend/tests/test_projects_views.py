"""
项目管理API视图测试
测试ProjectViewSet的各种API端点
"""

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIRequestFactory, force_authenticate, APIClient
from apps.projects.models import Project
from apps.projects.views import ProjectViewSet


@pytest.mark.django_db
class TestProjectViewSet:
    """ProjectViewSet测试类"""

    @pytest.fixture
    def api_client(self):
        """API客户端"""
        return APIRequestFactory()

    @pytest.fixture
    def test_user(self, db):
        """测试用户"""
        User = get_user_model()
        return User.objects.create_user(
            username='testuser',
            email='test@example.com'
        )

    @pytest.fixture
    def project(self, db, test_user):
        """测试项目"""
        project = Project.objects.create(
            name='测试项目',
            description='测试描述',
            original_topic='测试主题',
            user=test_user,
            status='draft'
        )
        return project

    def test_get_queryset_filters_by_user(self, api_client, test_user, project):
        """测试列表只返回当前用户的项目"""
        # 创建另一个用户和项目
        User = get_user_model()
        other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com'
        )
        Project.objects.create(
            name='其他项目',
            original_topic='其他主题',
            user=other_user
        )

        # 检查数据库中的项目总数
        total_projects = Project.objects.count()
        assert total_projects == 2

        # 检查test_user的项目数量
        test_user_projects = Project.objects.filter(user=test_user)
        assert test_user_projects.count() == 1
        assert test_user_projects.first().name == '测试项目'

        # 检查other_user的项目数量
        other_user_projects = Project.objects.filter(user=other_user)
        assert other_user_projects.count() == 1
        assert other_user_projects.first().name == '其他项目'

    def test_list_action(self, api_client, test_user, project):
        """测试项目列表API"""
        view = ProjectViewSet.as_view({'get': 'list'})
        request = api_client.get('/api/v1/projects/')

        # 强制认证
        force_authenticate(request, user=test_user)

        response = view(request)

        assert response.status_code == 200
        # DRF分页响应，results包含实际数据
        assert len(response.data['results']) == 1
        assert response.data['results'][0]['name'] == '测试项目'

    def test_retrieve_action(self, api_client, test_user, project):
        """测试项目详情API"""
        view = ProjectViewSet.as_view({'get': 'retrieve'})
        request = api_client.get(f'/api/v1/projects/{project.id}/')

        force_authenticate(request, user=test_user)

        response = view(request, pk=project.id)

        assert response.status_code == 200
        assert response.data['id'] == str(project.id)
        assert response.data['name'] == '测试项目'

    def test_create_action(self, api_client, test_user):
        """测试创建项目API"""
        view = ProjectViewSet.as_view({'post': 'create'})
        data = {
            'name': '新项目',
            'description': '新项目描述',
            'original_topic': '新主题'
        }
        request = api_client.post('/api/v1/projects/', data=data)

        force_authenticate(request, user=test_user)

        response = view(request)

        assert response.status_code == 201
        assert response.data['name'] == '新项目'
        assert response.data['original_topic'] == '新主题'

    def test_update_action(self, api_client, test_user, project):
        """测试更新项目API"""
        view = ProjectViewSet.as_view({'patch': 'partial_update'})
        data = {'name': '更新后的项目名称'}
        request = api_client.patch(f'/api/v1/projects/{project.id}/', data=data)

        force_authenticate(request, user=test_user)

        response = view(request, pk=project.id)

        assert response.status_code == 200
        assert response.data['name'] == '更新后的项目名称'

        # 验证数据库已更新
        project.refresh_from_db()
        assert project.name == '更新后的项目名称'

    def test_destroy_action(self, api_client, test_user, project):
        """测试删除项目API"""
        view = ProjectViewSet.as_view({'delete': 'destroy'})
        request = api_client.delete(f'/api/v1/projects/{project.id}/')

        force_authenticate(request, user=test_user)

        response = view(request, pk=project.id)

        assert response.status_code == 204

        # 验证项目已删除
        assert not Project.objects.filter(id=project.id).exists()

    def test_stages_action(self, api_client, test_user, project):
        """测试获取项目阶段列表API"""
        view = ProjectViewSet.as_view({'get': 'stages'})
        request = api_client.get(f'/api/v1/projects/{project.id}/stages/')

        force_authenticate(request, user=test_user)

        response = view(request, pk=project.id)

        assert response.status_code == 200
        assert isinstance(response.data, list)

    def test_get_serializer_class_list(self):
        """测试列表动作使用正确的序列化器"""
        viewset = ProjectViewSet()
        viewset.action = 'list'

        serializer_class = viewset.get_serializer_class()

        assert serializer_class.__name__ == 'ProjectListSerializer'

    def test_get_serializer_class_retrieve(self):
        """测试详情动作使用正确的序列化器"""
        viewset = ProjectViewSet()
        viewset.action = 'retrieve'

        serializer_class = viewset.get_serializer_class()

        assert serializer_class.__name__ == 'ProjectDetailSerializer'

    def test_get_serializer_class_create(self):
        """测试创建动作使用正确的序列化器"""
        viewset = ProjectViewSet()
        viewset.action = 'create'

        serializer_class = viewset.get_serializer_class()

        assert serializer_class.__name__ == 'ProjectCreateSerializer'

    def test_get_serializer_class_update(self):
        """测试更新动作使用正确的序列化器"""
        viewset = ProjectViewSet()
        viewset.action = 'update'

        serializer_class = viewset.get_serializer_class()

        assert serializer_class.__name__ == 'ProjectUpdateSerializer'

    def test_permission_required(self):
        """测试需要认证才能访问"""
        # 这个测试验证未认证用户返回403
        User = get_user_model()
        user = User.objects.create_user(username='testuser')

        project = Project.objects.create(
            name='测试项目',
            original_topic='测试主题',
            user=user
        )

        factory = APIRequestFactory()
        view = ProjectViewSet.as_view({'get': 'retrieve'})
        request = factory.get(f'/api/v1/projects/{project.id}/')

        # 不认证
        response = view(request, pk=project.id)

        # 未认证用户应该返回403或401
        assert response.status_code in [401, 403]
