# Engines Services Tests - 引擎服务层测试

from unittest.mock import Mock, patch

import pytest
from requests.exceptions import RequestException, Timeout

from apps.engines.models import (
    EngineConfig,
    EngineHealthLog,
    FallbackEventLog,
)
from apps.engines.services import (
    CostCalculationService,
    EngineMonitoringService,
    FallbackService,
    HealthCheckService,
    UsageService,
)


@pytest.mark.django_db
class TestHealthCheckService:
    """HealthCheckService 测试"""

    def test_check_ollama_online(self):
        """测试 Ollama 引擎在线状态"""
        engine = EngineConfig.objects.create(
            engine_type="llm",
            name="测试 Ollama",
            primary_provider="ollama",
            primary_config={
                "base_url": "http://localhost:11434",
                "model": "llama2:7b",
            },
        )

        service = HealthCheckService(engine)

        with patch("apps.engines.services.requests.get") as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_get.return_value = mock_response

            result = service.check()

            assert result["status"] == "online"
            assert result["response_time"] > 0
            assert result["error_message"] == ""

    def test_check_ollama_offline(self):
        """测试 Ollama 引擎离线状态"""
        engine = EngineConfig.objects.create(
            engine_type="llm",
            name="测试 Ollama",
            primary_provider="ollama",
            primary_config={
                "base_url": "http://localhost:11434",
                "model": "llama2:7b",
            },
        )

        service = HealthCheckService(engine)

        with patch("apps.engines.services.requests.get") as mock_get:
            mock_get.side_effect = RequestException("Connection refused")

            result = service.check()

            assert result["status"] == "offline"
            assert result["response_time"] is None
            assert "Connection refused" in result["error_message"]

    def test_check_ollama_timeout(self):
        """测试 Ollama 引擎超时"""
        engine = EngineConfig.objects.create(
            engine_type="llm",
            name="测试 Ollama",
            primary_provider="ollama",
            primary_config={
                "base_url": "http://localhost:11434",
                "model": "llama2:7b",
            },
        )

        service = HealthCheckService(engine)

        with patch("apps.engines.services.requests.get") as mock_get:
            mock_get.side_effect = Timeout()

            result = service.check()

            assert result["status"] == "offline"
            assert result["error_code"] == "TIMEOUT"

    def test_save_health_log(self):
        """测试保存健康日志"""
        engine = EngineConfig.objects.create(
            engine_type="llm",
            name="测试引擎",
            primary_provider="ollama",
            primary_config={"model": "llama2:7b"},
        )

        service = HealthCheckService(engine)
        result = {
            "status": "online",
            "response_time": 150.5,
            "error_message": "",
            "error_code": "",
        }

        service.save_health_log(result)

        # 验证日志已创建
        assert EngineHealthLog.objects.filter(engine=engine).count() == 1

        # 验证引擎状态已更新
        engine.refresh_from_db()
        assert engine.health_status == "online"

    def test_check_comfyui_online(self):
        """测试 ComfyUI 引擎在线状态"""
        engine = EngineConfig.objects.create(
            engine_type="image",
            name="测试 ComfyUI",
            primary_provider="comfyui",
            primary_config={
                "base_url": "http://localhost:8188",
                "workflow": "sdxl",
            },
        )

        service = HealthCheckService(engine)

        with patch("apps.engines.services.requests.get") as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_get.return_value = mock_response

            result = service.check()

            assert result["status"] == "online"

    def test_check_tts_edge(self):
        """测试 Edge-TTS 引擎（本地，总是在线）"""
        engine = EngineConfig.objects.create(
            engine_type="tts",
            name="测试 Edge-TTS",
            primary_provider="edge-tts",
            primary_config={
                "voice": "zh-CN-XiaoxiaoNeural",
                "rate": "+0%",
            },
        )

        service = HealthCheckService(engine)
        result = service.check()

        assert result["status"] == "online"
        assert result["response_time"] == 50.0


