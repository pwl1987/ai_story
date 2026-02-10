# Engines Models Tests - 引擎模型单元测试


import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError

from apps.engines.models import (
    EngineConfig,
    EngineHealthLog,
    EngineUsageLog,
    FallbackEventLog,
)


@pytest.mark.django_db
class TestEngineConfig:
    """EngineConfig 模型测试"""

    def test_create_llm_engine_config(self):
        """测试创建 LLM 引擎配置"""
        engine = EngineConfig.objects.create(
            engine_type="llm",
            name="LLM 引擎配置",
            description="用于文本生成的 LLM 引擎",
            primary_provider="ollama",
            primary_config={
                "base_url": "http://localhost:11434",
                "model": "llama2:7b",
                "temperature": 0.7,
                "max_tokens": 2000,
            },
            fallback_provider="openai",
            fallback_config={
                "api_key": "sk-test",
                "model": "gpt-4",
            },
            fallback_threshold=3,
            fallback_timeout=30,
        )

        assert engine.engine_type == "llm"
        assert engine.name == "LLM 引擎配置"
        assert engine.primary_provider == "ollama"
        assert engine.fallback_provider == "openai"
        assert engine.health_status == "unknown"
        assert engine.is_active is True
        assert str(engine) == "LLM文本生成 - ollama"

    def test_create_image_engine_config(self):
        """测试创建图像引擎配置"""
        engine = EngineConfig.objects.create(
            engine_type="image",
            name="图像生成引擎",
            primary_provider="comfyui",
            primary_config={
                "base_url": "http://localhost:8188",
                "workflow": "sdxl",
            },
            fallback_provider="dalle",
            fallback_config={"api_key": "sk-test"},
        )

        assert engine.engine_type == "image"
        assert str(engine) == "图像生成 - comfyui"

    def test_create_tts_engine_config(self):
        """测试创建 TTS 引擎配置"""
        engine = EngineConfig.objects.create(
            engine_type="tts",
            name="语音合成引擎",
            primary_provider="edge-tts",
            primary_config={
                "voice": "zh-CN-XiaoxiaoNeural",
                "rate": "+0%",
            },
        )

        assert engine.engine_type == "tts"
        assert str(engine) == "语音合成 - edge-tts"

    def test_engine_type_unique_constraint(self):
        """测试引擎类型唯一约束"""
        EngineConfig.objects.create(
            engine_type="llm",
            name="第一个 LLM 引擎",
            primary_provider="ollama",
            primary_config={"model": "llama2:7b"},
        )

        # 尝试创建第二个 LLM 引擎应该失败
        with pytest.raises(IntegrityError):
            EngineConfig.objects.create(
                engine_type="llm",
                name="第二个 LLM 引擎",
                primary_provider="openai",
                primary_config={"model": "gpt-4"},
            )

    def test_clean_validation_primary_fallback_different(self):
        """测试验证：主引擎和备份引擎不能相同"""
        engine = EngineConfig(
            engine_type="llm",
            name="无效配置",
            primary_provider="ollama",
            primary_config={"model": "llama2:7b"},
            fallback_provider="ollama",  # 与主引擎相同
        )

        with pytest.raises(ValidationError) as exc_info:
            engine.clean()

        assert "fallback_provider" in exc_info.value.message_dict

    def test_clean_validation_primary_config_not_empty(self):
        """测试验证：主引擎配置不能为空"""
        engine = EngineConfig(
            engine_type="llm",
            name="无效配置",
            primary_provider="ollama",
            primary_config={},  # 空配置
        )

        with pytest.raises(ValidationError) as exc_info:
            engine.clean()

        assert "primary_config" in exc_info.value.message_dict

    def test_clean_validation_allowed_providers(self):
        """测试验证：提供商必须在允许的列表中"""
        engine = EngineConfig(
            engine_type="llm",
            name="无效配置",
            primary_provider="invalid-provider",  # 不在允许列表中
            primary_config={"model": "test"},
        )

        with pytest.raises(ValidationError) as exc_info:
            engine.clean()

        assert "primary_provider" in exc_info.value.message_dict

    def test_get_active_provider_with_auto_fallback_disabled(self):
        """测试获取活动引擎：禁用自动 Fallback"""
        engine = EngineConfig.objects.create(
            engine_type="llm",
            name="测试引擎",
            primary_provider="ollama",
            primary_config={"model": "llama2:7b"},
            auto_fallback=False,
        )

        assert engine.get_active_provider() == "ollama"

    def test_get_active_provider_with_online_status(self):
        """测试获取活动引擎：引擎在线"""
        engine = EngineConfig.objects.create(
            engine_type="llm",
            name="测试引擎",
            primary_provider="ollama",
            primary_config={"model": "llama2:7b"},
            current_provider="ollama",
            health_status="online",
            auto_fallback=True,
        )

        assert engine.get_active_provider() == "ollama"

    def test_get_active_provider_with_unknown_status(self):
        """测试获取活动引擎：状态未知时返回主引擎"""
        engine = EngineConfig.objects.create(
            engine_type="llm",
            name="测试引擎",
            primary_provider="ollama",
            primary_config={"model": "llama2:7b"},
            health_status="unknown",
            auto_fallback=True,
        )

        assert engine.get_active_provider() == "ollama"

    def test_should_fallback_with_auto_fallback_disabled(self):
        """测试 Fallback 判断：禁用自动 Fallback"""
        engine = EngineConfig.objects.create(
            engine_type="llm",
            name="测试引擎",
            primary_provider="ollama",
            primary_config={"model": "llama2:7b"},
            fallback_provider="openai",
            fallback_config={"api_key": "sk-test"},
            auto_fallback=False,
        )

        assert engine.should_fallback() is False

    def test_should_fallback_without_fallback_provider(self):
        """测试 Fallback 判断：没有配置备份引擎"""
        engine = EngineConfig.objects.create(
            engine_type="llm",
            name="测试引擎",
            primary_provider="ollama",
            primary_config={"model": "llama2:7b"},
            auto_fallback=True,
        )

        assert engine.should_fallback() is False

    def test_should_fallback_with_failures(self):
        """测试 Fallback 判断：达到失败阈值"""
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

        # 失败次数未达到阈值
        engine.failure_count = 2
        engine.save()
        assert engine.should_fallback() is False

        # 失败次数达到阈值
        engine.failure_count = 3
        engine.save()
        assert engine.should_fallback() is True

    def test_calculate_success_rate_no_requests(self):
        """测试成功率计算：无请求"""
        engine = EngineConfig.objects.create(
            engine_type="llm",
            name="测试引擎",
            primary_provider="ollama",
            primary_config={"model": "llama2:7b"},
        )

        assert engine.calculate_success_rate() == 0.0

    def test_calculate_success_rate_with_requests(self):
        """测试成功率计算：有请求"""
        engine = EngineConfig.objects.create(
            engine_type="llm",
            name="测试引擎",
            primary_provider="ollama",
            primary_config={"model": "llama2:7b"},
            total_requests=100,
            success_count=95,
        )

        assert engine.calculate_success_rate() == 95.0

    def test_record_success(self):
        """测试记录成功请求"""
        engine = EngineConfig.objects.create(
            engine_type="llm",
            name="测试引擎",
            primary_provider="ollama",
            primary_config={"model": "llama2:7b"},
        )

        engine.record_success(response_time=150.0, cost=0.001, saved=0.01)

        engine.refresh_from_db()
        assert engine.total_requests == 1
        assert engine.success_count == 1
        assert engine.total_cost == 0.001
        assert engine.saved_cost == 0.01
        assert engine.avg_response_time == 150.0

    def test_record_success_updates_avg_response_time(self):
        """测试记录成功：更新平均响应时间"""
        engine = EngineConfig.objects.create(
            engine_type="llm",
            name="测试引擎",
            primary_provider="ollama",
            primary_config={"model": "llama2:7b"},
            avg_response_time=100.0,
        )

        # 记录第二次成功
        engine.total_requests = 1
        engine.record_success(response_time=200.0)

        # 平均响应时间应该平滑更新
        # 新平均 = 0.1 * 200 + 0.9 * 100 = 110
        engine.refresh_from_db()
        assert abs(engine.avg_response_time - 110.0) < 0.1

    def test_record_failure(self):
        """测试记录失败请求"""
        engine = EngineConfig.objects.create(
            engine_type="llm",
            name="测试引擎",
            primary_provider="ollama",
            primary_config={"model": "llama2:7b"},
        )

        engine.record_failure()

        engine.refresh_from_db()
        assert engine.total_requests == 1
        assert engine.failure_count == 1


