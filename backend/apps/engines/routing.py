# Engines WebSocket Routing - 引擎监控 WebSocket 路由

from django.urls import re_path

from .consumers import EngineHealthConsumer

websocket_urlpatterns = [
    re_path(r"^ws/engines/health/$", EngineHealthConsumer.as_asgi()),
]
