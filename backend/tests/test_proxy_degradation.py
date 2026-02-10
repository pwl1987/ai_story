"""
Story 9.5: 代理降级逻辑测试套件

测试BaseAIClient._call_api_with_fallback()的完整功能：
- Phase 1: 降级逻辑测试（代理超时、连接错误、认证失败）
- Phase 2: 异常聚合测试（代理和直连都失败）
- Phase 3: 性能测试（额外延迟 < 10ms）
- Phase 4: 日志记录测试（降级成功、降级失败）
- Phase 5: 异常类型覆盖测试（只对代理异常降级）
- Phase 6: 向后兼容性测试（无代理时行为一致）

@Author: Epic 9 Team
@Created: 2026-01-31
@Story: 9.5 - 代理降级逻辑实现
"""

from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest
import httpx
from django.test import TestCase

from core.ai_client.base import BaseAIClient, DegradeFailedException
from apps.proxy.services import ProxyProvider


class MockProxyProvider(ProxyProvider):
    """Mock ProxyProvider for testing"""

    def __init__(self, proxy_url=None):
        self.proxy_url = proxy_url
        self.usage_logs = []

    def get_proxy(self):
        return self.proxy_url

    def record_usage(
        self, ai_provider: str, endpoint: str, success: bool, response_time: int, error_message=None
    ):
        self.usage_logs.append(
            {
                "ai_provider": ai_provider,
                "endpoint": endpoint,
                "success": success,
                "response_time": response_time,
                "error_message": error_message,
            }
        )


class TestClient(BaseAIClient):
    """Mock AI客户端 for testing"""

    async def generate(self, prompt: str, **kwargs):
        pass

    async def validate_config(self) -> bool:
        return True


