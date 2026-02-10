"""
代理管理系统 - 性能测试

测试代理管理的性能指标：
- 密码加密/解密性能
- 代理URL构建性能
- 数据库查询性能

@Author: Epic 9 Team
@Created: 2026-01-31
@Story: 9.12 - 测试套件
"""

import time

import pytest

from apps.proxy.models import ProxyConfig, ProxyProtocol, ProxyUsageLog
from apps.proxy.services import ProxyManager


@pytest.mark.django_db
class TestProxyPerformance:
    """代理性能测试"""

    def test_password_encryption_performance(self):
        """测试密码加密性能"""
        proxy = ProxyConfig(
            name="性能测试代理",
            protocol=ProxyProtocol.HTTPS,
            host="perf.example.com",
            port=8443,
            password="test_password_for_performance_testing",
        )

        # 测试加密性能（应 < 10ms）
        start = time.time()
        for _ in range(100):
            result = proxy.encrypt_password("test_password_for_performance_testing")
        end = time.time()

        avg_time_ms = (end - start) / 100 * 1000

        # 验证结果
        assert len(result) == 140  # Fernet加密后的密码长度
        assert result.startswith(b"gAAAAAB")  # Fernet前缀
        assert avg_time_ms < 10, f"加密性能: {avg_time_ms:.2f}ms/次，超过10ms阈值"

    def test_password_decryption_performance(self):
        """测试密码解密性能"""
        proxy = ProxyConfig.objects.create(
            name="解密性能测试",
            protocol=ProxyProtocol.HTTP,
            host="decrypt.example.com",
            port=8080,
            password="test_password",
        )

        encrypted = proxy.password_encrypted

        # 测试解密性能（应 < 10ms）
        start = time.time()
        for _ in range(100):
            result = proxy.decrypt_password(encrypted)
        end = time.time()

        avg_time_ms = (end - start) / 100 * 1000

        # 验证结果
        assert result == "test_password"
        assert avg_time_ms < 10, f"解密性能: {avg_time_ms:.2f}ms/次，超过10ms阈值"

    def test_proxy_url_construction_performance(self):
        """测试代理URL构建性能"""
        proxy = ProxyConfig.objects.create(
            name="URL构建测试",
            protocol=ProxyProtocol.HTTPS,
            host="url.example.com",
            port=8443,
            username="test_user",
            password="test_pass",
        )

        # 测试URL构建性能（应 < 5ms）
        start = time.time()
        for _ in range(100):
            url = proxy.get_proxy_url()
        end = time.time()

        avg_time_ms = (end - start) / 100 * 1000

        # 验证结果
        assert url == "https://test_user:test_pass@url.example.com:8443"
        assert avg_time_ms < 5, f"URL构建性能: {avg_time_ms:.2f}ms/次，超过5ms阈值"

    def test_manager_get_provider_performance(self):
        """测试ProxyManager获取提供者性能"""
        proxy = ProxyConfig.objects.create(
            name="Manager性能测试",
            protocol=ProxyProtocol.HTTP,
            host="manager.example.com",
            port=8080,
        )

        # 测试获取提供者性能（应 < 50ms）
        start = time.time()
        for _ in range(100):
            provider = ProxyManager.get_provider(proxy_id=proxy.id)
        end = time.time()

        avg_time_ms = (end - start) / 100 * 1000

        # 验证结果
        assert provider is not None
        assert hasattr(provider, "get_proxy")
        assert avg_time_ms < 50, f"获取提供者性能: {avg_time_ms:.2f}ms/次，超过50ms阈值"

    def test_database_query_performance_active_healthy_proxies(self):
        """测试查询活跃健康代理的性能"""
        # 创建100个代理
        for i in range(100):
            ProxyConfig.objects.create(
                name=f"代理{i}",
                protocol=ProxyProtocol.HTTP,
                host=f"proxy{i}.example.com",
                port=8080,
                is_active=True,
                is_healthy=True,
                priority=i,
            )

        # 测试查询性能（应 < 100ms）
        start = time.time()
        for _ in range(10):
            proxies = list(
                ProxyConfig.objects.filter(is_active=True, is_healthy=True).order_by(
                    "priority", "name"
                )
            )
        end = time.time()

        avg_time_ms = (end - start) / 10 * 1000

        # 验证结果
        assert len(proxies) == 100
        assert avg_time_ms < 100, f"查询性能: {avg_time_ms:.2f}ms/次，超过100ms阈值"

    def test_usage_log_creation_performance(self):
        """测试使用日志创建性能"""
        proxy = ProxyConfig.objects.create(
            name="日志性能测试",
            protocol=ProxyProtocol.HTTP,
            host="logperf.example.com",
            port=8080,
        )

        # 测试日志创建性能（应 < 50ms）
        start = time.time()
        for _i in range(100):
            log = ProxyUsageLog.objects.create(
                proxy=proxy,
                ai_provider="OpenAIClient",
                endpoint="https://api.openai.com/v1/chat/completions",
                response_time_ms=250,
                success=True,
            )
        end = time.time()

        avg_time_ms = (end - start) / 100 * 1000

        # 验证结果
        assert log.id is not None
        assert log.success is True
        assert avg_time_ms < 50, f"日志创建性能: {avg_time_ms:.2f}ms/次，超过50ms阈值"

    def test_usage_log_query_performance(self):
        """测试使用日志查询性能"""
        proxy = ProxyConfig.objects.create(
            name="查询性能测试",
            protocol=ProxyProtocol.HTTP,
            host="queryperf.example.com",
            port=8080,
        )

        # 创建1000条日志
        for i in range(1000):
            ProxyUsageLog.objects.create(
                proxy=proxy,
                ai_provider="OpenAIClient",
                endpoint="https://api.openai.com/v1/test",
                response_time_ms=100 + i % 500,
                success=i % 10 < 9,  # 90%成功率
            )

        # 测试查询性能（应 < 50ms）
        start = time.time()
        for _ in range(10):
            logs = list(ProxyUsageLog.objects.filter(proxy=proxy).order_by("-timestamp")[:100])
        end = time.time()

        avg_time_ms = (end - start) / 10 * 1000

        # 验证结果
        assert len(logs) == 100
        assert avg_time_ms < 50, f"查询性能: {avg_time_ms:.2f}ms/次，超过50ms阈值"

    def test_consecutive_failures_update_performance(self):
        """测试连续失败计数更新性能"""
        proxy = ProxyConfig.objects.create(
            name="计数性能测试",
            protocol=ProxyProtocol.HTTP,
            host="countperf.example.com",
            port=8080,
            is_healthy=True,
            consecutive_failures=0,
        )

        # 测试更新性能（应 < 20ms）
        start = time.time()
        for _ in range(100):
            proxy.consecutive_failures += 1
            proxy.save(update_fields=["consecutive_failures"])
        end = time.time()

        avg_time_ms = (end - start) / 100 * 1000

        # 验证结果
        proxy.refresh_from_db()
        assert proxy.consecutive_failures == 100
        assert avg_time_ms < 20, f"更新性能: {avg_time_ms:.2f}ms/次，超过20ms阈值"

    def test_bulk_proxy_creation_performance(self):
        """测试批量创建代理性能"""
        # 准备数据
        proxies_data = [
            {
                "name": f"批量代理{i}",
                "protocol": ProxyProtocol.HTTP,
                "host": f"bulk{i}.example.com",
                "port": 8080,
                "is_active": True,
                "is_healthy": True,
            }
            for i in range(50)
        ]

        # 测试批量创建性能（应 < 1000ms）
        start = time.time()
        created_proxies = [ProxyConfig.objects.create(**data) for data in proxies_data]
        end = time.time()

        total_time_ms = (end - start) * 1000

        # 验证结果
        assert len(created_proxies) == 50
        assert total_time_ms < 1000, f"批量创建性能: {total_time_ms:.2f}ms，超过1000ms阈值"

    def test_health_check_task_performance(self):
        """测试健康检查任务性能"""
        # 创建10个代理
        for i in range(10):
            ProxyConfig.objects.create(
                name=f"健康检查{i}",
                protocol=ProxyProtocol.HTTP,
                host=f"health{i}.example.com",
                port=8080,
                is_active=True,
                is_healthy=True,
            )

        # 导入健康检查任务
        # 测试任务执行性能（应 < 1000ms for 10 proxies）
        from unittest.mock import MagicMock, patch

        from apps.proxy.tasks import check_proxy_health

        mock_response = MagicMock()
        mock_response.json.return_value = {"origin": "203.0.113.42"}
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.Client.get") as mock_get:
            mock_get.return_value = mock_response

            start = time.time()
            result = check_proxy_health()
            end = time.time()

        total_time_ms = (end - start) * 1000

        # 验证结果
        assert result["total"] == 10
        assert result["healthy_count"] == 10
        assert total_time_ms < 1000, f"健康检查性能: {total_time_ms:.2f}ms，超过1000ms阈值"
