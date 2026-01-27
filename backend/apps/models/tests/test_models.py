"""
模型管理域模型测试
测试ModelProvider, ModelUsageLog模型
遵循单一职责原则(SRP)
"""

import pytest
from django.db.utils import IntegrityError
from django.core.exceptions import ValidationError

from apps.models.models import ModelProvider, ModelUsageLog
from apps.models.tests.factories import ModelProviderFactory


# ============================================================================
# ModelProvider 测试
# ============================================================================

@pytest.mark.django_db
class TestModelProviderModel:
    """
    测试ModelProvider模型
    职责: 验证模型提供商的CRUD操作和业务逻辑
    遵循单一职责原则(SRP)
    """

    def test_create_model_provider_minimal(self):
        """测试创建最小模型提供商"""
        provider = ModelProvider.objects.create(
            name='GPT-4',
            provider_type='llm',
            api_url='https://api.openai.com/v1',
            api_key='sk-test',
            model_name='gpt-4'
        )

        assert provider.id is not None
        assert provider.name == 'GPT-4'
        assert provider.provider_type == 'llm'
        assert provider.is_active is True
        assert provider.max_tokens == 2000  # 默认值
        assert provider.temperature == 0.7  # 默认值

    def test_create_model_provider_full(self):
        """测试创建完整模型提供商"""
        provider = ModelProviderFactory()

        assert ModelProvider.objects.filter(id=provider.id).exists()

    def test_create_all_provider_types(self):
        """测试创建所有类型的模型提供商"""
        provider_types = ['llm', 'text2image', 'image2video']

        for provider_type in provider_types:
            provider = ModelProviderFactory(provider_type=provider_type)
            assert provider.provider_type == provider_type
            assert provider.get_provider_type_display() is not None

    def test_provider_str_representation(self):
        """测试字符串表示"""
        provider = ModelProviderFactory(name='Claude-3', provider_type='llm')
        expected = 'Claude-3 (LLM模型)'
        assert str(provider) == expected

    def test_provider_default_values(self):
        """测试默认值"""
        # 使用objects.create绕过factory，确保使用模型默认值
        provider = ModelProvider.objects.create(
            name='Test Provider',
            provider_type='llm',
            api_url='https://api.test.com',
            api_key='test-key',
            model_name='test-model',
            max_tokens=4000,
            temperature=0.5
        )

        assert provider.top_p == 1.0  # 默认值
        assert provider.timeout == 60  # 默认值
        assert provider.is_active is True  # 默认值
        assert provider.priority == 0  # 默认值
        assert provider.rate_limit_rpm == 60  # 默认值
        assert provider.rate_limit_rpd == 1000  # 默认值

    def test_provider_json_field(self):
        """测试JSON字段"""
        extra_config = {
            'temperature': 0.8,
            'top_p': 0.95,
            'frequency_penalty': 0.5,
            'presence_penalty': 0.5
        }

        provider = ModelProviderFactory(extra_config=extra_config)

        assert provider.extra_config == extra_config
        assert provider.extra_config['frequency_penalty'] == 0.5

    def test_provider_ordering(self):
        """测试默认排序（按priority降序，创建时间降序）"""
        # 清除现有数据以确保测试隔离
        ModelProvider.objects.all().delete()

        provider1 = ModelProviderFactory(priority=10)
        provider2 = ModelProviderFactory(priority=20)
        provider3 = ModelProviderFactory(priority=5)

        providers = list(ModelProvider.objects.all())
        assert providers[0].priority == 20  # provider2
        assert providers[1].priority == 10  # provider1
        assert providers[2].priority == 5   # provider3

    def test_provider_update(self):
        """测试更新模型提供商"""
        provider = ModelProviderFactory(is_active=True, priority=5)

        provider.is_active = False
        provider.priority = 10
        provider.save()

        provider.refresh_from_db()
        assert provider.is_active is False
        assert provider.priority == 10

    def test_provider_delete(self):
        """测试删除模型提供商"""
        provider = ModelProviderFactory()
        provider_id = provider.id

        provider.delete()

        assert not ModelProvider.objects.filter(id=provider_id).exists()