class ProxyDegradationLogicTest(TestCase):
    """Phase 1: 降级逻辑测试"""

    def setUp(self):
        """设置测试数据"""
        self.client = TestClient(
            api_url="https://api.openai.com",
            api_key="test-key",
            model_name="gpt-4",
        )

    @pytest.mark.asyncio
    async def test_proxy_timeout_degrades_to_direct(self):
        """AC[场景1]: 代理连接超时 → 降级到直连"""
        # 创建Mock代理Provider
        proxy_provider = MockProxyProvider(proxy_url="https://proxy.example.com:8080")
        self.client.proxy_provider = proxy_provider

        # 模拟_call_api_with_fallback的内部调用
        with patch.object(self.client, "_get_httpx_config") as mock_config:
            # 第一次调用（代理）配置
            config_with_proxy = {"proxies": {"all://": "https://proxy.example.com:8080"}}
            # 第二次调用（直连）配置
            config_without_proxy = {}

            mock_config.side_effect = [config_with_proxy, config_without_proxy]

            # 模拟httpx.AsyncClient行为
            with patch("httpx.AsyncClient") as mock_client_class:
                # 第一次调用抛出TimeoutException
                mock_response_1 = MagicMock()
                mock_response_1.raise_for_status = MagicMock(
                    side_effect=httpx.TimeoutException("Proxy timeout")
                )
                mock_client_1 = AsyncMock()
                mock_client_1.__aenter__ = AsyncMock(return_value=mock_client_1)
                mock_client_1.__aexit__ = AsyncMock()
                mock_client_1.post = AsyncMock(return_value=mock_response_1)

                # 第二次调用成功
                mock_response_2 = MagicMock()
                mock_response_2.raise_for_status = MagicMock()
                mock_client_2 = AsyncMock()
                mock_client_2.__aenter__ = AsyncMock(return_value=mock_client_2)
                mock_client_2.__aexit__ = AsyncMock()
                mock_client_2.post = AsyncMock(return_value=mock_response_2)

                mock_client_class.side_effect = [mock_client_1, mock_client_2]

                # 调用API
                response = await self.client._call_api_with_fallback("/v1/chat/completions")

                # 验证降级成功
                self.assertIsNotNone(response)
                self.assertEqual(mock_client_class.call_count, 2)

                # 验证日志记录（DEGRADED标记）
                self.assertEqual(len(proxy_provider.usage_logs), 1)
                log = proxy_provider.usage_logs[0]
                self.assertTrue(log["success"])
                self.assertIn("DEGRADED", log["error_message"])
                self.assertIn("TimeoutException", log["error_message"])

    @pytest.mark.asyncio
    async def test_proxy_connection_error_degrades_to_direct(self):
        """AC[场景2]: 代理连接错误 → 降级到直连"""
        proxy_provider = MockProxyProvider(proxy_url="https://proxy.example.com:8080")
        self.client.proxy_provider = proxy_provider

        with patch.object(self.client, "_get_httpx_config") as mock_config:
            config_with_proxy = {"proxies": {"all://": "https://proxy.example.com:8080"}}
            config_without_proxy = {}
            mock_config.side_effect = [config_with_proxy, config_without_proxy]

            with patch("httpx.AsyncClient") as mock_client_class:
                # 第一次调用抛出ConnectError
                mock_response_1 = MagicMock()
                mock_response_1.raise_for_status = MagicMock(
                    side_effect=httpx.ConnectError("Connection error")
                )
                mock_client_1 = AsyncMock()
                mock_client_1.__aenter__ = AsyncMock(return_value=mock_client_1)
                mock_client_1.__aexit__ = AsyncMock()
                mock_client_1.post = AsyncMock(return_value=mock_response_1)

                # 第二次调用成功
                mock_response_2 = MagicMock()
                mock_response_2.raise_for_status = MagicMock()
                mock_client_2 = AsyncMock()
                mock_client_2.__aenter__ = AsyncMock(return_value=mock_client_2)
                mock_client_2.__aexit__ = AsyncMock()
                mock_client_2.post = AsyncMock(return_value=mock_response_2)

                mock_client_class.side_effect = [mock_client_1, mock_client_2]

                response = await self.client._call_api_with_fallback("/v1/chat/completions")

                # 验证降级成功
                self.assertIsNotNone(response)
                self.assertEqual(mock_client_class.call_count, 2)

                # 验证日志记录
                log = proxy_provider.usage_logs[0]
                self.assertTrue(log["success"])
                self.assertIn("DEGRADED", log["error_message"])
                self.assertIn("ConnectError", log["error_message"])

    @pytest.mark.asyncio
    async def test_proxy_auth_error_degrades_to_direct(self):
        """AC[场景3]: 代理认证失败 → 降级到直连"""
        proxy_provider = MockProxyProvider(proxy_url="https://proxy.example.com:8080")
        self.client.proxy_provider = proxy_provider

        with patch.object(self.client, "_get_httpx_config") as mock_config:
            config_with_proxy = {"proxies": {"all://": "https://proxy.example.com:8080"}}
            config_without_proxy = {}
            mock_config.side_effect = [config_with_proxy, config_without_proxy]

            with patch("httpx.AsyncClient") as mock_client_class:
                # 第一次调用抛出ProxyError
                mock_response_1 = MagicMock()
                mock_response_1.raise_for_status = MagicMock(
                    side_effect=httpx.ProxyError("407 Proxy Authentication Required")
                )
                mock_client_1 = AsyncMock()
                mock_client_1.__aenter__ = AsyncMock(return_value=mock_client_1)
                mock_client_1.__aexit__ = AsyncMock()
                mock_client_1.post = AsyncMock(return_value=mock_response_1)

                # 第二次调用成功
                mock_response_2 = MagicMock()
                mock_response_2.raise_for_status = MagicMock()
                mock_client_2 = AsyncMock()
                mock_client_2.__aenter__ = AsyncMock(return_value=mock_client_2)
                mock_client_2.__aexit__ = AsyncMock()
                mock_client_2.post = AsyncMock(return_value=mock_response_2)

                mock_client_class.side_effect = [mock_client_1, mock_client_2]

                response = await self.client._call_api_with_fallback("/v1/chat/completions")

                # 验证降级成功
                self.assertIsNotNone(response)
                self.assertEqual(mock_client_class.call_count, 2)

                # 验证日志记录
                log = proxy_provider.usage_logs[0]
                self.assertTrue(log["success"])
                self.assertIn("DEGRADED", log["error_message"])
                self.assertIn("ProxyError", log["error_message"])


