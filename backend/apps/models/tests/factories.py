"""
测试数据工厂 - apps/models模块
使用Factory Boy创建测试数据，遵循DRY原则
"""

import factory
from faker import Faker

from apps.models.models import ModelProvider, ModelUsageLog

fake = Faker(['zh_CN'])


class ModelProviderFactory(factory.django.DjangoModelFactory):
    """
    模型提供商工厂
    职责: 创建ModelProvider测试数据
    遵循单一职责原则(SRP)
    """
    class Meta:
        model = ModelProvider

    name = factory.Sequence(lambda n: f"Provider{n}")
    provider_type = factory.Iterator(['llm', 'text2image', 'image2video'])
    executor_class = factory.LazyFunction(lambda: 'core.ai_client.mock_llm_client.MockLLMClient')

    api_url = factory.LazyFunction(lambda: fake.url())
    api_key = factory.LazyFunction(lambda: fake.uuid4())
    model_name = factory.LazyFunction(lambda: f"model-{fake.word()}")

    max_tokens = factory.LazyFunction(lambda: fake.random_int(min=1000, max=32000))
    temperature = 0.7
    top_p = 1.0

    timeout = 60
    is_active = True
    priority = factory.LazyFunction(lambda: fake.random_int(min=1, max=10))

    rate_limit_rpm = 60
    rate_limit_rpd = 1000

    extra_config = factory.LazyFunction(lambda: {
        'temperature': 0.7,
        'top_p': 0.9
    })


class ModelUsageLogFactory(factory.django.DjangoModelFactory):
    """
    模型使用日志工厂
    职责: 创建ModelUsageLog测试数据
    """
    class Meta:
        model = ModelUsageLog

    model_provider = factory.SubFactory(ModelProviderFactory)
    project_id = factory.LazyFunction(lambda: fake.uuid4())
    stage_type = factory.Iterator(['rewrite', 'storyboard', 'image_generation', 'video_generation'])
    status = factory.Iterator(['success', 'failed'])

    tokens_used = factory.LazyFunction(lambda: fake.random_int(min=300, max=13000))
    latency_ms = factory.LazyFunction(lambda: fake.random_int(min=500, max=10000))

    request_data = factory.LazyFunction(lambda: {'test': 'data'})
    response_data = factory.LazyFunction(lambda: {'result': 'success'})

    error_message = factory.LazyFunction(lambda: fake.sentence() if fake.boolean(chance_of_getting_true=30) else '')