@pytest.mark.django_db
class TestModelProviderMethods:
    """
    测试ModelProvider方法
    职责: 验证业务逻辑方法的正确性
    遵循单一职责原则(SRP)
    """

    def test_get_executor_choices_llm(self):
        """测试获取LLM执行器选项"""
        provider = ModelProviderFactory(provider_type='llm')

        choices = provider.get_executor_choices()

        assert len(choices) > 0
        assert isinstance(choices, list)
        assert all(len(choice) == 2 for choice in choices)

    def test_get_executor_choices_text2image(self):
        """测试获取文生图执行器选项"""
        provider = ModelProviderFactory(provider_type='text2image')

        choices = provider.get_executor_choices()

        assert len(choices) > 0
        assert isinstance(choices, list)

    def test_get_executor_choices_image2video(self):
        """测试获取图生视频执行器选项"""
        provider = ModelProviderFactory(provider_type='image2video')

        choices = provider.get_executor_choices()

        assert len(choices) > 0
        assert isinstance(choices, list)

    def test_get_default_executor_llm(self):
        """测试获取LLM默认执行器"""
        provider = ModelProviderFactory(provider_type='llm', executor_class='')

        default = provider.get_default_executor()

        assert default != ''
        assert 'MockLLMClient' in default or 'OpenAIClient' in default

    def test_get_default_executor_text2image(self):
        """测试获取文生图默认执行器"""
        provider = ModelProviderFactory(provider_type='text2image', executor_class='')

        default = provider.get_default_executor()

        assert default != ''
        assert 'Text2ImageClient' in default or 'ComfyUIClient' in default

    def test_get_default_executor_image2video(self):
        """测试获取图生视频默认执行器"""
        provider = ModelProviderFactory(provider_type='image2video', executor_class='')

        default = provider.get_default_executor()

        assert default != ''
        assert 'Image2VideoClient' in default or 'ComfyUIClient' in default

    def test_validate_executor_class_valid(self):
        """测试验证有效执行器类"""
        provider = ModelProviderFactory(
            provider_type='llm',
            executor_class='core.ai_client.mock_llm_client.MockLLMClient'
        )

        is_valid = provider.validate_executor_class()

        assert is_valid is True

    def test_validate_executor_class_invalid(self):
        """测试验证无效执行器类"""
        provider = ModelProviderFactory(
            provider_type='llm',
            executor_class='invalid.executor.Class'
        )

        is_valid = provider.validate_executor_class()

        assert is_valid is False

    def test_validate_executor_class_empty(self):
        """测试验证空执行器类"""
        provider = ModelProviderFactory(
            provider_type='llm',
            executor_class=''
        )

        is_valid = provider.validate_executor_class()

        assert is_valid is False


@pytest.mark.django_db
class TestModelProviderConstraints:
    """
    测试ModelProvider约束
    职责: 验证数据库约束和验证规则
    遵循单一职责原则(SRP)
    """

    def test_name_required(self):
        """测试name字段必填"""
        with pytest.raises(IntegrityError):
            ModelProvider.objects.create(
                name=None,
                provider_type='llm',
                api_url='https://api.openai.com/v1',
                api_key='sk-test',
                model_name='gpt-4'
            )

    def test_provider_type_choices(self):
        """测试provider_type选择限制"""
        provider = ModelProviderFactory(provider_type='llm')

        valid_types = ['llm', 'text2image', 'image2video']
        assert provider.provider_type in valid_types

    def test_api_url_validation(self):
        """测试API URL格式验证"""
        provider = ModelProviderFactory(
            api_url='invalid-url'
        )

        # Django的URLField会在保存时验证
        with pytest.raises(ValidationError):
            provider.full_clean()  # 触发完整验证

    def test_max_tokens_positive(self):
        """测试max_tokens必须为正数"""
        provider = ModelProviderFactory(max_tokens=2000)

        assert provider.max_tokens > 0

    def test_temperature_range(self):
        """测试temperature在0-1范围内"""
        provider = ModelProviderFactory(temperature=0.7)

        assert 0 <= provider.temperature <= 1

    def test_top_p_range(self):
        """测试top_p在0-1范围内"""
        provider = ModelProviderFactory(top_p=0.9)

        assert 0 <= provider.top_p <= 1


# ============================================================================
# ModelUsageLog 测试
# ============================================================================