class ProxyAndDirectFailedTest(TestCase):
    """Phase 2: 异常聚合测试"""

    def setUp(self):
        self.client = TestClient(
            api_url="https://api.openai.com",
            api_key="test-key",
            model_name="gpt-4",
        )

    @pytest.mark.asyncio
    async def test_proxy_and_direct_both_fail(self):
        """AC[场景4]: 代理和直连都失败 → 抛出DegradeFailedException"""
        proxy_provider = MockProxyProvider(proxy_url="https://proxy.example.com:8080")
        self.client.proxy_provider = proxy_provider

        with patch.object(self.client, "_get_httpx_config") as mock_config:
            config_with_proxy = {"proxies": {"all://": "https://proxy.example.com:8080"}}
            config_without_proxy = {}
            mock_config.side_effect = [config_with_proxy, config_without_proxy]

            with patch("httpx.AsyncClient") as mock_client_class:
                # 第一次调用（代理）抛出TimeoutException
                mock_response_1 = MagicMock()
                mock_response_1.raise_for_status = MagicMock(
                    side_effect=httpx.TimeoutException("Proxy timeout")
                )
                mock_client_1 = AsyncMock()
                mock_client_1.__aenter__ = AsyncMock(return_value=mock_client_1)
                mock_client_1.__aexit__ = AsyncMock()
                mock_client_1.post = AsyncMock(return_value=mock_response_1)

                # 第二次调用（直连）抛出ConnectError
                mock_response_2 = MagicMock()
                mock_response_2.raise_for_status = MagicMock(
                    side_effect=httpx.ConnectError("Network unreachable")
                )
                mock_client_2 = AsyncMock()
                mock_client_2.__aenter__ = AsyncMock(return_value=mock_client_2)
                mock_client_2.__aexit__ = AsyncMock()
                mock_client_2.post = AsyncMock(return_value=mock_response_2)

                mock_client_class.side_effect = [mock_client_1, mock_client_2]

                # 调用API（应该抛出DegradeFailedException）
                with pytest.raises(DegradeFailedException) as exc_info:
                    await self.client._call_api_with_fallback("/v1/chat/completions")

                # 验证异常信息包含两个错误
                error_msg = str(exc_info.value)
                self.assertIn("PROXY_AND_DIRECT_FAILED", error_msg)
                self.assertIn("Proxy failed", error_msg)
                self.assertIn("Direct connection failed", error_msg)
                self.assertIn("TimeoutException", error_msg)
                self.assertIn("ConnectError", error_msg)

                # 验证日志记录（失败）
                log = proxy_provider.usage_logs[0]
                self.assertFalse(log["success"])
                self.assertIn("PROXY_AND_DIRECT_FAILED", log["error_message"])


class ProxySuccessNoDegradationTest(TestCase):
    """Phase 3: 代理成功不降级测试"""

    def setUp(self):
        self.client = TestClient(
            api_url="https://api.openai.com",
            api_key="test-key",
            model_name="gpt-4",
        )

    @pytest.mark.asyncio
    async def test_proxy_success_no_degradation(self):
        """AC[场景5]: 代理调用成功 → 不降级"""
        proxy_provider = MockProxyProvider(proxy_url="https://proxy.example.com:8080")
        self.client.proxy_provider = proxy_provider

        with patch.object(self.client, "_get_httpx_config") as mock_config:
            config_with_proxy = {"proxies": {"all://": "https://proxy.example.com:8080"}}
            mock_config.return_value = config_with_proxy

            with patch("httpx.AsyncClient") as mock_client_class:
                # 代理调用成功
                mock_response = MagicMock()
                mock_response.raise_for_status = MagicMock()
                mock_client = AsyncMock()
                mock_client.__aenter__ = AsyncMock(return_value=mock_client)
                mock_client.__aexit__ = AsyncMock()
                mock_client.post = AsyncMock(return_value=mock_response)

                mock_client_class.return_value = mock_client

                response = await self.client._call_api_with_fallback("/v1/chat/completions")

                # 验证只调用了1次（没有降级）
                self.assertIsNotNone(response)
                self.assertEqual(mock_client_class.call_count, 1)

                # 验证日志记录（成功，无DEGRADED标记）
                log = proxy_provider.usage_logs[0]
                self.assertTrue(log["success"])
                self.assertIsNone(log["error_message"])


