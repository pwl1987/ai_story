"""
测试数据工厂 - apps/prompts模块
使用Factory Boy创建测试数据，遵循DRY原则
"""

import factory
from faker import Faker
from django.contrib.auth.models import User

from apps.prompts.models import PromptTemplateSet, PromptTemplate, GlobalVariable

fake = Faker(['zh_CN'])


class UserFactory(factory.django.DjangoModelFactory):
    """用户工厂"""
    class Meta:
        model = User

    username = factory.Sequence(lambda n: f"user_{n}")
    email = factory.LazyFunction(lambda: fake.email())


class PromptTemplateSetFactory(factory.django.DjangoModelFactory):
    """提示词集工厂"""
    class Meta:
        model = PromptTemplateSet

    name = factory.Sequence(lambda n: f"提示词集{n}")
    description = factory.LazyFunction(lambda: fake.text(max_nb_chars=200))
    is_active = True
    is_default = False
    created_by = factory.SubFactory(UserFactory)


class PromptTemplateFactory(factory.django.DjangoModelFactory):
    """提示词模板工厂"""
    class Meta:
        model = PromptTemplate

    template_set = factory.SubFactory(PromptTemplateSetFactory)

    stage_type = factory.Iterator(['rewrite', 'storyboard', 'image_generation', 'camera_movement', 'video_generation'])
    template_content = factory.LazyFunction(lambda: fake.text(max_nb_chars=500))
    variables = factory.LazyFunction(lambda: {'topic': 'string', 'style': 'string'})

    version = 1


class GlobalVariableFactory(factory.django.DjangoModelFactory):
    """全局变量工厂"""
    class Meta:
        model = GlobalVariable

    key = factory.Sequence(lambda n: f"variable_{n}")
    value = factory.LazyFunction(lambda: fake.word())
    variable_type = factory.Iterator(['string', 'number', 'boolean', 'object'])
    scope = factory.Iterator(['system', 'user'])
    group = factory.LazyFunction(lambda: fake.word())
    description = factory.LazyFunction(lambda: fake.sentence())
    created_by = None  # 可选字段