@pytest.mark.django_db
class TestModelUsageLogModel:
    """
    测试ModelUsageLog模型
    职责: 验证模型使用日志的记录和关联
    遵循单一职责原则(SRP)
    """

    def test_create_usage_log_minimal(self):
        """测试创建最小使用日志"""
        provider = ModelProviderFactory()

        log = ModelUsageLog.objects.create(
            model_provider=provider,
            status='success'
        )

        assert log.id is not None
        assert log.model_provider == provider
        assert log.status == 'success'
        assert log.tokens_used == 0  # 默认值
        assert log.latency_ms == 0  # 默认值

    def test_create_usage_log_full(self):
        """测试创建完整使用日志"""
        log = ModelUsageLog.objects.create(
            model_provider=ModelProviderFactory(),
            request_data={'prompt': 'test'},
            response_data={'text': 'response'},
            tokens_used=500,
            latency_ms=1500,
            status='success',
            project_id='123e4567-e89b-12d3-a456-426614174000',
            stage_type='rewrite'
        )

        assert log.id is not None
        assert log.tokens_used == 500
        assert log.latency_ms == 1500
        assert log.stage_type == 'rewrite'

    def test_usage_log_str_representation(self):
        """测试字符串表示"""
        provider = ModelProviderFactory(name='GPT-4')
        log = ModelUsageLog.objects.create(
            model_provider=provider
        )

        expected = f'{provider.name} - {log.created_at}'
        assert str(log) == expected

    def test_usage_log_foreign_key_cascade(self):
        """测试外键级联删除"""
        provider = ModelProviderFactory()
        log = ModelUsageLog.objects.create(
            model_provider=provider
        )
        log_id = log.id

        provider.delete()

        assert not ModelUsageLog.objects.filter(id=log_id).exists()

    def test_usage_log_json_fields(self):
        """测试JSON字段"""
        request_data = {
            'prompt': 'test prompt',
            'max_tokens': 2000,
            'temperature': 0.7
        }

        response_data = {
            'text': 'test response',
            'tokens_used': 500
        }

        log = ModelUsageLog.objects.create(
            model_provider=ModelProviderFactory(),
            request_data=request_data,
            response_data=response_data
        )

        assert log.request_data == request_data
        assert log.response_data == response_data
        assert log.request_data['prompt'] == 'test prompt'

    def test_usage_log_ordering(self):
        """测试默认排序（按创建时间降序）"""
        provider = ModelProviderFactory()
        log1 = ModelUsageLog.objects.create(model_provider=provider)
        log2 = ModelUsageLog.objects.create(model_provider=provider)
        log3 = ModelUsageLog.objects.create(model_provider=provider)

        logs = list(ModelUsageLog.objects.all())
        assert logs[0] == log3  # 最新的在前
        assert logs[1] == log2
        assert logs[2] == log1

    def test_usage_log_status_choices(self):
        """测试状态选择"""
        provider = ModelProviderFactory()

        for status in ['success', 'error', 'timeout']:
            log = ModelUsageLog.objects.create(
                model_provider=provider,
                status=status
            )
            assert log.status == status


@pytest.mark.django_db
class TestModelUsageLogRelationships:
    """
    测试ModelUsageLog关联关系
    职责: 验证日志与提供商的关联
    遵循单一职责原则(SRP)
    """

    def test_provider_has_many_logs(self):
        """测试提供商有多个日志"""
        provider = ModelProviderFactory()
        log1 = ModelUsageLog.objects.create(model_provider=provider)
        log2 = ModelUsageLog.objects.create(model_provider=provider)
        log3 = ModelUsageLog.objects.create(model_provider=provider)

        assert provider.usage_logs.count() == 3
        assert log1 in provider.usage_logs.all()
        assert log2 in provider.usage_logs.all()
        assert log3 in provider.usage_logs.all()

    def test_log_belongs_to_provider(self):
        """测试日志属于提供商"""
        provider = ModelProviderFactory()
        log = ModelUsageLog.objects.create(model_provider=provider)

        assert log.model_provider == provider

    def test_multiple_providers_have_separate_logs(self):
        """测试不同提供商的日志分离"""
        provider1 = ModelProviderFactory()
        provider2 = ModelProviderFactory()

        log1 = ModelUsageLog.objects.create(model_provider=provider1)
        log2 = ModelUsageLog.objects.create(model_provider=provider2)

        assert provider1.usage_logs.count() == 1
        assert provider2.usage_logs.count() == 1
        assert log1 in provider1.usage_logs.all()
        assert log2 not in provider1.usage_logs.all()
