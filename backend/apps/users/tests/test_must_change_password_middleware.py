"""
Story 8.4: 强制修改密码 - 验收测试

遵循TDD红-绿-重构循环：
- RED: 编写失败的测试
- GREEN: 实现最小功能使测试通过
- REFACTOR: 重构代码保持质量

测试范围:
1. MustChangePasswordMiddleware拦截
2. 白名单路径排除
3. 修改密码API
4. 清除must_change_password标志
"""

from django.contrib.auth.models import User
from django.test import Client, TestCase, override_settings
from django.urls import path

from apps.users.models import UserProfile


# 测试视图
def mock_api_view(request):
    """模拟API视图"""
    from django.http import JsonResponse

    return JsonResponse({"status": "success"})


def mock_change_password_view(request):
    """模拟修改密码视图"""
    from django.http import JsonResponse

    if not request.user.is_authenticated:
        return JsonResponse({"error": "未登录"}, status=401)

    # 简单实现：直接清除标志
    if hasattr(request.user, "profile"):
        request.user.profile.must_change_password = False
        request.user.profile.save()

    return JsonResponse({"status": "password_changed"})


# 测试URL配置
urlpatterns = [
    path("api/test/", mock_api_view),
    path("api/auth/change-password/", mock_change_password_view),
    path("api/auth/login/", mock_api_view),  # 模拟登录
    path("api/auth/logout/", mock_api_view),  # 模拟登出
]


@override_settings(ROOT_URLCONF=__name__)
class MustChangePasswordMiddlewareTest(TestCase):
    """强制修改密码中间件测试"""

    @classmethod
    def setUpTestData(cls):
        """创建测试数据"""
        # 创建需要修改密码的用户
        cls.user_must_change = User.objects.create_user(
            username="must_change",
            email="must_change@example.com",
            password="oldpass123",
        )
        UserProfile.objects.create(user=cls.user_must_change, must_change_password=True)

        # 创建正常用户
        cls.user_normal = User.objects.create_user(
            username="normal", email="normal@example.com", password="normalpass123"
        )
        UserProfile.objects.create(user=cls.user_normal, must_change_password=False)

    def test_middleware_blocks_user_with_must_change_true(self):
        """测试：中间件拦截must_change_password=True的用户"""
        client = Client()
        client.force_login(self.user_must_change)

        response = client.get("/api/test/")

        # 应该返回403 Forbidden
        self.assertEqual(response.status_code, 403)
        self.assertIn("必须修改密码", response.json()["error"])

    def test_middleware_allows_normal_user(self):
        """测试：中间件允许must_change_password=False的用户访问"""
        client = Client()
        client.force_login(self.user_normal)

        response = client.get("/api/test/")

        # 应该返回200 OK
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "success")

    def test_middleware_allows_change_password_endpoint(self):
        """测试：中间件允许访问修改密码API（白名单）"""
        client = Client()
        client.force_login(self.user_must_change)

        response = client.post("/api/auth/change-password/")

        # 应该返回200 OK（不被拦截）
        self.assertEqual(response.status_code, 200)

    def test_middleware_allows_anonymous_requests(self):
        """测试：中间件允许未认证用户访问"""
        client = Client()

        response = client.get("/api/test/")

        # 未认证用户应该被中间件忽略（由其他中间件处理）
        # 或者返回401，但不是403
        self.assertNotEqual(response.status_code, 403)

    def test_change_password_clears_must_change_flag(self):
        """测试：修改密码后清除must_change_password标志"""
        client = Client()
        client.force_login(self.user_must_change)

        # 确认标志为True
        self.assertTrue(
            self.user_must_change.profile.must_change_password,
            "初始状态must_change_password应该为True",
        )

        # 调用修改密码API
        response = client.post("/api/auth/change-password/")

        # 验证响应成功
        self.assertEqual(response.status_code, 200)

        # 刷新用户对象
        self.user_must_change.refresh_from_db()

        # 验证标志已清除
        self.assertFalse(
            self.user_must_change.profile.must_change_password,
            "修改密码后must_change_password应该为False",
        )

    def test_middleware_white_list_paths(self):
        """测试：中间件白名单路径不被拦截"""
        client = Client()
        client.force_login(self.user_must_change)

        # 测试登录相关路径
        white_list_paths = [
            "/api/auth/login/",
            "/api/auth/logout/",
            "/api/auth/change-password/",
            "/admin/login/",
            "/admin/logout/",
        ]

        for test_path in white_list_paths:
            response = client.get(test_path)
            # 白名单路径不应该返回403
            self.assertNotEqual(
                response.status_code,
                403,
                f"白名单路径 {test_path} 不应该被拦截",
            )

    def test_middleware_returns_custom_error_code(self):
        """测试：中间件返回自定义错误码和信息"""
        client = Client()
        client.force_login(self.user_must_change)

        response = client.get("/api/test/")

        self.assertEqual(response.status_code, 403)
        data = response.json()
        self.assertEqual(data["error_code"], "MUST_CHANGE_PASSWORD")
        self.assertIn("必须修改密码", data["error"])

    def test_middleware_ignores_static_files(self):
        """测试：中间件忽略静态文件请求"""
        client = Client()
        client.force_login(self.user_must_change)

        # 静态文件路径
        static_paths = [
            "/static/css/style.css",
            "/static/js/app.js",
            "/media/uploads/test.png",
        ]

        for test_path in static_paths:
            response = client.get(test_path)
            # 静态文件不应该返回403（可能返回404，但不是403）
            self.assertNotEqual(
                response.status_code,
                403,
                f"静态文件路径 {test_path} 不应该被拦截",
            )


@override_settings(ROOT_URLCONF=__name__)
class MustChangePasswordIntegrationTest(TestCase):
    """强制修改密码集成测试"""

    @classmethod
    def setUpTestData(cls):
        """创建测试数据"""
        cls.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="oldpass123"
        )
        UserProfile.objects.create(user=cls.user, must_change_password=True)

    def test_full_workflow_reset_to_change_password(self):
        """测试完整工作流：重置密码 -> 强制修改 -> 正常访问"""
        client = Client()

        # 1. 强制登录（模拟用户已登录但必须修改密码）
        client.force_login(self.user)

        # 2. 尝试访问API（应该被拦截）
        response = client.get("/api/test/")
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()["error_code"], "MUST_CHANGE_PASSWORD")

        # 3. 修改密码
        response = client.post("/api/auth/change-password/")
        self.assertEqual(response.status_code, 200)

        # 4. 再次访问API（应该成功）
        response = client.get("/api/test/")
        self.assertEqual(response.status_code, 200)