@pytest.mark.django_db
class TestFallbackService:
    """FallbackService 测试"""

    def test_should_trigger_fallback_disabled(self):
        """测试禁用自动 Fallback"""
        engine = EngineConfig.objects.create(
            engine_type="llm",
            name="测试引擎",
            primary_provider="ollama",
            primary_config={"model": "llama2:7b"},
            fallback_provider="openai",
            fallback_config={"api_key": "sk-test"},
            auto_fallback=False,
        )

        service = FallbackService(engine)
        assert service.should_trigger_fallback() is False

    def test_should_trigger_fallback_no_fallback_provider(self):
        """测试没有配置备份引擎"""
        engine = EngineConfig.objects.create(
            engine_type="llm",
            name="测试引擎",
            primary_provider="ollama",
            primary_config={"model": "llama2:7b"},
            auto_fallback=True,
        )

        service = FallbackService(engine)
        assert service.should_trigger_fallback() is False

    def test_should_trigger_fallback_with_failures(self):
        """测试达到失败阈值"""
        engine = EngineConfig.objects.create(
            engine_type="llm",
            name="测试引擎",
            primary_provider="ollama",
            primary_config={"model": "llama2:7b"},
            fallback_provider="openai",
            fallback_config={"api_key": "sk-test"},
            fallback_threshold=3,
            auto_fallback=True,
        )

        service = FallbackService(engine)

        # 失败次数未达到阈值
        engine.failure_count = 2
        engine.save()
        assert service.should_trigger_fallback() is False

        # 达到阈值
        engine.failure_count = 3
        engine.save()
        assert service.should_trigger_fallback() is True

    def test_switch_to_fallback(self):
        """测试切换到备份引擎"""
        engine = EngineConfig.objects.create(
            engine_type="llm",
            name="测试引擎",
            primary_provider="ollama",
            primary_config={"model": "llama2:7b"},
            fallback_provider="openai",
            fallback_config={"api_key": "sk-test"},
            current_provider="ollama",
        )

        service = FallbackService(engine)
        success = service.switch_to_fallback(
            reason="timeout",
            reason_detail="连接超时3次",
        )

        assert success is True

        # 验证引擎已切换
        engine.refresh_from_db()
        assert engine.current_provider == "openai"
        assert engine.failure_count == 0

        # 验证事件已记录
        assert FallbackEventLog.objects.filter(engine=engine).count() == 1

        event = FallbackEventLog.objects.get(engine=engine)
        assert event.from_provider == "ollama"
        assert event.to_provider == "openai"
        assert event.reason == "timeout"

    def test_switch_to_fallback_no_provider(self):
        """测试没有备份引擎时切换失败"""
        engine = EngineConfig.objects.create(
            engine_type="llm",
            name="测试引擎",
            primary_provider="ollama",
            primary_config={"model": "llama2:7b"},
        )

        service = FallbackService(engine)
        success = service.switch_to_fallback()

        assert success is False


@pytest.mark.django_db
class TestCostCalculationService:
    """CostCalculationService 测试"""

    def test_calculate_cost_ollama_free(self):
        """测试 Ollama 免费计算"""
        cost = CostCalculationService.calculate_cost(
            provider="ollama",
            model="llama2:7b",
            token_count=1000,
            request_type="llm",
        )

        assert cost == 0.0

    def test_calculate_cost_openai(self):
        """测试 OpenAI 计费"""
        cost = CostCalculationService.calculate_cost(
            provider="openai",
            model="gpt-4",
            token_count=1000,
            request_type="llm",
        )

        # gpt-4 定价: $0.03/1K tokens
        expected = 0.03
        assert abs(cost - expected) < 0.0001

    def test_calculate_cost_comfyui_free(self):
        """测试 ComfyUI 免费计算"""
        cost = CostCalculationService.calculate_cost(
            provider="comfyui",
            model="sdxl",
            token_count=0,
            request_type="image",
        )

        assert cost == 0.0

    def test_calculate_cost_dalle(self):
        """测试 DALL-E 计费"""
        cost = CostCalculationService.calculate_cost(
            provider="dalle",
            model="dall-e-3",
            token_count=0,
            request_type="image",
        )

        # dall-e-3 定价: $0.04/次
        assert abs(cost - 0.04) < 0.0001

    def test_calculate_cost_edge_tts_free(self):
        """测试 Edge-TTS 免费计算"""
        cost = CostCalculationService.calculate_cost(
            provider="edge-tts",
            model="",
            token_count=0,
            request_type="tts",
        )

        assert cost == 0.0

    def test_calculate_saved_cost_ollama_vs_openai(self):
        """测试使用 Ollama 相比 OpenAI 的节省"""
        saved = CostCalculationService.calculate_saved_cost(
            primary_provider="ollama",
            actual_provider="ollama",
            model="llama2:7b",
            token_count=1000,
            request_type="llm",
        )

        # Ollama 是本地的，节省 = OpenAI 的成本
        expected = CostCalculationService.calculate_cost("openai", "gpt-4", 1000, "llm")
        assert abs(saved - expected) < 0.0001


