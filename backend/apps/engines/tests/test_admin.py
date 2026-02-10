# Engines Admin Tests - 引擎管理后台测试

import pytest
from django.contrib.admin import site
from django.contrib.auth.models import User

from apps.engines.admin import (
    EngineConfigAdmin,
    EngineHealthLogAdmin,
    EngineUsageLogAdmin,
    FallbackEventLogAdmin,
)
from apps.engines.models import (
    EngineConfig,
    EngineHealthLog,
    EngineUsageLog,
    FallbackEventLog,
)


@pytest.mark.django_db
class TestEngineConfigAdmin:
    """EngineConfig Admin 测试"""

    def test_admin_is_registered(self):
        """测试 Admin 是否注册"""
        assert site.is_registered(EngineConfig)

    def test_list_display_configuration(self):
        """测试列表显示配置"""
        admin = EngineConfigAdmin(EngineConfig, site)

        expected_display = [
            "engine_type_display",
            "name",
            "primary_provider",
            "health_status_badge",
            "is_active",
            "success_rate",
            "total_requests",
            "saved_cost_display",
        ]

        assert admin.list_display == expected_display

    def test_list_filters(self):
        """测试列表过滤器"""
        admin = EngineConfigAdmin(EngineConfig, site)

        expected_filters = [
            "engine_type",
            "health_status",
            "is_active",
            "auto_fallback",
        ]

        assert admin.list_filter == expected_filters

    def test_search_fields(self):
        """测试搜索字段"""
        admin = EngineConfigAdmin(EngineConfig, site)

        expected_search = [
            "name",
            "primary_provider",
            "fallback_provider",
            "description",
        ]

        assert admin.search_fields == expected_search

    def test_readonly_fields(self):
        """测试只读字段"""
        admin = EngineConfigAdmin(EngineConfig, site)

        assert "total_requests" in admin.readonly_fields
        assert "success_count" in admin.readonly_fields
        assert "failure_count" in admin.readonly_fields
        assert "avg_response_time" in admin.readonly_fields
        assert "total_cost" in admin.readonly_fields
        assert "saved_cost" in admin.readonly_fields

    def test_admin_actions_exist(self):
        """测试 Admin 操作是否存在"""
        admin = EngineConfigAdmin(EngineConfig, site)

        expected_actions = [
            "test_connection_action",
            "reset_stats_action",
            "enable_auto_fallback",
            "disable_auto_fallback",
            "mark_as_online",
            "mark_as_offline",
        ]

        for action in expected_actions:
            assert action in admin.actions

    def test_engine_type_display_method(self):
        """测试引擎类型显示方法"""
        engine = EngineConfig.objects.create(
            engine_type="llm",
            name="LLM 引擎",
            primary_provider="ollama",
            primary_config={"model": "llama2:7b"},
        )

        admin = EngineConfigAdmin(EngineConfig, site)
        result = admin.engine_type_display(engine)

        assert "🤖" in result
        assert "LLM" in result

    def test_health_status_badge_method(self):
        """测试健康状态徽章方法"""
        engine = EngineConfig.objects.create(
            engine_type="llm",
            name="LLM 引擎",
            primary_provider="ollama",
            primary_config={"model": "llama2:7b"},
            health_status="online",
        )

        admin = EngineConfigAdmin(EngineConfig, site)
        result = admin.health_status_badge(engine)

        assert "green" in result
        assert "online" in result or "在线" in result

    def test_success_rate_method(self):
        """测试成功率显示方法"""
        engine = EngineConfig.objects.create(
            engine_type="llm",
            name="LLM 引擎",
            primary_provider="ollama",
            primary_config={"model": "llama2:7b"},
            total_requests=100,
            success_count=95,
        )

        admin = EngineConfigAdmin(EngineConfig, site)
        result = admin.success_rate(engine)

        assert "95.0" in result or "95%" in result

    def test_reset_stats_action(self, superuser):
        """测试重置统计操作"""
        from unittest.mock import patch

        from django.test import RequestFactory

        engine = EngineConfig.objects.create(
            engine_type="llm",
            name="LLM 引擎",
            primary_provider="ollama",
            primary_config={"model": "llama2:7b"},
            total_requests=100,
            success_count=95,
            failure_count=5,
            total_cost=10.0,
            saved_cost=50.0,
        )

        admin = EngineConfigAdmin(EngineConfig, site)
        queryset = EngineConfig.objects.filter(id=engine.id)

        # 创建请求对象
        factory = RequestFactory()
        request = factory.post("/admin/")
        request.user = superuser

        # 模拟 message_user 方法，避免消息中间件问题
        with patch.object(admin, "message_user"):
            # 执行重置操作
            admin.reset_stats_action(request, queryset)

        engine.refresh_from_db()
        assert engine.total_requests == 0
        assert engine.success_count == 0
        assert engine.failure_count == 0
        assert engine.total_cost == 0.0
        assert engine.saved_cost == 0.0


