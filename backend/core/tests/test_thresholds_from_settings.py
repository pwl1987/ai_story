"""
单元测试: 验证监控阈值从settings读取
Epic 2优化：确保阈值可以通过环境变量配置
"""

from django.test import override_settings

from config.celery import _get_slow_task_threshold
from core.middleware.api_response_time import SLOW_REQUEST_THRESHOLD_MS


class TestThresholdsFromSettings:
    """
    测试监控阈值从settings读取
    Epic 2优化：阈值可以通过环境变量覆盖
    """

    def test_default_api_threshold(self):
        """测试默认API慢请求阈值"""
        # 默认值应该是500ms
        assert SLOW_REQUEST_THRESHOLD_MS == 500

    def test_default_celery_threshold(self):
        """测试默认Celery慢任务阈值"""
        # 默认值应该是60秒
        assert _get_slow_task_threshold() == 60

    @override_settings(SLOW_REQUEST_THRESHOLD_MS=1000)
    def test_custom_api_threshold_from_settings(self):
        """测试从settings读取自定义API阈值"""
        # 重新导入模块以获取新的settings值
        from importlib import reload

        import core.middleware.api_response_time as api_module

        reload(api_module)

        # 验证阈值已被覆盖
        assert api_module.SLOW_REQUEST_THRESHOLD_MS == 1000

    @override_settings(SLOW_TASK_THRESHOLD_S=120)
    def test_custom_celery_threshold_from_settings(self):
        """测试从settings读取自定义Celery阈值"""
        # 验证阈值已被覆盖
        assert _get_slow_task_threshold() == 120

    def test_threshold_values_are_positive(self):
        """测试阈值值为正数"""
        assert SLOW_REQUEST_THRESHOLD_MS > 0
        assert _get_slow_task_threshold() > 0

    def test_threshold_types_are_correct(self):
        """测试阈值类型正确"""
        assert isinstance(SLOW_REQUEST_THRESHOLD_MS, int)
        assert isinstance(_get_slow_task_threshold(), int)
