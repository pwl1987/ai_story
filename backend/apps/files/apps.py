"""
Files App配置
Epic 6: 文件管理与预览
"""

from django.apps import AppConfig


class FilesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.files"
    verbose_name = "文件管理"

    def ready(self):
        """应用启动时的初始化逻辑"""
        # 导入信号处理器（如果需要）
        pass
