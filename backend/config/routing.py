"""
WebSocket路由配置（中心化）

整合所有应用的WebSocket路由
"""

from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from django.core.asgi import get_asgi_application
from apps.projects.routing import websocket_urlpatterns

# WebSocket应用协议路由
application = ProtocolTypeRouter(
    {
        # WebSocket请求
        "websocket": AuthMiddlewareStack(URLRouter(websocket_urlpatterns)),
        # HTTP请求（回退到Django ASGI应用）
        "http": get_asgi_application(),
    }
)

# 导出所有WebSocket路由模式和应用
__all__ = ["websocket_urlpatterns", "application"]