@pytest.mark.django_db
class TestUsageService:
    """UsageService 测试"""

    def test_record_usage_success(self):
        """测试记录成功使用"""
        engine = EngineConfig.objects.create(
            engine_type="llm",
            name="测试引擎",
            primary_provider="ollama",
            primary_config={"model": "llama2:7b"},
        )

        log = UsageService.record_usage(
            engine=engine,
            provider="ollama",
            request_type="llm",
            success=True,
            response_time=150.0,
            token_count=1000,
        )

        assert log.engine == engine
        assert log.success is True
        assert log.response_time == 150.0
        assert log.token_count == 1000
        assert log.cost == 0.0  # Ollama 免费

        # 验证引擎统计已更新
        engine.refresh_from_db()
        assert engine.total_requests == 1
        assert engine.success_count == 1

    def test_record_usage_failure(self):
        """测试记录失败使用"""
        engine = EngineConfig.objects.create(
            engine_type="llm",
            name="测试引擎",
            primary_provider="ollama",
            primary_config={"model": "llama2:7b"},
        )

        log = UsageService.record_usage(
            engine=engine,
            provider="ollama",
            request_type="llm",
            success=False,
            response_time=30000.0,
        )

        assert log.success is False
        assert log.response_time == 30000.0

        # 验证引擎统计已更新
        engine.refresh_from_db()
        assert engine.total_requests == 1
        assert engine.failure_count == 1

    def test_record_usage_with_cost(self):
        """测试记录使用并计算成本"""
        engine = EngineConfig.objects.create(
            engine_type="llm",
            name="测试引擎",
            primary_provider="openai",
            primary_config={"api_key": "sk-test", "model": "gpt-4"},
            fallback_provider="ollama",
            fallback_config={"model": "llama2:7b"},
        )

        # 使用 Ollama（节省成本）
        log = UsageService.record_usage(
            engine=engine,
            provider="ollama",
            request_type="llm",
            success=True,
            response_time=200.0,
            token_count=1000,
        )

        # Ollama 免费
        assert log.cost == 0.0
        # 节省了 OpenAI 的费用
        assert log.saved_cost > 0


@pytest.mark.django_db
class TestEngineMonitoringService:
    """EngineMonitoringService 测试"""

    def test_perform_health_check(self):
        """测试执行完整健康检查"""
        engine = EngineConfig.objects.create(
            engine_type="llm",
            name="测试引擎",
            primary_provider="ollama",
            primary_config={
                "base_url": "http://localhost:11434",
                "model": "llama2:7b",
            },
            health_status="unknown",
        )

        with patch("apps.engines.services.requests.get") as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_get.return_value = mock_response

            result = EngineMonitoringService.perform_health_check(engine)

            assert result["status"] == "online"

            # 验证健康日志已创建
            assert EngineHealthLog.objects.filter(engine=engine).count() == 1

    def test_perform_health_check_triggers_fallback(self):
        """测试健康检查触发 Fallback"""
        engine = EngineConfig.objects.create(
            engine_type="llm",
            name="测试引擎",
            primary_provider="ollama",
            primary_config={"model": "llama2:7b"},
            fallback_provider="openai",
            fallback_config={"api_key": "sk-test"},
            fallback_threshold=3,
            auto_fallback=True,
            failure_count=3,
            current_provider="ollama",
        )

        with patch("apps.engines.services.requests.get") as mock_get:
            # 引擎离线
            mock_get.side_effect = RequestException("Connection refused")

            result = EngineMonitoringService.perform_health_check(engine)

            assert result["status"] == "offline"

            # 验证已触发 Fallback
            engine.refresh_from_db()
            assert engine.current_provider == "openai"
            assert engine.failure_count == 0  # 重置计数

    def test_check_all_engines(self):
        """测试检查所有引擎"""
        EngineConfig.objects.create(
            engine_type="llm",
            name="LLM 引擎",
            primary_provider="ollama",
            primary_config={"model": "llama2:7b"},
        )
        EngineConfig.objects.create(
            engine_type="tts",
            name="TTS 引擎",
            primary_provider="edge-tts",
            primary_config={"voice": "zh-CN-XiaoxiaoNeural"},
        )

        with patch("apps.engines.services.requests.get") as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_get.return_value = mock_response

            results = EngineMonitoringService.check_all_engines()

            assert "llm" in results
            assert "tts" in results
            assert len(results) == 2