@pytest.mark.django_db
class TestEngineHealthLogAdmin:
    """EngineHealthLog Admin 测试"""

    def test_admin_is_registered(self):
        """测试 Admin 是否注册"""
        assert site.is_registered(EngineHealthLog)

    def test_list_display_configuration(self):
        """测试列表显示配置"""
        admin = EngineHealthLogAdmin(EngineHealthLog, site)

        expected_fields = [
            "engine_display",
            "status_badge",
            "response_time_display",
            "error_code",
            "checked_at",
        ]

        assert admin.list_display == expected_fields

    def test_readonly_fields(self):
        """测试只读字段"""
        admin = EngineHealthLogAdmin(EngineHealthLog, site)

        assert "engine" in admin.readonly_fields
        assert "status" in admin.readonly_fields
        assert "response_time" in admin.readonly_fields
        assert "error_message" in admin.readonly_fields

    def test_has_add_permission_false(self):
        """测试禁用手动添加"""
        admin = EngineHealthLogAdmin(EngineHealthLog, site)
        assert admin.has_add_permission(None) is False

    def test_has_change_permission_false(self):
        """测试禁用手动修改"""
        admin = EngineHealthLogAdmin(EngineHealthLog, site)
        assert admin.has_change_permission(None) is False

    def test_response_time_display_method(self):
        """测试响应时间显示方法"""
        engine = EngineConfig.objects.create(
            engine_type="llm",
            name="LLM 引擎",
            primary_provider="ollama",
            primary_config={"model": "llama2:7b"},
        )

        log = EngineHealthLog.objects.create(
            engine=engine,
            status="online",
            response_time=123.5,
        )

        admin = EngineHealthLogAdmin(EngineHealthLog, site)
        result = admin.response_time_display(log)

        assert "123" in result or "124" in result
        assert "ms" in result


