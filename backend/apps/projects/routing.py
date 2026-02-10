"""
WebSocket路由配置
用于实时状态推送和Redis Pub/Sub订阅
"""

from django.urls import re_path

from . import consumers

websocket_urlpatterns = [
    # 单个阶段的WebSocket - 订阅特定阶段的Redis频道
    # ws://localhost:8000/ws/projects/{project_id}/stage/{stage_name}/
    re_path(
        r"ws/projects/(?P<project_id>[0-9a-f-]+)/stage/(?P<stage_name>[^/]+)/$",
        consumers.ProjectStageConsumer.as_asgi(),
    ),
    # 整个项目的WebSocket - 订阅项目所有阶段的Redis频道
    # ws://localhost:8000/ws/projects/{project_id}/
    re_path(r"ws/projects/(?P<project_id>[0-9a-f-]+)/$", consumers.ProjectConsumer.as_asgi()),
    # Story 11.4.2: 项目进度WebSocket - 专门用于前端进度组件
    # ws://localhost:8000/ws/projects/{project_id}/progress/
    re_path(
        r"ws/projects/(?P<project_id>[0-9a-f-]+)/progress/$",
        consumers.ProjectProgressConsumer.as_asgi(),
    ),
]
