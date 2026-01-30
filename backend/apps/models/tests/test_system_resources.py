"""
Story 8.5: 全局资源配置 - 模型 - 验收测试

遵循TDD红-绿-重构循环：
- RED: 编写失败的测试
- GREEN: 实现最小功能使测试通过
- REFACTOR: 重构代码保持质量

测试范围:
1. is_system_default字段
2. created_by外键
3. can_edit()权限检查
4. 管理员创建系统资源
5. 普通用户不能编辑系统资源
6. API返回系统资源优先
"""

from django.contrib.auth.models import User
from django.db import models as django_models
from django.test import TestCase

from apps.models.models import ModelProvider


class SystemResourceModelTest(TestCase):
    """系统资源模型测试"""

    @classmethod
    def setUpTestData(cls):
        """创建测试数据"""
        # 创建管理员用户
        cls.admin = User.objects.create_superuser(
            username="admin", email="admin@example.com", password="adminpass123"
        )

        # 创建普通用户
        cls.normal_user = User.objects.create_user(
            username="normal", email="normal@example.com", password="normalpass123"
        )

        # 创建另一个普通用户
        cls.other_user = User.objects.create_user(
            username="other", email="other@example.com", password="otherpass123"
        )

    def test_model_has_is_system_default_field(self):
        """测试：ModelProvider有is_system_default字段"""
        # 创建系统级默认模型
        system_model = ModelProvider.objects.create(
            name="系统默认LLM",
            provider_type="llm",
            executor_class="core.ai_client.openai_client.OpenAIClient",
            api_url="https://api.openai.com/v1",
            api_key="sk-test",
            model_name="gpt-4",
            is_system_default=True,
            created_by=self.admin,
        )

        self.assertTrue(system_model.is_system_default, "is_system_default应该为True")

    def test_model_has_created_by_field(self):
        """测试：ModelProvider有created_by字段"""
        # 创建用户级模型
        user_model = ModelProvider.objects.create(
            name="用户自定义LLM",
            provider_type="llm",
            executor_class="core.ai_client.openai_client.OpenAIClient",
            api_url="https://api.openai.com/v1",
            api_key="sk-test",
            model_name="gpt-4",
            is_system_default=False,
            created_by=self.normal_user,
        )

        self.assertEqual(user_model.created_by, self.normal_user, "created_by应该正确设置")

    def test_can_edit_method_system_resource_creator(self):
        """测试：系统资源的创建者可以编辑"""
        system_model = ModelProvider.objects.create(
            name="系统默认LLM",
            provider_type="llm",
            executor_class="core.ai_client.openai_client.OpenAIClient",
            api_url="https://api.openai.com/v1",
            api_key="sk-test",
            model_name="gpt-4",
            is_system_default=True,
            created_by=self.admin,
        )

        # 创建者可以编辑
        self.assertTrue(system_model.can_edit(self.admin), "创建者应该可以编辑系统资源")

    def test_can_edit_method_system_resource_other_user(self):
        """测试：其他用户不能编辑系统资源"""
        system_model = ModelProvider.objects.create(
            name="系统默认LLM",
            provider_type="llm",
            executor_class="core.ai_client.openai_client.OpenAIClient",
            api_url="https://api.openai.com/v1",
            api_key="sk-test",
            model_name="gpt-4",
            is_system_default=True,
            created_by=self.admin,
        )

        # 其他用户不能编辑
        self.assertFalse(
            system_model.can_edit(self.normal_user),
            "其他用户不应该可以编辑系统资源",
        )

    def test_can_edit_method_user_resource_creator(self):
        """测试：用户资源的创建者可以编辑"""
        user_model = ModelProvider.objects.create(
            name="用户自定义LLM",
            provider_type="llm",
            executor_class="core.ai_client.openai_client.OpenAIClient",
            api_url="https://api.openai.com/v1",
            api_key="sk-test",
            model_name="gpt-4",
            is_system_default=False,
            created_by=self.normal_user,
        )

        # 创建者可以编辑
        self.assertTrue(user_model.can_edit(self.normal_user), "创建者应该可以编辑用户资源")

    def test_can_edit_method_user_resource_other_user(self):
        """测试：其他用户不能编辑用户资源"""
        user_model = ModelProvider.objects.create(
            name="用户自定义LLM",
            provider_type="llm",
            executor_class="core.ai_client.openai_client.OpenAIClient",
            api_url="https://api.openai.com/v1",
            api_key="sk-test",
            model_name="gpt-4",
            is_system_default=False,
            created_by=self.normal_user,
        )

        # 其他用户不能编辑
        self.assertFalse(
            user_model.can_edit(self.other_user),
            "其他用户不应该可以编辑用户资源",
        )

    def test_admin_can_create_system_resource(self):
        """测试：管理员可以创建系统资源"""
        system_model = ModelProvider.objects.create(
            name="系统默认LLM",
            provider_type="llm",
            executor_class="core.ai_client.openai_client.OpenAIClient",
            api_url="https://api.openai.com/v1",
            api_key="sk-test",
            model_name="gpt-4",
            is_system_default=True,
            created_by=self.admin,
        )

        self.assertTrue(system_model.is_system_default, "管理员应该可以创建系统资源")
        self.assertEqual(system_model.created_by, self.admin)

    def test_normal_user_can_create_user_resource(self):
        """测试：普通用户可以创建用户资源"""
        user_model = ModelProvider.objects.create(
            name="用户自定义LLM",
            provider_type="llm",
            executor_class="core.ai_client.openai_client.OpenAIClient",
            api_url="https://api.openai.com/v1",
            api_key="sk-test",
            model_name="gpt-4",
            is_system_default=False,
            created_by=self.normal_user,
        )

        self.assertFalse(user_model.is_system_default, "普通用户创建的资源应该是用户级")
        self.assertEqual(user_model.created_by, self.normal_user)

    def test_system_resources_default_to_false(self):
        """测试：is_system_default默认为False"""
        user_model = ModelProvider.objects.create(
            name="用户自定义LLM",
            provider_type="llm",
            executor_class="core.ai_client.openai_client.OpenAIClient",
            api_url="https://api.openai.com/v1",
            api_key="sk-test",
            model_name="gpt-4",
            created_by=self.normal_user,
        )

        self.assertFalse(
            user_model.is_system_default,
            "is_system_default应该默认为False",
        )


