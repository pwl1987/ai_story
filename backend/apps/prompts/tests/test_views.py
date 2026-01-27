"""
Prompts API集成测试
测试提示词管理API: PromptTemplateSet, PromptTemplate, GlobalVariable
"""

import pytest
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient

from apps.prompts.models import PromptTemplateSet, PromptTemplate, GlobalVariable

User = get_user_model()


@pytest.mark.django_db
class TestPromptTemplateSetViewSet:
    """测试提示词集ViewSet API"""

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

    def test_list_prompt_sets(self):
        """测试获取提示词集列表"""
        # 创建测试数据
        PromptTemplateSet.objects.create(
            name='测试集1',
            is_active=True,
            is_default=True,
            created_by=self.admin_user
        )
        PromptTemplateSet.objects.create(
            name='我的集',
            is_active=True,
            created_by=self.user
        )

        response = self.client.get('/api/v1/prompts/sets/')

        assert response.status_code == status.HTTP_200_OK
        # 用户应该能看到默认集和自己创建的集
        assert response.data['count'] >= 1

    def test_create_prompt_set(self):
        """测试创建提示词集"""
        data = {
            'name': '新提示词集',
            'description': '测试描述',
            'is_active': True
        }

        response = self.client.post('/api/v1/prompts/sets/', data)

        assert response.status_code == status.HTTP_201_CREATED
        assert PromptTemplateSet.objects.filter(name='新提示词集').exists()

    def test_retrieve_prompt_set(self):
        """测试获取提示词集详情"""
        prompt_set = PromptTemplateSet.objects.create(
            name='测试集',
            is_active=True,
            created_by=self.user
        )

        response = self.client.get(f'/api/v1/prompts/sets/{prompt_set.id}/')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == str(prompt_set.id)

    def test_update_prompt_set(self):
        """测试更新提示词集"""
        prompt_set = PromptTemplateSet.objects.create(
            name='原始名称',
            is_active=True,
            created_by=self.user
        )

        data = {'name': '更新后的名称'}
        response = self.client.patch(f'/api/v1/prompts/sets/{prompt_set.id}/', data)

        assert response.status_code == status.HTTP_200_OK
        prompt_set.refresh_from_db()
        assert prompt_set.name == '更新后的名称'

    def test_delete_prompt_set(self):
        """测试删除提示词集"""
        prompt_set = PromptTemplateSet.objects.create(
            name='待删除',
            is_active=True,
            created_by=self.user
        )

        response = self.client.delete(f'/api/v1/prompts/sets/{prompt_set.id}/')

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not PromptTemplateSet.objects.filter(id=prompt_set.id).exists()

    def test_clone_prompt_set(self):
        """测试克隆提示词集"""
        original_set = PromptTemplateSet.objects.create(
            name='原始集',
            is_active=True,
            created_by=self.user
        )
        # 创建模板
        PromptTemplate.objects.create(
            template_set=original_set,
            stage_type='rewrite',
            template_content='原始内容'
        )

        data = {'name': '克隆集'}
        response = self.client.post(f'/api/v1/prompts/sets/{original_set.id}/clone/', data)

        assert response.status_code == status.HTTP_201_CREATED
        assert PromptTemplateSet.objects.filter(name='克隆集').exists()

        # 验证模板也被复制了
        cloned_set = PromptTemplateSet.objects.get(name='克隆集')
        assert cloned_set.templates.count() == 1

    def test_clone_missing_name(self):
        """测试克隆提示词集 - 缺少名称"""
        prompt_set = PromptTemplateSet.objects.create(
            name='测试集',
            created_by=self.user
        )

        response = self.client.post(f'/api/v1/prompts/sets/{prompt_set.id}/clone/', {})

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_set_default_prompt_set(self):
        """测试设置为默认提示词集"""
        prompt_set = PromptTemplateSet.objects.create(
            name='默认集',
            created_by=self.admin_user
        )

        # 使用管理员权限
        self.client.force_authenticate(user=self.admin_user)

        response = self.client.post(f'/api/v1/prompts/sets/{prompt_set.id}/set_default/')

        assert response.status_code == status.HTTP_200_OK
        prompt_set.refresh_from_db()
        assert prompt_set.is_default is True

    def test_set_default_requires_admin(self):
        """测试设置默认集需要管理员权限"""
        prompt_set = PromptTemplateSet.objects.create(
            name='测试集',
            created_by=self.user
        )

        # 使用普通用户
        response = self.client.post(f'/api/v1/prompts/sets/{prompt_set.id}/set_default/')

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_get_default_prompt_set(self):
        """测试获取默认提示词集"""
        default_set = PromptTemplateSet.objects.create(
            name='默认集',
            is_default=True,
            created_by=self.admin_user
        )

        response = self.client.get('/api/v1/prompts/sets/default/')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == str(default_set.id)

    def test_get_default_not_found(self):
        """测试获取默认集 - 不存在"""
        response = self.client.get('/api/v1/prompts/sets/default/')

        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
