# Engines URL Configuration

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    EngineConfigViewSet,
    EngineHealthLogViewSet,
    EngineUsageLogViewSet,
    FallbackEventLogViewSet,
)

router = DefaultRouter()
router.register(r"", EngineConfigViewSet, basename="engineconfig")
router.register(r"health-logs", EngineHealthLogViewSet, basename="enginehealthlog")
router.register(r"usage-logs", EngineUsageLogViewSet, basename="engineusagelog")
router.register(r"fallback-events", FallbackEventLogViewSet, basename="fallbackeventlog")

urlpatterns = [
    path("", include(router.urls)),
]
