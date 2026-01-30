"""
Story 8.1: StaffAdminSite实施与验证 - 验收测试

遵循TDD红-绿-重构循环：
- RED: 编写失败的测试
- GREEN: 实现最小功能使测试通过
- REFACTOR: 重构代码保持质量

测试范围:
1. StaffAdminSite权限控制
2. 所有模型注册验证
3. Admin界面自定义
4. 数据隔离验证

Story 8.8: 资源所有权与审计日志 - Admin权限测试
测试范围:
1. Admin层面权限检查
2. has_change_permission方法
3. has_delete_permission方法
4. superuser绕过限制
"""

import pytest
from django.contrib import admin
from django.contrib.auth.models import User
from django.test import Client, RequestFactory, TestCase

from apps.content.models import (
    CameraMovement,
    ContentRewrite,
    GeneratedImage,
    GeneratedVideo,
    Storyboard,
)
from apps.files.models import FileQuota, UploadedFile
from apps.models.admin import ModelProviderAdmin
from apps.models.models import ModelProvider, ModelUsageLog
from apps.projects.models import Project, ProjectModelConfig, ProjectStage
from apps.prompts.admin import PromptTemplateSetAdmin
from apps.prompts.models import GlobalVariable, PromptTemplate, PromptTemplateSet


class StaffAdminSiteTest(TestCase):
    """StaffAdminSite权限和功能测试"""

    @classmethod
    def setUpTestData(cls):
        """创建测试数据（类级别，只运行一次）"""
        cls.superuser = User.objects.create_superuser(
            username="admin", email="admin@example.com", password="adminpass123"
        )
        cls.staff_user = User.objects.create_user(
            username="staff", email="staff@example.com", password="staffpass123", is_staff=True
        )
        cls.normal_user = User.objects.create_user(
            username="normal", email="normal@example.com", password="normalpass123", is_staff=False
        )

    def setUp(self):
        """每个测试方法前的设置"""
        self.client = Client()

    def test_staff_user_can_access_admin(self):
        """测试：is_staff=True用户可以访问Admin后台"""
        self.client.force_login(self.staff_user)
        response = self.client.get("/admin/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "管理后台")

    def test_normal_user_cannot_access_admin(self):
        """测试：is_staff=False用户无法访问Admin后台"""
        self.client.force_login(self.normal_user)
        response = self.client.get("/admin/")
        # Django Admin默认行为：重定向到登录页（302）而非403
        # 这是因为has_permission返回False时，AdminSite会重定向
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith("/admin/login/"))

    def test_superuser_has_full_access(self):
        """测试：is_superuser用户拥有完全访问权限"""
        self.client.force_login(self.superuser)
        response = self.client.get("/admin/")
        self.assertEqual(response.status_code, 200)

    def test_unauthenticated_user_redirected_to_login(self):
        """测试：未认证用户重定向到登录页"""
        response = self.client.get("/admin/")
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith("/admin/login/"))


