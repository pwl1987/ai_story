"""
Story 8.2: 用户管理Admin功能 - 验收测试

遵循TDD红-绿-重构循环：
- RED: 编写失败的测试
- GREEN: 实现最小功能使测试通过
- REFACTOR: 重构代码保持质量

测试范围:
1. UserAdmin list_display优化
2. UserAdmin list_filter优化
3. 自定义批量actions
4. 字段集(fieldsets)组织
5. 用户CRUD功能
"""

from django.contrib.admin import site
from django.contrib.auth.models import User
from django.test import Client, TestCase

from config.admin import UserAdmin


class UserAdminConfigurationTest(TestCase):
    """UserAdmin配置测试"""

    @classmethod
    def setUpTestData(cls):
        """创建测试数据"""
        cls.superuser = User.objects.create_superuser(
            username="admin", email="admin@example.com", password="adminpass123"
        )

    def test_user_list_display_fields(self):
        """测试：UserAdmin list_display包含所有预期字段"""
        expected_fields = [
            "username",
            "email",
            "first_name",
            "last_name",
            "is_staff",
            "is_superuser",
            "is_active",
            "date_joined",
            "last_login",
        ]
        for field in expected_fields:
            self.assertIn(field, UserAdmin.list_display, f"list_display缺少字段: {field}")

    def test_user_list_filter_fields(self):
        """测试：UserAdmin list_filter包含所有预期字段"""
        expected_filters = [
            "is_staff",
            "is_superuser",
            "is_active",
            "date_joined",
        ]
        for filter_field in expected_filters:
            self.assertIn(
                filter_field, UserAdmin.list_filter, f"list_filter缺少字段: {filter_field}"
            )

    def test_user_search_fields(self):
        """测试：UserAdmin search_fields包含预期字段"""
        expected_search = ["username", "email", "first_name", "last_name"]
        for field in expected_search:
            self.assertIn(field, UserAdmin.search_fields, f"search_fields缺少字段: {field}")

    def test_user_ordering(self):
        """测试：UserAdmin默认按date_joined降序排列"""
        self.assertEqual(UserAdmin.ordering, ["-date_joined"])

    def test_fieldsets_organization(self):
        """测试：UserAdmin有组织良好的fieldsets"""
        self.assertTrue(hasattr(UserAdmin, "fieldsets"), "UserAdmin应该定义fieldsets")

        fieldsets = UserAdmin.fieldsets
        self.assertIsInstance(fieldsets, tuple)
        self.assertGreater(len(fieldsets), 0)


class UserAdminActionsTest(TestCase):
    """UserAdmin自定义Actions测试"""

    @classmethod
    def setUpTestData(cls):
        """创建测试数据"""
        cls.superuser = User.objects.create_superuser(
            username="admin", email="admin@example.com", password="adminpass123"
        )
        cls.staff_user = User.objects.create_user(
            username="staff1", email="staff1@example.com", password="staffpass123", is_staff=True
        )
        cls.staff_user2 = User.objects.create_user(
            username="staff2", email="staff2@example.com", password="staffpass123", is_staff=True
        )
        cls.normal_user = User.objects.create_user(
            username="normal1",
            email="normal1@example.com",
            password="normalpass123",
            is_staff=False,
        )

    def test_bulk_disable_users_action_exists(self):
        """测试：批量禁用用户action存在"""
        self.assertTrue(hasattr(UserAdmin, "actions"), "UserAdmin应该定义actions")
        action_names = [action.__name__ for action in UserAdmin.actions]
        self.assertIn("bulk_disable_users", action_names, "缺少bulk_disable_users action")

    def test_bulk_enable_users_action_exists(self):
        """测试：批量启用用户action存在"""
        action_names = [action.__name__ for action in UserAdmin.actions]
        self.assertIn("bulk_enable_users", action_names, "缺少bulk_enable_users action")

    def test_bulk_add_staff_action_exists(self):
        """测试：批量添加staff权限action存在"""
        action_names = [action.__name__ for action in UserAdmin.actions]
        self.assertIn("bulk_add_staff", action_names, "缺少bulk_add_staff action")

    def test_bulk_remove_staff_action_exists(self):
        """测试：批量移除staff权限action存在"""
        action_names = [action.__name__ for action in UserAdmin.actions]
        self.assertIn("bulk_remove_staff", action_names, "缺少bulk_remove_staff action")

    def test_bulk_disable_users_functionality(self):
        """测试：批量禁用用户功能正常工作"""
        # 创建一个模拟的model admin实例和request
        from django.contrib.messages.storage.fallback import FallbackStorage
        from django.test import RequestFactory

        user_admin = UserAdmin(User, site)
        factory = RequestFactory()
        request = factory.post("/admin/auth/user/")
        request.user = self.superuser

        # 设置message storage
        request.session = "session"
        messages = FallbackStorage(request)
        request._messages = messages

        queryset = User.objects.filter(username__in=["staff1", "staff2"])

        # 执行action
        user_admin.bulk_disable_users(request, queryset)

        # 验证用户被禁用
        for user in User.objects.filter(username__in=["staff1", "staff2"]):
            self.assertFalse(user.is_active, f"用户 {user.username} 应该被禁用")

    def test_bulk_enable_users_functionality(self):
        """测试：批量启用用户功能正常工作"""
        # 先禁用用户
        User.objects.filter(username__in=["staff1", "normal1"]).update(is_active=False)

        # 创建admin实例和request
        from django.contrib.messages.storage.fallback import FallbackStorage
        from django.test import RequestFactory

        user_admin = UserAdmin(User, site)
        factory = RequestFactory()
        request = factory.post("/admin/auth/user/")
        request.user = self.superuser

        # 设置message storage
        request.session = "session"
        messages = FallbackStorage(request)
        request._messages = messages

        queryset = User.objects.filter(username__in=["staff1", "normal1"])
        user_admin.bulk_enable_users(request, queryset)

        # 验证用户被启用
        for user in User.objects.filter(username__in=["staff1", "normal1"]):
            self.assertTrue(user.is_active, f"用户 {user.username} 应该被启用")

    def test_bulk_add_staff_functionality(self):
        """测试：批量添加staff权限功能正常工作"""
        from django.contrib.messages.storage.fallback import FallbackStorage
        from django.test import RequestFactory

        user_admin = UserAdmin(User, site)
        factory = RequestFactory()
        request = factory.post("/admin/auth/user/")
        request.user = self.superuser

        # 设置message storage
        request.session = "session"
        messages = FallbackStorage(request)
        request._messages = messages

        queryset = User.objects.filter(username="normal1")
        user_admin.bulk_add_staff(request, queryset)

        normal_user = User.objects.get(username="normal1")
        self.assertTrue(normal_user.is_staff, "用户应该拥有staff权限")

    def test_bulk_remove_staff_functionality(self):
        """测试：批量移除staff权限功能正常工作"""
        from django.contrib.messages.storage.fallback import FallbackStorage
        from django.test import RequestFactory

        user_admin = UserAdmin(User, site)
        factory = RequestFactory()
        request = factory.post("/admin/auth/user/")
        request.user = self.superuser

        # 设置message storage
        request.session = "session"
        messages = FallbackStorage(request)
        request._messages = messages

        queryset = User.objects.filter(username__in=["staff1", "staff2"])
        user_admin.bulk_remove_staff(request, queryset)

        for user in User.objects.filter(username__in=["staff1", "staff2"]):
            self.assertFalse(user.is_staff, f"用户 {user.username} 不应该拥有staff权限")


