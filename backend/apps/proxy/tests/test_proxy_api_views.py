"""
Story 9.8 & 9.9: 代理API视图测试套件

测试代理选择和测试连接API：
- Phase 1: 代理选择列表 API
- Phase 2: 测试连接 API
- Phase 3: 权限控制
- Phase 4: 错误处理

@Author: Epic 9 Team
@Created: 2026-01-31
@Story: 9.8 - 前端代理选择器 + 9.9 - 测试连接功能
"""

from unittest.mock import MagicMock, patch

import httpx
from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIRequestFactory, force_authenticate

from apps.proxy.models import ProxyConfig, ProxyProtocol
from apps.proxy.views import ProxySelectViewSet, TestConnectionView

User = get_user_model()


class ProxySelectAPITest(TestCase):
    """Phase 1: 代理选择列表 API测试"""

    def setUp(self):
        """设置测试数据"""
        self.user = User.objects.create_user(username="testuser", password="testpass")
        self.factory = APIRequestFactory()

        # 创建代理配置
        self.proxy1 = ProxyConfig.objects.create(
            name="美国代理-01",
            protocol=ProxyProtocol.HTTP,
            host="proxy1.example.com",
            port=8080,
            is_active=True,
            is_healthy=True,
        )
        self.proxy2 = ProxyConfig.objects.create(
            name="香港代理-01",
            protocol=ProxyProtocol.HTTPS,
            host="proxy2.example.com",
            port=8443,
            is_active=True,
            is_healthy=True,
        )
        # 创建一个禁用的代理（不应出现在列表中）
        self.proxy3 = ProxyConfig.objects.create(
            name="禁用代理",
            protocol=ProxyProtocol.HTTP,
            host="proxy3.example.com",
            port=8080,
            is_active=False,
            is_healthy=True,
        )
        # 创建一个不健康的代理（不应出现在列表中）
        self.proxy4 = ProxyConfig.objects.create(
            name="不健康代理",
            protocol=ProxyProtocol.HTTP,
            host="proxy4.example.com",
            port=8080,
            is_active=True,
            is_healthy=False,
        )

    def test_proxy_select_returns_only_active_and_healthy(self):
        """AC[场景1]: 只返回is_active=True且is_healthy=True的代理"""
        # 创建请求
        request = self.factory.get("/api/v1/proxy/select/")
        force_authenticate(request, user=self.user)

        # 创建视图并调用
        view = ProxySelectViewSet.as_view({"get": "list"})
        response = view(request)

        # 验证响应
        self.assertEqual(response.status_code, 200)
        results = response.data["results"]
        self.assertEqual(len(results), 2)  # 只有2个代理可用

        # 验证返回的代理ID
        proxy_ids = [r["id"] for r in results]
        self.assertIn(self.proxy1.id, proxy_ids)
        self.assertIn(self.proxy2.id, proxy_ids)
        self.assertNotIn(self.proxy3.id, proxy_ids)
        self.assertNotIn(self.proxy4.id, proxy_ids)

    def test_proxy_select_response_format(self):
        """AC[场景1]: 响应格式正确"""
        request = self.factory.get("/api/v1/proxy/select/")
        force_authenticate(request, user=self.user)

        view = ProxySelectViewSet.as_view({"get": "list"})
        response = view(request)

        # 验证响应格式
        self.assertIn("results", response.data)
        result = response.data["results"][0]

        # 验证必需字段
        self.assertIn("id", result)
        self.assertIn("name", result)
        self.assertIn("protocol", result)
        self.assertIn("protocol_display", result)
        self.assertIn("host", result)
        self.assertIn("port", result)
        self.assertIn("is_healthy", result)
        self.assertIn("status", result)

    def test_proxy_select_status_field(self):
        """AC[场景2]: 状态字段显示正确"""
        request = self.factory.get("/api/v1/proxy/select/")
        force_authenticate(request, user=self.user)

        view = ProxySelectViewSet.as_view({"get": "list"})
        response = view(request)

        # 验证健康代理的状态
        results = response.data["results"]
        for result in results:
            self.assertEqual(result["status"], "✓ 健康")
            self.assertTrue(result["is_healthy"])

    def test_proxy_select_requires_authentication(self):
        """AC[场景7]: 需要认证才能访问"""
        # 创建未认证请求
        request = self.factory.get("/api/v1/proxy/select/")

        view = ProxySelectViewSet.as_view({"get": "list"})
        response = view(request)

        # 验证401错误
        self.assertEqual(response.status_code, 401)


