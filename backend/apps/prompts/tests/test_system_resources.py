"""
Story 8.6: 全局资源配置 - 提示词 - 验收测试

遵循TDD红-绿-重构循环：
- RED: 编写失败的测试
- GREEN: 实现最小功能使测试通过
- REFACTOR: 重构代码保持质量

测试范围:
1. is_system_default字段
2. created_by外键（PROTECT）
3. can_edit()权限检查
4. 管理员创建系统资源
5. 普通用户不能编辑系统资源
6. API返回系统资源优先
"""

from django.contrib.auth.models import User
from django.test import TestCase

from apps.prompts.models import PromptTemplateSet


class SystemResourcePromptSetTest(TestCase):
    """系统资源提示词集测试"""

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

    def test_prompt_set_has_is_system_default_field(self):
        """测试：PromptTemplateSet有is_system_default字段"""
        # 创建系统级默认提示词集
        system_set = PromptTemplateSet.objects.create(
            name="系统默认提示词集",
            description="系统级默认的提示词集",
            is_system_default=True,
            created_by=self.admin,
        )

        self.assertTrue(system_set.is_system_default, "is_system_default应该为True")

    def test_prompt_set_has_created_by_field(self):
        """测试：PromptTemplateSet有created_by字段"""
        # 创建用户级提示词集
        user_set = PromptTemplateSet.objects.create(
            name="用户自定义提示词集",
            description="用户自定义的提示词集",
            is_system_default=False,
            created_by=self.normal_user,
        )

        self.assertEqual(user_set.created_by, self.normal_user, "created_by应该正确设置")

    def test_can_edit_method_system_resource_creator(self):
        """测试：系统资源的创建者可以编辑"""
        system_set = PromptTemplateSet.objects.create(
            name="系统默认提示词集",
            description="系统级默认的提示词集",
            is_system_default=True,
            created_by=self.admin,
        )

        # 创建者可以编辑
        self.assertTrue(system_set.can_edit(self.admin), "创建者应该可以编辑系统资源")

    def test_can_edit_method_system_resource_other_user(self):
        """测试：其他用户不能编辑系统资源"""
        system_set = PromptTemplateSet.objects.create(
            name="系统默认提示词集",
            description="系统级默认的提示词集",
            is_system_default=True,
            created_by=self.admin,
        )

        # 其他用户不能编辑
        self.assertFalse(
            system_set.can_edit(self.normal_user),
            "其他用户不应该可以编辑系统资源",
        )

    def test_can_edit_method_user_resource_creator(self):
        """测试：用户资源的创建者可以编辑"""
        user_set = PromptTemplateSet.objects.create(
            name="用户自定义提示词集",
            description="用户自定义的提示词集",
            is_system_default=False,
            created_by=self.normal_user,
        )

        # 创建者可以编辑
        self.assertTrue(user_set.can_edit(self.normal_user), "创建者应该可以编辑用户资源")

    def test_can_edit_method_user_resource_other_user(self):
        """测试：其他用户不能编辑用户资源"""
        user_set = PromptTemplateSet.objects.create(
            name="用户自定义提示词集",
            description="用户自定义的提示词集",
            is_system_default=False,
            created_by=self.normal_user,
        )

        # 其他用户不能编辑
        self.assertFalse(
            user_set.can_edit(self.other_user),
            "其他用户不应该可以编辑用户资源",
        )

    def test_admin_can_create_system_resource(self):
        """测试：管理员可以创建系统资源"""
        system_set = PromptTemplateSet.objects.create(
            name="系统默认提示词集",
            description="系统级默认的提示词集",
            is_system_default=True,
            created_by=self.admin,
        )

        self.assertTrue(system_set.is_system_default, "管理员应该可以创建系统资源")
        self.assertEqual(system_set.created_by, self.admin)

    def test_normal_user_can_create_user_resource(self):
        """测试：普通用户可以创建用户资源"""
        user_set = PromptTemplateSet.objects.create(
            name="用户自定义提示词集",
            description="用户自定义的提示词集",
            is_system_default=False,
            created_by=self.normal_user,
        )

        self.assertFalse(user_set.is_system_default, "普通用户创建的资源应该是用户级")
        self.assertEqual(user_set.created_by, self.normal_user)

    def test_system_resources_default_to_false(self):
        """测试：is_system_default默认为False"""
        user_set = PromptTemplateSet.objects.create(
            name="用户自定义提示词集",
            description="用户自定义的提示词集",
            created_by=self.normal_user,
        )

        self.assertFalse(user_set.is_system_default, "is_system_default应该默认为False")

    def test_created_by_uses_protect(self):
        """测试：created_by使用PROTECT保护"""
        # 这个测试确保外键使用PROTECT而不是CASCADE
        field = PromptTemplateSet._meta.get_field("created_by")
        self.assertEqual(
            field.remote_field.on_delete.__name__,
            "PROTECT",
            "created_by应该使用PROTECT保护",
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

        # 创建系统级默认提示词集
        cls.system_set = PromptTemplateSet.objects.create(
            name="系统默认提示词集",
            description="系统级默认的提示词集",
            is_system_default=True,
            created_by=cls.admin,
        )

        # 创建用户级提示词集
        cls.user_set = PromptTemplateSet.objects.create(
            name="用户自定义提示词集",
            description="用户自定义的提示词集",
            is_system_default=False,
            created_by=cls.normal_user,
        )

    def test_system_resources_come_first_in_queryset(self):
        """测试：查询时系统资源排在前面"""
        all_sets = PromptTemplateSet.objects.all()

        # 第一个应该是系统资源
        self.assertEqual(
            all_sets[0].id,
            self.system_set.id,
            "系统资源应该排在第一位",
        )

    def test_user_can_see_system_resources(self):
        """测试：普通用户可以看到系统资源"""
        from django.db import models as django_models

        # 获取用户可见的所有提示词集（系统级 + 用户自己创建的）
        user_sets = PromptTemplateSet.objects.filter(
            django_models.Q(is_system_default=True) | django_models.Q(created_by=self.normal_user)
        )

        self.assertEqual(
            user_sets.count(), 2, "用户应该可以看到2个提示词集（1个系统级 + 1个用户级）"
        )
        self.assertIn(self.system_set, user_sets)
        self.assertIn(self.user_set, user_sets)

    def test_admin_can_see_all_resources(self):
        """测试：管理员可以看到所有资源"""
        # 获取非Mock的资源（排除测试数据）
        all_sets = PromptTemplateSet.objects.filter(created_by__in=[self.admin, self.normal_user])

        self.assertEqual(all_sets.count(), 2, "管理员应该可以看到所有资源")


class SystemResourceMigrationTest(TestCase):
    """系统资源迁移测试"""

    def test_is_system_default_field_exists(self):
        """测试：is_system_default字段已存在"""
        # 这个测试确保迁移已运行
        field_names = [f.name for f in PromptTemplateSet._meta.get_fields()]
        self.assertIn("is_system_default", field_names)

    def test_created_by_field_exists(self):
        """测试：created_by字段已存在"""
        field_names = [f.name for f in PromptTemplateSet._meta.get_fields()]
        self.assertIn("created_by", field_names)
