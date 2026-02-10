"""
Story 9.4: HttpProxyProvider完整实现测试套件

测试HttpProxyProvider的完整功能：
- Phase 1: get_proxy()方法测试
- Phase 2: record_usage()方法测试
- Phase 3: 异常处理测试
- Phase 4: ProxyManager集成测试
- Phase 5: 端到端测试

@Author: Epic 9 Team
@Created: 2026-01-31
@Story: 9.4 - HttpProxyProvider实现
"""

from unittest.mock import patch

import pytest
from django.test import TestCase

from apps.proxy.models import ProxyConfig, ProxyProtocol, ProxyUsageLog
from apps.proxy.services import HttpProxyProvider, NoProxyProvider, ProxyManager, ProxyProvider


class HttpProxyProviderGetProxyTest(TestCase):
    """Phase 1: get_proxy()方法测试"""

    def test_get_proxy_returns_valid_url(self):
        """AC[场景1]: 代理可用且健康，返回代理URL"""
        proxy = ProxyConfig.objects.create(
            name="测试代理",
            protocol=ProxyProtocol.HTTPS,
            host="proxy.example.com",
            port=8080,
            username="user",
            password="pass123",
            is_active=True,
            is_healthy=True,
        )

        provider = HttpProxyProvider(proxy)
        url = provider.get_proxy()

        # 验证返回有效的代理URL
        assert url is not None
        assert url == "https://user:pass123@proxy.example.com:8080"

    def test_get_proxy_without_auth(self):
        """测试无认证代理URL"""
        proxy = ProxyConfig.objects.create(
            name="无认证代理",
            protocol=ProxyProtocol.HTTP,
            host="proxy.example.com",
            port=8080,
            is_active=True,
            is_healthy=True,
        )

        provider = HttpProxyProvider(proxy)
        url = provider.get_proxy()

        assert url == "http://proxy.example.com:8080"

    def test_get_proxy_all_protocols(self):
        """测试所有协议的URL构建"""
        test_cases = [
            (ProxyProtocol.HTTP, "http://host:80"),
            (ProxyProtocol.HTTPS, "https://host:443"),
            (ProxyProtocol.SOCKS5, "socks5://host:1080"),
        ]

        for protocol, expected_prefix in test_cases:
            proxy = ProxyConfig.objects.create(
                name=f"{protocol}代理",
                protocol=protocol,
                host="host",
                port=80
                if protocol == ProxyProtocol.HTTP
                else (443 if protocol == ProxyProtocol.HTTPS else 1080),
                is_active=True,
                is_healthy=True,
            )

            provider = HttpProxyProvider(proxy)
            url = provider.get_proxy()
            assert url.startswith(expected_prefix)


class HttpProxyProviderRecordUsageTest(TestCase):
    """Phase 2: record_usage()方法测试"""

    def setUp(self):
        """设置测试数据"""
        self.proxy = ProxyConfig.objects.create(
            name="测试代理",
            protocol=ProxyProtocol.HTTPS,
            host="proxy.example.com",
            port=8080,
        )

    def test_record_usage_success(self):
        """AC[场景4]: 记录成功日志"""
        provider = HttpProxyProvider(self.proxy)

        initial_count = ProxyUsageLog.objects.count()

        provider.record_usage(
            ai_provider="OpenAIClient",
            endpoint="/v1/chat/completions",
            success=True,
            response_time=250,
        )

        # 验证日志创建
        assert ProxyUsageLog.objects.count() == initial_count + 1

        log = ProxyUsageLog.objects.first()
        assert log.proxy == self.proxy
        assert log.ai_provider == "OpenAIClient"
        assert log.endpoint == "/v1/chat/completions"
        assert log.success is True
        assert log.response_time_ms == 250

        # 验证last_used_at更新
        self.proxy.refresh_from_db()
        assert self.proxy.last_used_at is not None

    def test_record_usage_failure(self):
        """AC[场景5]: 记录失败日志"""
        provider = HttpProxyProvider(self.proxy)

        provider.record_usage(
            ai_provider="ClaudeClient",
            endpoint="/v1/messages",
            success=False,
            response_time=5000,
            error_message="Connection timeout",
        )

        # 验证日志创建
        log = ProxyUsageLog.objects.first()
        assert log.success is False
        assert log.error_message == "Connection timeout"
        assert log.response_time_ms == 5000

        # 验证last_used_at仍然更新
        self.proxy.refresh_from_db()
        assert self.proxy.last_used_at is not None

    def test_record_usage_updates_last_used_at(self):
        """AC[场景4/5]: 验证last_used_at更新"""
        provider = HttpProxyProvider(self.proxy)

        # 第一次调用
        assert self.proxy.last_used_at is None
        provider.record_usage("Test", "/test", True, 100)

        self.proxy.refresh_from_db()
        first_update = self.proxy.last_used_at
        assert first_update is not None

        # 第二次调用（验证时间戳更新）
        import time

        time.sleep(0.01)  # 确保时间戳不同
        provider.record_usage("Test", "/test", True, 100)

        self.proxy.refresh_from_db()
        second_update = self.proxy.last_used_at
        assert second_update > first_update


