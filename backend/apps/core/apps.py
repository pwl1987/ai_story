"""
Core应用配置
"""
from django.apps import AppConfig


class CoreConfig(AppConfig):
    """Core应用配置类"""
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.core'
    verbose_name = '系统核心功能'
