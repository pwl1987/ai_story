"""
Story 8.10: 操作日志 - 验收测试

遵循TDD红-绿-重构循环：
- RED: 编写失败的测试
- GREEN: 实现最小功能使测试通过
- REFACTOR: 重构代码保持质量

测试范围:
1. AuditLog 模型字段完整性
2. Admin 操作自动记录日志
3. 日志记录的详细程度（before/after数据）
4. 日志查询和过滤
"""

from django.contrib import admin
from django.contrib.auth.models import User
from django.test import TestCase

from apps.users.models import AuditLog, UserProfile


class AuditLogModelTestSuite(TestCase):
    """AuditLog 模型测试套件"""

    def test_audit_log_has_all_required_fields(self):
        """测试：AuditLog 有所有必需字段"""
        # 创建测试用户
        user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )

        # 创建审计日志
        log = AuditLog.objects.create(
            user=user,
            action="create",
            model_name="ModelProvider",
            object_id="1",
            object_repr="测试模型",
            change_message="创建了新的模型提供商",
        )

        self.assertIsNotNone(log.id, "日志应该有ID")
        self.assertEqual(log.user, user, "用户应该正确设置")
        self.assertEqual(log.action, "create", "操作类型应该正确")
        self.assertEqual(log.model_name, "ModelProvider", "模型名称应该正确")
        self.assertEqual(log.object_id, "1", "对象ID应该正确")
        self.assertEqual(log.object_repr, "测试模型", "对象表示应该正确")
        self.assertEqual(log.change_message, "创建了新的模型提供商", "变更消息应该正确")
        self.assertIsNotNone(log.created_at, "创建时间应该自动设置")

    def test_action_choices(self):
        """测试：action 字段有正确的选项"""
        valid_actions = ["create", "update", "delete", "view"]
        for action in valid_actions:
            log = AuditLog.objects.create(
                user=User.objects.create_user(
                    username=f"user_{action}", email=f"{action}@example.com", password="pass"
                ),
                action=action,
                model_name="TestModel",
                object_id="1",
                object_repr="Test",
            )
            self.assertEqual(log.action, action, f"操作类型 {action} 应该有效")


