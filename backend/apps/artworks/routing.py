"""
WebSocket路由配置 for Artworks应用

用于镜头生成进度实时推送
"""

from django.urls import re_path

from . import consumers

websocket_urlpatterns = [
    # 单个镜头重新生成的WebSocket - 订阅特定镜头的Redis频道
    # ws://localhost:8000/ws/artworks/shots/{shot_id}/regenerate/
    re_path(
        r"ws/artworks/shots/(?P<shot_id>\d+)/regenerate/$",
        consumers.ShotRegenerateConsumer.as_asgi(),
    ),
    # 批量镜头重新生成的WebSocket - 订阅批量任务的Redis频道
    # ws://localhost:8000/ws/artworks/batch-regenerate/{batch_id}/
    re_path(
        r"ws/artworks/batch-regenerate/(?P<batch_id>[^/]+)/$",
        consumers.BatchShotRegenerateConsumer.as_asgi(),
    ),
]
