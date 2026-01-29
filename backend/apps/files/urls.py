"""
文件管理URL路由
Epic 6: 文件管理与预览
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import FilePreviewView, FileUploadViewSet, PublicFileView

router = DefaultRouter()
router.register(r"", FileUploadViewSet, basename="uploaded-file")

urlpatterns = [
    # ViewSet路由
    path("", include(router.urls)),
    # 文件预览
    path("<uuid:pk>/preview/", FilePreviewView.as_view(), name="file-preview"),
    # 公开文件访问
    path("public/<str:file_hash>/", PublicFileView.as_view(), name="public-file"),
]
