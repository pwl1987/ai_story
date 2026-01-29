"""
模型管理服务测试
测试ModelProviderService和ModelUsageLogService的业务逻辑
遵循SOLID原则和TDD红绿重构循环
"""

import uuid
from datetime import timedelta
from unittest.mock import Mock, patch

import pytest
from asgiref.sync import sync_to_async
from django.utils import timezone

from apps.models.models import ModelProvider
from apps.models.services import ModelProviderService, ModelUsageLogService
from apps.models.tests.conftest import filter_mock_data
from apps.models.tests.factories import ModelProviderFactory, ModelUsageLogFactory

# 测试常量
MIN_PRIORITY_IMPOSSIBLY_HIGH = 999  # 远高于任何实际provider优先级


@pytest.mark.django_db
class TestModelProviderService:
    """测试ModelProviderService业务逻辑"""

    def test_get_active_providers_all(self):
        """测试获取激活的提供商 - 全部"""
        # Given
        ModelProviderFactory(is_active=True, name="HighPriorityProvider", priority=5)
        ModelProviderFactory(is_active=True, name="LowPriorityProvider", priority=3)
        ModelProviderFactory(is_active=False, name="InactiveProvider", priority=10)

        # When
        result = ModelProviderService.get_active_providers()

        # Then - 过滤掉Mock数据
        test_providers = [p for p in result if not p.name.startswith("Mock")]
        assert len(test_providers) == 2
        assert all(p.is_active for p in test_providers)
        # 验证按优先级排序（从高到低）
        test_providers_sorted = sorted(test_providers, key=lambda x: -x.priority)
        assert test_providers == test_providers_sorted

    def test_get_active_providers_by_type(self):
        """测试获取激活的提供商 - 按类型过滤"""
        # Given
        ModelProviderFactory(is_active=True, provider_type="llm")
        ModelProviderFactory(is_active=True, provider_type="text2image")
        ModelProviderFactory(is_active=False, provider_type="llm")

        # When
        result = ModelProviderService.get_active_providers(provider_type="llm")

        # Then
        test_providers = filter_mock_data(result)
        assert len(test_providers) == 1
        assert test_providers[0].provider_type == "llm"
        assert result[0].is_active is True

    def test_get_provider_by_type_and_priority(self):
        """测试根据类型和优先级获取提供商"""
        # Given
        provider1 = ModelProviderFactory(
            provider_type="llm",
            is_active=True,
            priority=10,  # 设置高于Mock数据
            name="HighPriorityLLM",
        )
        ModelProviderFactory(provider_type="llm", is_active=True, priority=3)
        # 不满足最小优先级
        ModelProviderFactory(provider_type="llm", is_active=True, priority=2)

        # When
        result = ModelProviderService.get_provider_by_type_and_priority("llm", min_priority=4)

        # Then - 排除Mock数据后验证
        assert result is not None
        assert result.priority >= 4
        # 如果返回的是我们创建的高优先级provider，验证其属性
        if result.name == "HighPriorityLLM":
            assert result.id == provider1.id
            assert result.priority == 10

    def test_get_provider_by_type_and_priority_not_found(self):
        """测试根据类型和优先级获取提供商 - 未找到"""
        # Given - 创建一个低优先级的provider
        ModelProviderFactory(provider_type="llm", is_active=True, priority=1)

        # When - 使用极高的min_priority，确保找不到
        result = ModelProviderService.get_provider_by_type_and_priority(
            "llm", min_priority=MIN_PRIORITY_IMPOSSIBLY_HIGH
        )

        # Then
        assert result is None

    def test_search_providers_by_keyword(self):
        """测试搜索提供商 - 按关键词"""
        # Given
        ModelProviderFactory(name="OpenAI GPT-4", provider_type="llm")
        ModelProviderFactory(name="Stable Diffusion", provider_type="text2image")
        ModelProviderFactory(name="Claude Anthropic", provider_type="llm")

        # When
        result = ModelProviderService.search_providers("GPT")

        # Then
        assert len(result) == 1
        assert "GPT" in result[0].name

    def test_search_providers_no_filter(self):
        """测试搜索提供商 - 无过滤条件"""
        # Given
        ModelProviderFactory(name="Provider1")
        ModelProviderFactory(name="Provider2")

        # When
        result = ModelProviderService.search_providers("")

        # Then
        assert len(result) >= 2

    def test_search_providers_with_type_filter(self):
        """测试搜索提供商 - 带类型过滤"""
        # Given
        ModelProviderFactory(provider_type="llm", name="LLM1")
        ModelProviderFactory(provider_type="text2image", name="Image1")

        # When
        result = ModelProviderService.search_providers(keyword="", provider_type="llm")

        # Then - 过滤掉Mock数据
        test_providers = filter_mock_data(result)
        assert len(test_providers) == 1
        assert test_providers[0].provider_type == "llm"
        assert test_providers[0].name == "LLM1"

    def test_search_providers_with_active_filter(self):
        """测试搜索提供商 - 带激活状态过滤"""
        # Given
        ModelProviderFactory(is_active=True, name="TestActive")
        ModelProviderFactory(is_active=False, name="TestInactive")

        # When
        result = ModelProviderService.search_providers(keyword="", is_active=True)

        # Then - 过滤Mock数据
        test_providers = filter_mock_data(result)
        assert len(test_providers) == 1
        assert test_providers[0].is_active is True
        assert test_providers[0].name == "TestActive"

    def test_create_provider(self):
        """测试创建提供商"""
        # Given
        data = {
            "name": "New Provider",
            "provider_type": "llm",
            "api_url": "https://api.example.com",
            "api_key": "test-key",
            "model_name": "gpt-4",
            "is_active": True,
            "priority": 5,
        }

        # When
        provider = ModelProviderService.create_provider(data)

        # Then
        assert provider.name == "New Provider"
        assert provider.provider_type == "llm"
        assert provider.is_active is True

    def test_update_provider(self):
        """测试更新提供商"""
        # Given
        provider = ModelProviderFactory(name="Original Name")
        update_data = {"name": "Updated Name", "priority": 10}

        # When
        result = ModelProviderService.update_provider(provider.id, update_data)

        # Then
        assert result.name == "Updated Name"
        assert result.priority == 10

    def test_update_provider_nonexistent(self):
        """测试更新提供商 - 不存在"""
        # Given
        fake_id = "00000000-0000-0000-0000-000000000000"
        update_data = {"name": "Test"}

        # When & Then
        with pytest.raises(ModelProvider.DoesNotExist):
            ModelProviderService.update_provider(fake_id, update_data)

    def test_delete_provider_success(self):
        """测试删除提供商 - 成功"""
        # Given
        provider = ModelProviderFactory()

        # When
        result = ModelProviderService.delete_provider(provider.id)

        # Then
        assert result is True
        assert not ModelProvider.objects.filter(id=provider.id).exists()

    def test_delete_provider_not_found(self):
        """测试删除提供商 - 不存在"""
        # Given
        fake_id = "00000000-0000-0000-0000-000000000000"

        # When
        result = ModelProviderService.delete_provider(fake_id)

        # Then
        assert result is False

    def test_toggle_provider_status(self):
        """测试切换提供商激活状态"""
        # Given
        provider = ModelProviderFactory(is_active=True)

        # When
        result = ModelProviderService.toggle_provider_status(provider.id)

        # Then
        assert result.is_active is False

        # 再次切换
        result2 = ModelProviderService.toggle_provider_status(provider.id)
        assert result2.is_active is True

    def test_get_provider_statistics(self):
        """测试获取提供商统计信息"""
        # Given - 使用特定名称的provider避免污染
        provider = ModelProviderFactory(name="StatsTestProvider")
        ModelUsageLogFactory(
            model_provider=provider, status="success", tokens_used=1000, latency_ms=500
        )
        ModelUsageLogFactory(model_provider=provider, status="failed", tokens_used=0, latency_ms=0)
        ModelUsageLogFactory(
            model_provider=provider,
            status="success",
            tokens_used=2000,
            latency_ms=800,
            created_at=timezone.now() - timedelta(days=3),
        )

        # When
        stats = ModelProviderService.get_provider_statistics(provider.id)

        # Then - 验证统计的是正确provider的数据
        assert stats["total_count"] >= 3  # 至少包含我们创建的3条
        assert stats["success_count"] >= 2
        assert stats["failed_count"] >= 1
        assert stats["total_tokens_used"] >= 3000
        # 验证百分比计算正确
        expected_rate = (stats["success_count"] / stats["total_count"]) * 100
        assert abs(stats["success_rate"] - expected_rate) < 0.01

    def test_get_provider_statistics_no_logs(self):
        """测试获取提供商统计信息 - 无日志"""
        # Given
        provider = ModelProviderFactory()

        # When
        stats = ModelProviderService.get_provider_statistics(provider.id)

        # Then
        assert stats["total_count"] == 0
        assert stats["success_count"] == 0
        assert stats["failed_count"] == 0
        assert stats["success_rate"] == 0
        assert stats["avg_latency_ms"] == 0

    @pytest.mark.asyncio
    @pytest.mark.django_db(transaction=True)
    async def test_test_provider_connection_llm_success(self):
        """测试连接测试 - LLM提供商成功"""
        # Given
        provider = await sync_to_async(ModelProviderFactory)(
            provider_type="llm",
            is_active=True,
            api_url="https://api.openai.com",
            model_name="gpt-4",
        )

        # Mock流式生成 - 返回迭代器而不是函数
        def mock_stream():
            yield {"type": "chunk", "text": "Hello"}
            yield {"type": "done", "full_text": "Hello World", "is_success": True}

        mock_client_instance = Mock()
        mock_client_instance.generate_stream = mock_stream()

        # When - Patch OpenAIClient并返回mock实例
        with patch("apps.models.services.ModelProviderService._test_llm_provider") as mock_test:
            mock_test.return_value = {
                "success": True,
                "text": "Hello World",
                "data": {"prompt": "test", "provider": provider.name},
                "tokens_used": 0,
            }
            result = await ModelProviderService.test_provider_connection(provider.id)

        # Then
        assert result["success"] is True

    @pytest.mark.asyncio
    @pytest.mark.django_db(transaction=True)
    async def test_test_provider_connection_not_active(self):
        """测试连接测试 - 提供商未激活"""
        # Given
        provider = await sync_to_async(ModelProviderFactory)(is_active=False)

        # When
        result = await ModelProviderService.test_provider_connection(provider.id)

        # Then
        assert result["success"] is False
        assert "未激活" in result["error"]

    @pytest.mark.asyncio
    @pytest.mark.django_db(transaction=True)
    async def test_test_provider_connection_exception(self):
        """测试连接测试 - 异常处理"""
        # Given
        provider = await sync_to_async(ModelProviderFactory)(is_active=True, provider_type="llm")

        # When - Mock _test_llm_provider抛出异常
        with patch("apps.models.services.ModelProviderService._test_llm_provider") as mock_test:
            mock_test.side_effect = Exception("Network error")
            result = await ModelProviderService.test_provider_connection(provider.id)

        # Then - 验证异常被正确捕获并返回有意义的错误
        assert result["success"] is False
        assert "error" in result  # 必须有error字段
        assert isinstance(result["error"], str)
        assert len(result["error"]) > 0  # 错误消息不能为空
        assert "Network error" in result["error"]  # 验证保留了原始异常信息

    def test_get_provider_statistics_aggregation(self):
        """测试获取提供商统计信息 - 聚合函数"""
        # Given
        provider = ModelProviderFactory()
        # 创建多个使用日志
        for i in range(5):
            ModelUsageLogFactory(
                model_provider=provider,
                status="success",
                tokens_used=1000 * (i + 1),
                latency_ms=500 + i * 100,
            )

        # When
        stats = ModelProviderService.get_provider_statistics(provider.id)

        # Then
        assert stats["total_count"] == 5
        assert stats["total_tokens_used"] == 15000  # 1000+2000+3000+4000+5000
        # 验证使用了聚合函数
        assert "avg_latency_ms" in stats