@pytest.mark.django_db
class TestEngineHealthLog:
    """EngineHealthLog 模型测试"""

    def test_create_health_log(self):
        """测试创建健康检查日志"""
        engine = EngineConfig.objects.create(
            engine_type="llm",
            name="测试引擎",
            primary_provider="ollama",
            primary_config={"model": "llama2:7b"},
        )

        log = EngineHealthLog.objects.create(
            engine=engine,
            status="online",
            response_time=123.5,
        )

        assert log.engine == engine
        assert log.status == "online"
        assert log.response_time == 123.5
        assert log.error_message == ""
        assert log.error_code == ""

    def test_create_health_log_with_error(self):
        """测试创建带错误的健康检查日志"""
        engine = EngineConfig.objects.create(
            engine_type="llm",
            name="测试引擎",
            primary_provider="ollama",
            primary_config={"model": "llama2:7b"},
        )

        log = EngineHealthLog.objects.create(
            engine=engine,
            status="error",
            error_message="Connection timeout",
            error_code="TIMEOUT",
        )

        assert log.status == "error"
        assert log.error_message == "Connection timeout"
        assert log.error_code == "TIMEOUT"

    def test_health_log_str_representation(self):
        """测试健康日志字符串表示"""
        engine = EngineConfig.objects.create(
            engine_type="llm",
            name="测试引擎",
            primary_provider="ollama",
            primary_config={"model": "llama2:7b"},
        )

        log = EngineHealthLog.objects.create(
            engine=engine,
            status="online",
        )

        str_repr = str(log)
        assert "llm" in str_repr
        # 包含中文 '在线' 而不是英文 'online'
        assert "在线" in str_repr


