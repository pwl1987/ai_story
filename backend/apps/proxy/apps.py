from django.apps import AppConfig


class ProxyConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.proxy"
    verbose_name = "Proxy Management"

    def ready(self):
        """
        App initialization hook.
        TODO (Story 9.10): Initialize Celery Beat health check task
        """
        pass
