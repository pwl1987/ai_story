"""项目管理URL路由"""
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .sse_views import (
    ProjectAllStagesSSEView,
    ProjectStageSSEView,
)
from .views import ProjectModelConfigViewSet, ProjectStageViewSet, ProjectViewSet
from .views_progress_history import ProjectProgressHistoryViewSet

# 创建路由器
router = DefaultRouter()
router.register(r'', ProjectViewSet, basename='project')
router.register(r'stages', ProjectStageViewSet, basename='stage')
router.register(r'model-configs', ProjectModelConfigViewSet, basename='model-config')

# Epic 3: 进度历史路由 (使用简单路由,需要project_id前缀)
progress_history_router = DefaultRouter()
progress_history_router.register(
    r'(?P<project_id>[^/.]+)/progress-history',
    ProjectProgressHistoryViewSet,
    basename='progress-history'
)

urlpatterns = [
    path('', include(router.urls)),

    # Epic 3: 进度历史API端点
    path('', include(progress_history_router.urls)),

    path('sse/projects/<str:project_id>/stages/<str:stage_name>/',
         ProjectStageSSEView.as_view(),
         name='project-stage-sse'),
    path('sse/projects/<str:project_id>/',
         ProjectAllStagesSSEView.as_view(),
         name='project-all-stages-sse'),
]