@pytest.mark.django_db
class TestEngineUsageLog:
    """EngineUsageLog 模型测试"""

    def test_create_usage_log(self):
        """测试创建使用日志"""
        engine = EngineConfig.objects.create(
            engine_type="llm",
            name="测试引擎",
            primary_provider="ollama",
            primary_config={"model": "llama2:7b"},
        )

        log = EngineUsageLog.objects.create(
            engine=engine,
            provider="ollama",
            request_type="llm",
            success=True,
            response_time=150.0,
            token_count=1000,
            cost=0.001,
            saved_cost=0.01,
        )

        assert log.engine == engine
        assert log.provider == "ollama"
        assert log.request_type == "llm"
        assert log.success is True
        assert log.response_time == 150.0
        assert log.token_count == 1000
        assert log.cost == 0.001
        assert log.saved_cost == 0.01

    def test_usage_log_str_representation(self):
        """测试使用日志字符串表示"""
        engine = EngineConfig.objects.create(
            engine_type="llm",
            name="测试引擎",
            primary_provider="ollama",
            primary_config={"model": "llama2:7b"},
        )

        log = EngineUsageLog.objects.create(
            engine=engine,
            provider="ollama",
            request_type="llm",
            success=True,
            response_time=150.0,
        )

        str_repr = str(log)
        assert "llm" in str_repr
        assert "ollama" in str_repr
        assert "✓" in str_repr

    def test_usage_log_failed_request(self):
        """测试失败请求的使用日志"""
        engine = EngineConfig.objects.create(
            engine_type="llm",
            name="测试引擎",
            primary_provider="ollama",
            primary_config={"model": "llama2:7b"},
        )

        log = EngineUsageLog.objects.create(
            engine=engine,
            provider="openai",
            request_type="llm",
            success=False,
            response_time=30000.0,  # 超时
        )

        assert log.success is False
        assert str(log).endswith("✗")