class TestPromptTemplateViewSet:
    """测试提示词模板ViewSet API"""

    def setup_method(self):
        """每个测试方法前的设置"""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)

        self.template_set = PromptTemplateSet.objects.create(
            name='测试集',
            created_by=self.user
        )

    def test_list_templates(self):
        """测试获取模板列表"""
        PromptTemplate.objects.create(
            template_set=self.template_set,
            stage_type='rewrite',
            template_content='测试内容'
        )

        response = self.client.get('/api/v1/prompts/templates/')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] >= 1

    def test_create_template(self):
        """测试创建模板"""
        data = {
            'template_set': str(self.template_set.id),
            'stage_type': 'rewrite',
            'template_content': '测试模板内容: {{ topic }}',
            'variables': {'topic': 'string'}
        }

        response = self.client.post('/api/v1/prompts/templates/', data, format='json')

        assert response.status_code == status.HTTP_201_CREATED
        assert PromptTemplate.objects.filter(stage_type='rewrite').exists()

    def test_retrieve_template(self):
        """测试获取模板详情"""
        template = PromptTemplate.objects.create(
            template_set=self.template_set,
            stage_type='storyboard',
            template_content='测试内容'
        )

        response = self.client.get(f'/api/v1/prompts/templates/{template.id}/')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == str(template.id)

    def test_update_template(self):
        """测试更新模板"""
        template = PromptTemplate.objects.create(
            template_set=self.template_set,
            stage_type='rewrite',
            template_content='原始内容'
        )

        data = {'template_content': '更新后的内容'}
        response = self.client.patch(f'/api/v1/prompts/templates/{template.id}/', data)

        assert response.status_code == status.HTTP_200_OK
        template.refresh_from_db()
        assert template.template_content == '更新后的内容'

    def test_delete_template(self):
        """测试删除模板"""
        template = PromptTemplate.objects.create(
            template_set=self.template_set,
            stage_type='rewrite',
            template_content='测试'
        )

        response = self.client.delete(f'/api/v1/prompts/templates/{template.id}/')

        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_create_version(self):
        """测试创建新版本"""
        original_template = PromptTemplate.objects.create(
            template_set=self.template_set,
            stage_type='rewrite',
            template_content='原始内容',
            version=1
        )

        data = {
            'template_content': '新版本内容',
            'variables': {'topic': 'string'}
        }

        response = self.client.post(
            f'/api/v1/prompts/templates/{original_template.id}/create_version/',
            data,
            format='json'
        )

        assert response.status_code == status.HTTP_201_CREATED

        # 验证新版本创建成功
        new_template = PromptTemplate.objects.filter(
            template_set=self.template_set,
            stage_type='rewrite'
        ).order_by('-version').first()

        assert new_template.version == 2
        assert new_template.template_content == '新版本内容'

    def test_get_versions(self):
        """测试获取版本历史"""
        template = PromptTemplate.objects.create(
            template_set=self.template_set,
            stage_type='rewrite',
            template_content='版本1',
            version=1
        )

        response = self.client.get(f'/api/v1/prompts/templates/{template.id}/versions/')

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 1

    def test_validate_template(self):
        """测试验证模板语法"""
        template = PromptTemplate.objects.create(
            template_set=self.template_set,
            stage_type='rewrite',
            template_content='测试: {{ topic }}'
        )

        data = {'template_content': '有效模板: {{ variable }}'}
        response = self.client.post(
            f'/api/v1/prompts/templates/{template.id}/validate/',
            data
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data['valid'] is True

    def test_preview_template(self):
        """测试预览模板渲染"""
        template = PromptTemplate.objects.create(
            template_set=self.template_set,
            stage_type='rewrite',
            template_content='主题: {{ topic }}, 风格: {{ style }}'
        )

        data = {
            'variables': {
                'topic': '科幻故事',
                'style': '赛博朋克'
            }
        }

        response = self.client.post(
            f'/api/v1/prompts/templates/{template.id}/preview/',
            data,
            format='json'
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
        assert '科幻故事' in response.data['rendered_content']

    def test_preview_invalid_template(self):
        """测试预览无效模板"""
        template = PromptTemplate.objects.create(
            template_set=self.template_set,
            stage_type='rewrite',
            template_content='无效模板: {{ undefined_var }'
        )

        data = {'variables': {}}

        response = self.client.post(
            f'/api/v1/prompts/templates/{template.id}/preview/',
            data,
            format='json'
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data['success'] is False


@pytest.mark.django_db
class TestGlobalVariableViewSet:
    """测试全局变量ViewSet API"""

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

    def test_list_variables(self):
        """测试获取变量列表"""
        # 创建系统级变量
        GlobalVariable.objects.create(
            key='system_var',
            value='系统值',
            scope='system',
            group='系统',
            created_by=self.admin_user
        )
        # 创建用户级变量
        GlobalVariable.objects.create(
            key='user_var',
            value='用户值',
            scope='user',
            group='用户',
            created_by=self.user
        )

        response = self.client.get('/api/v1/prompts/variables/')

        assert response.status_code == status.HTTP_200_OK
        # 用户应该能看到系统级变量和自己创建的用户级变量
        assert response.data['count'] >= 1

    def test_create_variable(self):
        """测试创建变量"""
        data = {
            'key': 'brand_name',
            'value': '我的品牌',
            'variable_type': 'string',
            'scope': 'user',
            'group': '品牌',
            'description': '品牌名称'
        }

        response = self.client.post('/api/v1/prompts/variables/', data)

        assert response.status_code == status.HTTP_201_CREATED
        assert GlobalVariable.objects.filter(key='brand_name').exists()

    def test_retrieve_variable(self):
        """测试获取变量详情"""
        variable = GlobalVariable.objects.create(
            key='test_var',
            value='test_value',
            scope='user',
            created_by=self.user
        )

        response = self.client.get(f'/api/v1/prompts/variables/{variable.id}/')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['key'] == 'test_var'

    def test_update_variable(self):
        """测试更新变量"""
        variable = GlobalVariable.objects.create(
            key='test_var',
            value='原始值',
            scope='user',
            created_by=self.user
        )

        data = {'value': '更新后的值'}
        response = self.client.patch(f'/api/v1/prompts/variables/{variable.id}/', data)

        assert response.status_code == status.HTTP_200_OK
        variable.refresh_from_db()
        assert variable.value == '更新后的值'

    def test_delete_user_variable(self):
        """测试删除用户级变量"""
        variable = GlobalVariable.objects.create(
            key='test_var',
            value='test',
            scope='user',
            created_by=self.user
        )

        response = self.client.delete(f'/api/v1/prompts/variables/{variable.id}/')

        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_delete_system_variable_requires_admin(self):
        """测试删除系统级变量需要管理员权限"""
        variable = GlobalVariable.objects.create(
            key='system_var',
            value='system',
            scope='system',
            created_by=self.admin_user
        )

        # 使用普通用户尝试删除
        response = self.client.delete(f'/api/v1/prompts/variables/{variable.id}/')

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_get_variable_groups(self):
        """测试获取变量分组"""
        GlobalVariable.objects.create(
            key='var1',
            value='val1',
            scope='user',
            group='分组1',
            created_by=self.user
        )
        GlobalVariable.objects.create(
            key='var2',
            value='val2',
            scope='user',
            group='分组2',
            created_by=self.user
        )

        response = self.client.get('/api/v1/prompts/variables/groups/')

        assert response.status_code == status.HTTP_200_OK
        assert '分组1' in response.data['groups']

    def test_batch_create_variables(self):
        """测试批量创建变量"""
        data = {
            'variables': [
                {
                    'key': 'brand_name',
                    'value': '我的品牌',
                    'variable_type': 'string',
                    'scope': 'user',
                    'group': '品牌'
                },
                {
                    'key': 'brand_color',
                    'value': '#FF0000',
                    'variable_type': 'string',
                    'scope': 'user',
                    'group': '品牌'
                }
            ]
        }

        response = self.client.post('/api/v1/prompts/variables/batch_create/', data, format='json')

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['summary']['created_count'] == 2

    def test_validate_key_valid(self):
        """测试验证变量键 - 有效"""
        data = {
            'key': 'my_variable',
            'scope': 'user'
        }

        response = self.client.post('/api/v1/prompts/variables/validate_key/', data, format='json')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['valid'] is True

    def test_validate_key_invalid_format(self):
        """测试验证变量键 - 无效格式"""
        data = {
            'key': '123invalid',  # 以数字开头
            'scope': 'user'
        }

        response = self.client.post('/api/v1/prompts/variables/validate_key/', data, format='json')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['valid'] is False

    def test_validate_key_python_keyword(self):
        """测试验证变量键 - Python保留字"""
        data = {
            'key': 'class',  # Python保留字
            'scope': 'user'
        }

        response = self.client.post('/api/v1/prompts/variables/validate_key/', data, format='json')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['valid'] is False


@pytest.mark.django_db
class TestPromptPermissions:
    """测试提示词权限"""

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

    def test_user_can_only_access_own_template_sets(self):
        """测试用户只能访问自己的或默认的提示词集"""
        # 创建其他用户的非默认集
        PromptTemplateSet.objects.create(
            name='其他用户的集',
            is_default=False,
            created_by=self.other_user
        )
        # 创建默认集
        default_set = PromptTemplateSet.objects.create(
            name='默认集',
            is_default=True,
            created_by=self.other_user
        )

        response = self.client.get('/api/v1/prompts/sets/')

        assert response.status_code == status.HTTP_200_OK
        # 应该只能看到默认集
        assert response.data['count'] == 1
        assert response.data['results'][0]['id'] == str(default_set.id)
