"""
Story 8.9: 用户删除级联删除 - 验收测试

遵循TDD红-绿-重构循环：
- RED: 编写失败的测试
- GREEN: 实现最小功能使测试通过
- REFACTOR: 重构代码保持质量

测试范围:
1. 删除普通用户时级联删除用户资源
2. 删除管理员时转移系统资源所有权
3. UserProfile 自动级联删除
4. ProtectedError 不再抛出
"""

from django.db.models import ProtectedError
from django.test import TestCase

# 确保signals被注册（虽然我们使用UserProxy，但保留导入以防万一）
import apps.users.signals  # noqa: F401
from apps.models.models import ModelProvider
from apps.prompts.models import PromptTemplateSet
from apps.users.models import UserProfile, UserProxy


class UserDeletionCascadeTestSuite(TestCase):
    """用户删除级联删除测试套件"""

    @classmethod
    def setUpTestData(cls):
        """创建测试数据"""
        # 创建管理员
        cls.admin = UserProxy.objects.create_superuser(
            username="admin", email="admin@example.com", password="adminpass123"
        )
        UserProfile.objects.create(user=cls.admin)

        # 创建另一个管理员（用于测试所有权转移）
        cls.admin2 = UserProxy.objects.create_superuser(
            username="admin2", email="admin2@example.com", password="adminpass123"
        )
        UserProfile.objects.create(user=cls.admin2)

        # 创建普通用户
        cls.normal_user = UserProxy.objects.create_user(
            username="normal", email="normal@example.com", password="normalpass123"
        )
        UserProfile.objects.create(user=cls.normal_user)

        # 创建用户级模型提供商
        cls.user_model = ModelProvider.objects.create(
            name="用户模型",
            provider_type="llm",
            executor_class="core.ai_client.openai_client.OpenAIClient",
            api_url="https://api.openai.com/v1",
            api_key="sk-test",
            model_name="gpt-4",
            is_system_default=False,
            created_by=cls.normal_user,
        )

        # 创建系统级模型提供商（admin创建）
        cls.system_model = ModelProvider.objects.create(
            name="系统模型",
            provider_type="llm",
            executor_class="core.ai_client.openai_client.OpenAIClient",
            api_url="https://api.openai.com/v1",
            api_key="sk-test",
            model_name="gpt-4",
            is_system_default=True,
            created_by=cls.admin,
        )

        # 创建用户级提示词集
        cls.user_prompt_set = PromptTemplateSet.objects.create(
            name="用户提示词集",
            description="用户自定义提示词集",
            is_system_default=False,
            created_by=cls.normal_user,
        )

        # 创建系统级提示词集（admin创建）
        cls.system_prompt_set = PromptTemplateSet.objects.create(
            name="系统提示词集",
            description="系统级默认提示词集",
            is_system_default=True,
            created_by=cls.admin,
        )

    def test_user_profile_cascade_deleted(self):
        """测试：删除用户时Profile自动级联删除"""
        user_id = self.normal_user.id
        profile_id = self.normal_user.profile.id

        # 删除用户
        self.normal_user.delete()

        # 验证用户已删除
        self.assertFalse(UserProxy.objects.filter(id=user_id).exists(), "用户应该被删除")

        # 验证Profile已级联删除
        self.assertFalse(
            UserProfile.objects.filter(id=profile_id).exists(),
            "UserProfile应该级联删除",
        )

    def test_user_resources_cascade_deleted(self):
        """测试：删除用户时用户资源级联删除"""
        user_model_id = self.user_model.id
        user_prompt_set_id = self.user_prompt_set.id

        # 删除用户
        self.normal_user.delete()

        # 验证用户级模型已级联删除
        self.assertFalse(
            ModelProvider.objects.filter(id=user_model_id).exists(),
            "用户级模型应该级联删除",
        )

        # 验证用户级提示词集已级联删除
        self.assertFalse(
            PromptTemplateSet.objects.filter(id=user_prompt_set_id).exists(),
            "用户级提示词集应该级联删除",
        )

    def test_system_resources_ownership_transferred(self):
        """测试：删除管理员时系统资源所有权转移"""
        system_model_id = self.system_model.id
        system_prompt_set_id = self.system_prompt_set.id
        admin_id = self.admin.id

        # 删除管理员
        self.admin.delete()

        # 验证管理员已删除
        self.assertFalse(UserProxy.objects.filter(id=admin_id).exists(), "管理员应该被删除")

        # 验证系统模型仍然存在
        self.assertTrue(
            ModelProvider.objects.filter(id=system_model_id).exists(),
            "系统模型应该保留",
        )

        # 验证系统提示词集仍然存在
        self.assertTrue(
            PromptTemplateSet.objects.filter(id=system_prompt_set_id).exists(),
            "系统提示词集应该保留",
        )

        # 验证所有权已转移给其他superuser
        self.system_model.refresh_from_db()
        self.system_prompt_set.refresh_from_db()

        self.assertEqual(
            self.system_model.created_by,
            self.admin2,
            "系统模型所有权应该转移给admin2",
        )
        self.assertEqual(
            self.system_prompt_set.created_by,
            self.admin2,
            "系统提示词集所有权应该转移给admin2",
        )

    def test_delete_user_does_not_raise_protected_error(self):
        """测试：删除用户不再抛出ProtectedError"""
        # 应该能正常删除，不抛出ProtectedError
        try:
            self.normal_user.delete()
            self.assertTrue(True, "用户删除应该成功")
        except ProtectedError:
            self.fail("不应该抛出ProtectedError")

    def test_delete_admin_does_not_raise_protected_error(self):
        """测试：删除管理员不再抛出ProtectedError"""
        # 应该能正常删除，不抛出ProtectedError
        try:
            self.admin.delete()
            self.assertTrue(True, "管理员删除应该成功")
        except ProtectedError:
            self.fail("不应该抛出ProtectedError")

    def test_delete_last_superuser_raises_error(self):
        """测试：删除最后一个superuser应该被阻止"""
        # 先删除admin2
        self.admin2.delete()

        # 尝试删除最后一个superuser（admin）
        # Django的User模型默认会阻止删除最后一个superuser
        with self.assertRaises(Exception):  # noqa: B017 - 测试中需要捕获通用异常
            self.admin.delete()

    def test_transfer_to_first_available_superuser(self):
        """测试：系统资源转移给第一个可用的superuser"""
        # 创建第三个superuser
        admin3 = UserProxy.objects.create_superuser(
            username="admin3", email="admin3@example.com", password="adminpass123"
        )
        UserProfile.objects.create(user=admin3)

        # 删除admin
        self.admin.delete()

        # 验证系统资源所有权转移给admin2（第一个可用的superuser）
        self.system_model.refresh_from_db()
        self.system_prompt_set.refresh_from_db()

        self.assertEqual(
            self.system_model.created_by,
            self.admin2,
            "应该转移给第一个可用的superuser（admin2）",
        )

    def test_mixed_resources_handling(self):
        """测试：混合资源（系统+用户）的正确处理"""
        # 为admin创建一些用户级资源
        admin_user_model = ModelProvider.objects.create(
            name="管理员用户级模型",
            provider_type="llm",
            executor_class="core.ai_client.openai_client.OpenAIClient",
            api_url="https://api.openai.com/v1",
            api_key="sk-test",
            model_name="gpt-4",
            is_system_default=False,
            created_by=self.admin,
        )

        admin_user_model_id = admin_user_model.id
        system_model_id = self.system_model.id

        # 删除admin
        self.admin.delete()

        # 验证admin的用户级模型已级联删除
        self.assertFalse(
            ModelProvider.objects.filter(id=admin_user_model_id).exists(),
            "管理员的用户级模型应该级联删除",
        )

        # 验证admin的系统级模型已转移所有权
        self.assertTrue(
            ModelProvider.objects.filter(id=system_model_id).exists(),
            "管理员的系统级模型应该保留",
        )
        self.system_model.refresh_from_db()
        self.assertEqual(
            self.system_model.created_by,
            self.admin2,
            "系统级模型应该转移所有权",
        )


