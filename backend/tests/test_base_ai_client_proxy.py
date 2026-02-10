"""
Story 9.6: BaseAIClient代理支持测试套件

测试BaseAIClient的代理集成功能：
- Phase 1: proxy_id初始化测试
- Phase 2: _get_httpx_config()代理配置测试
- Phase 3: 代理使用测试
- Phase 4: 自动降级测试
- Phase 5: 向后兼容性测试
- Phase 6: 子类继承测试
- Phase 7: 项目上下文传递测试

@Author: Epic 9 Team
@Created: 2026-01-31
@Story: 9.6 - BaseAIClient代理支持
"""

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from django.test import TestCase

from apps.proxy.models import ProxyConfig, ProxyProtocol
from apps.proxy.services import HttpProxyProvider, NoProxyProvider
from core.ai_client.base import AIResponse, BaseAIClient


class TestClient(BaseAIClient):
    """Mock AI客户端 for testing"""

    async def generate(self, prompt: str, **kwargs):
        pass

    async def validate_config(self) -> bool:
        return True

    async def chat_completions(self, messages, **kwargs):
        """模拟聊天完成API调用"""
        return self._call_api_with_fallback(
            "/v1/chat/completions", json={"model": self.model_name, "messages": messages, **kwargs}
        )


class ProxyIdInitializationTest(TestCase):
    """Phase 1: proxy_id初始化测试"""

    def test_init_with_proxy_id_initializes_http_proxy_provider(self):
        """AC[场景1]: 传递proxy_id时初始化HttpProxyProvider"""
        # 创建代理配置
        proxy = ProxyConfig.objects.create(
            name="测试代理",
            protocol=ProxyProtocol.HTTP,
            host="proxy.example.com",
            port=8080,
            is_active=True,
            is_healthy=True,
        )

        # 创建客户端（传递proxy_id）
        client = TestClient(
            api_url="https://api.openai.com",
            api_key="test-key",
            model_name="gpt-4",
            proxy_id=proxy.id,
            project_id=10,
        )

        # 验证proxy_provider初始化为HttpProxyProvider
        self.assertIsInstance(client.proxy_provider, HttpProxyProvider)
        self.assertEqual(client.project_id, 10)

    def test_init_without_proxy_id_initializes_no_proxy_provider(self):
        """AC[场景1]: 不传递proxy_id时初始化NoProxyProvider"""
        # 创建客户端（不传proxy_id）
        client = TestClient(
            api_url="https://api.openai.com",
            api_key="test-key",
            model_name="gpt-4",
        )

        # 验证proxy_provider初始化为NoProxyProvider
        self.assertIsInstance(client.proxy_provider, NoProxyProvider)
        self.assertIsNone(client.project_id)

    def test_init_with_invalid_proxy_id_initializes_no_proxy_provider(self):
        """测试无效proxy_id时降级到NoProxyProvider"""
        # 创建客户端（传递不存在的proxy_id）
        client = TestClient(
            api_url="https://api.openai.com",
            api_key="test-key",
            model_name="gpt-4",
            proxy_id=99999,  # 不存在的代理
            project_id=10,
        )

        # 验证降级到NoProxyProvider
        self.assertIsInstance(client.proxy_provider, NoProxyProvider)
        self.assertEqual(client.project_id, 10)

    def test_init_with_inactive_proxy_initializes_no_proxy_provider(self):
        """测试代理不活跃时降级到NoProxyProvider"""
        # 创建禁用的代理
        proxy = ProxyConfig.objects.create(
            name="禁用代理",
            protocol=ProxyProtocol.HTTP,
            host="proxy.example.com",
            port=8080,
            is_active=False,  # 禁用
            is_healthy=True,
        )

        client = TestClient(
            api_url="https://api.openai.com",
            api_key="test-key",
            model_name="gpt-4",
            proxy_id=proxy.id,
        )

        # 验证降级到NoProxyProvider
        self.assertIsInstance(client.proxy_provider, NoProxyProvider)


