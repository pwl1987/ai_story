"""
WebSocket消费者 for Artworks应用

职责: 订阅镜头生成进度，实时推送给前端
"""

import json
import logging

from channels.generic.websocket import AsyncWebsocketConsumer

logger = logging.getLogger(__name__)


class ShotRegenerateConsumer(AsyncWebsocketConsumer):
    """
    镜头重新生成进度WebSocket消费者

    WebSocket URL: ws://localhost:8000/ws/artworks/shots/{shot_id}/regenerate/

    订阅Redis频道: shot_{shot_id}:regenerate

    消息格式:
    {
        "type": "progress",
        "progress": 50,
        "message": "正在生成图像..."
    }
    """

    async def connect(self):
        """建立WebSocket连接"""
        self.shot_id = self.scope["url_route"]["kwargs"]["shot_id"]
        self.channel_name = f"shot_{self.shot_id}_regenerate"

        # Redis频道名称（与regenerate_shot_content任务中使用的保持一致）
        # RedisStreamPublisher使用的格式: ai_story:project:{project_id}:stage:{stage_name}
        # 任务中传入: RedisStreamPublisher(f"shot_{shot_id}", "regenerate")
        # 所以频道是: ai_story:project:shot_{shot_id}:stage:regenerate
        self.redis_channel = f"ai_story:project:shot_{self.shot_id}:stage:regenerate"

        # 接受连接
        await self.accept()

        logger.info(f"WebSocket连接建立: shot_id={self.shot_id}, channel={self.channel_name}")
        logger.info(f"订阅Redis频道: {self.redis_channel}")

        # 发送连接确认消息
        await self.send_json(
            {
                "type": "connected",
                "shot_id": self.shot_id,
                "message": "已连接到镜头生成进度频道",
                "redis_channel": self.redis_channel,
            }
        )

    async def disconnect(self, close_code):
        """断开WebSocket连接"""
        logger.info(f"WebSocket连接断开: shot_id={self.shot_id}, code={close_code}")

    async def receive(self, text_data):
        """
        接收来自客户端的消息

        支持的消息类型:
        - ping: 心跳检测
        """
        try:
            data = json.loads(text_data) if isinstance(text_data, str) else text_data

            message_type = data.get("type")

            if message_type == "ping":
                # 心跳响应
                await self.send_json({"type": "pong", "timestamp": data.get("timestamp")})
            else:
                logger.warning(f"未知的消息类型: {message_type}")

        except json.JSONDecodeError as e:
            logger.error(f"JSON解析错误: {e}")
        except Exception as e:
            logger.error(f"处理消息时发生错误: {e}")

    async def shot_progress(self, event):
        """
        接收来自Redis的进度消息并转发到WebSocket客户端

        这个方法由Channels框架调用，当Redis频道收到消息时触发
        """
        # 转发消息到客户端
        await self.send_json(
            {
                "type": event.get("type", "progress"),
                "shot_id": self.shot_id,
                "progress": event.get("progress", 0),
                "message": event.get("message", ""),
                "data": event.get("data", {}),
            }
        )

    async def send_json(self, data):
        """发送JSON格式的消息"""
        await self.send(text_data=json.dumps(data, ensure_ascii=False))


class BatchShotRegenerateConsumer(AsyncWebsocketConsumer):
    """
    批量镜头重新生成进度WebSocket消费者

    WebSocket URL: ws://localhost:8000/ws/artworks/batch-regenerate/{batch_id}/

    订阅Redis频道: batch_{batch_id}:regenerate

    消息格式:
    {
        "type": "batch_progress",
        "total": 5,
        "completed": 2,
        "failed": 0,
        "current_shot_id": 123,
        "message": "正在生成第3/5个镜头..."
    }
    """

    async def connect(self):
        """建立WebSocket连接"""
        self.batch_id = self.scope["url_route"]["kwargs"]["batch_id"]
        self.channel_name = f"batch_{self.batch_id}_regenerate"
        self.redis_channel = f"batch_{self.batch_id}:regenerate"

        await self.accept()

        logger.info(f"批量生成WebSocket连接建立: batch_id={self.batch_id}")

        await self.send_json(
            {"type": "connected", "batch_id": self.batch_id, "message": "已连接到批量生成进度频道"}
        )

    async def disconnect(self, close_code):
        """断开WebSocket连接"""
        logger.info(f"批量生成WebSocket连接断开: batch_id={self.batch_id}, code={close_code}")

    async def receive(self, text_data):
        """接收来自客户端的消息"""
        try:
            data = json.loads(text_data) if isinstance(text_data, str) else text_data

            if data.get("type") == "ping":
                await self.send_json({"type": "pong", "timestamp": data.get("timestamp")})

        except json.JSONDecodeError as e:
            logger.error(f"JSON解析错误: {e}")

    async def batch_progress(self, event):
        """接收来自Redis的批量进度消息并转发到客户端"""
        await self.send_json(
            {
                "type": "batch_progress",
                "batch_id": self.batch_id,
                "total": event.get("total", 0),
                "completed": event.get("completed", 0),
                "failed": event.get("failed", 0),
                "current_shot_id": event.get("current_shot_id"),
                "message": event.get("message", ""),
                "data": event.get("data", {}),
            }
        )

    async def send_json(self, data):
        """发送JSON格式的消息"""
        await self.send(text_data=json.dumps(data, ensure_ascii=False))
