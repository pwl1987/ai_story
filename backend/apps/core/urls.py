"""
Core app URL配置
"""

from django.urls import path

from .api_views import LatestPercentileStatsView, PercentileStatsView
from .views import health_check, metrics

app_name = 'core'

urlpatterns = [
    path('health/', health_check, name='health_check'),
    path('metrics/', metrics, name='prometheus_metrics'),
    # Epic 2优化: 百分位数统计端点
    path('percentile-stats/', PercentileStatsView.as_view(), name='percentile_stats'),
    path('percentile-stats/latest/', LatestPercentileStatsView.as_view(), name='latest_percentile_stats'),
]