class HttpxConfigTest(TestCase):
    """Phase 2: _get_httpx_config()代理配置测试"""

    def setUp(self):
        """设置测试数据"""
        self.client = TestClient(
            api_url="https://api.openai.com",
            api_key="test-key",
            model_name="gpt-4",
        )

    def test_get_httpx_config_without_proxy(self):
        """AC[场景2]: 无代理时不包含proxies键"""
        config = self.client._get_httpx_config(proxy_url=None)

        # 验证不包含proxies键
        self.assertNotIn("proxies", config)
        # 验证包含timeout
        self.assertIn("timeout", config)

    def test_get_httpx_config_with_proxy(self):
        """AC[场景2]: 有代理时包含proxies键"""
        proxy_url = "https://proxy.example.com:8080"
        config = self.client._get_httpx_config(proxy_url=proxy_url)

        # 验证包含proxies键
        self.assertIn("proxies", config)
        # 验证代理格式正确
        self.assertEqual(config["proxies"]["http://"], proxy_url)
        self.assertEqual(config["proxies"]["https://"], proxy_url)

    def test_get_httpx_config_merges_with_other_settings(self):
        """测试配置合并其他设置"""
        proxy_url = "https://proxy.example.com:8080"
        config = self.client._get_httpx_config(proxy_url=proxy_url)

        # 验证包含timeout
        self.assertIn("timeout", config)
        # 验证包含limits
        self.assertIn("limits", config)
        # 验证包含proxies
        self.assertIn("proxies", config)


class ProxyUsageTest(TestCase):
    """Phase 3: 代理使用测试"""

    def setUp(self):
        """设置测试数据"""
        # 创建代理配置
        self.proxy = ProxyConfig.objects.create(
            name="测试代理",
            protocol=ProxyProtocol.HTTPS,
            host="proxy.example.com",
            port=8080,
            is_active=True,
            is_healthy=True,
        )

    @pytest.mark.asyncio
    async def test_ai_call_uses_proxy(self):
        """AC[场景3]: AI调用自动使用代理"""
        client = TestClient(
            api_url="https://api.openai.com",
            api_key="test-key",
            model_name="gpt-4",
            proxy_id=self.proxy.id,
        )

        # Mock httpx.AsyncClient
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock()

            mock_response = MagicMock()
            mock_response.raise_for_status = MagicMock()
            mock_client.post = AsyncMock(return_value=mock_response)

            mock_client_class.return_value = mock_client

            # 调用API
            await client.chat_completions([{"role": "user", "content": "Hello"}])

            # 验证调用了httpx.AsyncClient
            mock_client_class.assert_called_once()

            # 验证配置包含代理
            call_args = mock_client_class.call_args
            config = call_args[1] if call_args else {}
            self.assertIn("proxies", config)

            # 验证代理URL正确
            proxy_url = config["proxies"]["https://"]
            self.assertIn("proxy.example.com:8080", proxy_url)

    @pytest.mark.asyncio
    async def test_ai_call_without_proxy_uses_direct_connection(self):
        """测试无代理时使用直连"""
        client = TestClient(
            api_url="https://api.openai.com",
            api_key="test-key",
            model_name="gpt-4",
        )

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock()

            mock_response = MagicMock()
            mock_response.raise_for_status = MagicMock()
            mock_client.post = AsyncMock(return_value=mock_response)

            mock_client_class.return_value = mock_client

            await client.chat_completions([{"role": "user", "content": "Hello"}])

            # 验证配置不包含代理
            call_args = mock_client_class.call_args
            config = call_args[1] if call_args else {}
            self.assertNotIn("proxies", config)