@pytest.mark.django_db
class TestEngineUsageLogAdmin:
    """EngineUsageLog Admin 测试"""

    def test_admin_is_registered(self):
        """测试 Admin 是否注册"""
        assert site.is_registered(EngineUsageLog)

    def test_list_display_configuration(self):
        """测试列表显示配置"""
        admin = EngineUsageLogAdmin(EngineUsageLog, site)

        expected_fields = [
            "engine_display",
            "provider",
            "request_type",
            "success_badge",
            "response_time_display",
            "cost_display",
            "created_at",
        ]

        assert admin.list_display == expected_fields

    def test_list_filters(self):
        """测试列表过滤器"""
        admin = EngineUsageLogAdmin(EngineUsageLog, site)

        expected_filters = [
            "success",
            "request_type",
            "engine__engine_type",
            "provider",
        ]

        assert admin.list_filter == expected_filters

    def test_has_add_permission_false(self):
        """测试禁用手动添加"""
        admin = EngineUsageLogAdmin(EngineUsageLog, site)
        assert admin.has_add_permission(None) is False

    def test_has_change_permission_false(self):
        """测试禁用手动修改"""
        admin = EngineUsageLogAdmin(EngineUsageLog, site)
        assert admin.has_change_permission(None) is False

    def test_success_badge_method(self):
        """测试成功状态徽章方法"""
        engine = EngineConfig.objects.create(
            engine_type="llm",
            name="LLM 引擎",
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

        admin = EngineUsageLogAdmin(EngineUsageLog, site)
        result = admin.success_badge(log)

        assert "green" in result
        assert "✓" in result

    def test_cost_display_method(self):
        """测试成本显示方法"""
        engine = EngineConfig.objects.create(
            engine_type="llm",
            name="LLM 引擎",
            primary_provider="ollama",
            primary_config={"model": "llama2:7b"},
        )

        log = EngineUsageLog.objects.create(
            engine=engine,
            provider="openai",
            request_type="llm",
            success=True,
            response_time=200.0,
            cost=0.01,
            saved_cost=0.05,
        )

        admin = EngineUsageLogAdmin(EngineUsageLog, site)
        result = admin.cost_display(log)

        assert "0.01" in result
        assert "0.05" in result


@pytest.mark.django_db
class TestFallbackEventLogAdmin:
    """FallbackEventLog Admin 测试"""

    def test_admin_is_registered(self):
        """测试 Admin 是否注册"""
        assert site.is_registered(FallbackEventLog)

    def test_list_display_configuration(self):
        """测试列表显示配置"""
        admin = FallbackEventLogAdmin(FallbackEventLog, site)

        expected_fields = [
            "engine_display",
            "switch_display",
            "reason_badge",
            "affected_requests",
            "occurred_at",
        ]

        assert admin.list_display == expected_fields

    def test_list_filters(self):
        """测试列表过滤器"""
        admin = FallbackEventLogAdmin(FallbackEventLog, site)

        expected_filters = [
            "reason",
            "engine__engine_type",
        ]

        assert admin.list_filter == expected_filters

    def test_has_add_permission_false(self):
        """测试禁用手动添加"""
        admin = FallbackEventLogAdmin(FallbackEventLog, site)
        assert admin.has_add_permission(None) is False

    def test_has_change_permission_false(self):
        """测试禁用手动修改"""
        admin = FallbackEventLogAdmin(FallbackEventLog, site)
        assert admin.has_change_permission(None) is False

    def test_switch_display_method(self):
        """测试切换路径显示方法"""
        engine = EngineConfig.objects.create(
            engine_type="llm",
            name="LLM 引擎",
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
        )

        admin = FallbackEventLogAdmin(FallbackEventLog, site)
        result = admin.switch_display(event)

        assert "ollama" in result
        assert "openai" in result
        assert "→" in result

    def test_reason_badge_method(self):
        """测试原因徽章方法"""
        engine = EngineConfig.objects.create(
            engine_type="llm",
            name="LLM 引擎",
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
        )

        admin = FallbackEventLogAdmin(FallbackEventLog, site)
        result = admin.reason_badge(event)

        assert "orange" in result
        assert "超时" in result or "timeout" in result.lower()


# ==================== Fixtures ====================


@pytest.fixture
def superuser(db):
    """创建超级用户"""
    return User.objects.create_superuser(
        username="admin", email="admin@example.com", password="testpass123"
    )


@pytest.fixture
def engine_config(db):
    """创建测试引擎配置"""
    return EngineConfig.objects.create(
        engine_type="llm",
        name="测试 LLM 引擎",
        primary_provider="ollama",
        primary_config={
            "base_url": "http://localhost:11434",
            "model": "llama2:7b",
        },
        fallback_provider="openai",
        fallback_config={
            "api_key": "sk-test",
            "model": "gpt-4",
        },
    )


@pytest.fixture
def health_log(db, engine_config):
    """创建测试健康日志"""
    return EngineHealthLog.objects.create(
        engine=engine_config,
        status="online",
        response_time=100.0,
    )


@pytest.fixture
def usage_log(db, engine_config):
    """创建测试使用日志"""
    return EngineUsageLog.objects.create(
        engine=engine_config,
        provider="ollama",
        request_type="llm",
        success=True,
        response_time=150.0,
        cost=0.001,
    )


@pytest.fixture
def fallback_event(db, engine_config):
    """创建测试 Fallback 事件"""
    return FallbackEventLog.objects.create(
        engine=engine_config,
        from_provider="ollama",
        to_provider="openai",
        reason="timeout",
        reason_detail="连续3次超时",
    )