@pytest.mark.django_db
class TestFallbackEventLog:
    """FallbackEventLog 模型测试"""

    def test_create_fallback_event(self):
        """测试创建 Fallback 事件"""
        engine = EngineConfig.objects.create(
            engine_type="llm",
            name="测试引擎",
            primary_provider="ollama",
            primary_config={"model": "llama2:7b"},
            fallback_provider="openai",
            fallback_config={"api_key": "sk-test"},
        )

        event = FallbackEventLog.objects.create(
            engine=engine,
            from_provider="ollama",
            to_provider="openai",
            reason="timeout",
            reason_detail="连续3次超时",
            affected_requests=5,
        )

        assert event.engine == engine
        assert event.from_provider == "ollama"
        assert event.to_provider == "openai"
        assert event.reason == "timeout"
        assert event.reason_detail == "连续3次超时"
        assert event.affected_requests == 5

    def test_fallback_event_str_representation(self):
        """测试 Fallback 事件字符串表示"""
        engine = EngineConfig.objects.create(
            engine_type="llm",
            name="测试引擎",
            primary_provider="ollama",
            primary_config={"model": "llama2:7b"},
            fallback_provider="openai",
            fallback_config={"api_key": "sk-test"},
        )

        event = FallbackEventLog.objects.create(
            engine=engine,
            from_provider="ollama",
            to_provider="openai",
            reason="failure",
        )

        str_repr = str(event)
        assert "llm" in str_repr
        assert "ollama" in str_repr
        assert "openai" in str_repr
        assert "→" in str_repr

    def test_fallback_event_all_reasons(self):
        """测试所有 Fallback 原因类型"""
        engine = EngineConfig.objects.create(
            engine_type="llm",
            name="测试引擎",
            primary_provider="ollama",
            primary_config={"model": "llama2:7b"},
            fallback_provider="openai",
            fallback_config={"api_key": "sk-test"},
        )

        reasons = ["timeout", "failure", "manual", "error"]

        for reason in reasons:
            event = FallbackEventLog.objects.create(
                engine=engine,
                from_provider="ollama",
                to_provider="openai",
                reason=reason,
            )
            assert event.reason == reason
            event.delete()