class UserDeletionEdgeCasesTestSuite(TestCase):
    """用户删除边缘案例测试套件"""

    @classmethod
    def setUpTestData(cls):
        """创建测试数据"""
        cls.admin = UserProxy.objects.create_superuser(
            username="admin", email="admin@example.com", password="adminpass123"
        )
        UserProfile.objects.create(user=cls.admin)

        cls.normal_user = UserProxy.objects.create_user(
            username="normal", email="normal@example.com", password="normalpass123"
        )
        UserProfile.objects.create(user=cls.normal_user)

    def test_delete_user_with_no_resources(self):
        """测试：删除没有任何资源的用户"""
        user = UserProxy.objects.create_user(
            username="nor resources", email="no_resources@example.com", password="pass123"
        )
        UserProfile.objects.create(user=user)

        # 应该能正常删除
        user.delete()
        self.assertFalse(UserProxy.objects.filter(username="no resources").exists())

    def test_delete_user_without_profile(self):
        """测试：删除没有Profile的用户（边缘情况）"""
        # 创建用户但不创建Profile
        user = UserProxy.objects.create_user(
            username="noprofile", email="noprofile@example.com", password="pass123"
        )

        # 应该能正常删除
        user.delete()
        self.assertFalse(UserProxy.objects.filter(username="noprofile").exists())
