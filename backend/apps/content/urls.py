"""内容生成URL路由"""
from django.urls import path

from .views import StorageImageDetailView, StorageImageListView, StorageVideoDetailView

urlpatterns = [
    # Storage图片API
    path('storage/image/', StorageImageListView.as_view(), name='storage-image-list'),
    # 支持日期子目录: storage/image/2025-11-30/xx.png
    path('storage/image/<path:filepath>', StorageImageDetailView.as_view(), name='storage-image-detail'),
    # 支持日期子目录: storage/video/2025-11-30/xx.mp4
    path('storage/video/<path:filepath>', StorageVideoDetailView.as_view(), name='storage-video-detail'),

    # 内容生成API
    # 待实现
]