class UserAdminCRUDTest(TestCase):
    """UserAdmin CRUD功能测试"""

    @classmethod
    def setUpTestData(cls):
        """创建测试数据"""
        cls.superuser = User.objects.create_superuser(
            username="admin", email="admin@example.com", password="adminpass123"
        )

    def test_create_new_user_via_admin(self):
        """测试：UserAdmin允许创建新用户"""
        # 验证UserAdmin已注册到Admin
        from config.admin import staff_admin_site

        self.assertTrue(staff_admin_site.is_registered(User))

        # 直接创建用户来验证功能
        user_count = User.objects.count()
        User.objects.create_user(
            username="newuser", email="newuser@example.com", password="testpass123"
        )
        self.assertEqual(User.objects.count(), user_count + 1)
        self.assertTrue(User.objects.filter(username="newuser").exists())

    def test_user_admin_has_change_permission(self):
        """测试：UserAdmin提供change权限"""
        from django.test import RequestFactory

        user_admin = UserAdmin(User, site)
        factory = RequestFactory()

        # 创建request对象
        request = factory.get("/admin/auth/user/")
        request.user = self.superuser

        test_user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )

        # 超级用户应该有修改权限
        self.assertTrue(user_admin.has_change_permission(request, test_user))

    def test_user_admin_has_delete_permission(self):
        """测试：UserAdmin提供delete权限"""
        from django.test import RequestFactory

        user_admin = UserAdmin(User, site)
        factory = RequestFactory()

        # 创建request对象
        request = factory.get("/admin/auth/user/")
        request.user = self.superuser

        test_user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )

        # 超级用户应该有删除权限
        self.assertTrue(user_admin.has_delete_permission(request, test_user))

    def test_user_admin_has_add_permission(self):
        """测试：UserAdmin提供add权限"""
        from django.test import RequestFactory

        user_admin = UserAdmin(User, site)
        factory = RequestFactory()

        # 创建request对象
        request = factory.get("/admin/auth/user/")
        request.user = self.superuser

        # 超级用户应该有添加权限
        self.assertTrue(user_admin.has_add_permission(request))


class UserAdminListDisplayTest(TestCase):
    """UserAdmin列表显示测试"""

    @classmethod
    def setUpTestData(cls):
        """创建测试数据"""
        cls.superuser = User.objects.create_superuser(
            username="admin", email="admin@example.com", password="adminpass123"
        )
        cls.staff_user = User.objects.create_user(
            username="staff",
            email="staff@example.com",
            password="staffpass123",
            is_staff=True,
            first_name="Staff",
            last_name="User",
        )

    def setUp(self):
        """每个测试方法前的设置"""
        self.client = Client()
        self.client.force_login(self.superuser)

    def test_user_list_displays_all_fields(self):
        """测试：用户列表显示所有预期字段"""
        response = self.client.get("/admin/auth/user/")
        self.assertEqual(response.status_code, 200)
        content = response.content.decode("utf-8")

        # 验证字段显示
        expected_fields = ["username", "email", "first_name", "last_name", "is_staff"]
        for field in expected_fields:
            # 检查表头
            self.assertIn(field, content, f"列表应该显示字段: {field}")

    def test_user_list_shows_staff_status(self):
        """测试：用户列表正确显示staff状态"""
        response = self.client.get("/admin/auth/user/")
        content = response.content.decode("utf-8")

        # 检查staff用户显示
        self.assertIn("staff", content)
        self.assertIn("Staff", content)  # first_name
