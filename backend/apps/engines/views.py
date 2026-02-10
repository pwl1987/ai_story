# Engines Views - 引擎配置 API 视图

import logging

from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import (
    EngineConfig,
    EngineHealthLog,
    EngineUsageLog,
    FallbackEventLog,
)
from .serializers import (
    EngineConfigCreateSerializer,
    EngineConfigSerializer,
    EngineHealthLogSerializer,
    EngineStatsSerializer,
    EngineUsageLogSerializer,
    FallbackEventLogSerializer,
    HealthCheckTriggerSerializer,
)
from .services import (
    HealthCheckService,
)

logger = logging.getLogger(__name__)


class EngineConfigViewSet(viewsets.ModelViewSet):
    """引擎配置 ViewSet"""

    permission_classes = [IsAuthenticated]
    lookup_field = "engine_type"

    def get_queryset(self):
        """获取查询集"""
        return EngineConfig.objects.select_related().order_by("engine_type")

    def get_serializer_class(self):
        """根据操作返回不同的序列化器"""
        if self.action == "create":
            return EngineConfigCreateSerializer
        return EngineConfigSerializer

    @action(detail=False, methods=["get"])
    def stats(self, request):
        """
        获取引擎统计信息

        GET /api/v1/engines/stats/
        """
        engines = self.get_queryset()

        stats_data = []
        for engine in engines:
            # 获取今日请求数
            today = timezone.now().date()
            today_logs = EngineUsageLog.objects.filter(
                engine=engine, created_at__date=today
            ).count()

            # 获取本周请求数
            from datetime import timedelta

            week_ago = timezone.now() - timedelta(days=7)
            week_logs = EngineUsageLog.objects.filter(
                engine=engine, created_at__gte=week_ago
            ).count()

            # 获取本月请求数
            month_ago = timezone.now() - timedelta(days=30)
            month_logs = EngineUsageLog.objects.filter(
                engine=engine, created_at__gte=month_ago
            ).count()

            stats_data.append(
                {
                    "engine_type": engine.engine_type,
                    "engine_name": engine.name,
                    "total_requests": engine.total_requests,
                    "success_count": engine.success_count,
                    "failure_count": engine.failure_count,
                    "success_rate": engine.calculate_success_rate(),
                    "avg_response_time": engine.avg_response_time,
                    "total_cost": float(engine.total_cost),
                    "saved_cost": float(engine.saved_cost),
                    "today_requests": today_logs,
                    "week_requests": week_logs,
                    "month_requests": month_logs,
                }
            )

        serializer = EngineStatsSerializer(stats_data, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["post"])
    def check_health(self, request):
        """
        手动触发健康检查

        POST /api/v1/engines/check_health/
        Body: {"engine_type": "llm"}  # 可选，不传则检查所有
        """
        serializer = HealthCheckTriggerSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        engine_type = serializer.validated_data.get("engine_type")

        from .tasks import manual_health_check_task

        # 异步执行健康检查
        task = manual_health_check_task.delay(engine_type=engine_type)

        return Response(
            {
                "message": "健康检查已启动",
                "task_id": task.id,
                "engine_type": engine_type or "全部",
            },
            status=status.HTTP_202_ACCEPTED,
        )

    @action(detail=True, methods=["post"])
    def test_connection(self, request, engine_type=None):
        """
        测试引擎连接

        POST /api/v1/engines/{engine_type}/test_connection/
        """
        try:
            engine = self.get_object()
            service = HealthCheckService(engine)
            result = service.check()

            return Response(
                {
                    "success": result["status"] == "online",
                    "status": result["status"],
                    "response_time": result.get("response_time"),
                    "error_message": result.get("error_message", ""),
                }
            )
        except Exception as e:
            logger.error(f"测试引擎连接失败: {e}")
            return Response(
                {
                    "success": False,
                    "error": str(e),
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=True, methods=["post"])
    def reset_stats(self, request, engine_type=None):
        """
        重置引擎统计

        POST /api/v1/engines/{engine_type}/reset_stats/
        """
        engine = self.get_object()

        # 重置统计字段
        engine.total_requests = 0
        engine.success_count = 0
        engine.failure_count = 0
        engine.avg_response_time = 0
        engine.total_cost = 0
        engine.saved_cost = 0
        engine.save(
            update_fields=[
                "total_requests",
                "success_count",
                "failure_count",
                "avg_response_time",
                "total_cost",
                "saved_cost",
            ]
        )

        return Response({"message": f"引擎 {engine.name} 统计已重置"})

    @action(detail=True, methods=["post"])
    def switch_provider(self, request, engine_type=None):
        """
        手动切换引擎提供商

        POST /api/v1/engines/{engine_type}/switch_provider/
        Body: {"provider": "ollama"}
        """
        engine = self.get_object()
        provider = request.data.get("provider")

        if not provider:
            return Response({"error": "请指定要切换的提供商"}, status=status.HTTP_400_BAD_REQUEST)

        if provider not in [engine.primary_provider, engine.fallback_provider]:
            return Response(
                {"error": "只能切换到主引擎或备份引擎"}, status=status.HTTP_400_BAD_REQUEST
            )

        from_provider = engine.current_provider or engine.primary_provider

        # 手动切换
        engine.current_provider = provider
        engine.health_status = "unknown"
        engine.failure_count = 0
        engine.save(update_fields=["current_provider", "health_status", "failure_count"])

        # 记录切换事件
        FallbackEventLog.objects.create(
            engine=engine,
            from_provider=from_provider,
            to_provider=provider,
            reason="manual",
            reason_detail="手动切换",
            affected_requests=0,
        )

        return Response(
            {
                "message": f"已切换到 {provider}",
                "current_provider": provider,
            }
        )

    @action(detail=True, methods=["get"])
    def health_history(self, request, engine_type=None):
        """
        获取引擎健康历史

        GET /api/v1/engines/{engine_type}/health_history/?limit=10
        """
        engine = self.get_object()
        limit = int(request.query_params.get("limit", 10))

        logs = EngineHealthLog.objects.filter(engine=engine).order_by("-checked_at")[:limit]

        serializer = EngineHealthLogSerializer(logs, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["get"])
    def usage_logs(self, request, engine_type=None):
        """
        获取引擎使用日志

        GET /api/v1/engines/{engine_type}/usage_logs/?limit=20
        """
        engine = self.get_object()
        limit = int(request.query_params.get("limit", 20))

        logs = (
            EngineUsageLog.objects.filter(engine=engine)
            .select_related("engine")
            .order_by("-created_at")[:limit]
        )

        serializer = EngineUsageLogSerializer(logs, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["get"])
    def fallback_events(self, request, engine_type=None):
        """
        获取 Fallback 事件历史

        GET /api/v1/engines/{engine_type}/fallback_events/?limit=10
        """
        engine = self.get_object()
        limit = int(request.query_params.get("limit", 10))

        events = FallbackEventLog.objects.filter(engine=engine).order_by("-switched_at")[:limit]

        serializer = FallbackEventLogSerializer(events, many=True)
        return Response(serializer.data)


class EngineHealthLogViewSet(viewsets.ReadOnlyModelViewSet):
    """引擎健康日志 ViewSet（只读）"""

    permission_classes = [IsAuthenticated]
    serializer_class = EngineHealthLogSerializer

    def get_queryset(self):
        """获取查询集"""
        queryset = EngineHealthLog.objects.select_related("engine").order_by("-checked_at")

        engine_type = self.request.query_params.get("engine_type")
        if engine_type:
            queryset = queryset.filter(engine__engine_type=engine_type)

        # 按引擎分组，只返回每个引擎的最新记录
        limit = int(self.request.query_params.get("limit", 100))
        return queryset[:limit]


class EngineUsageLogViewSet(viewsets.ReadOnlyModelViewSet):
    """引擎使用日志 ViewSet（只读）"""

    permission_classes = [IsAuthenticated]
    serializer_class = EngineUsageLogSerializer

    def get_queryset(self):
        """获取查询集"""
        queryset = EngineUsageLog.objects.select_related("engine").order_by("-created_at")

        engine_type = self.request.query_params.get("engine_type")
        if engine_type:
            queryset = queryset.filter(engine__engine_type=engine_type)

        success = self.request.query_params.get("success")
        if success is not None:
            queryset = queryset.filter(success=success.lower() == "true")

        # 按引擎分组，只返回每个引擎的最新记录
        limit = int(self.request.query_params.get("limit", 100))
        return queryset[:limit]


class FallbackEventLogViewSet(viewsets.ReadOnlyModelViewSet):
    """Fallback 事件日志 ViewSet（只读）"""

    permission_classes = [IsAuthenticated]
    serializer_class = FallbackEventLogSerializer

    def get_queryset(self):
        """获取查询集"""
        queryset = FallbackEventLog.objects.select_related("engine").order_by("-switched_at")

        engine_type = self.request.query_params.get("engine_type")
        if engine_type:
            queryset = queryset.filter(engine__engine_type=engine_type)

        reason = self.request.query_params.get("reason")
        if reason:
            queryset = queryset.filter(reason=reason)

        # 按引擎分组，只返回每个引擎的最新记录
        limit = int(self.request.query_params.get("limit", 100))
        return queryset[:limit]