class HttpProxyProviderValidationTest(TestCase):
    """Phase 2: 参数验证测试"""

    def setUp(self):
        """设置测试数据"""
        self.proxy = ProxyConfig.objects.create(
            name="测试代理",
            protocol=ProxyProtocol.HTTP,
            host="proxy.example.com",
            port=8080,
        )
        self.provider = HttpProxyProvider(self.proxy)

    def test_record_usage_empty_ai_provider(self):
        """AC[场景8]: ai_provider为空时抛出ValueError"""
        with pytest.raises(ValueError) as exc:
            self.provider.record_usage(
                ai_provider="",  # 空字符串
                endpoint="/v1/chat/completions",
                success=True,
                response_time=100,
            )
        assert "ai_provider cannot be empty" in str(exc.value)

    def test_record_usage_none_ai_provider(self):
        """ai_provider为None时抛出ValueError"""
        with pytest.raises(ValueError) as exc:
            self.provider.record_usage(
                ai_provider=None,
                endpoint="/v1/chat/completions",
                success=True,
                response_time=100,
            )
        assert "ai_provider cannot be empty" in str(exc.value)

    def test_record_usage_empty_endpoint(self):
        """endpoint为空时抛出ValueError"""
        with pytest.raises(ValueError) as exc:
            self.provider.record_usage(
                ai_provider="OpenAIClient",
                endpoint="",  # 空字符串
                success=True,
                response_time=100,
            )
        assert "endpoint cannot be empty" in str(exc.value)

    def test_record_usage_negative_response_time(self):
        """response_time为负数时抛出ValueError"""
        with pytest.raises(ValueError) as exc:
            self.provider.record_usage(
                ai_provider="OpenAIClient",
                endpoint="/v1/chat/completions",
                success=True,
                response_time=-1,  # 负数
            )
        assert "response_time must be non-negative" in str(exc.value)


class HttpProxyProviderExceptionHandlingTest(TestCase):
    """Phase 3: 异常处理测试"""

    def setUp(self):
        """设置测试数据"""
        self.proxy = ProxyConfig.objects.create(
            name="测试代理",
            protocol=ProxyProtocol.HTTPS,
            host="proxy.example.com",
            port=8080,
            username="user",
            password="pass123",
        )

    @patch("apps.proxy.services.logger")
    def test_get_proxy_handles_decryption_error(self, mock_logger):
        """AC[场景6]: 密码解密错误时返回None"""
        # Mock get_proxy_url()抛出解密异常
        with patch.object(ProxyConfig, "get_proxy_url", side_effect=Exception("Decryption failed")):
            provider = HttpProxyProvider(self.proxy)
            url = provider.get_proxy()

            # 验证返回None（触发降级）
            assert url is None

            # 验证错误日志记录
            mock_logger.error.assert_called_once()
            assert "Failed to decrypt proxy" in str(mock_logger.error.call_args)

    @patch("apps.proxy.services.logger")
    def test_record_usage_handles_database_error(self, mock_logger):
        """记录日志时数据库异常不影响AI调用"""
        # Mock ProxyUsageLog.objects.create抛出异常
        with patch(
            "apps.proxy.services.ProxyUsageLog.objects.create",
            side_effect=Exception("Database error"),
        ):
            provider = HttpProxyProvider(self.proxy)

            # 不应抛出异常
            provider.record_usage(
                ai_provider="OpenAIClient",
                endpoint="/v1/chat/completions",
                success=True,
                response_time=100,
            )

            # 验证错误日志记录
            mock_logger.error.assert_called_once()
            assert "Failed to record proxy usage" in str(mock_logger.error.call_args)

    @patch("apps.proxy.services.logger")
    def test_get_proxy_logs_proxy_name(self, mock_logger):
        """验证get_proxy记录使用的代理名称"""
        provider = HttpProxyProvider(self.proxy)
        provider.get_proxy()

        # 验证info日志记录
        mock_logger.info.assert_called_once()
        assert "Using proxy:" in str(mock_logger.info.call_args)


