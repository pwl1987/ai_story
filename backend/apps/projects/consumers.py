"""
WebSocket消费者
职责: 订阅Redis Pub/Sub频道，将消息推送给前端
遵循单一职责原则(SRP)

Epic 3: 集成自动重连机制
"""

import asyncio
import contextlib
import json
import logging
import time

import redis.asyncio as aioredis
from channels.generic.websocket import AsyncWebsocketConsumer
from django.conf import settings

# Epic 3: 导入自动重连管理器
from core.websocket import WebSocketReconnectManager

logger = logging.getLogger(__name__)


class ProjectStageConsumer(AsyncWebsocketConsumer):
    """
    项目阶段WebSocket消费者

    订阅Redis Pub/Sub频道，实时推送AI生成进度给前端

    WebSocket URL: ws://localhost:8000/ws/projects/{project_id}/stage/{stage_name}/

    消息格式:
    {
        "type": "token|stage_update|done|error|progress",
        "content": "...",
        ...
    }

    Epic 3: 集成自动重连机制
    """

    def __init__(self, *args, **kwargs):
        """初始化消费者"""
        super().__init__(*args, **kwargs)
        self.redis_client = None
        self.pubsub = None
        self.reconnect_manager = None

    async def connect(self):
        """
        WebSocket连接建立

        Epic 3: 集成自动重连管理器
        """
        # 从URL获取参数
        self.project_id = self.scope['url_route']['kwargs']['project_id']
        self.stage_name = self.scope['url_route']['kwargs']['stage_name']

        # 构建Redis频道名称
        self.channel_name = f"ai_story:project:{self.project_id}:stage:{self.stage_name}"

        logger.info(f"WebSocket连接: {self.channel_name}")

        # 接受WebSocket连接
        await self.accept()

        # Epic 3: 创建重连管理器
        self.reconnect_manager = WebSocketReconnectManager(
            project_id=self.project_id,
            stage=self.stage_name,
            connect_callback=self._connect_redis,
            disconnect_callback=self._disconnect_redis,
            max_retries=5
        )

        # 启动自动重连
        success = await self.reconnect_manager.start()

        if not success:
            # 重连失败，发送错误消息
            await self.send(text_data=json.dumps({
                'type': 'error',
                'error': 'Redis连接失败，已达到最大重连次数',
                'retries': self.reconnect_manager.get_retry_count()
            }))
            await self.close()

    async def _connect_redis(self) -> bool:
        """
        连接Redis (供重连管理器调用)

        Returns:
            bool: 连接是否成功
        """
        redis_url = getattr(settings, 'CELERY_BROKER_URL', 'redis://localhost:6379/5')

        try:
            # 创建Redis连接
            self.redis_client = await aioredis.from_url(
                redis_url,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                socket_keepalive=True
            )

            # 创建Pub/Sub对象
            self.pubsub = self.redis_client.pubsub()

            # 订阅频道
            await self.pubsub.subscribe(self.channel_name)

            logger.info(f"已订阅Redis频道: {self.channel_name}")

            # 发送连接成功消息
            await self.send(text_data=json.dumps({
                'type': 'connected',
                'channel': self.channel_name,
                'message': '已连接到实时流'
            }))

            # 启动消息监听任务
            asyncio.create_task(self._listen_messages())

            return True

        except Exception as e:
            logger.error(f"Redis连接失败: {e}")
            return False

    async def _disconnect_redis(self) -> None:
        """断开Redis连接"""
        try:
            if self.pubsub:
                await self.pubsub.unsubscribe(self.channel_name)
            if self.redis_client:
                await self.redis_client.close()
            logger.info(f"已关闭Redis连接: {self.channel_name}")
        except Exception as e:
            logger.error(f"关闭Redis连接失败: {e}")

    async def disconnect(self, close_code):
        """
        WebSocket连接断开

        Epic 3: 停止重连管理器
        """
        logger.info(f"WebSocket断开: {self.channel_name}, code: {close_code}")

        # Epic 3: 停止重连管理器
        if self.reconnect_manager:
            await self.reconnect_manager.stop()

    async def receive(self, text_data=None, bytes_data=None):
        """
        接收来自前端的消息

        Epic 3: 处理心跳检测 (ping/pong)
        """
        if text_data:
            try:
                data = json.loads(text_data)
                message_type = data.get('type')

                if message_type == 'ping':
                    # Epic 3: 心跳响应
                    timestamp = data.get('timestamp', time.time())
                    await self.send(text_data=json.dumps({
                        'type': 'pong',
                        'timestamp': timestamp
                    }))

                    # 更新重连管理器的心跳时间
                    if self.reconnect_manager:
                        self.reconnect_manager.on_ping(timestamp)

            except json.JSONDecodeError:
                logger.warning(f"无效的JSON消息: {text_data}")
            except Exception as e:
                logger.error(f"处理消息异常: {e}")

    async def _listen_messages(self):
        """
        Epic 3: 监听Redis消息 (由_connect_redis启动)

        持续监听并转发消息到WebSocket
        """
        try:
            # 持续监听消息
            async for message in self.pubsub.listen():
                if message['type'] == 'message':
                    try:
                        # 解析消息
                        data = json.loads(message['data'])

                        # 转发到WebSocket
                        await self.send(text_data=json.dumps(data))

                        # 如果是完成或错误消息，可以选择关闭连接
                        if data.get('type') in ['done', 'error']:
                            logger.info(f"任务结束，准备关闭连接: {self.channel_name}")
                            # 等待1秒后关闭，确保消息已发送
                            await asyncio.sleep(1)
                            await self.close()
                            break

                    except json.JSONDecodeError as e:
                        logger.error(f"Redis消息解析失败: {e}")
                    except Exception as e:
                        logger.error(f"消息处理异常: {e}")

        except asyncio.CancelledError:
            logger.info(f"Redis消息监听已取消: {self.channel_name}")
        except Exception as e:
            logger.error(f"Redis消息监听失败: {e}")

            # Epic 3: 发送错误消息到前端
            with contextlib.suppress(Exception):
                await self.send(text_data=json.dumps({
                    'type': 'error',
                    'error': f'Redis连接失败: {e!s}'
                }))

            # Epic 3: 触发重连
            if self.reconnect_manager and self.reconnect_manager.should_retry():
                await self.reconnect_manager.start()


