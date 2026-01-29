"""
WebSocket路由配置（中心化）

整合所有应用的WebSocket路由
"""

from apps.projects.routing import websocket_urlpatterns

# 导出所有WebSocket路由模式
__all__ = ["websocket_urlpatterns"]