class ProxyManagerIntegrationTest(TestCase):
    """Phase 4: ProxyManager集成测试"""

    def test_get_provider_returns_http_proxy_provider(self):
        """AC[场景7]: ProxyManager返回HttpProxyProvider实例"""
        proxy = ProxyConfig.objects.create(
            name="测试代理",
            protocol=ProxyProtocol.HTTP,
            host="proxy.example.com",
            port=8080,
            is_active=True,
            is_healthy=True,
        )

        provider = ProxyManager.get_provider(proxy.id)

        # 验证返回HttpProxyProvider实例
        assert isinstance(provider, HttpProxyProvider)
        assert provider.proxy_config == proxy

    def test_get_provider_passes_project_id(self):
        """验证project_id正确传递给HttpProxyProvider"""
        proxy = ProxyConfig.objects.create(
            name="测试代理",
            protocol=ProxyProtocol.HTTP,
            host="proxy.example.com",
            port=8080,
        )

        provider = ProxyManager.get_provider(proxy.id, project_id=10)

        # 验证project_id传递
        assert provider.project_id == 10

    def test_inactive_proxy_returns_no_proxy_provider(self):
        """AC[场景2]: 代理已禁用时返回NoProxyProvider"""
        proxy = ProxyConfig.objects.create(
            name="禁用代理",
            protocol=ProxyProtocol.HTTP,
            host="proxy.example.com",
            port=8080,
            is_active=False,  # 已禁用
            is_healthy=True,
        )

        provider = ProxyManager.get_provider(proxy.id)

        # 验证返回NoProxyProvider（降级）
        assert isinstance(provider, NoProxyProvider)

    def test_unhealthy_proxy_returns_no_proxy_provider(self):
        """AC[场景3]: 代理不健康时返回NoProxyProvider"""
        proxy = ProxyConfig.objects.create(
            name="不健康代理",
            protocol=ProxyProtocol.HTTP,
            host="proxy.example.com",
            port=8080,
            is_active=True,
            is_healthy=False,  # 不健康
        )

        provider = ProxyManager.get_provider(proxy.id)

        # 验证返回NoProxyProvider（降级）
        assert isinstance(provider, NoProxyProvider)

    @patch("apps.proxy.services.ProxyConfig.objects.get")
    def test_database_exception_returns_no_proxy_provider(self, mock_get):
        """测试数据库通用异常处理（line 295-298）"""
        # 模拟数据库连接错误
        mock_get.side_effect = Exception("Database connection error")

        provider = ProxyManager.get_provider(999)

        # 验证返回NoProxyProvider（降级）
        assert isinstance(provider, NoProxyProvider)