class TestConnectionAPITest(TestCase):
    """Phase 2: 测试连接 API测试"""

    def setUp(self):
        """设置测试数据"""
        self.user = User.objects.create_user(username="testuser", password="testpass")
        self.factory = APIRequestFactory()

        self.proxy = ProxyConfig.objects.create(
            name="测试代理",
            protocol=ProxyProtocol.HTTP,
            host="proxy.example.com",
            port=8080,
            is_active=True,
            is_healthy=True,
        )

    @patch("httpx.Client.get")
    def test_connection_success(self, mock_get):
        """AC[场景2]: 测试连接成功"""
        # Mock httpx响应
        mock_response = MagicMock()
        mock_response.json.return_value = {"origin": "203.0.113.42"}
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        # 创建请求
        request = self.factory.post(f"/api/v1/proxy/{self.proxy.id}/test_connection/")
        force_authenticate(request, user=self.user)

        # 创建视图并调用
        view = TestConnectionView.as_view()
        response = view(request, pk=self.proxy.id)

        # 验证响应
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["success"])
        self.assertEqual(response.data["ip"], "203.0.113.42")
        self.assertIn("response_time_ms", response.data)

        # 验证代理健康状态更新
        self.proxy.refresh_from_db()
        self.assertTrue(self.proxy.is_healthy)

    @patch("httpx.Client.get")
    def test_connection_timeout(self, mock_get):
        """AC[场景3]: 测试连接超时"""
        # Mock超时异常
        mock_get.side_effect = httpx.TimeoutException("Connection timeout")

        request = self.factory.post(f"/api/v1/proxy/{self.proxy.id}/test_connection/")
        force_authenticate(request, user=self.user)

        view = TestConnectionView.as_view()
        response = view(request, pk=self.proxy.id)

        # 验证响应
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.data["success"])
        self.assertEqual(response.data["error"], "Connection timeout")

        # 验证代理健康状态更新为False
        self.proxy.refresh_from_db()
        self.assertFalse(self.proxy.is_healthy)

    @patch("httpx.Client.get")
    def test_connection_http_error(self, mock_get):
        """测试HTTP错误"""
        # Mock HTTP错误
        mock_response = MagicMock()
        mock_response.status_code = 403
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Forbidden", request=MagicMock(), response=mock_response
        )
        mock_get.return_value = mock_response

        request = self.factory.post(f"/api/v1/proxy/{self.proxy.id}/test_connection/")
        force_authenticate(request, user=self.user)

        view = TestConnectionView.as_view()
        response = view(request, pk=self.proxy.id)

        # 验证响应
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.data["success"])
        self.assertIn("HTTP error", response.data["error"])

    def test_connection_proxy_not_found(self):
        """测试代理不存在"""
        request = self.factory.post("/api/v1/proxy/99999/test_connection/")
        force_authenticate(request, user=self.user)

        view = TestConnectionView.as_view()
        response = view(request, pk=99999)

        # 验证404错误
        self.assertEqual(response.status_code, 404)
        self.assertFalse(response.data["success"])
        self.assertEqual(response.data["error"], "代理配置不存在")

    def test_connection_proxy_inactive(self):
        """测试代理未启用"""
        # 禁用代理
        self.proxy.is_active = False
        self.proxy.save()

        request = self.factory.post(f"/api/v1/proxy/{self.proxy.id}/test_connection/")
        force_authenticate(request, user=self.user)

        view = TestConnectionView.as_view()
        response = view(request, pk=self.proxy.id)

        # 验证400错误
        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.data["success"])
        self.assertEqual(response.data["error"], "代理未启用")

    def test_connection_requires_authentication(self):
        """AC[场景7]: 需要认证才能访问"""
        request = self.factory.post(f"/api/v1/proxy/{self.proxy.id}/test_connection/")

        view = TestConnectionView.as_view()
        response = view(request, pk=self.proxy.id)

        # 验证401错误
        self.assertEqual(response.status_code, 401)


class ErrorHandlingTest(TestCase):
    """Phase 3: 错误处理测试"""

    def setUp(self):
        """设置测试数据"""
        self.user = User.objects.create_user(username="testuser", password="testpass")
        self.factory = APIRequestFactory()

    def test_empty_proxy_list(self):
        """测试无代理时返回空列表"""
        request = self.factory.get("/api/v1/proxy/select/")
        force_authenticate(request, user=self.user)

        view = ProxySelectViewSet.as_view({"get": "list"})
        response = view(request)

        # 验证空列表
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["results"]), 0)