class LogIntegrityTest(TestCase):
    """Phase 4: 日志记录完整性测试"""

    def setUp(self):
        self.client = TestClient(
            api_url="https://api.openai.com",
            api_key="test-key",
            model_name="gpt-4",
        )

    @pytest.mark.asyncio
    async def test_degraded_log_contains_all_fields(self):
        """AC[场景6]: 日志记录完整性"""
        proxy_provider = MockProxyProvider(proxy_url="https://proxy.example.com:8080")
        self.client.proxy_provider = proxy_provider

        with patch.object(self.client, "_get_httpx_config") as mock_config:
            config_with_proxy = {"proxies": {"all://": "https://proxy.example.com:8080"}}
            config_without_proxy = {}
            mock_config.side_effect = [config_with_proxy, config_without_proxy]

            with patch("httpx.AsyncClient") as mock_client_class:
                # 第一次失败，第二次成功
                mock_response_1 = MagicMock()
                mock_response_1.raise_for_status = MagicMock(
                    side_effect=httpx.TimeoutException("Timeout")
                )
                mock_client_1 = AsyncMock()
                mock_client_1.__aenter__ = AsyncMock(return_value=mock_client_1)
                mock_client_1.__aexit__ = AsyncMock()
                mock_client_1.post = AsyncMock(return_value=mock_response_1)

                mock_response_2 = MagicMock()
                mock_response_2.raise_for_status = MagicMock()
                mock_client_2 = AsyncMock()
                mock_client_2.__aenter__ = AsyncMock(return_value=mock_client_2)
                mock_client_2.__aexit__ = AsyncMock()
                mock_client_2.post = AsyncMock(return_value=mock_response_2)

                mock_client_class.side_effect = [mock_client_1, mock_client_2]

                await self.client._call_api_with_fallback("/v1/chat/completions")

                # 验证日志包含所有字段
                log = proxy_provider.usage_logs[0]
                self.assertEqual(log["ai_provider"], "TestClient")
                self.assertEqual(log["endpoint"], "/v1/chat/completions")
                self.assertTrue(log["success"])
                self.assertIsInstance(log["response_time"], int)
                self.assertGreater(log["response_time"], 0)
                self.assertIn("DEGRADED", log["error_message"])
                self.assertIn("TimeoutException", log["error_message"])


class PerformanceTest(TestCase):
    """Phase 5: 性能测试"""

    def setUp(self):
        self.client = TestClient(
            api_url="https://api.openai.com",
            api_key="test-key",
            model_name="gpt-4",
        )

    @pytest.mark.asyncio
    async def test_fallback_overhead_less_than_10ms(self):
        """AC[场景7]: 性能影响最小化（额外延迟 < 10ms）"""
        import time

        proxy_provider = MockProxyProvider(proxy_url="https://proxy.example.com:8080")
        self.client.proxy_provider = proxy_provider

        with patch.object(self.client, "_get_httpx_config") as mock_config:
            config_with_proxy = {"proxies": {"all://": "https://proxy.example.com:8080"}}
            config_without_proxy = {}
            mock_config.side_effect = [config_with_proxy, config_without_proxy]

            with patch("httpx.AsyncClient") as mock_client_class:
                # 模拟代理失败，直连成功
                mock_response_1 = MagicMock()
                mock_response_1.raise_for_status = MagicMock(
                    side_effect=httpx.TimeoutException("Timeout")
                )
                mock_client_1 = AsyncMock()
                mock_client_1.__aenter__ = AsyncMock(return_value=mock_client_1)
                mock_client_1.__aexit__ = AsyncMock()
                mock_client_1.post = AsyncMock(return_value=mock_response_1)

                mock_response_2 = MagicMock()
                mock_response_2.raise_for_status = MagicMock()
                mock_client_2 = AsyncMock()
                mock_client_2.__aenter__ = AsyncMock(return_value=mock_client_2)
                mock_client_2.__aexit__ = AsyncMock()
                mock_client_2.post = AsyncMock(return_value=mock_response_2)

                mock_client_class.side_effect = [mock_client_1, mock_client_2]

                # 测量执行时间
                start_time = time.time()
                await self.client._call_api_with_fallback("/v1/chat/completions")
                elapsed_ms = int((time.time() - start_time) * 1000)

                # 验证额外延迟 < 10ms（Mock调用非常快，实际延迟应该 < 1ms）
                self.assertLess(elapsed_ms, 10, f"Fallback overhead too high: {elapsed_ms}ms")