class HttpProxyProviderE2ETest(TestCase):
    """Phase 5: 端到端集成测试"""

    def test_complete_proxy_usage_workflow(self):
        """AC[场景8]: 完整的代理使用流程"""
        # 1. 创建代理配置
        proxy = ProxyConfig.objects.create(
            name="E2E测试代理",
            protocol=ProxyProtocol.HTTPS,
            host="e2e.example.com",
            port=8888,
            username="e2euser",
            password="e2epass",
            is_active=True,
            is_healthy=True,
        )

        # 2. 获取Provider
        provider = ProxyManager.get_provider(proxy.id)
        assert isinstance(provider, HttpProxyProvider)

        # 3. 获取代理URL
        url = provider.get_proxy()
        assert url == "https://e2euser:e2epass@e2e.example.com:8888"

        # 4. 记录成功使用
        provider.record_usage(
            ai_provider="OpenAIClient",
            endpoint="/v1/chat/completions",
            success=True,
            response_time=150,
        )

        # 5. 验证日志创建
        log = ProxyUsageLog.objects.get(proxy=proxy)
        assert log.ai_provider == "OpenAIClient"
        assert log.success is True
        assert log.response_time_ms == 150

        # 6. 验证last_used_at更新
        proxy.refresh_from_db()
        assert proxy.last_used_at is not None

    def test_proxy_degradation_to_direct_connection(self):
        """测试代理降级到直连"""
        # 1. 创建禁用的代理
        proxy = ProxyConfig.objects.create(
            name="降级测试代理",
            protocol=ProxyProtocol.HTTP,
            host="proxy.example.com",
            port=8080,
            is_active=False,  # 已禁用
            is_healthy=True,
        )

        # 2. 获取Provider（应降级到NoProxyProvider）
        provider = ProxyManager.get_provider(proxy.id)
        assert isinstance(provider, NoProxyProvider)

        # 3. 验证返回None（直连）
        assert provider.get_proxy() is None

    def test_multiple_api_calls_same_proxy(self):
        """测试同一代理多次调用的日志记录"""
        proxy = ProxyConfig.objects.create(
            name="多次调用代理",
            protocol=ProxyProtocol.HTTPS,
            host="multi.example.com",
            port=8080,
        )

        provider = ProxyManager.get_provider(proxy.id)

        # 模拟3次AI调用
        for i in range(3):
            provider.record_usage(
                ai_provider="OpenAIClient",
                endpoint=f"/v1/chat/completions/{i}",
                success=True,
                response_time=100 + i * 50,
            )

        # 验证创建了3条日志
        logs = ProxyUsageLog.objects.filter(proxy=proxy)
        assert logs.count() == 3

        # 验证所有日志成功
        for log in logs:
            assert log.success is True

        # 验证last_used_at更新
        proxy.refresh_from_db()
        assert proxy.last_used_at is not None


class SOLIDPrinciplesVerificationTest(TestCase):
    """SOLID原则验证测试"""

    def test_single_responsibility(self):
        """SOLID - S: 单一职责原则"""
        proxy = ProxyConfig.objects.create(
            name="SRP测试", protocol=ProxyProtocol.HTTP, host="host", port=80
        )

        provider = HttpProxyProvider(proxy)

        # 验证职责单一：
        # - get_proxy(): 只负责返回URL
        # - record_usage(): 只负责记录日志
        assert provider.get_proxy() is not None
        provider.record_usage("Test", "/test", True, 100)

    def test_open_closed_principle(self):
        """SOLID - O: 开闭原则"""
        # 可以通过继承HttpProxyProvider来扩展（虽然当前不需要）
        # 不需要修改现有代码

        class ExtendedHttpProxyProvider(HttpProxyProvider):
            """扩展的HttpProxyProvider（示例）"""

            def get_proxy_with_cache(self):
                """添加缓存功能的扩展方法"""
                return self.get_proxy()

        proxy = ProxyConfig.objects.create(
            name="OCP测试", protocol=ProxyProtocol.HTTP, host="host", port=80
        )

        extended = ExtendedHttpProxyProvider(proxy)
        assert extended.get_proxy_with_cache() is not None

    def test_liskov_substitution(self):
        """SOLID - L: 里氏替换原则"""
        proxy = ProxyConfig.objects.create(
            name="LSP测试", protocol=ProxyProtocol.HTTP, host="host", port=80
        )

        # HttpProxyProvider和NoProxyProvider可以互换
        http_provider = HttpProxyProvider(proxy)
        no_proxy = NoProxyProvider()

        # 两者都可以调用get_proxy()
        assert http_provider.get_proxy() is not None
        assert no_proxy.get_proxy() is None

        # 两者都可以调用record_usage()
        http_provider.record_usage("Test", "/test", True, 100)
        no_proxy.record_usage("Test", "/test", True, 100)

    def test_interface_segregation(self):
        """SOLID - I: 接口隔离原则"""
        # ProxyProvider接口专一（只有2个方法）
        # 没有"胖接口"

        proxy = ProxyConfig.objects.create(
            name="ISP测试", protocol=ProxyProtocol.HTTP, host="host", port=80
        )

        provider = HttpProxyProvider(proxy)
        # 可以调用两个方法
        provider.get_proxy()
        provider.record_usage("Test", "/test", True, 100)

    def test_dependency_inversion(self):
        """SOLID - D: 依赖倒置原则"""
        # ProxyManager依赖ProxyProvider抽象，而非具体实现

        proxy = ProxyConfig.objects.create(
            name="DIP测试", protocol=ProxyProtocol.HTTP, host="host", port=80
        )

        # 工厂方法返回抽象类型
        provider = ProxyManager.get_provider(proxy.id)
        assert isinstance(provider, ProxyProvider)
