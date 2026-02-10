"""
Story 9.9: Django Admin测试连接功能测试套件

测试ProxyConfigAdmin的test_connection action：
- Phase 1: 测试连接成功
- Phase 2: 测试连接失败（超时）
- Phase 3: 测试连接失败（HTTP错误）
- Phase 4: 代理未启用
- Phase 5: 批量测试
- Phase 6: 日志记录验证

@Author: Epic 9 Team
@Created: 2026-01-31
@Story: 9.9 - Admin测试连接功能
"""

from unittest.mock import MagicMock, patch

import httpx
from django.contrib.auth.models import User
from django.contrib.messages.storage.cookie import CookieStorage
from django.test import RequestFactory, TestCase

from apps.proxy.admin import ProxyConfigAdmin
from apps.proxy.models import ProxyConfig, ProxyProtocol, ProxyUsageLog


class AdminTestConnectionTest(TestCase):
    """Story 9.9: 测试连接功能测试"""

    def setUp(self):
        """设置测试数据"""
        # 创建超级用户
        self.superuser = User.objects.create_superuser(
            username="admin", password="admin", email="admin@example.com"
        )

        # 创建代理配置
        self.proxy1 = ProxyConfig.objects.create(
            name="美国代理-01",
            protocol=ProxyProtocol.HTTP,
            host="proxy1.example.com",
            port=8080,
            username="user1",
            password="pass1",
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
        # 禁用的代理
        self.proxy3 = ProxyConfig.objects.create(
            name="禁用代理",
            protocol=ProxyProtocol.HTTP,
            host="proxy3.example.com",
            port=8080,
            is_active=False,
            is_healthy=True,
        )

        # 创建request factory和admin实例
        self.factory = RequestFactory()
        self.admin = ProxyConfigAdmin(ProxyConfig, None)

    def _get_request(self):
        """获取模拟的admin请求"""
        request = self.factory.post("/admin/proxy/proxyconfig/")
        request.user = self.superuser
        # 添加messages storage（使用CookieStorage避免session依赖）
        request._messages = CookieStorage(request)
        return request

    @patch("httpx.Client.get")
    def test_connection_success(self, mock_get):
        """AC[场景2]: 测试连接成功"""
        # Mock httpx响应
        mock_response = MagicMock()
        mock_response.json.return_value = {"origin": "203.0.113.42"}
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        # 获取request并执行action
        request = self._get_request()
        queryset = ProxyConfig.objects.filter(id=self.proxy1.id)

        self.admin.test_connection(request, queryset)

        # 验证代理健康状态更新
        self.proxy1.refresh_from_db()
        self.assertTrue(self.proxy1.is_healthy)

        # 验证ProxyUsageLog创建
        logs = ProxyUsageLog.objects.filter(proxy=self.proxy1)
        self.assertEqual(logs.count(), 1)
        log = logs.first()
        self.assertTrue(log.success)
        self.assertEqual(log.ai_provider, "system")
        self.assertEqual(log.endpoint, "https://httpbin.org/ip")
        self.assertGreater(log.response_time_ms, 0)

    @patch("httpx.Client.get")
    def test_connection_timeout(self, mock_get):
        """AC[场景3]: 测试连接超时"""
        # Mock超时异常
        mock_get.side_effect = httpx.TimeoutException("Connection timeout")

        request = self._get_request()
        queryset = ProxyConfig.objects.filter(id=self.proxy1.id)

        self.admin.test_connection(request, queryset)

        # 验证代理健康状态更新为False
        self.proxy1.refresh_from_db()
        self.assertFalse(self.proxy1.is_healthy)

        # 验证ProxyUsageLog创建（失败记录）
        logs = ProxyUsageLog.objects.filter(proxy=self.proxy1)
        self.assertEqual(logs.count(), 1)
        log = logs.first()
        self.assertFalse(log.success)
        self.assertEqual(log.error_message, "Connection timeout")

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

        request = self._get_request()
        queryset = ProxyConfig.objects.filter(id=self.proxy1.id)

        self.admin.test_connection(request, queryset)

        # 验证代理健康状态更新为False
        self.proxy1.refresh_from_db()
        self.assertFalse(self.proxy1.is_healthy)

        # 验证ProxyUsageLog创建
        logs = ProxyUsageLog.objects.filter(proxy=self.proxy1)
        self.assertEqual(logs.count(), 1)
        log = logs.first()
        self.assertFalse(log.success)
        self.assertIn("HTTP error", log.error_message)

    def test_connection_proxy_inactive(self):
        """AC[场景4]: 代理未启用"""
        request = self._get_request()
        queryset = ProxyConfig.objects.filter(id=self.proxy3.id)

        self.admin.test_connection(request, queryset)

        # 验证代理健康状态未改变（仍然为True）
        self.proxy3.refresh_from_db()
        self.assertTrue(self.proxy3.is_healthy)

        # 验证没有创建ProxyUsageLog（因为没有实际测试）
        logs = ProxyUsageLog.objects.filter(proxy=self.proxy3)
        self.assertEqual(logs.count(), 0)

    @patch("httpx.Client.get")
    def test_connection_response_time(self, mock_get):
        """AC[场景5]: 显示响应时间"""
        # Mock httpx响应
        mock_response = MagicMock()
        mock_response.json.return_value = {"origin": "203.0.113.42"}
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        request = self._get_request()
        queryset = ProxyConfig.objects.filter(id=self.proxy1.id)

        self.admin.test_connection(request, queryset)

        # 验证响应时间被记录
        logs = ProxyUsageLog.objects.filter(proxy=self.proxy1)
        log = logs.first()
        self.assertGreater(log.response_time_ms, 0)
        self.assertLess(log.response_time_ms, 5000)  # 应该小于5秒超时

    @patch("httpx.Client.get")
    def test_batch_test_connection(self, mock_get):
        """AC[场景6]: 批量测试"""
        # Mock第一个代理成功，第二个代理失败
        mock_response_1 = MagicMock()
        mock_response_1.json.return_value = {"origin": "203.0.113.42"}
        mock_response_1.raise_for_status = MagicMock()

        mock_response_2 = MagicMock()
        mock_response_2.status_code = 403
        mock_response_2.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Forbidden", request=MagicMock(), response=mock_response_2
        )

        mock_get.side_effect = [mock_response_1, mock_response_2]

        request = self._get_request()
        queryset = ProxyConfig.objects.filter(id__in=[self.proxy1.id, self.proxy2.id])

        self.admin.test_connection(request, queryset)

        # 验证两个代理的健康状态都更新了
        self.proxy1.refresh_from_db()
        self.proxy2.refresh_from_db()
        self.assertTrue(self.proxy1.is_healthy)
        self.assertFalse(self.proxy2.is_healthy)

        # 验证创建了2条ProxyUsageLog
        logs = ProxyUsageLog.objects.filter(proxy__in=[self.proxy1.id, self.proxy2.id])
        self.assertEqual(logs.count(), 2)

    @patch("httpx.Client.get")
    def test_connection_updates_last_used_at(self, mock_get):
        """测试连接成功时不更新last_used_at"""
        # Mock httpx响应
        mock_response = MagicMock()
        mock_response.json.return_value = {"origin": "203.0.113.42"}
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        # 获取初始last_used_at
        initial_last_used_at = self.proxy1.last_used_at

        request = self._get_request()
        queryset = ProxyConfig.objects.filter(id=self.proxy1.id)

        self.admin.test_connection(request, queryset)

        # 验证last_used_at未改变（测试连接不应更新此字段）
        self.proxy1.refresh_from_db()
        self.assertEqual(self.proxy1.last_used_at, initial_last_used_at)

    def test_action_description(self):
        """测试action描述"""
        # 验证action有正确的描述
        action = self.admin.actions[0]
        self.assertEqual(action, "test_connection")

        # 验证@test_connection装饰器的short_description
        self.assertEqual(self.admin.test_connection.short_description, "测试连接")
