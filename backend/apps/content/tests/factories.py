"""
测试数据工厂 - apps/content模块
使用Factory Boy创建测试数据，遵循DRY原则
"""

import uuid

import factory
from django.contrib.auth import get_user_model
from faker import Faker

from apps.content.models import (
    CameraMovement,
    ContentRewrite,
    GeneratedImage,
    GeneratedVideo,
    Storyboard,
)
from apps.projects.tests.factories import ProjectFactory

User = get_user_model()
fake = Faker(["zh_CN"])


class ContentRewriteFactory(factory.django.DjangoModelFactory):
    """
    文案改写工厂
    职责: 创建ContentRewrite测试数据
    遵循单一职责原则(SRP)
    """

    class Meta:
        model = ContentRewrite

    id = factory.LazyFunction(uuid.uuid4)
    project = factory.SubFactory(ProjectFactory)

    original_text = factory.LazyFunction(lambda: fake.text(max_nb_chars=500))
    rewritten_text = factory.LazyFunction(lambda: fake.text(max_nb_chars=500))

    model_provider = None  # 设为None，避免关联
    prompt_used = factory.LazyFunction(lambda: fake.sentence())

    generation_metadata = factory.LazyFunction(dict)  # 默认空dict


class StoryboardFactory(factory.django.DjangoModelFactory):
    """
    分镜工厂
    职责: 创建Storyboard测试数据
    遵循单一职责原则(SRP)
    """

    class Meta:
        model = Storyboard

    id = factory.LazyFunction(uuid.uuid4)
    project = factory.SubFactory(ProjectFactory)

    sequence_number = factory.Sequence(lambda n: n + 1)
    scene_description = factory.LazyFunction(lambda: fake.sentence())
    narration_text = factory.LazyFunction(lambda: fake.paragraph(nb_sentences=3))
    image_prompt = factory.LazyFunction(lambda: fake.paragraph(nb_sentences=5))

    duration_seconds = 3.0  # 固定默认值，避免浮点精度问题


class GeneratedImageFactory(factory.django.DjangoModelFactory):
    """
    生成图片工厂
    职责: 创建GeneratedImage测试数据
    遵循单一职责原则(SRP)
    """

    class Meta:
        model = GeneratedImage

    id = factory.LazyFunction(uuid.uuid4)
    storyboard = factory.SubFactory(StoryboardFactory)

    image_url = factory.LazyFunction(lambda: fake.url())
    thumbnail_url = factory.LazyFunction(lambda: fake.url())

    generation_params = factory.LazyFunction(
        lambda: {"width": 1024, "height": 1024, "steps": fake.random_int(min=20, max=50)}
    )

    model_provider = None  # 设为None，避免关联

    status = "pending"
    retry_count = 0

    file_size = factory.LazyFunction(lambda: fake.random_int(min=100000, max=5000000))
    width = 1024
    height = 1024


class CameraMovementFactory(factory.django.DjangoModelFactory):
    """
    运镜工厂
    职责: 创建CameraMovement测试数据
    遵循单一职责原则(SRP)
    """

    class Meta:
        model = CameraMovement

    id = factory.LazyFunction(uuid.uuid4)
    storyboard = factory.SubFactory(StoryboardFactory)

    movement_type = factory.Iterator(["static", "zoom_in", "zoom_out", "pan_left", "pan_right"])

    movement_params = factory.LazyFunction(
        lambda: {
            "intensity": fake.pyfloat(min_value=0.1, max_value=1.0, right_digits=2),
            "duration": fake.pyfloat(min_value=1.0, max_value=5.0, right_digits=1),
        }
    )

    model_provider = None  # 设为None，避免关联
    prompt_used = factory.LazyFunction(lambda: fake.sentence())


class GeneratedVideoFactory(factory.django.DjangoModelFactory):
    """
    生成视频工厂
    职责: 创建GeneratedVideo测试数据
    遵循单一职责原则(SRP)
    """

    class Meta:
        model = GeneratedVideo

    id = factory.LazyFunction(uuid.uuid4)
    storyboard = factory.SubFactory(StoryboardFactory)

    image = factory.SubFactory(GeneratedImageFactory)
    camera_movement = factory.SubFactory(CameraMovementFactory)

    video_url = factory.LazyFunction(lambda: fake.url())
    thumbnail_url = factory.LazyFunction(lambda: fake.url())

    duration = factory.LazyFunction(
        lambda: fake.pyfloat(min_value=2.0, max_value=10.0, right_digits=1)
    )
    width = 1080
    height = 1920
    fps = 24
    file_size = factory.LazyFunction(lambda: fake.random_int(min=1000000, max=50000000))

    model_provider = None  # 设为None，避免关联

    generation_params = factory.LazyFunction(
        lambda: {"duration": 3.0, "fps": 24, "quality": "high"}
    )

    status = "pending"
    retry_count = 0
