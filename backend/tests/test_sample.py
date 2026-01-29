"""
示例测试文件

验证pytest配置正确
"""

import pytest
from django.test import TestCase


@pytest.mark.unit
class TestBasicSetup(TestCase):
    """
    基础设置测试

    验证测试框架已正确配置
    """

    def test_django_configured(self):
        """
        测试Django已正确配置
        """
        from django.conf import settings

        self.assertIsNotNone(settings)
        self.assertTrue(settings.configured)

    def test_database_available(self):
        """
        测试测试数据库可用
        """
        from django.db import connection

        cursor = connection.cursor()
        # 执行简单查询验证数据库连接
        cursor.execute("SELECT 1")
        result = cursor.fetchone()
        self.assertEqual(result[0], 1)


@pytest.mark.unit
def test_pytest_installed():
    """
    测试pytest已安装
    """
    import pytest

    assert pytest.__version__ is not None


@pytest.mark.django_db
def test_project_fixture(test_project):
    """
    测试项目fixture工作正常

    使用conftest.py中定义的test_project fixture
    """
    from apps.projects.models import Project

    assert test_project.name == "测试项目"
    assert test_project.description == "这是一个测试项目"
    assert test_project.id is not None

    # 验证可以从数据库查询
    retrieved = Project.objects.get(id=test_project.id)
    assert retrieved == test_project


@pytest.mark.unit
def test_sample_fixture(sample_project_data):
    """
    测试示例数据fixture
    """
    assert sample_project_data["name"] == "示例项目"
    assert "video_style" in sample_project_data
