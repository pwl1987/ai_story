"""
健康检查URL配置
"""
from django.urls import path

from health.views import HealthCheckView, PrometheusMetricsView

app_name = 'health'

urlpatterns = [
    path('', HealthCheckView.as_view(), name='health-check'),
    path('metrics/', PrometheusMetricsView.as_view(), name='prometheus-metrics'),
]
