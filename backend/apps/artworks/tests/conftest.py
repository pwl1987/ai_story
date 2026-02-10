"""
角色资产批量生成测试 Fixtures
"""

import pytest
from django.contrib.auth import get_user_model

from apps.artworks.models import (
    Artwork,
    CharacterProfile,
)

User = get_user_model()


@pytest.fixture
def user(db):
    """创建测试用户"""
    return User.objects.create_user(
        username="test_user",
        email="test@example.com",
        password="testpass123",
    )


@pytest.fixture
def artwork(db):
    """创建测试作品"""
    User.objects.create_user(
        username="artwork_user",
        email="artwork@example.com",
        password="testpass123",
    )
    return Artwork.objects.create(
        title="测试作品",
        author="测试作者",
        artwork_type="novel",
    )


@pytest.fixture
def character(db, artwork):
    """创建测试角色"""
    return CharacterProfile.objects.create(
        artwork=artwork,
        name="test_char",
        display_name="测试角色",
        description="这是一个测试角色",
        appearance_count=10,
        dialogue_count=50,
    )