@pytest.mark.django_db
class TestModelUsageLogService:
    """测试ModelUsageLogService业务逻辑"""

    def test_get_logs_by_provider(self):
        """测试获取提供商的使用日志"""
        # Given
        provider = ModelProviderFactory()
        log1 = ModelUsageLogFactory(model_provider=provider, stage_type="rewrite")
        log2 = ModelUsageLogFactory(model_provider=provider, stage_type="storyboard")
        ModelUsageLogFactory()  # 其他提供商的日志

        # When
        result = ModelUsageLogService.get_logs_by_provider(provider.id, limit=10)

        # Then
        assert len(result) == 2
        assert log1 in result
        assert log2 in result

    def test_get_logs_by_provider_with_limit(self):
        """测试获取提供商的使用日志 - 带限制"""
        # Given
        provider = ModelProviderFactory()
        for _i in range(20):
            ModelUsageLogFactory(model_provider=provider)

        # When
        result = ModelUsageLogService.get_logs_by_provider(provider.id, limit=5)

        # Then
        assert len(result) == 5

    def test_get_logs_by_project(self):
        """测试获取项目的使用日志"""
        # Given
        project_id = str(uuid.uuid4())
        provider = ModelProviderFactory()
        log1 = ModelUsageLogFactory(
            model_provider=provider, project_id=project_id, stage_type="rewrite"
        )
        log2 = ModelUsageLogFactory(
            model_provider=provider, project_id=project_id, stage_type="storyboard"
        )
        ModelUsageLogFactory(project_id=str(uuid.uuid4()))

        # When
        result = ModelUsageLogService.get_logs_by_project(project_id)

        # Then
        assert len(result) == 2
        assert log1 in result
        assert log2 in result

    def test_get_logs_by_project_with_stage_filter(self):
        """测试获取项目的使用日志 - 带阶段过滤"""
        # Given
        project_id = str(uuid.uuid4())
        provider = ModelProviderFactory()
        ModelUsageLogFactory(model_provider=provider, project_id=project_id, stage_type="rewrite")
        ModelUsageLogFactory(
            model_provider=provider, project_id=project_id, stage_type="storyboard"
        )

        # When
        result = ModelUsageLogService.get_logs_by_project(project_id, stage_type="rewrite")

        # Then
        assert len(result) == 1
        assert result[0].stage_type == "rewrite"

    def test_get_failed_logs(self):
        """测试获取失败的日志"""
        # Given
        ModelProviderFactory()
        ModelUsageLogFactory(status="failed")
        ModelUsageLogFactory(status="failed")
        ModelUsageLogFactory(status="success")
        ModelUsageLogFactory(status="success")

        # When
        result = ModelUsageLogService.get_failed_logs(limit=10)

        # Then
        assert len(result) >= 2
        assert all(log.status == "failed" for log in result)
        # 验证按时间倒序
        timestamps = [log.created_at for log in result]
        assert timestamps == sorted(timestamps, reverse=True)

    def test_get_failed_logs_with_limit(self):
        """测试获取失败的日志 - 带限制"""
        # Given
        for _i in range(20):
            ModelUsageLogFactory(status="failed")

        # When
        result = ModelUsageLogService.get_failed_logs(limit=5)

        # Then
        assert len(result) == 5

    def test_create_usage_log(self):
        """测试创建使用日志"""
        # Given
        provider = ModelProviderFactory()
        project_id = str(uuid.uuid4())
        data = {
            "model_provider": provider,
            "project_id": project_id,
            "stage_type": "rewrite",
            "status": "success",
            "tokens_used": 1500,
            "latency_ms": 800,
            "request_data": {"prompt": "test"},
            "response_data": {"result": "ok"},
        }

        # When
        log = ModelUsageLogService.create_usage_log(data)

        # Then
        assert log.id is not None
        assert log.model_provider == provider
        assert log.project_id == project_id
        assert log.status == "success"
        assert log.tokens_used == 1500

    def test_create_usage_log_all_fields(self):
        """测试创建使用日志 - 包含所有字段"""
        # Given
        provider = ModelProviderFactory()
        data = {
            "model_provider": provider,
            "project_id": str(uuid.uuid4()),
            "stage_type": "image_generation",
            "status": "success",
            "tokens_used": 2000,
            "latency_ms": 1200,
            "request_data": {"test": "data"},
            "response_data": {"result": "success"},
            "error_message": "",
        }

        # When
        log = ModelUsageLogService.create_usage_log(data)

        # Then
        assert log.stage_type == "image_generation"
        assert log.request_data == {"test": "data"}
        assert log.response_data == {"result": "success"}
        assert log.error_message == ""

    def test_search_providers_by_url(self):
        """测试搜索提供商 - 按URL关键词"""
        # Given
        ModelProviderFactory(api_url="https://api.openai.com/v1")
        ModelProviderFactory(api_url="https://api.anthropic.com")

        # When
        result = ModelProviderService.search_providers("openai")

        # Then
        assert len(result) == 1
        assert "openai" in result[0].api_url.lower()

    def test_search_providers_by_model_name(self):
        """测试搜索提供商 - 按模型名称"""
        # Given
        ModelProviderFactory(model_name="gpt-4")
        ModelProviderFactory(model_name="claude-3")

        # When
        result = ModelProviderService.search_providers("gpt")

        # Then
        assert len(result) == 1
        assert "gpt" in result[0].model_name.lower()

    def test_get_active_providers_empty_result(self):
        """测试获取激活的提供商 - 无我们自己创建的激活provider（排除Mock迁移数据）"""
        # Given - 创建一个非激活的provider
        ModelProviderFactory(is_active=False, name="InactiveProvider")

        # When
        result = ModelProviderService.get_active_providers()

        # Then - 验证没有我们创建的激活provider（Mock迁移数据会被过滤）
        test_providers = filter_mock_data(result)
        assert len(test_providers) == 0
        # 确认Mock迁移数据存在但不计入测试结果
        assert len(result) >= 3  # Mock LLM, Text2Image, Image2Video

    def test_search_providers_combined_filters(self):
        """测试搜索提供商 - 组合过滤条件"""
        # Given
        ModelProviderFactory(
            name="Test LLM Provider", provider_type="llm", is_active=True, priority=5
        )
        ModelProviderFactory(
            name="Test Image Provider", provider_type="text2image", is_active=False, priority=3
        )

        # When
        result = ModelProviderService.search_providers(
            keyword="Test", provider_type="llm", is_active=True
        )

        # Then
        assert len(result) == 1
        assert result[0].provider_type == "llm"
        assert result[0].is_active is True
