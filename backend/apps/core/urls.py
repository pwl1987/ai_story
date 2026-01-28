"""
Core app URL配置
"""

from django.urls import path
from .views import health_check
from .api_views import PercentileStatsView, LatestPercentileStatsView

app_name = 'core'

urlpatterns = [
    path('health/', health_check, name='health_check'),
    # Epic 2优化: 百分位数统计端点
    path('percentile-stats/', PercentileStatsView.as_view(), name='percentile_stats'),
    path('percentile-stats/latest/', LatestPercentileStatsView.as_view(), name='latest_percentile_stats'),
]
