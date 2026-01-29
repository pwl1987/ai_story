"""
pytest配置文件

定义全局fixtures和pytest钩子
"""

import os
import sys
import importlib.util
from pathlib import Path

# 添加项目根目录到Python路径
backend_root = Path(__file__).parent.parent
sys.path.insert(0, str(backend_root))

# 设置Django设置模块
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')


import django
import pytest
from django.conf import settings

# 确保Django已设置
if not settings.configured:
    django.setup()


@pytest.fixture(scope='session')
def django_db_setup():
    """
    会话级别的数据库设置

    在所有测试运行前执行一次
    """
    settings.DATABASES['default'] = {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }


@pytest.fixture(autouse=True)
def clear_prometheus_registry():
    """
    自动清理Prometheus CollectorRegistry

    解决"ValueError: Duplicated timeseries in CollectorRegistry"问题
    在每个测试前自动清理注册的指标
    """
    # 测试开始前清理Prometheus指标
    if importlib.util.find_spec('prometheus_client'):
        from prometheus_client import REGISTRY
        # 清理所有收集器
        collectors = list(REGISTRY._collector_to_names.keys())
        for collector in collectors:
            REGISTRY.unregister(collector)

    yield

    # 测试结束后再次清理，防止残留
    if importlib.util.find_spec('prometheus_client'):
        from prometheus_client import REGISTRY
        collectors = list(REGISTRY._collector_to_names.keys())
        for collector in collectors:
            try:
                REGISTRY.unregister(collector)
            except Exception:
                pass  # 忽略清理错误



@pytest.fixture
def test_project(db):
    """
    创建测试项目的fixture

    用于测试项目管理功能
    """
    from django.contrib.auth import get_user_model

    from apps.projects.models import Project

    User = get_user_model()

    # 创建测试用户
    user = User.objects.create_user(
        username='testuser',
        email='test@example.com'
    )

    project = Project.objects.create(
        name='测试项目',
        description='这是一个测试项目',
        original_topic='测试原始主题',
        user=user  # 添加必需的user字段
    )
    return project


@pytest.fixture
def sample_project_data():
    """
    提供示例项目数据的fixture

    用于测试项目数据结构
    """
    return {
        'name': '示例项目',
        'description': '这是一个示例项目',
        'original_topic': '示例原始主题',
        'video_style': '示例风格',
        'target_duration': 60,
    }


@pytest.fixture
def mock_ai_response(monkeypatch):
    """
    Mock AI API响应的fixture

    用于离线测试AI客户端功能
    """
    def mock_generate(*args, **kwargs):
        return {
            'text': '这是Mock AI生成的文本',
            'success': True
        }

    return mock_generate


@pytest.fixture
def temp_media_root(tmp_path, settings):
    """
    临时媒体目录fixture

    用于测试文件上传和生成
    """
    settings.MEDIA_ROOT = str(tmp_path / 'media')
    settings.MEDIA_URL = '/media/'
    return settings.MEDIA_ROOT


@pytest.fixture
def enable_mock_ai(monkeypatch):
    """
    启用Mock AI客户端的fixture

    设置环境变量以启用Mock AI
    """
    monkeypatch.setenv('ENABLE_MOCK_AI', 'true')
    return True


def pytest_configure(config):
    """
    pytest配置钩子

    注册自定义标记
    """
    config.addinivalue_line(
        'markers', 'slow: 标记运行较慢的测试'
    )
    config.addinivalue_line(
        'markers', 'integration: 标记集成测试'
    )
    config.addinivalue_line(
        'markers', 'unit: 标记单元测试'
    )
