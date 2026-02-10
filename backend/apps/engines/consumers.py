# Engines WebSocket Consumers - 引擎监控实时推送

import json
import logging

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer

from .models import EngineConfig
from .services import EngineMonitoringService

logger = logging.getLogger(__name__)


class EngineHealthConsumer(AsyncWebsocketConsumer):
    """
    引擎健康状态 WebSocket 消费者

    实时推送引擎健康状态变化。
    """

    async def connect(self):
        """建立 WebSocket 连接"""
        self.room_group_name = "engine_health"

        # 加入房间组
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)

        await self.accept()

        logger.info(f"WebSocket 连接已建立: {self.channel_name}")

        # 发送当前状态
        await self.send_current_status()

    async def disconnect(self, close_code):
        """断开 WebSocket 连接"""
        # 离开房间组
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

        logger.info(f"WebSocket 连接已断开: {self.channel_name} (code: {close_code})")

    async def receive(self, text_data):
        """
        接收客户端消息

        支持的命令:
        - {"action": "refresh"} - 刷新状态
        - {"action": "check", "engine_type": "llm"} - 检查指定引擎
        - {"action": "check_all"} - 检查所有引擎
        """
        try:
            data = json.loads(text_data)
            action = data.get("action")

            if action == "refresh":
                await self.send_current_status()

            elif action == "check":
                engine_type = data.get("engine_type")
                if engine_type:
                    await self.check_engine(engine_type)

            elif action == "check_all":
                await self.check_all_engines()

            else:
                await self.send_json(
                    {
                        "type": "error",
                        "message": f"未知操作: {action}",
                    }
                )

        except json.JSONDecodeError:
            await self.send_json(
                {
                    "type": "error",
                    "message": "无效的 JSON 格式",
                }
            )
        except Exception as e:
            logger.error(f"处理 WebSocket 消息时出错: {e}")
            await self.send_json(
                {
                    "type": "error",
                    "message": str(e),
                }
            )

    async def send_current_status(self):
        """发送当前所有引擎状态"""
        engines = await self.get_all_engines()

        status_data = {
            "type": "current_status",
            "timestamp": self._get_timestamp(),
            "engines": {
                engine.engine_type: {
                    "id": str(engine.id),
                    "name": engine.name,
                    "primary_provider": engine.primary_provider,
                    "fallback_provider": engine.fallback_provider,
                    "current_provider": engine.current_provider,
                    "health_status": engine.health_status,
                    "is_active": engine.is_active,
                    "total_requests": engine.total_requests,
                    "success_count": engine.success_count,
                    "failure_count": engine.failure_count,
                    "avg_response_time": engine.avg_response_time,
                    "total_cost": engine.total_cost,
                    "saved_cost": engine.saved_cost,
                    "last_health_check": engine.last_health_check.isoformat()
                    if engine.last_health_check
                    else None,
                }
                for engine in engines
            },
        }

        await self.send_json(status_data)

    async def check_engine(self, engine_type: str):
        """检查指定引擎并推送结果"""
        engine = await self.get_engine_by_type(engine_type)
        if not engine:
            await self.send_json(
                {
                    "type": "error",
                    "message": f"引擎类型不存在: {engine_type}",
                }
            )
            return

        # 执行健康检查
        result = await self.perform_health_check(engine)

        # 推送结果
        await self.send_json(
            {
                "type": "health_check_result",
                "timestamp": self._get_timestamp(),
                "engine_type": engine_type,
                "result": result,
            }
        )

    async def check_all_engines(self):
        """检查所有引擎并推送结果"""
        engines = await self.get_all_engines()
        results = {}

        for engine in engines:
            result = await self.perform_health_check(engine)
            results[engine.engine_type] = result

        await self.send_json(
            {
                "type": "health_check_results",
                "timestamp": self._get_timestamp(),
                "results": results,
            }
        )

    async def health_status_changed(self, engine_type: str, status: str):
        """
        健康状态变化时调用

        这个方法可以被其他服务调用，用于推送状态变化通知。

        Args:
            engine_type: 引擎类型
            status: 新状态
        """
        await self.send_json(
            {
                "type": "status_change",
                "timestamp": self._get_timestamp(),
                "engine_type": engine_type,
                "status": status,
            }
        )

    # ==================== 辅助方法 ====================

    @database_sync_to_async
    def get_all_engines(self):
        """获取所有引擎配置"""
        return list(EngineConfig.objects.filter(is_active=True))

    @database_sync_to_async
    def get_engine_by_type(self, engine_type: str):
        """根据类型获取引擎"""
        try:
            return EngineConfig.objects.get(engine_type=engine_type, is_active=True)
        except EngineConfig.DoesNotExist:
            return None

    @database_sync_to_async
    def perform_health_check(self, engine: EngineConfig):
        """执行健康检查"""
        return EngineMonitoringService.perform_health_check(engine)

    async def send_json(self, data: dict):
        """发送 JSON 数据"""
        await self.send(text_data=json.dumps(data))

    @staticmethod
    def _get_timestamp() -> str:
        """获取当前时间戳字符串"""
        from django.utils import timezone

        return timezone.now().isoformat()


# ==================== 广播辅助函数 ====================


async def broadcast_health_status(engine_type: str, status: str, result: dict = None):
    """
    向所有连接的客户端广播健康状态变化

    Args:
        engine_type: 引擎类型
        status: 新状态
        result: 健康检查结果 (可选)
    """
    from channels.layers import get_channel_layer

    channel_layer = get_channel_layer()
    if not channel_layer:
        logger.warning("Channel layer 不可用")
        return

    message = {
        "type": "health_status_update",
        "timestamp": EngineHealthConsumer._get_timestamp(),
        "engine_type": engine_type,
        "status": status,
        "result": result,
    }

    # 广播到引擎健康房间组
    await channel_layer.group_send(
        "engine_health",
        {
            "type": "broadcast",
            "message": message,
        },
    )


# ==================== Celery 任务结果推送 ====================


async def notify_health_check_complete(engine_type: str, result: dict):
    """
    健康检查完成后推送结果

    Args:
        engine_type: 引擎类型
        result: 检查结果
    """
    await broadcast_health_status(engine_type, result["status"], result)


async def notify_fallback_event(
    engine_type: str,
    from_provider: str,
    to_provider: str,
    reason: str,
):
    """
    推送 Fallback 事件通知

    Args:
        engine_type: 引擎类型
        from_provider: 源引擎
        to_provider: 目标引擎
        reason: 切换原因
    """
    from channels.layers import get_channel_layer

    channel_layer = get_channel_layer()
    if not channel_layer:
        return

    message = {
        "type": "fallback_event",
        "timestamp": EngineHealthConsumer._get_timestamp(),
        "engine_type": engine_type,
        "from_provider": from_provider,
        "to_provider": to_provider,
        "reason": reason,
    }

    await channel_layer.group_send(
        "engine_health",
        {
            "type": "broadcast",
            "message": message,
        },
    )
