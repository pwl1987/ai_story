"""
Story 8.11: 系统资源视觉标记 - 验收测试

遵循TDD红-绿-重构循环：
- RED: 编写失败的测试
- GREEN: 实现最小功能使测试通过
- REFACTOR: 重构代码保持质量

测试范围:
1. SystemResourceBadgeMixin - 统一的系统资源标记Mixin
2. 所有支持is_system_default的模型都使用统一的标记
3. 视觉标记样式统一（颜色、图标、字体）
4. Admin列表显示优化
"""

from django.contrib import admin
from django.contrib.auth.models import User
from django.test import TestCase

from apps.models.models import ModelProvider
from apps.prompts.models import PromptTemplateSet


class SystemResourceBadgeMixinTestSuite(TestCase):
    """系统资源标记Mixin测试套件"""

    @classmethod
    def setUpTestData(cls):
        """创建测试数据"""
        cls.admin = User.objects.create_superuser(
            username="admin", email="admin@example.com", password="adminpass123"
        )

        # 创建系统级模型
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

        # 创建用户级模型
        cls.user_model = ModelProvider.objects.create(
            name="用户模型",
            provider_type="llm",
            executor_class="core.ai_client.openai_client.OpenAIClient",
            api_url="https://api.openai.com/v1",
            api_key="sk-test",
            model_name="gpt-4",
            is_system_default=False,
            created_by=cls.admin,
        )

        # 创建系统级提示词集
        cls.system_prompt_set = PromptTemplateSet.objects.create(
            name="系统提示词集",
            description="系统级默认提示词集",
            is_system_default=True,
            created_by=cls.admin,
        )

        # 创建用户级提示词集
        cls.user_prompt_set = PromptTemplateSet.objects.create(
            name="用户提示词集",
            description="用户自定义提示词集",
            is_system_default=False,
            created_by=cls.admin,
        )

    def test_model_provider_has_badge_mixin(self):
        """测试：ModelProviderAdmin 使用 SystemResourceBadgeMixin"""
        from apps.models.admin import ModelProviderAdmin

        # 验证Admin类使用了正确的Mixin
        self.assertTrue(
            hasattr(ModelProviderAdmin, "system_resource_badge"),
            "ModelProviderAdmin 应该有 system_resource_badge 方法",
        )

    def test_prompt_template_set_has_badge_mixin(self):
        """测试：PromptTemplateSetAdmin 使用 SystemResourceBadgeMixin"""
        from apps.prompts.admin import PromptTemplateSetAdmin

        # 验证Admin类使用了正确的Mixin
        self.assertTrue(
            hasattr(PromptTemplateSetAdmin, "system_resource_badge"),
            "PromptTemplateSetAdmin 应该有 system_resource_badge 方法",
        )

    def test_system_resource_badge_gold_star(self):
        """测试：系统资源显示金色星标"""
        from apps.models.admin import ModelProviderAdmin

        admin_instance = ModelProviderAdmin(ModelProvider, admin.site)
        badge_html = admin_instance.system_resource_badge(self.system_model)

        self.assertIn("🌟 系统级", badge_html, "系统资源应该显示金色星标")
        self.assertIn("#D4AF37", badge_html, "系统资源应该是金色")
        self.assertIn("font-weight: bold", badge_html, "系统资源应该加粗")

    def test_user_resource_badge_gray(self):
        """测试：用户资源显示灰色标记"""
        from apps.models.admin import ModelProviderAdmin

        admin_instance = ModelProviderAdmin(ModelProvider, admin.site)
        badge_html = admin_instance.system_resource_badge(self.user_model)

        self.assertIn("👤 用户级", badge_html, "用户资源应该显示用户图标")
        self.assertIn("#808080", badge_html, "用户资源应该是灰色")

    def test_prompt_system_resource_badge_consistent(self):
        """测试：PromptTemplateSet 的标记与 ModelProvider 一致"""
        from apps.models.admin import ModelProviderAdmin
        from apps.prompts.admin import PromptTemplateSetAdmin

        model_admin = ModelProviderAdmin(ModelProvider, admin.site)
        prompt_admin = PromptTemplateSetAdmin(PromptTemplateSet, admin.site)

        # 系统资源标记
        model_system_badge = model_admin.system_resource_badge(self.system_model)
        prompt_system_badge = prompt_admin.system_resource_badge(self.system_prompt_set)

        # 都应该包含金色和星标
        self.assertIn("#D4AF37", model_system_badge)
        self.assertIn("#D4AF37", prompt_system_badge)
        self.assertIn("🌟 系统级", model_system_badge)
        self.assertIn("🌟 系统级", prompt_system_badge)

    def test_badge_short_description(self):
        """测试：badge 有正确的 short_description"""
        from apps.models.admin import ModelProviderAdmin

        admin_instance = ModelProviderAdmin(ModelProvider, admin.site)
        description = admin_instance.system_resource_badge.short_description

        self.assertEqual(description, "资源类型", "short_description 应该是'资源类型'")

    def test_admin_list_display_includes_badge(self):
        """测试：Admin list_display 包含 badge"""
        from apps.models.admin import ModelProviderAdmin

        list_display = ModelProviderAdmin.list_display

        self.assertIn("system_resource_badge", list_display, "list_display 应该包含 badge")

    def test_badge_html_safe(self):
        """测试：badge HTML 是安全的（使用format_html）"""
        from apps.models.admin import ModelProviderAdmin

        admin_instance = ModelProviderAdmin(ModelProvider, admin.site)
        badge_html = admin_instance.system_resource_badge(self.system_model)

        # 验证返回的是字符串
        self.assertIsInstance(badge_html, str, "badge 应该返回字符串")

        # 验证包含基本的 HTML 结构
        self.assertIn("<span", badge_html, "应该包含 span 标签")
        self.assertIn("style=", badge_html, "应该包含样式")

    def test_badge_consistent_across_models(self):
        """测试：不同模型的 badge 样式一致"""
        from apps.models.admin import ModelProviderAdmin
        from apps.prompts.admin import PromptTemplateSetAdmin

        model_admin = ModelProviderAdmin(ModelProvider, admin.site)
        prompt_admin = PromptTemplateSetAdmin(PromptTemplateSet, admin.site)

        # 系统资源
        model_system_badge = model_admin.system_resource_badge(self.system_model)
        prompt_system_badge = prompt_admin.system_resource_badge(self.system_prompt_set)

        # 验证金色样式一致
        self.assertIn("#D4AF37", model_system_badge)
        self.assertIn("#D4AF37", prompt_system_badge)
        self.assertIn("font-weight: bold", model_system_badge)
        self.assertIn("font-weight: bold", prompt_system_badge)

        # 用户资源
        model_user_badge = model_admin.system_resource_badge(self.user_model)
        prompt_user_badge = prompt_admin.system_resource_badge(self.user_prompt_set)

        # 验证灰色样式一致
        self.assertIn("#808080", model_user_badge)
        self.assertIn("#808080", prompt_user_badge)


class SystemResourceBadgeAdminUITestSuite(TestCase):
    """Admin UI 视觉标记测试套件"""

    @classmethod
    def setUpTestData(cls):
        """创建测试数据"""
        cls.admin = User.objects.create_superuser(
            username="admin", email="admin@example.com", password="adminpass123"
        )

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

    def test_admin_list_page_displays_badge(self):
        """测试：Admin 列表页正确显示 badge"""
        from django.test import Client

        client = Client()
        client.force_login(self.admin)

        # 访问 ModelProvider 列表页
        response = client.get("/admin/models/modelprovider/")

        self.assertEqual(response.status_code, 200, "应该能访问列表页")
        self.assertIn("🌟 系统级", response.content.decode("utf-8"), "列表页应该显示系统资源标记")

    def test_system_resource_badge_visible(self):
        """测试：系统资源标记在列表页可见"""
        from django.test import Client

        client = Client()
        client.force_login(self.admin)

        response = client.get("/admin/models/modelprovider/")

        # 检查金色样式
        content = response.content.decode("utf-8")
        self.assertIn("#D4AF37", content, "应该包含金色样式")
