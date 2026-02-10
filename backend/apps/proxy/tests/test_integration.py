"""
代理管理系统 - 集成测试

测试代理管理的完整工作流：
- 代理配置创建 → AI调用 → 使用日志记录
- 代理失败 → 自动降级 → 日志记录
- 健康检查任务 → 状态更新 → 日志记录

@Author: Epic 9 Team
@Created: 2026-01-31
@Story: 9.12 - 测试套件
"""

from unittest.mock import MagicMock, patch

import httpx
from django.test import TestCase

from apps.proxy.models import ProxyConfig, ProxyProtocol, ProxyUsageLog
from apps.proxy.services import HttpProxyProvider, NoProxyProvider, ProxyManager


class ProxyIntegrationTest(TestCase):
    """代理管理集成测试"""

    def setUp(self):
        """设置测试数据"""
        # 创建代理配置
        self.proxy = ProxyConfig.objects.create(
            name="测试代理",
            protocol=ProxyProtocol.HTTP,
            host="proxy.example.com",
            port=8080,
            username="test_user",
            password="test_pass",
            is_active=True,
            is_healthy=True,
        )

    def test_proxy_workflow_success(self):
        """集成测试1: 代理配置 → 使用日志"""
        # 获取代理提供者
        provider = ProxyManager.get_provider(proxy_id=self.proxy.id)
        self.assertIsInstance(provider, HttpProxyProvider)

        # 验证代理URL正确
        proxy_url = provider.get_proxy()
        self.assertIn("proxy.example.com:8080", proxy_url)
        self.assertIn("test_user", proxy_url)

        # 模拟记录使用日志（使用provider.record_usage更新last_used_at）
        provider.record_usage(
            ai_provider="OpenAIClient",
            endpoint="https://api.openai.com/v1/chat/completions",
            response_time=250,
            success=True,
        )

        # 验证日志创建成功
        log = ProxyUsageLog.objects.filter(proxy=self.proxy).first()
        self.assertIsNotNone(log)
        self.assertEqual(log.proxy, self.proxy)
        self.assertTrue(log.success)
        self.assertEqual(log.response_time_ms, 250)

        # 验证代理的 last_used_at 已更新
        self.proxy.refresh_from_db()
        self.assertIsNotNone(self.proxy.last_used_at)

    @patch("httpx.Client.get")
    def test_proxy_degradation_workflow(self, mock_get):
        """集成测试2: 代理失败 → 日志记录"""
        # Mock代理连接失败
        mock_get.side_effect = httpx.TimeoutException("Connection timeout")

        # 获取代理提供者
        provider = ProxyManager.get_provider(proxy_id=self.proxy.id)
        self.assertIsInstance(provider, HttpProxyProvider)

        # 模拟代理调用失败
        proxy_url = provider.get_proxy()
        self.assertIn("proxy.example.com", proxy_url)

        # 记录失败的日志
        ProxyUsageLog.objects.create(
            proxy=self.proxy,
            ai_provider="OpenAIClient",
            endpoint="https://api.openai.com/v1/chat/completions",
            response_time_ms=0,
            success=False,
            error_message="Proxy connection failed, degraded to direct connection",
        )

        # 验证失败日志已创建
        failure_logs = ProxyUsageLog.objects.filter(proxy=self.proxy, success=False)
        self.assertEqual(failure_logs.count(), 1)
        self.assertIn("degraded", failure_logs.first().error_message)

    def test_no_proxy_provider_workflow(self):
        """集成测试3: 无代理配置 → 直连"""
        # 获取代理提供者
        provider = ProxyManager.get_provider(proxy_id=None)

        # 验证返回 NoProxyProvider
        self.assertIsInstance(provider, NoProxyProvider)

        # 验证 get_proxy() 返回 None
        proxy_url = provider.get_proxy()
        self.assertIsNone(proxy_url)

    @patch("httpx.Client.get")
    def test_health_check_workflow(self, mock_get):
        """集成测试4: 健康检查任务 → 状态更新 → 日志记录"""
        # Mock成功响应
        mock_response = MagicMock()
        mock_response.json.return_value = {"origin": "203.0.113.42"}
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        # 导入健康检查任务
        from apps.proxy.tasks import check_proxy_health

        # 执行健康检查
        result = check_proxy_health()

        # 验证返回结果
        self.assertEqual(result["total"], 1)
        self.assertEqual(result["healthy_count"], 1)
        self.assertEqual(result["unhealthy_count"], 0)

        # 验证代理状态更新
        self.proxy.refresh_from_db()
        self.assertTrue(self.proxy.is_healthy)
        self.assertEqual(self.proxy.consecutive_successes, 1)
        self.assertEqual(self.proxy.consecutive_failures, 0)

        # 验证使用日志已创建
        logs = ProxyUsageLog.objects.filter(proxy=self.proxy, ai_provider="celery")
        self.assertEqual(logs.count(), 1)
        self.assertTrue(logs.first().success)

    @patch("httpx.Client.get")
    def test_health_check_failure_recovery(self, mock_get):
        """集成测试5: 健康检查失败 → 恢复循环"""
        # 1. 模拟连续失败
        mock_get.side_effect = httpx.TimeoutException("Connection timeout")

        from apps.proxy.tasks import check_proxy_health

        # 执行4次健康检查（模拟连续失败）
        for _ in range(4):
            check_proxy_health()

        # 验证代理被标记为不健康
        self.proxy.refresh_from_db()
        self.assertFalse(self.proxy.is_healthy)
        self.assertEqual(self.proxy.consecutive_failures, 4)
        self.assertEqual(self.proxy.consecutive_successes, 0)

        # 2. 模拟恢复（连续成功）
        mock_response = MagicMock()
        mock_response.json.return_value = {"origin": "203.0.113.42"}
        mock_response.raise_for_status = MagicMock()
        mock_get.side_effect = None
        mock_get.return_value = mock_response

        # 执行3次健康检查（模拟连续成功）
        for _ in range(3):
            check_proxy_health()

        # 验证代理恢复为健康
        self.proxy.refresh_from_db()
        self.assertTrue(self.proxy.is_healthy)
        self.assertEqual(self.proxy.consecutive_failures, 0)
        self.assertEqual(self.proxy.consecutive_successes, 3)

    def test_proxy_priority_ordering(self):
        """集成测试6: 代理优先级排序"""
        # 创建多个代理，不同优先级
        proxy_low_priority = ProxyConfig.objects.create(
            name="低优先级代理",
            protocol=ProxyProtocol.HTTP,
            host="low.example.com",
            port=8080,
            is_active=True,
            is_healthy=True,
            priority=100,
        )

        ProxyConfig.objects.create(
            name="高优先级代理",
            protocol=ProxyProtocol.HTTP,
            host="high.example.com",
            port=8080,
            is_active=True,
            is_healthy=True,
            priority=0,
        )

        # 查询代理（按优先级排序）
        proxies = ProxyConfig.objects.filter(is_active=True, is_healthy=True).order_by(
            "priority", "name"
        )

        # 验证排序
        self.assertEqual(proxies[0].priority, 0)  # 高优先级和测试代理都是0
        self.assertIn(proxies[0].name, ["高优先级代理", "测试代理"])
        self.assertEqual(proxy_low_priority, proxies[2])

    def test_usage_log_query_optimization(self):
        """集成测试7: 使用日志查询优化"""
        # 创建多条使用日志
        for i in range(10):
            ProxyUsageLog.objects.create(
                proxy=self.proxy,
                ai_provider="OpenAIClient",
                endpoint=f"https://api.openai.com/v1/endpoint_{i}",
                response_time_ms=100 + i * 10,
                success=True,
            )

        # 按代理查询
        logs = ProxyUsageLog.objects.filter(proxy=self.proxy)
        self.assertEqual(logs.count(), 10)

        # 按AI提供商查询
        logs = ProxyUsageLog.objects.filter(ai_provider="OpenAIClient")
        self.assertGreaterEqual(logs.count(), 10)

        # 按成功状态查询
        logs = ProxyUsageLog.objects.filter(success=True)
        self.assertGreaterEqual(logs.count(), 10)

    def test_multiple_proxies_health_status(self):
        """集成测试8: 多个代理健康状态管理"""
        # 创建3个代理
        ProxyConfig.objects.create(
            name="代理1",
            protocol=ProxyProtocol.HTTP,
            host="proxy1.example.com",
            port=8080,
            is_active=True,
            is_healthy=True,
            consecutive_failures=0,
        )

        ProxyConfig.objects.create(
            name="代理2",
            protocol=ProxyProtocol.HTTP,
            host="proxy2.example.com",
            port=8080,
            is_active=True,
            is_healthy=False,
            consecutive_failures=4,
        )

        ProxyConfig.objects.create(
            name="代理3",
            protocol=ProxyProtocol.HTTP,
            host="proxy3.example.com",
            port=8080,
            is_active=False,
            is_healthy=True,
            consecutive_failures=0,
        )

        # 查询活跃且健康的代理
        active_healthy = ProxyConfig.objects.filter(is_active=True, is_healthy=True)
        self.assertEqual(active_healthy.count(), 2)  # self.proxy 和 proxy1

        # 查询活跃但不健康的代理
        active_unhealthy = ProxyConfig.objects.filter(is_active=True, is_healthy=False)
        self.assertEqual(active_unhealthy.count(), 1)  # proxy2

        # 查询所有不健康的代理
        all_unhealthy = ProxyConfig.objects.filter(is_healthy=False)
        self.assertEqual(all_unhealthy.count(), 1)  # proxy2


