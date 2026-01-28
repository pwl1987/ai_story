"""
Models API集成测试
测试模型管理API: ModelProvider, ModelUsageLog
"""

import pytest
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient

from apps.models.models import ModelProvider, ModelUsageLog
from apps.models.tests.factories import ModelProviderFactory, ModelUsageLogFactory

User = get_user_model()


@pytest.mark.django_db
class TestModelProviderViewSet:
    """测试模型提供商ViewSet API"""

    def setup_method(self):
        """每个测试方法前的设置"""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.admin_user = User.objects.create_superuser(
            username='admin',
            password='admin123'
        )
        self.client.force_authenticate(user=self.user)

    def test_list_providers(self):
        """测试获取模型提供商列表"""
        ModelProviderFactory(
            name='OpenAI',
            provider_type='llm',
            is_active=True
        )
        ModelProviderFactory(
            name='Stable Diffusion',
            provider_type='text2image',
            is_active=True
        )

        response = self.client.get('/api/v1/models/providers/')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] >= 2

    def test_list_providers_filtered_by_type(self):
        """测试按类型过滤模型提供商"""
        ModelProviderFactory(
            name='OpenAI',
            provider_type='llm',
            is_active=True
        )
        ModelProviderFactory(
            name='Stable Diffusion',
            provider_type='text2image',
            is_active=True
        )

        response = self.client.get('/api/v1/models/providers/?provider_type=llm')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] >= 1
        for provider in response.data['results']:
            assert provider['provider_type'] == 'llm'

    def test_list_providers_filtered_by_status(self):
        """测试按激活状态过滤"""
        ModelProviderFactory(
            name='Active Provider',
            provider_type='llm',
            is_active=True
        )
        ModelProviderFactory(
            name='Inactive Provider',
            provider_type='llm',
            is_active=False
        )

        response = self.client.get('/api/v1/models/providers/?is_active=true')

        assert response.status_code == status.HTTP_200_OK
        for provider in response.data['results']:
            assert provider['is_active'] is True

    def test_search_providers(self):
        """测试搜索模型提供商"""
        ModelProviderFactory(
            name='GPT-4 Provider',
            provider_type='llm',
            is_active=True
        )
        ModelProviderFactory(
            name='Claude Provider',
            provider_type='llm',
            is_active=True
        )

        response = self.client.get('/api/v1/models/providers/?search=GPT')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] >= 1

    def test_create_provider(self):
        """测试创建模型提供商"""
        data = {
            'name': 'Test Provider',
            'provider_type': 'llm',
            'model_name': 'gpt-4',
            'api_url': 'https://api.openai.com/v1',
            'api_key': 'test-api-key-12345',
            'executor_class': 'core.ai_client.openai_client.OpenAIClient',
            'max_tokens': 4096,  # LLM模型必填
            'priority': 10,
            'is_active': True
        }

        response = self.client.post('/api/v1/models/providers/', data)

        assert response.status_code == status.HTTP_201_CREATED
        assert ModelProvider.objects.filter(name='Test Provider').exists()

    def test_retrieve_provider(self):
        """测试获取模型提供商详情"""
        provider = ModelProviderFactory(
            name='Test Provider',
            provider_type='llm',
            is_active=True
        )

        response = self.client.get(f'/api/v1/models/providers/{provider.id}/')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == str(provider.id)

    def test_update_provider(self):
        """测试更新模型提供商"""
        provider = ModelProviderFactory(
            name='Original Name',
            provider_type='llm',
            is_active=True
        )

        data = {'name': 'Updated Name'}
        response = self.client.patch(f'/api/v1/models/providers/{provider.id}/', data)

        assert response.status_code == status.HTTP_200_OK
        provider.refresh_from_db()
        assert provider.name == 'Updated Name'

    def test_delete_provider(self):
        """测试删除模型提供商"""
        provider = ModelProviderFactory(
            name='To Delete',
            provider_type='llm',
            is_active=True
        )

        response = self.client.delete(f'/api/v1/models/providers/{provider.id}/')

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not ModelProvider.objects.filter(id=provider.id).exists()

    def test_toggle_status_active_to_inactive(self):
        """测试切换状态 - 从激活到停用"""
        provider = ModelProviderFactory(
            name='Test Provider',
            provider_type='llm',
            is_active=True
        )

        response = self.client.post(f'/api/v1/models/providers/{provider.id}/toggle_status/')

        assert response.status_code == status.HTTP_200_OK
        provider.refresh_from_db()
        assert provider.is_active is False
        assert '停用' in response.data['message']

    def test_toggle_status_inactive_to_active(self):
        """测试切换状态 - 从停用到激活"""
        provider = ModelProviderFactory(
            name='Test Provider',
            provider_type='llm',
            is_active=False
        )

        response = self.client.post(f'/api/v1/models/providers/{provider.id}/toggle_status/')

        assert response.status_code == status.HTTP_200_OK
        provider.refresh_from_db()
        assert provider.is_active is True
        assert '激活' in response.data['message']

    def test_get_provider_statistics(self):
        """测试获取模型提供商统计信息"""
        provider = ModelProviderFactory(
            name='Test Provider',
            provider_type='llm',
            is_active=True
        )
        # 创建一些使用日志
        ModelUsageLogFactory(
            model_provider=provider,
            status='success',
            tokens_used=1000
        )
        ModelUsageLogFactory(
            model_provider=provider,
            status='success',
            tokens_used=2000
        )

        response = self.client.get(f'/api/v1/models/providers/{provider.id}/statistics/')

        assert response.status_code == status.HTTP_200_OK
        # API返回total_count而非total_calls
        assert 'total_count' in response.data

    def test_test_connection(self):
        """测试连接测试API"""
        provider = ModelProviderFactory(
            name='Test Provider',
            provider_type='llm',
            is_active=True
        )

        data = {'test_prompt': 'Hello'}
        response = self.client.post(
            f'/api/v1/models/providers/{provider.id}/test_connection/',
            data,
            format='json'
        )

        # 可能成功或失败,取决于实际API配置
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_400_BAD_REQUEST
        ]

    def test_get_usage_logs(self):
        """测试获取使用日志"""
        provider = ModelProviderFactory(
            name='Test Provider',
            provider_type='llm',
            is_active=True
        )
        ModelUsageLogFactory(
            model_provider=provider,
            status='success'
        )

        response = self.client.get(f'/api/v1/models/providers/{provider.id}/usage_logs/')

        assert response.status_code == status.HTTP_200_OK
        assert 'count' in response.data
        assert 'results' in response.data

    def test_get_active_providers(self):
        """测试获取激活的模型提供商"""
        ModelProviderFactory(
            name='Active Provider',
            provider_type='llm',
            is_active=True
        )
        ModelProviderFactory(
            name='Inactive Provider',
            provider_type='llm',
            is_active=False
        )

        response = self.client.get('/api/v1/models/providers/active_providers/')

        assert response.status_code == status.HTTP_200_OK
        # 应该只返回激活的提供商
        assert all(p['is_active'] for p in response.data['results'])

    def test_get_active_providers_by_type(self):
        """测试按类型获取激活的模型提供商"""
        ModelProviderFactory(
            name='LLM Provider',
            provider_type='llm',
            is_active=True
        )
        ModelProviderFactory(
            name='Image Provider',
            provider_type='text2image',
            is_active=True
        )

        response = self.client.get('/api/v1/models/providers/active_providers/?provider_type=llm')

        assert response.status_code == status.HTTP_200_OK
        for provider in response.data['results']:
            assert provider['provider_type'] == 'llm'

    def test_get_providers_by_type(self):
        """测试按类型分组获取模型提供商"""
        ModelProviderFactory(
            name='GPT-4',
            provider_type='llm',
            is_active=True
        )
        ModelProviderFactory(
            name='Stable Diffusion',
            provider_type='text2image',
            is_active=True
        )

        response = self.client.get('/api/v1/models/providers/by_type/')

        assert response.status_code == status.HTTP_200_OK
        assert 'llm' in response.data
        assert 'text2image' in response.data

    def test_get_simple_list(self):
        """测试获取简化的模型列表"""
        ModelProviderFactory(
            name='Provider 1',
            provider_type='llm',
            is_active=True
        )
        ModelProviderFactory(
            name='Provider 2',
            provider_type='llm',
            is_active=True
        )

        response = self.client.get('/api/v1/models/providers/simple_list/')

        assert response.status_code == status.HTTP_200_OK
        # 简化列表应该只包含id和name
        assert 'count' in response.data
        assert 'results' in response.data

    def test_get_simple_list_filtered_by_type(self):
        """测试获取简化的模型列表 - 按类型过滤"""
        ModelProviderFactory(
            name='LLM Provider',
            provider_type='llm',
            is_active=True
        )
        ModelProviderFactory(
            name='Image Provider',
            provider_type='text2image',
            is_active=True
        )

        response = self.client.get('/api/v1/models/providers/simple_list/?provider_type=llm')

        assert response.status_code == status.HTTP_200_OK
        # simple_list只返回id和name，不包含provider_type
        assert 'results' in response.data
        assert len(response.data['results']) >= 1
        # 验证至少有一个LLM provider
        assert any('LLM' in p.get('name', '') for p in response.data['results'])

    def test_get_executor_choices(self):
        """测试获取执行器选项"""
        response = self.client.get('/api/v1/models/providers/executor_choices/')

        assert response.status_code == status.HTTP_200_OK
        # 应该包含所有类型的执行器
        assert 'llm' in response.data or any(key in response.data for key in ['llm', 'text2image', 'image2video'])

    def test_get_executor_choices_by_type(self):
        """测试获取特定类型的执行器选项"""
        response = self.client.get('/api/v1/models/providers/executor_choices/?provider_type=llm')

        assert response.status_code == status.HTTP_200_OK
        assert 'provider_type' in response.data
        assert response.data['provider_type'] == 'llm'
        assert 'executors' in response.data


