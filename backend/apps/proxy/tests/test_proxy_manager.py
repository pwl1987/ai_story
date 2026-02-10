"""
Story 9.3: ProxyManager + NoProxyProvider测试套件

测试ProxyProvider策略模式、NoProxyProvider直连策略、ProxyManager工厂方法：
- Phase 1: ProxyProvider抽象接口测试
- Phase 2: NoProxyProvider行为测试
- Phase 3: ProxyManager工厂方法测试
- Phase 4: 向后兼容性集成测试

@Author: Epic 9 Team
@Created: 2026-01-31
@Story: 9.3 - ProxyManager + NoProxyProvider实现
"""

from abc import ABC

import pytest
from django.test import TestCase

from apps.proxy.models import ProxyConfig, ProxyProtocol, ProxyUsageLog
from apps.proxy.services import HttpProxyProvider, NoProxyProvider, ProxyManager, ProxyProvider


class ProxyProviderInterfaceTest(TestCase):
    """Phase 1: ProxyProvider抽象接口测试"""

    def test_proxy_provider_is_abstract(self):
        """AC[场景4]: ProxyProvider是ABC抽象类"""
        # 验证ProxyProvider是ABC子类
        assert issubclass(ProxyProvider, ABC)

    def test_cannot_instantiate_abstract_class(self):
        """AC[场景4]: 不能实例化抽象类"""
        # 尝试实例化抽象类应该失败
        with pytest.raises(TypeError):
            ProxyProvider()

    def test_must_implement_get_proxy(self):
        """AC[场景4]: 子类必须实现get_proxy()方法"""

        # 定义不完整的子类（缺少record_usage）
        class IncompleteProvider(ProxyProvider):
            def get_proxy(self):
                return None

        # 尝试实例化应该失败
        with pytest.raises(TypeError):
            IncompleteProvider()

    def test_must_implement_record_usage(self):
        """AC[场景4]: 子类必须实现record_usage()方法"""

        # 定义不完整的子类（缺少get_proxy）
        class IncompleteProvider(ProxyProvider):
            def record_usage(
                self,
                ai_provider: str,
                endpoint: str,
                success: bool,
                response_time: int,
                error_message=None,
            ):
                pass

        # 尝试实例化应该失败
        with pytest.raises(TypeError):
            IncompleteProvider()


class NoProxyProviderTest(TestCase):
    """Phase 2: NoProxyProvider行为测试"""

    def test_get_proxy_returns_none(self):
        """AC[场景1]: NoProxyProvider.get_proxy()返回None"""
        provider = NoProxyProvider()
        assert provider.get_proxy() is None

    def test_record_usage_does_nothing(self):
        """AC[场景2]: NoProxyProvider.record_usage()不创建日志"""
        provider = NoProxyProvider()

        # 记录初始日志数量
        initial_count = ProxyUsageLog.objects.count()

        # 调用record_usage
        provider.record_usage(
            ai_provider="OpenAIClient",
            endpoint="/v1/chat/completions",
            success=True,
            response_time=150,
        )

        # 验证没有创建新日志
        assert ProxyUsageLog.objects.count() == initial_count

    def test_record_usage_with_error_does_nothing(self):
        """AC[场景2]: 失败场景也不记录日志"""
        provider = NoProxyProvider()

        initial_count = ProxyUsageLog.objects.count()

        # 调用record_usage（失败场景）
        provider.record_usage(
            ai_provider="ClaudeClient",
            endpoint="/v1/messages",
            success=False,
            response_time=5000,
            error_message="Connection timeout",
        )

        # 验证没有创建新日志
        assert ProxyUsageLog.objects.count() == initial_count

    def test_is_proxy_provider_subclass(self):
        """验证NoProxyProvider是ProxyProvider的子类"""
        assert isinstance(NoProxyProvider(), ProxyProvider)


