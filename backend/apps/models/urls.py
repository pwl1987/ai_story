"""模型管理URL路由"""
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import ModelProviderViewSet, ModelUsageLogViewSet

# 创建路由器
router = DefaultRouter()
router.register(r'providers', ModelProviderViewSet, basename='model-provider')
router.register(r'usage-logs', ModelUsageLogViewSet, basename='usage-log')

urlpatterns = [
    path('', include(router.urls)),
]