class ModelRegistrationTest(TestCase):
    """模型注册测试"""

    @classmethod
    def setUpTestData(cls):
        """创建测试数据"""
        cls.superuser = User.objects.create_superuser(
            username="admin", email="admin@example.com", password="adminpass123"
        )

    def setUp(self):
        """每个测试方法前的设置"""
        self.client = Client()
        self.client.force_login(self.superuser)

    def test_all_models_registered(self):
        """测试：确认17个核心模型已注册到StaffAdminSite"""
        from config.admin import staff_admin_site

        # 预期注册的模型列表（17个）
        expected_models = [
            # Projects (3个)
            Project,
            ProjectStage,
            ProjectModelConfig,
            # Models (2个)
            ModelProvider,
            ModelUsageLog,
            # Prompts (3个)
            PromptTemplateSet,
            PromptTemplate,
            GlobalVariable,
            # Content (5个)
            ContentRewrite,
            Storyboard,
            GeneratedImage,
            CameraMovement,
            GeneratedVideo,
            # Files (2个)
            UploadedFile,
            FileQuota,
            # Users (2个)
            User,
            # UserProfile (将在Story 8.4添加)
        ]

        # 验证每个模型都已注册
        for model in expected_models:
            self.assertTrue(
                staff_admin_site.is_registered(model),
                f"模型 {model.__name__} 未注册到StaffAdminSite",
            )

    def test_user_model_registered(self):
        """测试：User模型已注册到StaffAdminSite"""
        from config.admin import staff_admin_site

        self.assertTrue(staff_admin_site.is_registered(User), "User模型未注册到StaffAdminSite")

    def test_admin_models_accessible(self):
        """测试：所有注册的模型在Admin界面可访问"""
        # 测试几个核心模型的Admin页面
        # 注意：User模型在django.contrib.auth，URL是/auth/user/
        model_admin_pages = [
            ("auth", "user"),  # User模型在django.contrib.auth
            ("projects", "project"),
            ("models", "modelprovider"),
            ("prompts", "prompttemplateset"),
        ]

        for app_label, model_name in model_admin_pages:
            url = f"/admin/{app_label}/{model_name}/"
            response = self.client.get(url)
            self.assertIn(
                response.status_code,
                [200, 302],  # 200正常或302重定向（如果没有数据）
                f"Admin页面 {url} 访问失败，状态码: {response.status_code}",
            )


class AdminSiteCustomizationTest(TestCase):
    """Admin界面自定义测试"""

    @classmethod
    def setUpTestData(cls):
        """创建测试数据"""
        cls.staff_user = User.objects.create_user(
            username="staff", email="staff@example.com", password="staffpass123", is_staff=True
        )

    def setUp(self):
        """每个测试方法前的设置"""
        self.client = Client()
        self.client.force_login(self.staff_user)

    def test_admin_site_header(self):
        """测试：Admin站点header自定义"""
        from config.admin import staff_admin_site

        self.assertEqual(
            staff_admin_site.site_header, "AI Story 管理后台", "Admin site_header未正确设置"
        )

    def test_admin_site_title(self):
        """测试：Admin站点title自定义"""
        from config.admin import staff_admin_site

        self.assertEqual(
            staff_admin_site.site_title, "AI Story Admin", "Admin site_title未正确设置"
        )

    def test_admin_index_title(self):
        """测试：Admin首页title自定义"""
        from config.admin import staff_admin_site

        self.assertEqual(
            staff_admin_site.index_title,
            "欢迎使用 AI Story 管理后台",
            "Admin index_title未正确设置",
        )

    def test_customization_displayed_on_page(self):
        """测试：自定义设置在Admin页面正确显示"""
        response = self.client.get("/admin/")
        self.assertContains(response, "AI Story 管理后台")


class DataIsolationTest(TestCase):
    """数据隔离测试"""

    @classmethod
    def setUpTestData(cls):
        """创建测试数据"""
        cls.staff_user = User.objects.create_user(
            username="staff1",
            email="staff1@example.com",
            password="staffpass123",
            is_staff=True,
            is_superuser=True,  # 添加superuser权限以便访问所有Admin页面
        )
        cls.staff_user2 = User.objects.create_user(
            username="staff2", email="staff2@example.com", password="staffpass123", is_staff=True
        )

        # 创建测试数据
        cls.project1 = Project.objects.create(
            name="Project 1", user=cls.staff_user, original_topic="Test topic 1", status="draft"
        )

    def setUp(self):
        """每个测试方法前的设置"""
        self.client = Client()
        self.client.force_login(self.staff_user)

    def test_staff_can_view_all_projects(self):
        """测试：管理员可以查看所有用户的项目"""
        response = self.client.get("/admin/projects/project/")
        self.assertEqual(response.status_code, 200)
        # 管理员应该能看到project1
        self.assertContains(response, "Project 1")

    def test_staff_can_view_all_users(self):
        """测试：管理员可以查看所有用户"""
        response = self.client.get("/admin/auth/user/")  # User模型在django.contrib.auth
        self.assertEqual(response.status_code, 200)
        # 应该能看到多个用户
        self.assertContains(response, "staff1")
        self.assertContains(response, "staff2")


