"""
主URL配置
遵循REST API最佳实践
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from core.prometheus_metrics import metrics_view  # Epic 2优化: Prometheus指标导出

urlpatterns = [
    path('admin/', admin.site.urls),
    path('metrics/', metrics_view),  # Prometheus指标端点 (Epic 2优化)
    path('api/v1/health/', include('health.urls')),  # 健康检查端点 (Story 2.2)
    path('api/v1/projects/', include('apps.projects.urls')),
    path('api/v1/prompts/', include('apps.prompts.urls')),
    path('api/v1/models/', include('apps.models.urls')),
    path('api/v1/content/', include('apps.content.urls')),
    path('api/v1/users/', include('apps.users.urls')),
    path('api/mock/', include('apps.mock_api.urls')),
    path('api/v1/core/', include('apps.core.urls')),
]

# 开发环境下提供媒体文件访问
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