class AutoDegradationTest(TestCase):
    """Phase 4: 自动降级测试"""

    def setUp(self):
        """设置测试数据"""
        self.proxy = ProxyConfig.objects.create(
            name="测试代理",
            protocol=ProxyProtocol.HTTPS,
            host="proxy.example.com",
            port=8080,
            is_active=True,
            is_healthy=True,
        )

    @pytest.mark.asyncio
    async def test_ai_call_auto_degrades_on_proxy_error(self):
        """AC[场景4]: AI调用自动降级"""
        client = TestClient(
            api_url="https://api.openai.com",
            api_key="test-key",
            model_name="gpt-4",
            proxy_id=self.proxy.id,
        )

        with patch.object(client, "_get_httpx_config") as mock_config:
            config_with_proxy = {"proxies": {"all://": "https://proxy.example.com:8080"}}
            config_without_proxy = {}
            mock_config.side_effect = [config_with_proxy, config_without_proxy]

            with patch("httpx.AsyncClient") as mock_client_class:
                # 第一次调用失败（代理）
                mock_response_1 = MagicMock()
                mock_response_1.raise_for_status = MagicMock(
                    side_effect=httpx.ProxyError("Connection error")
                )
                mock_client_1 = AsyncMock()
                mock_client_1.__aenter__ = AsyncMock(return_value=mock_client_1)
                mock_client_1.__aexit__ = AsyncMock()
                mock_client_1.post = AsyncMock(return_value=mock_response_1)

                # 第二次调用成功（直连）
                mock_response_2 = MagicMock()
                mock_response_2.raise_for_status = MagicMock()
                mock_client_2 = AsyncMock()
                mock_client_2.__aenter__ = AsyncMock(return_value=mock_client_2)
                mock_client_2.__aexit__ = AsyncMock()
                mock_client_2.post = AsyncMock(return_value=mock_response_2)

                mock_client_class.side_effect = [mock_client_1, mock_client_2]

                # 调用API
                await client.chat_completions([{"role": "user", "content": "Hello"}])

                # 验证降级（调用了2次）
                self.assertEqual(mock_client_class.call_count, 2)


class BackwardCompatibilityTest(TestCase):
    """Phase 5: 向后兼容性测试"""

    @pytest.mark.asyncio
    async def test_existing_code_without_proxy_id_works(self):
        """AC[场景6]: 现有代码不传proxy_id时行为一致"""
        # 模拟现有代码（不传proxy_id）
        client = TestClient(
            api_url="https://api.openai.com",
            api_key="test-key",
            model_name="gpt-4",
        )

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock()

            mock_response = MagicMock()
            mock_response.raise_for_status = MagicMock()
            mock_client.post = AsyncMock(return_value=mock_response)

            mock_client_class.return_value = mock_client

            # 调用API
            response = await client.chat_completions([{"role": "user", "content": "Hello"}])

            # 验证成功调用
            self.assertIsNotNone(response)
            mock_client_class.assert_called_once()

            # 验证使用直连（无proxies配置）
            call_args = mock_client_class.call_args
            config = call_args[1] if call_args else {}
            self.assertNotIn("proxies", config)


class SubclassInheritanceTest(TestCase):
    """Phase 6: 子类继承测试"""

    def test_subclass_inherits_proxy_functionality(self):
        """AC[场景5]: 子类自动继承代理功能"""

        # 创建子类
        class MyCustomClient(TestClient):
            """自定义AI客户端"""

            async def validate_config(self) -> bool:
                return True

        # 创建代理配置
        proxy = ProxyConfig.objects.create(
            name="测试代理",
            protocol=ProxyProtocol.HTTP,
            host="proxy.example.com",
            port=8080,
            is_active=True,
            is_healthy=True,
        )

        # 创建子类实例（传递proxy_id）
        client = MyCustomClient(
            api_url="https://api.openai.com",
            api_key="test-key",
            model_name="gpt-4",
            proxy_id=proxy.id,
        )

        # 验证子类继承了代理功能
        self.assertIsInstance(client.proxy_provider, HttpProxyProvider)
        self.assertIsNotNone(client.proxy_provider)

    def test_subclass_without_modification_uses_proxy(self):
        """AC[场景5]: 子类无需修改代码即可使用代理"""

        # 任何继承BaseAIClient的子类都自动支持代理
        class AnotherClient(BaseAIClient):
            async def generate(self, prompt: str, **kwargs):
                return AIResponse(success=True, text="Generated")

        proxy = ProxyConfig.objects.create(
            name="测试代理",
            protocol=ProxyProtocol.HTTP,
            host="proxy.example.com",
            port=8080,
            is_active=True,
            is_healthy=True,
        )

        client = AnotherClient(
            api_url="https://api.example.com",
            api_key="test",
            model_name="model",
            proxy_id=proxy.id,
        )

        # 验证代理支持已自动集成
        self.assertIsInstance(client.proxy_provider, HttpProxyProvider)


