"""
WebSocket路由配置（中心化）

整合所有应用的WebSocket路由
"""

from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application

from apps.projects.routing import websocket_urlpatterns as projects_ws_patterns
from apps.artworks.routing import websocket_urlpatterns as artworks_ws_patterns
from apps.engines.routing import websocket_urlpatterns as engines_ws_patterns

# 合并所有应用的WebSocket路由
websocket_urlpatterns = projects_ws_patterns + artworks_ws_patterns + engines_ws_patterns

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
__all__ = ["application", "websocket_urlpatterns"]
