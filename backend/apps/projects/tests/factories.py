"""
测试数据工厂
使用Factory Boy创建测试数据
遵循单一职责原则(SRP)
"""

import uuid

import factory
from django.contrib.auth import get_user_model
from faker import Faker

from apps.projects.models import Project, ProjectModelConfig, ProjectStage

User = get_user_model()
fake = Faker(['zh_CN'])


class UserFactory(factory.django.DjangoModelFactory):
    """用户工厂"""

    class Meta:
        model = User
        django_get_or_create = ('username',)

    username = factory.Sequence(lambda n: f"user{n}")
    email = factory.LazyAttribute(lambda obj: f"{obj.username}@example.com")
    is_active = True


class ProjectFactory(factory.django.DjangoModelFactory):
    """项目工厂"""

    class Meta:
        model = Project

    id = factory.LazyFunction(uuid.uuid4)
    name = factory.LazyFunction(lambda: fake.sentence(nb_words=4)[:-1])
    description = factory.LazyFunction(lambda: fake.text(max_nb_chars=200))
    original_topic = factory.LazyFunction(lambda: fake.sentence(nb_words=10))

    status = 'draft'
    jianying_draft_path = ''

    user = factory.SubFactory(UserFactory)
    prompt_template_set = None  # 可选字段,设为None


class ProjectStageFactory(factory.django.DjangoModelFactory):
    """项目阶段工厂"""

    class Meta:
        model = ProjectStage

    id = factory.LazyFunction(uuid.uuid4)
    project = factory.SubFactory(ProjectFactory)

    stage_type = 'rewrite'
    status = 'pending'

    input_data = {}
    output_data = {}

    retry_count = 0
    max_retries = 3
    error_message = ''


class ProjectModelConfigFactory(factory.django.DjangoModelFactory):
    """项目模型配置工厂"""

    class Meta:
        model = ProjectModelConfig

    id = factory.LazyFunction(uuid.uuid4)
    project = factory.SubFactory(ProjectFactory)

    load_balance_strategy = 'weighted'
