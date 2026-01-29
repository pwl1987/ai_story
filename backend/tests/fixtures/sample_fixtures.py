"""
示例测试fixtures

演示如何创建自定义fixtures
"""

import pytest
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.fixture
def test_user(db):
    """
    创建测试用户

    用法:
        def test_user_profile(test_user):
            assert test_user.username == 'testuser'
    """
    user = User.objects.create_user(
        username="testuser", email="test@example.com", password="testpass123"
    )
    return user


@pytest.fixture
def authenticated_client(client, test_user):
    """
    已认证的测试客户端

    用法:
        def test_authenticated_request(authenticated_client):
            response = authenticated_client.get('/api/v1/protected/')
            assert response.status_code == 200
    """
    client.force_login(test_user)
    return client


@pytest.fixture
def sample_project_data():
    """
    示例项目数据fixture

    返回不依赖数据库的测试数据
    """
    return {
        "name": "示例项目",
        "description": "这是一个示例项目描述",
        "story_idea": "一个关于AI的故事",
        "video_style": "科幻风格",
    }


@pytest.fixture
def mock_ai_text_response():
    """
    Mock LLM文本生成响应
    """
    return {"text": "这是AI生成的文本内容", "tokens_used": 100, "model": "gpt-4", "success": True}


@pytest.fixture
def mock_image_generation_response():
    """
    Mock文生图响应
    """
    return {
        "image_url": "https://example.com/generated/image.png",
        "prompt_used": "测试提示词",
        "model": "stable-diffusion-v1.5",
        "success": True,
    }


@pytest.fixture
def mock_video_generation_response():
    """
    Mock图生视频响应
    """
    return {
        "video_url": "https://example.com/generated/video.mp4",
        "duration": 5.0,
        "model": "runway-gen2",
        "success": True,
    }


# 数据库fixture示例
@pytest.fixture
def multiple_test_projects(db):
    """
    创建多个测试项目

    用于批量测试
    """
    from apps.projects.models import Project

    projects = []
    for i in range(3):
        project = Project.objects.create(
            name=f"测试项目{i}",
            description=f"这是第{i}个测试项目",
            story_idea=f"故事创意{i}",
            video_style=f"风格{i}",
        )
        projects.append(project)

    return projects


@pytest.fixture
def sample_prompt_template(db):
    """
    示例提示词模板fixture
    """
    from apps.prompts.models import PromptTemplate

    template_set = PromptTemplate.objects.create(name="测试模板集", description="用于测试的模板集")

    template = PromptTemplate.objects.create(
        template_set=template_set,
        stage="rewrite",
        name="测试文案改写模板",
        template_content="这是{{ variable }}测试模板",
        variables=["variable"],
    )

    return template