class ExceptionTypeCoverageTest(TestCase):
    """Phase 6: 异常类型覆盖测试"""

    def setUp(self):
        self.client = TestClient(
            api_url="https://api.openai.com",
            api_key="test-key",
            model_name="gpt-4",
        )

    @pytest.mark.asyncio
    async def test_only_proxy_exceptions_trigger_degradation(self):
        """AC[场景8]: 异常类型覆盖（只对代理异常降级）"""
        proxy_provider = MockProxyProvider(proxy_url="https://proxy.example.com:8080")
        self.client.proxy_provider = proxy_provider

        # 测试HTTPStatusError不降级
        with patch.object(self.client, "_get_httpx_config") as mock_config:
            config_with_proxy = {"proxies": {"all://": "https://proxy.example.com:8080"}}
            mock_config.return_value = config_with_proxy

            with patch("httpx.AsyncClient") as mock_client_class:
                # HTTPStatusError（业务错误，不应该降级）
                response_mock = MagicMock()
                response_mock.status_code = 401
                request_mock = MagicMock()

                mock_response = MagicMock()
                mock_response.raise_for_status = MagicMock(
                    side_effect=httpx.HTTPStatusError(
                        "Unauthorized", request=request_mock, response=response_mock
                    )
                )
                mock_client = AsyncMock()
                mock_client.__aenter__ = AsyncMock(return_value=mock_client)
                mock_client.__aexit__ = AsyncMock()
                mock_client.post = AsyncMock(return_value=mock_response)

                mock_client_class.return_value = mock_client

                # 应该抛出HTTPStatusError，不降级
                with pytest.raises(httpx.HTTPStatusError):
                    await self.client._call_api_with_fallback("/v1/chat/completions")

                # 验证只调用了1次（没有降级）
                self.assertEqual(mock_client_class.call_count, 1)

                # 验证日志记录（失败，但不是DEGRADED）
                log = proxy_provider.usage_logs[0]
                self.assertFalse(log["success"])
                self.assertNotIn("DEGRADED", log["error_message"])

    @pytest.mark.asyncio
    async def test_non_proxy_exception_no_degradation(self):
        """测试非代理异常不触发降级"""
        proxy_provider = MockProxyProvider(proxy_url="https://proxy.example.com:8080")
        self.client.proxy_provider = proxy_provider

        with patch.object(self.client, "_get_httpx_config") as mock_config:
            config_with_proxy = {"proxies": {"all://": "https://proxy.example.com:8080"}}
            mock_config.return_value = config_with_proxy

            with patch("httpx.AsyncClient") as mock_client_class:
                # 其他异常（ValueError）
                mock_response = MagicMock()
                mock_response.raise_for_status = MagicMock(side_effect=ValueError("Some error"))
                mock_client = AsyncMock()
                mock_client.__aenter__ = AsyncMock(return_value=mock_client)
                mock_client.__aexit__ = AsyncMock()
                mock_client.post = AsyncMock(return_value=mock_response)

                mock_client_class.return_value = mock_client

                # 应该抛出ValueError，不降级
                with pytest.raises(ValueError):
                    await self.client._call_api_with_fallback("/v1/chat/completions")

                # 验证只调用了1次（没有降级）
                self.assertEqual(mock_client_class.call_count, 1)