@pytest.mark.django_db
class TestModelUsageLogViewSet:
    """测试模型使用日志ViewSet API"""

    def setup_method(self):
        """每个测试方法前的设置"""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)

        self.provider = ModelProviderFactory(
            name='Test Provider',
            provider_type='llm',
            is_active=True
        )

    def test_list_usage_logs(self):
        """测试获取使用日志列表"""
        ModelUsageLogFactory(
            model_provider=self.provider,
            status='success'
        )
        ModelUsageLogFactory(
            model_provider=self.provider,
            status='failed'
        )

        response = self.client.get('/api/v1/models/usage-logs/')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] >= 2

    def test_retrieve_usage_log(self):
        """测试获取使用日志详情"""
        log = ModelUsageLogFactory(
            model_provider=self.provider,
            status='success'
        )

        response = self.client.get(f'/api/v1/models/usage-logs/{log.id}/')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == str(log.id)

    def test_filter_logs_by_status(self):
        """测试按状态过滤日志"""
        ModelUsageLogFactory(
            model_provider=self.provider,
            status='success'
        )
        ModelUsageLogFactory(
            model_provider=self.provider,
            status='failed'
        )

        response = self.client.get('/api/v1/models/usage-logs/?status=success')

        assert response.status_code == status.HTTP_200_OK
        for log in response.data['results']:
            assert log['status'] == 'success'

    def test_filter_logs_by_project(self):
        """测试按项目过滤日志"""
        import uuid
        test_project_id = str(uuid.uuid4())
        ModelUsageLogFactory(
            model_provider=self.provider,
            status='success',
            project_id=test_project_id
        )

        response = self.client.get(f'/api/v1/models/usage-logs/?project_id={test_project_id}')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] >= 1

    def test_get_logs_by_project(self):
        """测试按项目获取日志"""
        import uuid
        project_id = str(uuid.uuid4())
        ModelUsageLogFactory(
            model_provider=self.provider,
            status='success',
            project_id=project_id
        )

        response = self.client.get(f'/api/v1/models/usage-logs/by_project/?project_id={project_id}')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] >= 1

    def test_get_logs_by_project_missing_project_id(self):
        """测试按项目获取日志 - 缺少project_id"""
        response = self.client.get('/api/v1/models/usage-logs/by_project/')

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'error' in response.data

    def test_get_failed_logs(self):
        """测试获取失败的日志"""
        ModelUsageLogFactory(
            model_provider=self.provider,
            status='success'
        )
        ModelUsageLogFactory(
            model_provider=self.provider,
            status='failed',
            error_message='API error'
        )

        response = self.client.get('/api/v1/models/usage-logs/failed_logs/')

        assert response.status_code == status.HTTP_200_OK
        # 应该只包含失败的日志
        assert response.data['count'] >= 1


