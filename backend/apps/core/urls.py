"""
Core app URL配置
"""

from django.urls import path
from .views import health_check

app_name = 'core'

urlpatterns = [
    path('health/', health_check, name='health_check'),
]