@pytest.mark.django_db
class TestServiceIntegration:
    """服务集成测试"""

    def test_full_health_check_workflow(self):
        """测试完整健康检查工作流"""
        # 创建引擎配置
        engine = EngineConfig.objects.create(
            engine_type="llm",
            name="测试引擎",
            primary_provider="ollama",
            primary_config={
                "base_url": "http://localhost:11434",
                "model": "llama2:7b",
            },
            fallback_provider="openai",
            fallback_config={"api_key": "sk-test"},
            fallback_threshold=2,
            auto_fallback=True,
        )

        service = HealthCheckService(engine)

        with patch("apps.engines.services.requests.get") as mock_get:
            # 第一次检查：在线
            mock_response = Mock()
            mock_response.status_code = 200
            mock_get.return_value = mock_response

            result1 = service.check()
            service.save_health_log(result1)

            # 第二次检查：离线
            mock_get.side_effect = RequestException("Failed")
            result2 = service.check()
            service.save_health_log(result2)
            if result2["status"] != "online":
                engine.record_failure()

            # 第三次检查：离线
            result3 = service.check()
            service.save_health_log(result3)
            if result3["status"] != "online":
                engine.record_failure()

            # 验证 Fallback 被触发
            engine.refresh_from_db()
            assert engine.failure_count >= 2

            # 触发 Fallback
            fallback_service = FallbackService(engine)
            if fallback_service.should_trigger_fallback():
                fallback_service.switch_to_fallback(reason="failure")

            # 验证已切换
            engine.refresh_from_db()
            assert engine.current_provider == "openai"

    def test_usage_tracking_with_cost(self):
        """测试使用追踪和成本计算"""
        engine = EngineConfig.objects.create(
            engine_type="llm",
            name="测试引擎",
            primary_provider="openai",
            primary_config={"api_key": "sk-test", "model": "gpt-4"},
            fallback_provider="ollama",
            fallback_config={"model": "llama2:7b"},
        )

        # 使用云端引擎
        log1 = UsageService.record_usage(
            engine=engine,
            provider="openai",
            request_type="llm",
            success=True,
            response_time=500.0,
            token_count=1000,
        )

        assert log1.cost > 0  # OpenAI 有费用
        assert log1.saved_cost == 0.0  # 使用云端没有节省

        # 使用本地引擎
        log2 = UsageService.record_usage(
            engine=engine,
            provider="ollama",
            request_type="llm",
            success=True,
            response_time=200.0,
            token_count=1000,
        )

        assert log2.cost == 0.0  # Ollama 免费
        assert log2.saved_cost > 0  # 节省了云端费用

        # 验证总成本
        engine.refresh_from_db()
        total_cost = log1.cost + log2.cost
        saved_cost = log1.saved_cost + log2.saved_cost
        assert engine.total_cost == total_cost
        assert engine.saved_cost == saved_cost


@pytest.mark.django_db
class TestErrorHandling:
    """错误处理测试"""

    def test_health_check_unknown_engine_type(self):
        """测试未知引擎类型的处理"""
        engine = EngineConfig.objects.create(
            engine_type="llm",
            name="测试引擎",
            primary_provider="unknown_provider",
            primary_config={"model": "test"},
        )

        service = HealthCheckService(engine)
        result = service.check()

        # 应该返回在线（通用处理）
        assert result["status"] in ("online", "error")

    def test_fallback_no_provider_returns_false(self):
        """测试没有备份引擎时切换失败"""
        engine = EngineConfig.objects.create(
            engine_type="llm",
            name="测试引擎",
            primary_provider="ollama",
            primary_config={"model": "llama2:7b"},
        )

        service = FallbackService(engine)
        success = service.switch_to_fallback()

        assert success is False

        # 验证没有创建 Fallback 事件
        assert FallbackEventLog.objects.filter(engine=engine).count() == 0

    def test_cost_unknown_provider(self):
        """测试未知提供商的成本计算"""
        cost = CostCalculationService.calculate_cost(
            provider="unknown",
            model="unknown",
            token_count=1000,
            request_type="llm",
        )

        assert cost == 0.0

    def test_usage_service_with_invalid_token_count(self):
        """测试使用记录服务处理无效 token 数量"""
        engine = EngineConfig.objects.create(
            engine_type="llm",
            name="测试引擎",
            primary_provider="ollama",
            primary_config={"model": "llama2:7b"},
        )

        # token_count 为 None
        log = UsageService.record_usage(
            engine=engine,
            provider="ollama",
            request_type="llm",
            success=True,
            response_time=150.0,
            token_count=None,
        )

        assert log.cost == 0.0
        assert log.token_count is None
