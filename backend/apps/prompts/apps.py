"""提示词应用配置"""

from django.apps import AppConfig


class PromptsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.prompts"
    verbose_name = "提示词管理"