class AuditLogAdminIntegrationTestSuite(TestCase):
    """Admin 集成测试套件"""

    @classmethod
    def setUpTestData(cls):
        """创建测试数据"""
        cls.admin = User.objects.create_superuser(
            username="admin", email="admin@example.com", password="adminpass123"
        )
        UserProfile.objects.create(user=cls.admin)

    def test_admin_action_logs_create(self):
        """测试：Admin 创建操作自动记录日志"""
        from django.contrib.admin import site
        from django.test import RequestFactory

        from apps.models.admin import ModelProviderAdmin
        from apps.models.models import ModelProvider

        # 创建 Admin 实例
        admin_instance = ModelProviderAdmin(ModelProvider, site)
        factory = RequestFactory()
        request = factory.post("/admin/models/modelprovider/")
        request.user = self.admin

        # 创建模型对象
        model = ModelProvider(
            name="测试模型",
            provider_type="llm",
            executor_class="core.ai_client.openai_client.OpenAIClient",
            api_url="https://api.openai.com/v1",
            api_key="sk-test",
            model_name="gpt-4",
            created_by=self.admin,
        )

        # 调用 Admin 的保存方法
        admin_instance.save_model(request, model, None, False)

        # 验证日志已记录
        logs = AuditLog.objects.filter(
            user=self.admin,
            action="create",
            model_name="ModelProvider",
            object_id=str(model.id),
        )

        self.assertTrue(logs.exists(), "创建操作应该记录日志")
        log = logs.first()
        self.assertEqual(log.object_repr, str(model), "对象表示应该正确")

    def test_admin_action_logs_delete(self):
        """测试：Admin 删除操作自动记录日志"""
        from django.contrib.admin import site
        from django.test import RequestFactory

        from apps.models.admin import ModelProviderAdmin
        from apps.models.models import ModelProvider

        # 创建 Admin 实例
        admin_instance = ModelProviderAdmin(ModelProvider, site)
        factory = RequestFactory()
        request = factory.post("/admin/models/modelprovider/")
        request.user = self.admin

        # 创建模型对象
        model = ModelProvider.objects.create(
            name="要删除的模型",
            provider_type="llm",
            executor_class="core.ai_client.openai_client.OpenAIClient",
            api_url="https://api.openai.com/v1",
            api_key="sk-test",
            model_name="gpt-4",
            created_by=self.admin,
        )

        model_id = model.id
        model_repr = str(model)

        # 调用 Admin 的删除方法
        admin_instance.delete_model(request, model)

        # 验证删除日志已记录
        logs = AuditLog.objects.filter(
            user=self.admin,
            action="delete",
            model_name="ModelProvider",
            object_id=str(model_id),
        )

        self.assertTrue(logs.exists(), "删除操作应该记录日志")
        log = logs.first()
        self.assertEqual(log.object_repr, model_repr, "对象表示应该保留删除前的值")

    def test_admin_action_logs_update(self):
        """测试：Admin 更新操作自动记录日志"""
        from django.contrib.admin import site
        from django.test import RequestFactory

        from apps.models.admin import ModelProviderAdmin
        from apps.models.models import ModelProvider

        # 创建 Admin 实例
        admin_instance = ModelProviderAdmin(ModelProvider, site)
        factory = RequestFactory()
        request = factory.post("/admin/models/modelprovider/")
        request.user = self.admin

        # 创建模型对象
        model = ModelProvider.objects.create(
            name="原始名称",
            provider_type="llm",
            executor_class="core.ai_client.openai_client.OpenAIClient",
            api_url="https://api.openai.com/v1",
            api_key="sk-test",
            model_name="gpt-4",
            created_by=self.admin,
        )

        # 更新模型
        model.name = "更新后的名称"

        # 调用 Admin 的保存方法
        admin_instance.save_model(request, model, None, True)

        # 验证更新日志已记录
        logs = AuditLog.objects.filter(
            user=self.admin,
            action="update",
            model_name="ModelProvider",
            object_id=str(model.id),
        )

        self.assertTrue(logs.exists(), "更新操作应该记录日志")

    def test_audit_log_list_display(self):
        """测试：AuditLog Admin 列表显示正确"""
        from django.test import Client

        # 创建日志
        AuditLog.objects.create(
            user=self.admin,
            action="create",
            model_name="TestModel",
            object_id="1",
            object_repr="测试对象",
            change_message="测试消息",
        )

        client = Client()
        client.force_login(self.admin)

        # 访问 Admin 日志列表（使用 staffadmin）
        response = client.get("/admin/users/auditlog/")

        self.assertEqual(response.status_code, 200, "应该能访问日志列表")
        self.assertIn("测试对象", response.content.decode("utf-8"), "日志列表应该显示对象表示")
        self.assertIn("创建", response.content.decode("utf-8"), "日志列表应该显示操作类型")

    def test_audit_log_readonly_fields(self):
        """测试：AuditLog Admin 只读字段设置正确"""
        from apps.users.admin import AuditLogAdmin

        # 验证 readonly_fields
        admin_instance = AuditLogAdmin(AuditLog, admin.site)
        readonly_fields = admin_instance.readonly_fields

        self.assertIn("user", readonly_fields, "user 应该是只读")
        self.assertIn("action", readonly_fields, "action 应该是只读")
        self.assertIn("model_name", readonly_fields, "model_name 应该是只读")
        self.assertIn("object_id", readonly_fields, "object_id 应该是只读")
        self.assertIn("created_at", readonly_fields, "created_at 应该是只读")

    def test_audit_log_has_no_add_permission(self):
        """测试：AuditLog Admin 禁止手动添加"""
        from django.test import RequestFactory

        from apps.users.admin import AuditLogAdmin

        admin_instance = AuditLogAdmin(AuditLog, admin.site)
        factory = RequestFactory()
        request = factory.get("/admin/users/auditlog/")
        request.user = self.admin

        # 不应该有添加权限
        has_add = admin_instance.has_add_permission(request)
        self.assertFalse(has_add, "不应该允许手动添加审计日志")

    def test_audit_log_has_no_change_permission(self):
        """测试：AuditLog Admin 禁止修改"""
        from django.test import RequestFactory

        from apps.users.admin import AuditLogAdmin

        admin_instance = AuditLogAdmin(AuditLog, admin.site)
        factory = RequestFactory()
        request = factory.get("/admin/users/auditlog/")
        request.user = self.admin

        log = AuditLog.objects.create(
            user=self.admin,
            action="create",
            model_name="TestModel",
            object_id="1",
            object_repr="测试对象",
        )

        # 不应该有修改权限
        has_change = admin_instance.has_change_permission(request, log)
        self.assertFalse(has_change, "不应该允许修改审计日志")

    def test_audit_log_has_no_delete_permission(self):
        """测试：AuditLog Admin 禁止删除"""
        from django.test import RequestFactory

        from apps.users.admin import AuditLogAdmin

        admin_instance = AuditLogAdmin(AuditLog, admin.site)
        factory = RequestFactory()
        request = factory.get("/admin/users/auditlog/")
        request.user = self.admin

        log = AuditLog.objects.create(
            user=self.admin,
            action="create",
            model_name="TestModel",
            object_id="1",
            object_repr="测试对象",
        )

        # 不应该有删除权限
        has_delete = admin_instance.has_delete_permission(request, log)
        self.assertFalse(has_delete, "不应该允许删除审计日志")

    def test_audit_log_filter_by_user(self):
        """测试：可以按用户过滤日志"""
        user1 = User.objects.create_user(
            username="user1", email="user1@example.com", password="pass123"
        )
        user2 = User.objects.create_user(
            username="user2", email="user2@example.com", password="pass123"
        )

        # 创建日志
        AuditLog.objects.create(
            user=user1, action="create", model_name="Model1", object_id="1", object_repr="对象1"
        )
        AuditLog.objects.create(
            user=user2, action="delete", model_name="Model2", object_id="2", object_repr="对象2"
        )

        # 按用户1过滤
        user1_logs = AuditLog.objects.filter(user=user1)
        self.assertEqual(user1_logs.count(), 1, "用户1应该有1条日志")

        # 按用户2过滤
        user2_logs = AuditLog.objects.filter(user=user2)
        self.assertEqual(user2_logs.count(), 1, "用户2应该有1条日志")

    def test_audit_log_filter_by_action(self):
        """测试：可以按操作类型过滤日志"""
        # 创建不同类型的日志
        AuditLog.objects.create(
            user=self.admin,
            action="create",
            model_name="Model1",
            object_id="1",
            object_repr="对象1",
        )
        AuditLog.objects.create(
            user=self.admin,
            action="delete",
            model_name="Model2",
            object_id="2",
            object_repr="对象2",
        )

        # 按创建操作过滤
        create_logs = AuditLog.objects.filter(action="create")
        self.assertEqual(create_logs.count(), 1, "应该有1条创建日志")

        # 按删除操作过滤
        delete_logs = AuditLog.objects.filter(action="delete")
        self.assertEqual(delete_logs.count(), 1, "应该有1条删除日志")

    def test_audit_log_ordering(self):
        """测试：日志按创建时间倒序排列"""
        # 创建多条日志
        log1 = AuditLog.objects.create(
            user=self.admin,
            action="create",
            model_name="Model1",
            object_id="1",
            object_repr="对象1",
        )
        log2 = AuditLog.objects.create(
            user=self.admin,
            action="delete",
            model_name="Model2",
            object_id="2",
            object_repr="对象2",
        )

        # 查询所有日志
        all_logs = AuditLog.objects.all()

        # 最新的应该在前面
        self.assertEqual(all_logs.first().id, log2.id, "最新的日志应该在前面")
        self.assertEqual(all_logs.last().id, log1.id, "最旧的日志应该在后面")
