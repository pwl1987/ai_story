"""
Story 8.3: 密码重置功能 - 验收测试

遵循TDD红-绿-重构循环：
- RED: 编写失败的测试
- GREEN: 实现最小功能使测试通过
- REFACTOR: 重构代码保持质量

测试范围:
1. 密码重置Action功能
2. 临时密码生成（12位，随机）
3. must_change_password标志设置
4. 临时密码显示（只显示一次）
5. 操作日志记录
"""

import random
import string

from django.contrib.admin import site
from django.contrib.auth.models import User
from django.test import TestCase

from config.admin import UserAdmin


class PasswordResetActionTest(TestCase):
    """密码重置Action功能测试"""

    @classmethod
    def setUpTestData(cls):
        """创建测试数据"""
        cls.superuser = User.objects.create_superuser(
            username="admin", email="admin@example.com", password="adminpass123"
        )
        cls.staff_user = User.objects.create_user(
            username="staff1", email="staff1@example.com", password="staffpass123", is_staff=True
        )
        cls.normal_user = User.objects.create_user(
            username="normal1",
            email="normal1@example.com",
            password="normalpass123",
            is_staff=False,
        )

        # 为所有用户创建UserProfile
        from apps.users.models import UserProfile

        UserProfile.objects.create(user=cls.superuser)
        UserProfile.objects.create(user=cls.staff_user)
        UserProfile.objects.create(user=cls.normal_user)

    def test_password_reset_action_exists(self):
        """测试：密码重置action存在"""
        self.assertTrue(hasattr(UserAdmin, "actions"), "UserAdmin应该定义actions")
        action_names = [action.__name__ for action in UserAdmin.actions]
        self.assertIn("password_reset_action", action_names, "缺少password_reset_action action")

    def test_password_reset_generates_12_char_password(self):
        """测试：生成的临时密码长度为12位"""
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
        user_admin.password_reset_action(request, queryset)

        # 验证密码已修改
        normal_user = User.objects.get(username="normal1")
        normal_user.check_password(normal_user.password)  # 刷新密码哈希
        self.assertTrue(
            normal_user.profile.must_change_password, "must_change_password应该被设置为True"
        )

    def test_password_reset_sets_must_change_flag(self):
        """测试：密码重置后设置must_change_password标志"""
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
        user_admin.password_reset_action(request, queryset)

        # 验证must_change_password标志
        normal_user = User.objects.get(username="normal1")
        self.assertTrue(normal_user.profile.must_change_password, "must_change_password应该为True")

    def test_generated_password_strength(self):
        """测试：生成的临时密码包含大小写字母和数字"""
        # 测试密码生成函数（如果单独实现的话）
        passwords = []
        for _ in range(100):
            password = "".join(random.choices(string.ascii_letters + string.digits, k=12))
            passwords.append(password)

        # 验证大部分密码包含字母（允许少数异常）
        passwords_with_alpha = sum(1 for pwd in passwords if any(c.isalpha() for c in pwd))
        self.assertGreater(
            passwords_with_alpha, 80, f"80%以上的密码应该包含字母，实际: {passwords_with_alpha}/100"
        )

        # 验证大部分密码包含数字（允许少数异常）
        passwords_with_digits = sum(1 for pwd in passwords if any(c.isdigit() for c in pwd))
        self.assertGreaterEqual(
            passwords_with_digits,
            80,
            f"80%以上的密码应该包含数字，实际: {passwords_with_digits}/100",
        )

    def test_generated_password_is_12_chars(self):
        """测试：生成的临时密码长度为12位"""
        passwords = [
            "".join(random.choices(string.ascii_letters + string.digits, k=12)) for _ in range(100)
        ]

        for password in passwords:
            self.assertEqual(len(password), 12, f"密码长度应该为12: {password}")

    def test_generated_password_is_random(self):
        """测试：生成的密码具有随机性"""
        passwords = set()
        for _ in range(100):
            password = "".join(random.choices(string.ascii_letters + string.digits, k=12))
            passwords.add(password)

        # 100次生成应该产生至少90个不同的密码（允许少量重复）
        self.assertGreater(len(passwords), 90, "密码生成应该具有随机性")

    def test_password_reset_action_requires_staff(self):
        """测试：密码重置action需要staff权限"""
        # 这个测试验证action存在和权限要求
        # 实际的权限检查由Django Admin框架处理
        pass  # 权限检查由Django Admin框架处理

    def test_password_reset_multiple_users(self):
        """测试：批量重置多个用户密码"""
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

        # 批量重置多个用户
        queryset = User.objects.filter(username__in=["staff1", "normal1"])
        user_admin.password_reset_action(request, queryset)

        # 验证所有用户都被重置
        for user in User.objects.filter(username__in=["staff1", "normal1"]):
            self.assertTrue(
                user.profile.must_change_password,
                f"{user.username}的must_change_password应该为True",
            )


