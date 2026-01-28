"""
ASGI配置
用于异步Web服务器和WebSocket
"""

import os

from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application

from apps.projects.routing import websocket_urlpatterns

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')

# 初始化Django ASGI应用
django_asgi_app = get_asgi_application()

# WebSocket路由配置
websocket_application = AuthMiddlewareStack(
    URLRouter(
        websocket_urlpatterns
    )
)

# 支持HTTP和WebSocket协议
application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": websocket_application,
})