@pytest.mark.django_db
class TestModelRelationships:
    """测试模型之间的关系"""

    def test_engine_config_has_many_health_logs(self):
        """测试引擎配置有多个健康日志"""
        engine = EngineConfig.objects.create(
            engine_type="llm",
            name="测试引擎",
            primary_provider="ollama",
            primary_config={"model": "llama2:7b"},
        )

        EngineHealthLog.objects.create(engine=engine, status="online")
        EngineHealthLog.objects.create(engine=engine, status="offline")

        assert engine.health_logs.count() == 2

    def test_engine_config_has_many_usage_logs(self):
        """测试引擎配置有多个使用日志"""
        engine = EngineConfig.objects.create(
            engine_type="llm",
            name="测试引擎",
            primary_provider="ollama",
            primary_config={"model": "llama2:7b"},
        )

        EngineUsageLog.objects.create(
            engine=engine,
            provider="ollama",
            request_type="llm",
            success=True,
            response_time=100.0,
        )
        EngineUsageLog.objects.create(
            engine=engine,
            provider="openai",
            request_type="llm",
            success=True,
            response_time=200.0,
        )

        assert engine.usage_logs.count() == 2

    def test_engine_config_has_many_fallback_logs(self):
        """测试引擎配置有多个 Fallback 日志"""
        engine = EngineConfig.objects.create(
            engine_type="llm",
            name="测试引擎",
            primary_provider="ollama",
            primary_config={"model": "llama2:7b"},
            fallback_provider="openai",
            fallback_config={"api_key": "sk-test"},
        )

        FallbackEventLog.objects.create(
            engine=engine,
            from_provider="ollama",
            to_provider="openai",
            reason="timeout",
        )
        FallbackEventLog.objects.create(
            engine=engine,
            from_provider="openai",
            to_provider="ollama",
            reason="manual",
        )

        assert engine.fallback_logs.count() == 2

    def test_cascade_delete_health_logs(self):
        """测试级联删除健康日志"""
        engine = EngineConfig.objects.create(
            engine_type="llm",
            name="测试引擎",
            primary_provider="ollama",
            primary_config={"model": "llama2:7b"},
        )

        log = EngineHealthLog.objects.create(
            engine=engine,
            status="online",
        )

        engine.delete()

        # 日志应该被级联删除
        assert EngineHealthLog.objects.filter(id=log.id).count() == 0

    def test_cascade_delete_usage_logs(self):
        """测试级联删除使用日志"""
        engine = EngineConfig.objects.create(
            engine_type="llm",
            name="测试引擎",
            primary_provider="ollama",
            primary_config={"model": "llama2:7b"},
        )

        log = EngineUsageLog.objects.create(
            engine=engine,
            provider="ollama",
            request_type="llm",
            success=True,
            response_time=100.0,
        )

        engine.delete()

        # 日志应该被级联删除
        assert EngineUsageLog.objects.filter(id=log.id).count() == 0

    def test_cascade_delete_fallback_logs(self):
        """测试级联删除 Fallback 日志"""
        engine = EngineConfig.objects.create(
            engine_type="llm",
            name="测试引擎",
            primary_provider="ollama",
            primary_config={"model": "llama2:7b"},
            fallback_provider="openai",
            fallback_config={"api_key": "sk-test"},
        )

        log = FallbackEventLog.objects.create(
            engine=engine,
            from_provider="ollama",
            to_provider="openai",
            reason="timeout",
        )

        engine.delete()

        # 日志应该被级联删除
        assert FallbackEventLog.objects.filter(id=log.id).count() == 0


@pytest.mark.django_db
class TestModelIndexes:
    """测试模型索引"""

    def test_health_log_indexes(self):
        """测试健康日志索引"""
        engine = EngineConfig.objects.create(
            engine_type="llm",
            name="测试引擎",
            primary_provider="ollama",
            primary_config={"model": "llama2:7b"},
        )

        # 创建多个日志以测试索引
        for i in range(5):
            EngineHealthLog.objects.create(
                engine=engine,
                status="online",
                response_time=100.0 + i,
            )

        # 验证按引擎查询应该使用索引
        logs = EngineHealthLog.objects.filter(engine=engine)
        assert logs.count() == 5

    def test_usage_log_indexes(self):
        """测试使用日志索引"""
        engine = EngineConfig.objects.create(
            engine_type="llm",
            name="测试引擎",
            primary_provider="ollama",
            primary_config={"model": "llama2:7b"},
        )

        # 创建成功和失败的日志
        EngineUsageLog.objects.create(
            engine=engine,
            provider="ollama",
            request_type="llm",
            success=True,
            response_time=100.0,
        )
        EngineUsageLog.objects.create(
            engine=engine,
            provider="ollama",
            request_type="llm",
            success=False,
            response_time=30000.0,
        )

        # 验证按成功状态查询
        success_logs = EngineUsageLog.objects.filter(success=True)
        assert success_logs.count() == 1