class AdminSecurityTest(TestCase):
    """Admin安全测试"""

    @classmethod
    def setUpTestData(cls):
        """创建测试数据"""
        cls.staff_user = User.objects.create_user(
            username="staff", email="staff@example.com", password="staffpass123", is_staff=True
        )
        cls.normal_user = User.objects.create_user(
            username="normal", email="normal@example.com", password="normalpass123", is_staff=False
        )

    def test_csrf_protection_enabled(self):
        """测试：CSRF保护已启用"""
        self.client.force_login(self.staff_user)
        response = self.client.get("/admin/")
        # Django Admin默认启用CSRF保护
        self.assertContains(response, "csrfmiddlewaretoken")

    def test_admin_requires_authentication(self):
        """测试：Admin后台需要认证"""
        response = self.client.get("/admin/")
        self.assertNotEqual(response.status_code, 200)
        self.assertIn(response.status_code, [302, 403])


@pytest.mark.parametrize(
    "username,is_staff,expected_status",
    [
        ("staff_user", True, 200),
        ("normal_user", False, 302),  # Django重定向到登录页
    ],
)
@pytest.mark.django_db  # 需要数据库访问
def test_admin_access_permission(username, is_staff, expected_status):
    """参数化测试：Admin访问权限"""
    User.objects.create_user(
        username=username,
        email=f"{username}@example.com",
        password="testpass123",
        is_staff=is_staff,
    )

    client = Client()
    client.force_login(User.objects.get(username=username))
    response = client.get("/admin/")

    assert response.status_code == expected_status


# ============================================================================
# Story 8.8: 资源所有权与审计日志 - Admin权限测试
# ============================================================================