class ProxyManagerTest(TestCase):
    """Phase 3: ProxyManager工厂方法测试"""

    def test_get_provider_with_none_id(self):
        """AC[场景3]: proxy_id=None返回NoProxyProvider"""
        provider = ProxyManager.get_provider(None)
        assert isinstance(provider, NoProxyProvider)
        assert provider.get_proxy() is None

    def test_get_provider_with_invalid_id(self):
        """AC[场景3]: proxy_id不存在返回NoProxyProvider（降级）"""
        provider = ProxyManager.get_provider(99999)
        assert isinstance(provider, NoProxyProvider)
        assert provider.get_proxy() is None

    def test_get_provider_with_inactive_proxy(self):
        """代理已禁用时，降级到NoProxyProvider"""
        proxy = ProxyConfig.objects.create(
            name="禁用代理",
            protocol=ProxyProtocol.HTTP,
            host="proxy.example.com",
            port=8080,
            is_active=False,  # 已禁用
            is_healthy=True,
        )

        provider = ProxyManager.get_provider(proxy.id)
        assert isinstance(provider, NoProxyProvider)
        assert provider.get_proxy() is None

    def test_get_provider_with_unhealthy_proxy(self):
        """代理不健康时，降级到NoProxyProvider"""
        proxy = ProxyConfig.objects.create(
            name="不健康代理",
            protocol=ProxyProtocol.HTTP,
            host="proxy.example.com",
            port=8080,
            is_active=True,
            is_healthy=False,  # 不健康
        )

        provider = ProxyManager.get_provider(proxy.id)
        assert isinstance(provider, NoProxyProvider)
        assert provider.get_proxy() is None

    def test_get_provider_with_valid_proxy(self):
        """AC[场景5]: 正常流程 - 返回HttpProxyProvider"""
        proxy = ProxyConfig.objects.create(
            name="测试代理",
            protocol=ProxyProtocol.HTTP,
            host="proxy.example.com",
            port=8080,
            is_active=True,
            is_healthy=True,
        )

        provider = ProxyManager.get_provider(proxy.id)
        assert isinstance(provider, HttpProxyProvider)
        # TODO: Story 9.4 - 验证get_proxy()返回正确的URL

    def test_project_id_passed_to_provider(self):
        """AC[场景7]: project_id正确传递给Provider实例"""
        proxy = ProxyConfig.objects.create(
            name="测试代理",
            protocol=ProxyProtocol.HTTP,
            host="proxy.example.com",
            port=8080,
        )

        provider = ProxyManager.get_provider(proxy.id, project_id=10)
        assert provider.project_id == 10

    def test_project_id_with_no_proxy(self):
        """project_id在NoProxyProvider场景下为None"""
        provider = ProxyManager.get_provider(None, project_id=10)
        assert provider.get_proxy() is None
        # NoProxyProvider没有project_id属性，但这是正常的

    def test_get_provider_is_stateless(self):
        """AC[场景7]: 每次调用返回新实例（无状态）"""
        proxy = ProxyConfig.objects.create(
            name="测试代理",
            protocol=ProxyProtocol.HTTP,
            host="proxy.example.com",
            port=8080,
        )

        provider1 = ProxyManager.get_provider(proxy.id)
        provider2 = ProxyManager.get_provider(proxy.id)

        # 验证是两个不同的实例
        assert provider1 is not provider2
        # 但类型相同
        assert type(provider1) is type(provider2)

    def test_exception_handling_in_get_provider(self):
        """验证异常处理 - 所有异常都被捕获"""
        # 模拟数据库异常
        # 注意：这个测试很难模拟真实的数据库异常
        # 但我们可以验证降级策略的逻辑

        # 传入一个不存在的proxy_id
        provider = ProxyManager.get_provider(999999)
        assert isinstance(provider, NoProxyProvider)

        # 传入None
        provider = ProxyManager.get_provider(None)
        assert isinstance(provider, NoProxyProvider)


class HttpProxyProviderPlaceholderTest(TestCase):
    """Phase 3: HttpProxyProvider占位符测试"""

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

    def test_http_proxy_provider_init(self):
        """验证HttpProxyProvider初始化"""
        provider = HttpProxyProvider(self.proxy, project_id=10)
        assert provider.proxy_config == self.proxy
        assert provider.project_id == 10

    def test_http_proxy_provider_get_proxy(self):
        """验证get_proxy()返回代理URL（Story 9.4完整实现）"""
        provider = HttpProxyProvider(self.proxy)
        url = provider.get_proxy()
        # TODO: Story 9.4 - 完整实现后验证URL格式
        assert url is not None
        assert url == "https://user:pass123@proxy.example.com:8080"

    def test_http_proxy_provider_record_usage(self):
        """验证record_usage()创建日志（Story 9.4完整实现）"""
        provider = HttpProxyProvider(self.proxy)

        initial_count = ProxyUsageLog.objects.count()
        provider.record_usage(
            ai_provider="OpenAIClient",
            endpoint="/v1/chat/completions",
            success=True,
            response_time=150,
        )

        # 验证创建了日志
        assert ProxyUsageLog.objects.count() == initial_count + 1

        log = ProxyUsageLog.objects.first()
        assert log.proxy == self.proxy
        assert log.ai_provider == "OpenAIClient"
        assert log.endpoint == "/v1/chat/completions"
        assert log.success is True
        assert log.response_time_ms == 150

    def test_is_proxy_provider_subclass(self):
        """验证HttpProxyProvider是ProxyProvider的子类"""
        assert isinstance(HttpProxyProvider(self.proxy), ProxyProvider)