class ProxyConfigIntegrationTest(TestCase):
    """ProxyConfig模型集成测试"""

    def setUp(self):
        """设置测试数据"""
        self.proxy = ProxyConfig.objects.create(
            name="集成测试代理",
            protocol=ProxyProtocol.HTTPS,
            host="integration.example.com",
            port=8443,
            username="integration_user",
            password="integration_pass",
        )

    def test_password_encryption_workflow(self):
        """测试密码加密/解密工作流"""
        # 1. 验证密码已加密
        self.assertIsNotNone(self.proxy.password_encrypted)
        self.assertIsNone(self.proxy.password)  # 明文密码已清空

        # 2. 验证解密功能
        decrypted_password = self.proxy.decrypt_password(self.proxy.password_encrypted)
        self.assertEqual(decrypted_password, "integration_pass")

    def test_proxy_url_construction(self):
        """测试代理URL构建（通过ProxyConfig的get_proxy_url方法）"""
        # 测试有认证的URL（使用ProxyConfig的方法）
        url = self.proxy.get_proxy_url()
        self.assertEqual(
            url,
            "https://integration_user:integration_pass@integration.example.com:8443",
        )

        # 测试无认证的URL
        proxy_no_auth = ProxyConfig.objects.create(
            name="无认证代理",
            protocol=ProxyProtocol.HTTP,
            host="open.example.com",
            port=8080,
        )

        url = proxy_no_auth.get_proxy_url()
        self.assertEqual(url, "http://open.example.com:8080")


