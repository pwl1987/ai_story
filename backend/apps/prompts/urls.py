"""提示词管理URL路由"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import GlobalVariableViewSet, PromptTemplateSetViewSet, PromptTemplateViewSet

router = DefaultRouter()
router.register(r"sets", PromptTemplateSetViewSet, basename="prompttemplateset")
router.register(r"templates", PromptTemplateViewSet, basename="prompttemplate")
router.register(r"variables", GlobalVariableViewSet, basename="globalvariable")

urlpatterns = [
    path("", include(router.urls)),
]