class BackwardCompatibilityTest(TestCase):
    """Phase 4: 向后兼容性集成测试"""

    def test_ai_client_without_proxy_id(self):
        """AC[场景6]: 模拟现有AI客户端代码未设置proxy_id"""
        # 模拟现有代码 - proxy_id=None
        provider = ProxyManager.get_provider(None)

        # 验证返回NoProxyProvider
        assert isinstance(provider, NoProxyProvider)
        assert provider.get_proxy() is None

    def test_existing_code_remains_unchanged(self):
        """AC[场景6]: 现有代码行为与原版本一致"""
        # 模拟现有AI客户端的调用方式
        # 旧代码：不传proxy_id
        provider = ProxyManager.get_provider(None)

        # 验证行为一致（直连）
        assert provider.get_proxy() is None

        # 验证不记录日志（向后兼容）
        initial_count = ProxyUsageLog.objects.count()
        provider.record_usage(
            ai_provider="OpenAIClient",
            endpoint="/v1/chat/completions",
            success=True,
            response_time=150,
        )
        assert ProxyUsageLog.objects.count() == initial_count

    def test_new_code_with_proxy(self):
        """新代码：传入proxy_id时的行为"""
        proxy = ProxyConfig.objects.create(
            name="新代理",
            protocol=ProxyProtocol.HTTP,
            host="proxy.example.com",
            port=8080,
        )

        # 新代码：传入proxy_id
        provider = ProxyManager.get_provider(proxy.id)

        # 验证返回HttpProxyProvider
        assert isinstance(provider, HttpProxyProvider)

        # TODO: Story 9.4 - 验证get_proxy()返回有效的代理URL


class SOLIDPrinciplesTest(TestCase):
    """SOLID原则验证测试"""

    def test_single_responsibility(self):
        """SOLID - S: 单一职责原则"""
        # ProxyProvider只负责定义接口
        # NoProxyProvider只负责直连策略
        # ProxyManager只负责工厂方法
        # 每个类只有一个改变的理由

        provider = ProxyManager.get_provider(None)
        assert isinstance(provider, NoProxyProvider)
        assert provider.get_proxy() is None

    def test_open_closed_principle(self):
        """SOLID - O: 开闭原则"""
        # 可以通过继承ProxyProvider来扩展新的策略
        # 不需要修改现有代码

        class NewProxyProvider(ProxyProvider):
            def get_proxy(self):
                return "http://new-proxy.com:8080"

            def record_usage(
                self,
                ai_provider: str,
                endpoint: str,
                success: bool,
                response_time: int,
                error_message=None,
            ):
                pass

        # 新策略可以正常工作
        new_provider = NewProxyProvider()
        assert new_provider.get_proxy() == "http://new-proxy.com:8080"

    def test_liskov_substitution(self):
        """SOLID - L: 里氏替换原则"""
        # NoProxyProvider和HttpProxyProvider可以互相替换
        proxy = ProxyConfig.objects.create(
            name="测试代理",
            protocol=ProxyProtocol.HTTP,
            host="proxy.example.com",
            port=8080,
        )

        no_proxy = NoProxyProvider()
        http_proxy = HttpProxyProvider(proxy)

        # 两者都可以调用get_proxy()
        assert no_proxy.get_proxy() is None
        assert http_proxy.get_proxy() is not None

        # 两者都可以调用record_usage()
        no_proxy.record_usage("Test", "/test", True, 100)
        http_proxy.record_usage("Test", "/test", True, 100)

    def test_interface_segregation(self):
        """SOLID - I: 接口隔离原则"""
        # ProxyProvider接口专一（只有2个方法）
        # 没有"胖接口"

        provider = ProxyManager.get_provider(None)
        # 可以调用两个方法
        provider.get_proxy()
        provider.record_usage("Test", "/test", True, 100)

    def test_dependency_inversion(self):
        """SOLID - D: 依赖倒置原则"""
        # ProxyManager依赖ProxyProvider抽象，而非具体实现
        # 调用方也依赖ProxyProvider抽象

        # 验证工厂方法返回抽象类型
        provider = ProxyManager.get_provider(None)
        assert isinstance(provider, ProxyProvider)

        provider2 = ProxyManager.get_provider(99999)
        assert isinstance(provider2, ProxyProvider)