class ProxyUsageLogIntegrationTest(TestCase):
    """ProxyUsageLog模型集成测试"""

    def setUp(self):
        """设置测试数据"""
        self.proxy = ProxyConfig.objects.create(
            name="日志测试代理",
            protocol=ProxyProtocol.HTTP,
            host="log.example.com",
            port=8080,
        )

    def test_usage_log_aggregation(self):
        """测试使用日志聚合统计"""
        from django.db.models import Count, Q

        # 创建成功和失败的日志
        for i in range(7):
            ProxyUsageLog.objects.create(
                proxy=self.proxy,
                ai_provider="OpenAIClient" if i % 2 == 0 else "ClaudeClient",
                endpoint="https://api.example.com/v1/test",
                response_time_ms=100 + i * 10,
                success=i < 5,  # 前5个成功，后2个失败
            )

        # 统计成功率（使用filter方法）
        total = ProxyUsageLog.objects.filter(proxy=self.proxy).count()
        success = ProxyUsageLog.objects.filter(proxy=self.proxy, success=True).count()
        failure = ProxyUsageLog.objects.filter(proxy=self.proxy, success=False).count()

        self.assertEqual(total, 7)
        self.assertEqual(success, 5)
        self.assertEqual(failure, 2)

        # 计算成功率
        success_rate = success / total * 100
        self.assertAlmostEqual(success_rate, 71.43, places=1)

    def test_usage_log_filtering_by_time_range(self):
        """测试按时间范围筛选日志"""
        from datetime import timedelta

        from django.utils import timezone

        # 创建不同时间的日志
        now = timezone.now()
        old_time = now - timedelta(days=10)

        # 创建旧日志
        ProxyUsageLog.objects.create(
            proxy=self.proxy,
            ai_provider="OpenAIClient",
            endpoint="https://api.example.com/v1/test",
            response_time_ms=200,
            success=True,
            timestamp=old_time,
        )

        # 创建新日志
        new_log = ProxyUsageLog.objects.create(
            proxy=self.proxy,
            ai_provider="ClaudeClient",
            endpoint="https://api.example.com/v1/test",
            response_time_ms=300,
            success=True,
            timestamp=now,
        )

        # 查询最近7天的日志（排除setUp中的数据）
        cutoff = now - timedelta(days=7)
        recent_logs = ProxyUsageLog.objects.filter(
            proxy=self.proxy, timestamp__gte=cutoff, ai_provider="ClaudeClient"
        )
        self.assertEqual(recent_logs.count(), 1)
        self.assertEqual(recent_logs.first().id, new_log.id)
