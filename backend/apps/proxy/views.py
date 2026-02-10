"""
代理配置API视图
Story 9.8: 前端代理选择器
Story 9.9: 测试连接功能
"""

import logging
import time

import httpx
from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import ProxyConfig
from .serializers import ProxySelectSerializer

logger = logging.getLogger(__name__)


class ProxySelectViewSet(viewsets.ReadOnlyModelViewSet):
    """
    代理选择器ViewSet - 用于前端下拉框
    Story 9.8: 只返回is_active=True且is_healthy=True的代理
    """

    serializer_class = ProxySelectSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """只返回启用且健康的代理"""
        return ProxyConfig.objects.filter(is_active=True, is_healthy=True).order_by("name")


class TestConnectionView(APIView):
    """
    测试代理连接视图
    Story 9.9: 测试代理连接是否可用
    """

    permission_classes = [IsAuthenticated]

    def post(self, request, pk=None):
        """
        测试代理连接

        测试流程：
        1. 获取代理配置
        2. 尝试通过代理访问 https://httpbin.org/ip
        3. 返回测试结果（IP地址、响应时间）
        """
        try:
            # 获取代理配置
            proxy_config = ProxyConfig.objects.get(pk=pk)
        except ProxyConfig.DoesNotExist:
            return Response(
                {"success": False, "error": "代理配置不存在"},
                status=status.HTTP_404_NOT_FOUND,
            )

        # 检查代理是否启用
        if not proxy_config.is_active:
            return Response(
                {"success": False, "error": "代理未启用"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # 测试连接
        start_time = time.time()
        try:
            # 获取代理URL
            proxy_url = proxy_config.get_proxy_url()

            # 发送测试请求
            with httpx.Client(timeout=5.0) as client:
                response = client.get(
                    "https://httpbin.org/ip",
                    proxies={"all://": proxy_url},
                )
                response.raise_for_status()

            # 计算响应时间
            response_time_ms = int((time.time() - start_time) * 1000)

            # 解析响应
            result = response.json()
            origin_ip = result.get("origin", "")

            # 更新代理健康状态
            proxy_config.is_healthy = True
            proxy_config.save(update_fields=["is_healthy"])

            # 返回成功结果
            return Response(
                {
                    "success": True,
                    "ip": origin_ip,
                    "response_time_ms": response_time_ms,
                }
            )

        except httpx.TimeoutException:
            # 超时错误
            logger.warning(f"Proxy connection timeout: {proxy_config.name}")
            proxy_config.is_healthy = False
            proxy_config.save(update_fields=["is_healthy"])

            return Response(
                {"success": False, "error": "Connection timeout"},
                status=status.HTTP_200_OK,  # 返回200但success=False
            )

        except httpx.HTTPStatusError as e:
            # HTTP错误
            logger.warning(f"Proxy HTTP error: {proxy_config.name} - {e}")
            proxy_config.is_healthy = False
            proxy_config.save(update_fields=["is_healthy"])

            return Response(
                {"success": False, "error": f"HTTP error: {e.response.status_code}"},
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            # 其他错误
            logger.error(f"Proxy connection error: {proxy_config.name} - {e}", exc_info=True)
            proxy_config.is_healthy = False
            proxy_config.save(update_fields=["is_healthy"])

            return Response(
                {"success": False, "error": str(e)},
                status=status.HTTP_200_OK,
            )