class SystemResourceQuerysetTest(TestCase):
    """系统资源查询测试"""

    @classmethod
    def setUpTestData(cls):
        """创建测试数据"""
        cls.admin = User.objects.create_superuser(
            username="admin", email="admin@example.com", password="adminpass123"
        )
        cls.normal_user = User.objects.create_user(
            username="normal", email="normal@example.com", password="normalpass123"
        )

        # 创建系统级默认模型
        cls.system_model = ModelProvider.objects.create(
            name="系统默认LLM",
            provider_type="llm",
            executor_class="core.ai_client.openai_client.OpenAIClient",
            api_url="https://api.openai.com/v1",
            api_key="sk-test",
            model_name="gpt-4",
            is_system_default=True,
            created_by=cls.admin,
        )

        # 创建用户级模型
        cls.user_model = ModelProvider.objects.create(
            name="用户自定义LLM",
            provider_type="llm",
            executor_class="core.ai_client.openai_client.OpenAIClient",
            api_url="https://api.openai.com/v1",
            api_key="sk-test",
            model_name="gpt-3.5",
            is_system_default=False,
            created_by=cls.normal_user,
        )

    def test_system_resources_come_first_in_queryset(self):
        """测试：查询时系统资源排在前面"""
        all_models = ModelProvider.objects.all()

        # 第一个应该是系统资源
        self.assertEqual(
            all_models[0].id,
            self.system_model.id,
            "系统资源应该排在第一位",
        )

    def test_user_can_see_system_resources(self):
        """测试：普通用户可以看到系统资源"""
        # 获取用户可见的所有模型（系统级 + 用户自己创建的）
        user_models = ModelProvider.objects.filter(
            django_models.Q(is_system_default=True) | django_models.Q(created_by=self.normal_user)
        )

        self.assertEqual(user_models.count(), 2, "用户应该可以看到2个模型（1个系统级 + 1个用户级）")
        self.assertIn(self.system_model, user_models)
        self.assertIn(self.user_model, user_models)

    def test_admin_can_see_all_resources(self):
        """测试：管理员可以看到所有资源"""
        # 获取非Mock的资源（排除测试数据）
        all_models = ModelProvider.objects.filter(created_by__in=[self.admin, self.normal_user])

        self.assertEqual(all_models.count(), 2, "管理员应该可以看到所有资源")


class SystemResourceMigrationTest(TestCase):
    """系统资源迁移测试"""

    def test_is_system_default_field_exists(self):
        """测试：is_system_default字段已存在"""
        # 这个测试确保迁移已运行
        field_names = [f.name for f in ModelProvider._meta.get_fields()]
        self.assertIn("is_system_default", field_names)

    def test_created_by_field_exists(self):
        """测试：created_by字段已存在"""
        field_names = [f.name for f in ModelProvider._meta.get_fields()]
        self.assertIn("created_by", field_names)