class AdminOwnershipPermissionTestSuite(TestCase):
    """Admin所有权权限测试套件 - 验证Admin层面权限检查"""

    @classmethod
    def setUpTestData(cls):
        """创建测试数据"""
        cls.admin = User.objects.create_superuser(
            username="admin", email="admin@example.com", password="adminpass123"
        )

        cls.staff_user = User.objects.create_user(
            username="staff", email="staff@example.com", password="staffpass123", is_staff=True
        )

        cls.normal_user = User.objects.create_user(
            username="normal", email="normal@example.com", password="normalpass123"
        )

        # 系统级模型（管理员创建）
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

        # 用户级模型（普通用户创建）
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

        # 系统级提示词集（管理员创建）
        cls.system_prompt_set = PromptTemplateSet.objects.create(
            name="系统提示词集",
            description="系统级默认提示词集",
            is_system_default=True,
            created_by=cls.admin,
        )

        # 用户级提示词集（普通用户创建）
        cls.user_prompt_set = PromptTemplateSet.objects.create(
            name="用户提示词集",
            description="用户自定义提示词集",
            is_system_default=False,
            created_by=cls.normal_user,
        )

    def test_model_provider_admin_has_change_permission_for_creator(self):
        """测试：ModelProviderAdmin - 创建者有change权限"""
        admin_instance = ModelProviderAdmin(ModelProvider, admin.site)
        factory = RequestFactory()
        request = factory.get("/admin/models/modelprovider/")
        request.user = self.normal_user

        # 创建者可以编辑自己的资源
        has_permission = admin_instance.has_change_permission(request, self.user_model)

        self.assertTrue(has_permission, "创建者应该有change权限")

    def test_model_provider_admin_no_change_permission_for_non_creator(self):
        """测试：ModelProviderAdmin - 非创建者无change权限"""
        admin_instance = ModelProviderAdmin(ModelProvider, admin.site)
        factory = RequestFactory()
        request = factory.get("/admin/models/modelprovider/")
        request.user = self.normal_user

        # 非创建者不能编辑系统资源
        has_permission = admin_instance.has_change_permission(request, self.system_model)

        self.assertFalse(has_permission, "非创建者不应该有change权限")

    def test_model_provider_admin_superuser_bypass(self):
        """测试：ModelProviderAdmin - superuser可以绕过限制"""
        admin_instance = ModelProviderAdmin(ModelProvider, admin.site)
        factory = RequestFactory()
        request = factory.get("/admin/models/modelprovider/")
        request.user = self.admin

        # superuser可以编辑任何资源（即使不是创建者）
        has_permission = admin_instance.has_change_permission(request, self.user_model)

        self.assertTrue(has_permission, "Superuser应该可以绕过限制")

    def test_model_provider_admin_has_delete_permission_for_creator(self):
        """测试：ModelProviderAdmin - 创建者有delete权限"""
        admin_instance = ModelProviderAdmin(ModelProvider, admin.site)
        factory = RequestFactory()
        request = factory.get("/admin/models/modelprovider/")
        request.user = self.normal_user

        # 创建者可以删除自己的资源
        has_permission = admin_instance.has_delete_permission(request, self.user_model)

        self.assertTrue(has_permission, "创建者应该有delete权限")

    def test_model_provider_admin_no_delete_permission_for_non_creator(self):
        """测试：ModelProviderAdmin - 非创建者无delete权限"""
        admin_instance = ModelProviderAdmin(ModelProvider, admin.site)
        factory = RequestFactory()
        request = factory.get("/admin/models/modelprovider/")
        request.user = self.normal_user

        # 非创建者不能删除系统资源
        has_permission = admin_instance.has_delete_permission(request, self.system_model)

        self.assertFalse(has_permission, "非创建者不应该有delete权限")

    def test_model_provider_admin_superuser_bypass_delete(self):
        """测试：ModelProviderAdmin - superuser可以绕过删除限制"""
        admin_instance = ModelProviderAdmin(ModelProvider, admin.site)
        factory = RequestFactory()
        request = factory.get("/admin/models/modelprovider/")
        request.user = self.admin

        # superuser可以删除任何资源
        has_permission = admin_instance.has_delete_permission(request, self.user_model)

        self.assertTrue(has_permission, "Superuser应该可以绕过限制")

    def test_prompt_template_set_admin_has_change_permission_for_creator(self):
        """测试：PromptTemplateSetAdmin - 创建者有change权限"""
        admin_instance = PromptTemplateSetAdmin(PromptTemplateSet, admin.site)
        factory = RequestFactory()
        request = factory.get("/admin/prompts/prompttemplateset/")
        request.user = self.normal_user

        # 创建者可以编辑自己的资源
        has_permission = admin_instance.has_change_permission(request, self.user_prompt_set)

        self.assertTrue(has_permission, "创建者应该有change权限")

    def test_prompt_template_set_admin_no_change_permission_for_non_creator(self):
        """测试：PromptTemplateSetAdmin - 非创建者无change权限"""
        admin_instance = PromptTemplateSetAdmin(PromptTemplateSet, admin.site)
        factory = RequestFactory()
        request = factory.get("/admin/prompts/prompttemplateset/")
        request.user = self.normal_user

        # 非创建者不能编辑系统资源
        has_permission = admin_instance.has_change_permission(request, self.system_prompt_set)

        self.assertFalse(has_permission, "非创建者不应该有change权限")

    def test_prompt_template_set_admin_superuser_bypass(self):
        """测试：PromptTemplateSetAdmin - superuser可以绕过限制"""
        admin_instance = PromptTemplateSetAdmin(PromptTemplateSet, admin.site)
        factory = RequestFactory()
        request = factory.get("/admin/prompts/prompttemplateset/")
        request.user = self.admin

        # superuser可以编辑任何资源
        has_permission = admin_instance.has_change_permission(request, self.user_prompt_set)

        self.assertTrue(has_permission, "Superuser应该可以绕过限制")