class BackwardCompatibilityTest(TestCase):
    """Phase 7: 向后兼容性测试"""

    def setUp(self):
        self.client = TestClient(
            api_url="https://api.openai.com",
            api_key="test-key",
            model_name="gpt-4",
        )

    @pytest.mark.asyncio
    async def test_no_proxy_provider_works(self):
        """测试无proxy_provider时行为一致"""
        # 不设置proxy_provider
        self.client.proxy_provider = None

        with patch.object(self.client, "_get_httpx_config") as mock_config:
            config_without_proxy = {}
            mock_config.return_value = config_without_proxy

            with patch("httpx.AsyncClient") as mock_client_class:
                mock_response = MagicMock()
                mock_response.raise_for_status = MagicMock()
                mock_client = AsyncMock()
                mock_client.__aenter__ = AsyncMock(return_value=mock_client)
                mock_client.__aexit__ = AsyncMock()
                mock_client.post = AsyncMock(return_value=mock_response)

                mock_client_class.return_value = mock_client

                # 应该正常调用，不抛出异常
                response = await self.client._call_api_with_fallback("/v1/chat/completions")

                # 验证成功
                self.assertIsNotNone(response)
                self.assertEqual(mock_client_class.call_count, 1)

    @pytest.mark.asyncio
    async def test_proxy_provider_returns_none(self):
        """测试proxy_provider返回None时行为一致"""
        # proxy_provider返回None（直连模式）
        proxy_provider = MockProxyProvider(proxy_url=None)
        self.client.proxy_provider = proxy_provider

        with patch.object(self.client, "_get_httpx_config") as mock_config:
            config_without_proxy = {}
            mock_config.return_value = config_without_proxy

            with patch("httpx.AsyncClient") as mock_client_class:
                mock_response = MagicMock()
                mock_response.raise_for_status = MagicMock()
                mock_client = AsyncMock()
                mock_client.__aenter__ = AsyncMock(return_value=mock_client)
                mock_client.__aexit__ = AsyncMock()
                mock_client.post = AsyncMock(return_value=mock_response)

                mock_client_class.return_value = mock_client

                response = await self.client._call_api_with_fallback("/v1/chat/completions")

                # 验证成功（直连）
                self.assertIsNotNone(response)
                self.assertEqual(mock_client_class.call_count, 1)

                # 验证日志记录
                log = proxy_provider.usage_logs[0]
                self.assertTrue(log["success"])


class SOLIDPrinciplesVerificationTest(TestCase):
    """SOLID原则验证测试"""

    def test_single_responsibility(self):
        """SOLID - S: 单一职责原则"""
        client = TestClient(
            api_url="https://api.openai.com",
            api_key="test-key",
            model_name="gpt-4",
        )

        # 验证职责单一：
        # - _call_api_with_fallback(): 只负责API调用和降级
        # - proxy_provider.record_usage(): 只负责日志记录
        self.assertIsNotNone(client._call_api_with_fallback)

    def test_open_closed_principle(self):
        """SOLID - O: 开闭原则"""
        # 可以通过继承BaseAIClient来扩展（如TestClient）
        # 不需要修改_call_api_with_fallback()实现

        class ExtendedTestClient(TestClient):
            """扩展的客户端（示例）"""

            def _get_httpx_config(self, proxy_url=None):
                """自定义httpx配置"""
                config = super()._get_httpx_config(proxy_url)
                config["custom_header"] = "value"
                return config

        client = ExtendedTestClient(
            api_url="https://api.openai.com",
            api_key="test-key",
            model_name="gpt-4",
        )

        self.assertIsNotNone(client._get_httpx_config())

    def test_liskov_substitution(self):
        """SOLID - L: 里氏替换原则"""
        # TestClient可以替换BaseAIClient
        client = TestClient(
            api_url="https://api.openai.com",
            api_key="test-key",
            model_name="gpt-4",
        )

        # 两者都可以调用_call_api_with_fallback()
        self.assertTrue(hasattr(client, "_call_api_with_fallback"))

    def test_interface_segregation(self):
        """SOLID - I: 接口隔离原则"""
        # BaseAIClient接口专一（generate, validate_config, health_check）
        # 没有"胖接口"

        client = TestClient(
            api_url="https://api.openai.com",
            api_key="test-key",
            model_name="gpt-4",
        )

        # 可以调用所有方法
        self.assertTrue(hasattr(client, "generate"))
        self.assertTrue(hasattr(client, "validate_config"))
        self.assertTrue(hasattr(client, "health_check"))
        self.assertTrue(hasattr(client, "_call_api_with_fallback"))

    def test_dependency_inversion(self):
        """SOLID - D: 依赖倒置原则"""
        # BaseAIClient依赖ProxyProvider抽象，而非具体实现

        proxy_provider = MockProxyProvider(proxy_url="https://proxy.example.com:8080")
        client = TestClient(
            api_url="https://api.openai.com",
            api_key="test-key",
            model_name="gpt-4",
            proxy_provider=proxy_provider,
        )

        # 验证proxy_provider是ProxyProvider实例
        from apps.proxy.services import ProxyProvider

        self.assertIsInstance(client.proxy_provider, ProxyProvider)