class ProjectConsumer(AsyncWebsocketConsumer):
    """
    项目级WebSocket消费者

    订阅整个项目的所有阶段更新

    WebSocket URL: ws://localhost:8000/ws/projects/{project_id}/

    可用于监控项目整体进度

    Epic 3: 集成自动重连机制
    """

    def __init__(self, *args, **kwargs):
        """初始化消费者"""
        super().__init__(*args, **kwargs)
        self.redis_client = None
        self.pubsub = None
        self.reconnect_manager = None

    async def connect(self):
        """
        WebSocket连接建立

        Epic 3: 集成自动重连管理器
        """
        self.project_id = self.scope['url_route']['kwargs']['project_id']

        # 订阅项目所有阶段的频道
        self.channels = [
            f"ai_story:project:{self.project_id}:stage:rewrite",
            f"ai_story:project:{self.project_id}:stage:storyboard",
            f"ai_story:project:{self.project_id}:stage:image_generation",
            f"ai_story:project:{self.project_id}:stage:camera_movement",
            f"ai_story:project:{self.project_id}:stage:video_generation",
        ]

        logger.info(f"WebSocket连接: 项目 {self.project_id}")

        await self.accept()

        # Epic 3: 创建重连管理器
        self.reconnect_manager = WebSocketReconnectManager(
            project_id=self.project_id,
            stage='all',  # 所有阶段
            connect_callback=self._connect_redis,
            disconnect_callback=self._disconnect_redis,
            max_retries=5
        )

        # 启动自动重连
        success = await self.reconnect_manager.start()

        if not success:
            # 重连失败，发送错误消息
            await self.send(text_data=json.dumps({
                'type': 'error',
                'error': 'Redis连接失败，已达到最大重连次数',
                'retries': self.reconnect_manager.get_retry_count()
            }))
            await self.close()

    async def _connect_redis(self) -> bool:
        """
        连接Redis (供重连管理器调用)

        Returns:
            bool: 连接是否成功
        """
        redis_url = getattr(settings, 'CELERY_BROKER_URL', 'redis://localhost:6379/5')

        try:
            # 创建Redis连接
            self.redis_client = await aioredis.from_url(
                redis_url,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                socket_keepalive=True
            )

            # 创建Pub/Sub对象
            self.pubsub = self.redis_client.pubsub()

            # 订阅所有阶段频道
            await self.pubsub.subscribe(*self.channels)

            logger.info(f"已订阅项目 {self.project_id} 的所有阶段频道")

            # 发送连接成功消息
            await self.send(text_data=json.dumps({
                'type': 'connected',
                'project_id': self.project_id,
                'message': '已连接到项目实时流'
            }))

            # 启动消息监听任务
            asyncio.create_task(self._listen_messages())

            return True

        except Exception as e:
            logger.error(f"Redis连接失败: {e}")
            return False

    async def _disconnect_redis(self) -> None:
        """断开Redis连接"""
        try:
            if self.pubsub:
                await self.pubsub.unsubscribe(*self.channels)
            if self.redis_client:
                await self.redis_client.close()
            logger.info(f"已关闭Redis连接: 项目 {self.project_id}")
        except Exception as e:
            logger.error(f"关闭Redis连接失败: {e}")

    async def disconnect(self, close_code):
        """
        WebSocket连接断开

        Epic 3: 停止重连管理器
        """
        logger.info(f"WebSocket断开: 项目 {self.project_id}, code: {close_code}")

        # Epic 3: 停止重连管理器
        if self.reconnect_manager:
            await self.reconnect_manager.stop()

    async def receive(self, text_data=None, bytes_data=None):
        """
        接收来自前端的消息

        Epic 3: 处理心跳检测 (ping/pong)
        """
        if text_data:
            try:
                data = json.loads(text_data)
                message_type = data.get('type')

                if message_type == 'ping':
                    # Epic 3: 心跳响应
                    timestamp = data.get('timestamp', time.time())
                    await self.send(text_data=json.dumps({
                        'type': 'pong',
                        'timestamp': timestamp
                    }))

                    # 更新重连管理器的心跳时间
                    if self.reconnect_manager:
                        self.reconnect_manager.on_ping(timestamp)

            except json.JSONDecodeError:
                logger.warning(f"无效的JSON消息: {text_data}")
            except Exception as e:
                logger.error(f"处理消息异常: {e}")

    async def _listen_messages(self):
        """
        Epic 3: 监听Redis消息 (由_connect_redis启动)

        持续监听并转发消息到WebSocket
        """
        try:
            # 持续监听消息
            async for message in self.pubsub.listen():
                if message['type'] == 'message':
                    try:
                        data = json.loads(message['data'])
                        await self.send(text_data=json.dumps(data))
                    except json.JSONDecodeError as e:
                        logger.error(f"Redis消息解析失败: {e}")
                    except Exception as e:
                        logger.error(f"消息处理异常: {e}")

        except asyncio.CancelledError:
            logger.info(f"Redis消息监听已取消: 项目 {self.project_id}")
        except Exception as e:
            logger.error(f"Redis消息监听失败: {e}")

            # Epic 3: 发送错误消息到前端
            with contextlib.suppress(Exception):
                await self.send(text_data=json.dumps({
                    'type': 'error',
                    'error': f'Redis连接失败: {e!s}'
                }))

            # Epic 3: 触发重连
            if self.reconnect_manager and self.reconnect_manager.should_retry():
                await self.reconnect_manager.start()