@pytest.mark.django_db
class TestModelPermissions:
    """测试模型管理权限"""

    def setup_method(self):
        """每个测试方法前的设置"""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.other_user = User.objects.create_user(
            username='otheruser',
            password='otherpass123'
        )
        self.client.force_authenticate(user=self.user)

    def test_authenticated_access_required(self):
        """测试需要认证才能访问"""
        # 清除认证
        self.client.force_authenticate(user=None)

        response = self.client.get('/api/v1/models/providers/')

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestModelValidation:
    """测试模型验证逻辑"""

    def setup_method(self):
        """每个测试方法前的设置"""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)

    def test_create_provider_missing_required_fields(self):
        """测试创建提供商 - 缺少必填字段"""
        data = {
            'name': 'Incomplete Provider'
            # 缺少provider_type和其他必填字段
        }

        response = self.client.post('/api/v1/models/providers/', data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_create_provider_invalid_provider_type(self):
        """测试创建提供商 - 无效的provider_type"""
        data = {
            'name': 'Invalid Provider',
            'provider_type': 'invalid_type',
            'executor_class': 'test.Class'
        }

        response = self.client.post('/api/v1/models/providers/', data)

        # 应该返回400错误,因为provider_type无效
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_update_provider_priority(self):
        """测试更新提供商优先级"""
        provider = ModelProviderFactory(
            name='Test Provider',
            provider_type='llm',
            priority=10
        )

        data = {'priority': 20}
        response = self.client.patch(f'/api/v1/models/providers/{provider.id}/', data)

        assert response.status_code == status.HTTP_200_OK
        provider.refresh_from_db()
        assert provider.priority == 20
