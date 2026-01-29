"""配置包初始化"""

# 导入 Celery app，确保 Django 启动时加载 Celery
from .celery import app as celery_app

__all__ = ("celery_app",)
