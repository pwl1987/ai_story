# Engines App Configuration
from django.apps import AppConfig


class EnginesConfig(AppConfig):
    """引擎配置管理 App"""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.engines"
    verbose_name = "引擎监控与配置"

    def ready(self):
        """App 启动时执行"""
        # 导入信号处理器（如果需要）
        pass
