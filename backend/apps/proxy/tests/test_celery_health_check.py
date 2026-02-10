"""
Story 9.10: Celery Beat健康检查测试套件

测试check_proxy_health任务：
- Phase 1: 任务执行成功
- Phase 2: 任务执行失败（超时）
- Phase 3: 任务执行失败（HTTP错误）
- Phase 4: 连续失败阈值判断
- Phase 5: 健康恢复逻辑
- Phase 6: 日志记录验证

@Author: Epic 9 Team
@Created: 2026-01-31
@Story: 9.10 - Celery健康检查
"""

from unittest.mock import MagicMock, patch

import httpx
from django.test import TestCase

from apps.proxy.models import ProxyConfig, ProxyProtocol, ProxyUsageLog
from apps.proxy.tasks import check_proxy_health


class CeleryHealthCheckTest(TestCase):
    """Story 9.10: Celery健康检查测试"""

    def setUp(self):
        """设置测试数据"""
        # 创建健康代理
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

        # 创建第二个健康代理（与proxy1相同状态）
        self.proxy2 = ProxyConfig.objects.create(
            name="香港代理-01",
            protocol=ProxyProtocol.HTTPS,
            host="proxy2.example.com",
            port=8443,
            is_active=True,
            is_healthy=True,
        )

        # 创建禁用的代理
        self.proxy3 = ProxyConfig.objects.create(
            name="禁用代理",
            protocol=ProxyProtocol.HTTP,
            host="proxy3.example.com",
            port=8080,
            is_active=False,
            is_healthy=True,
        )

    @patch("httpx.Client.get")
    def test_health_check_success(self, mock_get):
        """AC[场景2]: 健康检查成功"""
        # Mock httpx响应
        mock_response = MagicMock()
        mock_response.json.return_value = {"origin": "203.0.113.42"}
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        # 执行健康检查任务
        result = check_proxy_health()

        # 验证返回值
        self.assertEqual(result["total"], 2)  # proxy1 + proxy2 (proxy3被禁用)
        self.assertEqual(result["healthy_count"], 2)
        self.assertEqual(result["unhealthy_count"], 0)

        # 验证代理状态更新
        self.proxy1.refresh_from_db()
        self.assertTrue(self.proxy1.is_healthy)
        self.assertEqual(self.proxy1.consecutive_failures, 0)
        self.assertEqual(self.proxy1.consecutive_successes, 1)

        self.proxy2.refresh_from_db()
        self.assertTrue(self.proxy2.is_healthy)
        self.assertEqual(self.proxy2.consecutive_failures, 0)
        self.assertEqual(self.proxy2.consecutive_successes, 1)

        # 验证ProxyUsageLog创建
        logs = ProxyUsageLog.objects.filter(proxy=self.proxy1)
        self.assertEqual(logs.count(), 1)
        log = logs.first()
        self.assertTrue(log.success)
        self.assertEqual(log.ai_provider, "celery")
        self.assertEqual(log.endpoint, "https://httpbin.org/ip")
        self.assertGreater(log.response_time_ms, 0)

    @patch("httpx.Client.get")
    def test_health_check_timeout(self, mock_get):
        """AC[场景3]: 健康检查超时"""
        # Mock超时异常
        mock_get.side_effect = httpx.TimeoutException("Connection timeout")

        # 执行健康检查任务
        result = check_proxy_health()

        # 验证返回值
        self.assertEqual(result["total"], 2)
        self.assertEqual(result["healthy_count"], 0)
        self.assertEqual(result["unhealthy_count"], 2)

        # 验证代理状态更新
        self.proxy1.refresh_from_db()
        self.assertTrue(self.proxy1.is_healthy)  # 第1次失败，仍然健康
        self.assertEqual(self.proxy1.consecutive_failures, 1)
        self.assertEqual(self.proxy1.consecutive_successes, 0)

        # 验证ProxyUsageLog创建（失败记录）
        logs = ProxyUsageLog.objects.filter(proxy=self.proxy1)
        self.assertEqual(logs.count(), 1)
        log = logs.first()
        self.assertFalse(log.success)
        self.assertEqual(log.error_message, "Connection timeout")

    @patch("httpx.Client.get")
    def test_health_check_http_error(self, mock_get):
        """测试HTTP错误"""
        # Mock HTTP错误
        mock_response = MagicMock()
        mock_response.status_code = 403
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Forbidden", request=MagicMock(), response=mock_response
        )
        mock_get.return_value = mock_response

        # 执行健康检查任务
        result = check_proxy_health()

        # 验证返回值
        self.assertEqual(result["unhealthy_count"], 2)

        # 验证代理状态更新
        self.proxy1.refresh_from_db()
        self.assertEqual(self.proxy1.consecutive_failures, 1)
        self.assertEqual(self.proxy1.consecutive_successes, 0)

    @patch("httpx.Client.get")
    def test_consecutive_failures_threshold(self, mock_get):
        """AC[场景4]: 连续失败阈值判断（>3次）"""
        # Mock超时异常
        mock_get.side_effect = httpx.TimeoutException("Connection timeout")

        # 执行4次健康检查任务（模拟多次失败）
        for _i in range(4):
            check_proxy_health()

        # 验证代理状态：第4次后应该标记为不健康
        self.proxy1.refresh_from_db()
        self.assertFalse(self.proxy1.is_healthy)
        self.assertEqual(self.proxy1.consecutive_failures, 4)
        self.assertEqual(self.proxy1.consecutive_successes, 0)

    @patch("httpx.Client.get")
    def test_health_recovery_logic(self, mock_get):
        """AC[场景5]: 健康恢复逻辑（连续3次成功）"""
        # Mock httpx响应
        mock_response = MagicMock()
        mock_response.json.return_value = {"origin": "203.0.113.42"}
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        # 设置代理为不健康状态
        self.proxy1.is_healthy = False
        self.proxy1.consecutive_failures = 4
        self.proxy1.consecutive_successes = 0
        self.proxy1.save()

        # 执行3次健康检查任务（模拟连续成功）
        for _i in range(3):
            check_proxy_health()

        # 验证代理状态：第3次成功后应该恢复为健康
        self.proxy1.refresh_from_db()
        self.assertTrue(self.proxy1.is_healthy)
        self.assertEqual(self.proxy1.consecutive_failures, 0)
        self.assertEqual(self.proxy1.consecutive_successes, 3)

    @patch("httpx.Client.get")
    def test_inactive_proxy_skipped(self, mock_get):
        """测试禁用的代理被跳过"""
        # Mock httpx响应
        mock_response = MagicMock()
        mock_response.json.return_value = {"origin": "203.0.113.42"}
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        # 执行健康检查任务
        result = check_proxy_health()

        # 验证返回值（禁用的代理不应该计入total）
        self.assertEqual(result["total"], 2)  # 只有proxy1和proxy2

        # 验证禁用的代理没有被测试
        self.proxy3.refresh_from_db()
        self.assertEqual(self.proxy3.consecutive_failures, 0)
        self.assertEqual(self.proxy3.consecutive_successes, 0)

        # 验证没有为禁用的代理创建日志
        logs = ProxyUsageLog.objects.filter(proxy=self.proxy3)
        self.assertEqual(logs.count(), 0)

    @patch("httpx.Client.get")
    def test_no_active_proxies(self, mock_get):
        """测试没有启用的代理"""
        # 禁用所有代理
        ProxyConfig.objects.update(is_active=False)

        # 执行健康检查任务
        result = check_proxy_health()

        # 验证返回值
        self.assertEqual(result["total"], 0)
        self.assertEqual(result["healthy_count"], 0)
        self.assertEqual(result["unhealthy_count"], 0)

        # 验证没有创建任何日志
        logs = ProxyUsageLog.objects.all()
        self.assertEqual(logs.count(), 0)

    @patch("httpx.Client.get")
    def test_response_time_recorded(self, mock_get):
        """测试响应时间被记录"""
        # Mock httpx响应
        mock_response = MagicMock()
        mock_response.json.return_value = {"origin": "203.0.113.42"}
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        # 执行健康检查任务
        check_proxy_health()

        # 验证响应时间被记录
        logs = ProxyUsageLog.objects.filter(proxy=self.proxy1)
        log = logs.first()
        self.assertGreater(log.response_time_ms, 0)
        self.assertLess(log.response_time_ms, 5000)  # 应该小于5秒超时