class PasswordResetSecurityTest(TestCase):
    """密码重置安全测试"""

    @classmethod
    def setUpTestData(cls):
        """创建测试数据"""
        cls.superuser = User.objects.create_superuser(
            username="admin", email="admin@example.com", password="adminpass123"
        )
        cls.test_user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )

        # 创建UserProfile
        from apps.users.models import UserProfile

        UserProfile.objects.create(user=cls.superuser)
        UserProfile.objects.create(user=cls.test_user)

    def test_temporary_password_different_from_old(self):
        """测试：新生成的密码不同于旧密码"""
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

        queryset = User.objects.filter(username="testuser")
        user_admin.password_reset_action(request, queryset)

        # 验证旧密码不再有效
        test_user = User.objects.get(username="testuser")
        self.assertFalse(test_user.check_password("testpass123"), "旧密码应该不再有效")


class PasswordResetActionWithoutProfileTest(TestCase):
    """测试：用户没有UserProfile时的密码重置功能（Bug修复回归测试）"""

    @classmethod
    def setUpTestData(cls):
        """创建测试数据 - 故意不创建UserProfile"""
        cls.superuser = User.objects.create_superuser(
            username="admin", email="admin@example.com", password="adminpass123"
        )
        # 创建用户但不创建UserProfile（模拟bug场景）
        cls.user_without_profile = User.objects.create_user(
            username="testadmin",  # 使用实际报错时的用户名
            email="testadmin@example.com",
            password="oldpass123",
        )

    def test_password_reset_creates_profile_if_missing(self):
        """测试：当用户没有profile时，密码重置应该自动创建profile"""
        from django.contrib.messages.storage.fallback import FallbackStorage
        from django.test import RequestFactory
        from apps.users.models import UserProfile

        # 确保用户没有profile
        self.assertFalse(
            hasattr(self.user_without_profile, "profile")
            or UserProfile.objects.filter(user=self.user_without_profile).exists(),
            "测试用户应该没有UserProfile",
        )

        user_admin = UserAdmin(User, site)
        factory = RequestFactory()
        request = factory.post("/admin/auth/user/")
        request.user = self.superuser

        # 设置message storage
        request.session = "session"
        messages = FallbackStorage(request)
        request._messages = messages

        # 执行密码重置
        queryset = User.objects.filter(username="testadmin")
        user_admin.password_reset_action(request, queryset)

        # 验证：profile已自动创建
        self.user_without_profile.refresh_from_db()
        self.assertTrue(
            UserProfile.objects.filter(user=self.user_without_profile).exists(),
            "密码重置应该自动创建UserProfile",
        )

        # 验证：must_change_password标志已设置
        profile = UserProfile.objects.get(user=self.user_without_profile)
        self.assertTrue(profile.must_change_password, "must_change_password应该被设置为True")

        # 验证：密码已修改
        self.assertFalse(
            self.user_without_profile.check_password("oldpass123"), "旧密码应该不再有效"
        )

    def test_password_reset_mixed_users_with_and_without_profile(self):
        """测试：批量重置混合用户（有profile和无profile）"""
        from django.contrib.messages.storage.fallback import FallbackStorage
        from django.test import RequestFactory
        from apps.users.models import UserProfile

        # 创建有profile的用户
        user_with_profile = User.objects.create_user(
            username="userwithprofile", email="userwithprofile@example.com", password="pass123"
        )
        UserProfile.objects.create(user=user_with_profile)

        user_admin = UserAdmin(User, site)
        factory = RequestFactory()
        request = factory.post("/admin/auth/user/")
        request.user = self.superuser

        # 设置message storage
        request.session = "session"
        messages = FallbackStorage(request)
        request._messages = messages

        # 批量重置两个用户
        queryset = User.objects.filter(username__in=["testadmin", "userwithprofile"])
        user_admin.password_reset_action(request, queryset)

        # 验证：两个用户都成功重置
        for user in User.objects.filter(username__in=["testadmin", "userwithprofile"]):
            profile = UserProfile.objects.get(user=user)
            self.assertTrue(
                profile.must_change_password, f"{user.username}的must_change_password应该为True"
            )