class ProjectContextTest(TestCase):
    """Phase 7: 项目上下文传递测试"""

    def test_project_id_passed_to_proxy_provider(self):
        """AC[场景7]: project_id正确传递给ProxyProvider"""
        proxy = ProxyConfig.objects.create(
            name="测试代理",
            protocol=ProxyProtocol.HTTP,
            host="proxy.example.com",
            port=8080,
        )

        client = TestClient(
            api_url="https://api.openai.com",
            api_key="test-key",
            model_name="gpt-4",
            proxy_id=proxy.id,
            project_id=20,
        )

        # 验证project_id传递给ProxyProvider
        # （ProxyManager.get_provider()会传递project_id）
        self.assertEqual(client.project_id, 20)

    def test_project_id_none_when_not_provided(self):
        """测试不传project_id时为None"""
        proxy = ProxyConfig.objects.create(
            name="测试代理",
            protocol=ProxyProtocol.HTTP,
            host="proxy.example.com",
            port=8080,
        )

        client = TestClient(
            api_url="https://api.openai.com",
            api_key="test-key",
            model_name="gpt-4",
            proxy_id=proxy.id,
        )

        # 验证project_id为None
        self.assertIsNone(client.project_id)


class SOLIDPrinciplesTest(TestCase):
    """SOLID原则验证测试"""

    def test_open_closed_principle(self):
        """AC[场景5]: SOLID - O（开闭原则）"""

        # 通过扩展BaseAIClient添加代理功能
        # 子类自动继承，无需修改
        class ExtendedClient(TestClient):
            async def validate_config(self) -> bool:
                return True

        proxy = ProxyConfig.objects.create(
            name="测试代理",
            protocol=ProxyProtocol.HTTP,
            host="proxy.example.com",
            port=8080,
        )

        client = ExtendedClient(
            api_url="https://api.openai.com",
            api_key="test-key",
            model_name="gpt-4",
            proxy_id=proxy.id,
        )

        # 验证子类自动支持代理
        self.assertIsNotNone(client.proxy_provider)

    def test_liskov_substitution(self):
        """SOLID - L（里氏替换原则）"""
        # TestClient可以替换BaseAIClient
        client = TestClient(
            api_url="https://api.openai.com",
            api_key="test-key",
            model_name="gpt-4",
        )

        # 验证可以调用所有方法
        self.assertTrue(hasattr(client, "project_id"))
        self.assertTrue(hasattr(client, "proxy_provider"))
        self.assertTrue(hasattr(client, "_get_httpx_config"))
        self.assertTrue(hasattr(client, "_call_api_with_fallback"))

    def test_single_responsibility(self):
        """SOLID - S（单一职责原则）"""
        # BaseAIClient负责：
        # - 初始化客户端配置（包括代理）
        # - 提供API调用方法（generate, validate_config）
        # - 提供降级逻辑（_call_api_with_fallback）
        client = TestClient(
            api_url="https://api.openai.com",
            api_key="test-key",
            model_name="gpt-4",
        )

        self.assertIsNotNone(client.proxy_provider)

    def test_dependency_inversion(self):
        """SOLID - D（依赖倒置原则）"""
        # BaseAIClient依赖ProxyProvider抽象（通过ProxyManager）
        # 而非具体的HttpProxyProvider

        from apps.proxy.services import ProxyProvider

        proxy = ProxyConfig.objects.create(
            name="测试代理",
            protocol=ProxyProtocol.HTTP,
            host="proxy.example.com",
            port=8080,
        )

        client = TestClient(
            api_url="https://api.openai.com",
            api_key="test-key",
            model_name="gpt-4",
            proxy_id=proxy.id,
        )

        # 验证proxy_provider是ProxyProvider实例（抽象类型）
        self.assertIsInstance(client.proxy_provider, ProxyProvider)
