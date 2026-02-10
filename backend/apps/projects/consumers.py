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
from typing import Dict

import redis.asyncio as aioredis
from channels.generic.websocket import AsyncWebsocketConsumer
from django.conf import settings
from django.core.cache import cache

# Epic 3: 导入自动重连管理器
from core.websocket import WebSocketReconnectManager

logger = logging.getLogger(__name__)

# Story 3-1: 连接性能监控常量
CONNECTION_METRICS_KEY = "websocket:connection_metrics"
CONNECTION_TIMEOUT = 5  # 连接超时时间（秒）
MAX_METRICS_HISTORY = 1000  # 最大历史记录数量
METRICS_CACHE_TIMEOUT = 3600  # 缓存超时时间（秒）
MS_PER_SECOND = 1000  # 毫秒转换系数


class BaseProjectConsumer(AsyncWebsocketConsumer):
    """
    项目WebSocket消费者基类
    提供Redis连接、自动重连、心跳检测等公共功能

    Epic 3: 集成自动重连机制
    """

    def __init__(self, *args, **kwargs):
        """初始化消费者"""
        super().__init__(*args, **kwargs)
        self.redis_client = None
        self.pubsub = None
        self.reconnect_manager = None
        self._connection_start_time = None

    async def connect(self):
        """WebSocket连接建立"""
        # Story 3-1: 记录连接开始时间
        self._connection_start_time = time.time()

        self.project_id = self.scope["url_route"]["kwargs"]["project_id"]

        logger.info(f"WebSocket连接开始: 项目 {self.project_id}, 阶段: {self._get_stage_name()}")

        # 接受WebSocket连接（优化：立即接受，不等待Redis）
        await self.accept()

        # Epic 3: 创建重连管理器
        self.reconnect_manager = WebSocketReconnectManager(
            project_id=self.project_id,
            stage=self._get_stage_name(),
            connect_callback=self._connect_redis,
            disconnect_callback=self._disconnect_redis,
            max_retries=5,
        )

        # 启动自动重连（优化：设置连接超时）
        try:
            # 使用asyncio.wait_for添加超时控制
            success = await asyncio.wait_for(
                self.reconnect_manager.start(), timeout=CONNECTION_TIMEOUT
            )
        except asyncio.TimeoutError:
            logger.error(f"Redis连接超时（{CONNECTION_TIMEOUT}秒）: 项目 {self.project_id}")
            success = False
        except Exception as e:
            logger.error(f"Redis连接异常: {e}")
            success = False

        # Story 3-1: 记录连接指标
        connection_time_ms = (time.time() - self._connection_start_time) * MS_PER_SECOND
        WebSocketConnectionMetrics.record_connection(
            project_id=self.project_id,
            stage=self._get_stage_name(),
            connection_time_ms=connection_time_ms,
            success=success,
        )

        logger.info(
            f"WebSocket连接{'成功' if success else '失败'}: "
            f"项目 {self.project_id} (耗时: {connection_time_ms:.2f}ms)"
        )

        if not success:
            # 重连失败，发送错误消息
            await self.send(
                text_data=json.dumps(
                    {
                        "type": "error",
                        "error": "Redis连接失败，已达到最大重连次数",
                        "retries": self.reconnect_manager.get_retry_count(),
                    }
                )
            )
            await self.close()

    async def _connect_redis(self) -> bool:
        """连接Redis (供重连管理器调用)"""
        # 使用 Redis Pub/Sub 专用数据库 (DB2)，而非 Celery 结果存储 (DB5)
        redis_url = getattr(settings, "REDIS_PUBSUB_URL", "redis://localhost:6379/2")

        try:
            # 创建Redis连接
            self.redis_client = await aioredis.from_url(
                redis_url,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                socket_keepalive=True,
            )

            # 创建Pub/Sub对象
            self.pubsub = self.redis_client.pubsub()

            # 订阅频道（由子类实现）
            channels = self._get_channels()
            if isinstance(channels, list):
                await self.pubsub.subscribe(*channels)
                logger.info(f"已订阅 {len(channels)} 个Redis频道")
            else:
                await self.pubsub.subscribe(channels)
                logger.info(f"已订阅Redis频道: {channels}")

            # 发送连接成功消息
            await self.send(
                text_data=json.dumps(
                    {
                        "type": "connected",
                        "project_id": self.project_id,
                        "message": self._get_connection_success_message(),
                    }
                )
            )

            # 启动消息监听任务
            asyncio.create_task(self._listen_messages())

            return True

        except Exception as e:
            logger.error(f"Redis连接失败: {e}")
            return False

    async def _disconnect_redis(self) -> None:
        """断开Redis连接"""
        try:
            channels = self._get_channels()
            if self.pubsub:
                if isinstance(channels, list):
                    await self.pubsub.unsubscribe(*channels)
                else:
                    await self.pubsub.unsubscribe(channels)
            if self.redis_client:
                await self.redis_client.close()
            logger.info(f"已关闭Redis连接: 项目 {self.project_id}")
        except Exception as e:
            logger.error(f"关闭Redis连接失败: {e}")

    async def disconnect(self, close_code):
        """WebSocket连接断开"""
        logger.info(
            f"WebSocket断开: 项目 {self.project_id}, 阶段: {self._get_stage_name()}, code: {close_code}"
        )

        # Epic 3: 停止重连管理器
        if self.reconnect_manager:
            await self.reconnect_manager.stop()

    async def receive(self, text_data=None, bytes_data=None):
        """接收来自前端消息"""
        if text_data:
            try:
                data = json.loads(text_data)
                message_type = data.get("type")

                if message_type == "ping":
                    # Epic 3: 心跳响应
                    timestamp = data.get("timestamp", time.time())
                    await self.send(text_data=json.dumps({"type": "pong", "timestamp": timestamp}))

                    # 更新重连管理器的心跳时间
                    if self.reconnect_manager:
                        self.reconnect_manager.on_ping(timestamp)

            except json.JSONDecodeError:
                logger.warning(f"无效的JSON消息: {text_data}")
            except Exception as e:
                logger.error(f"处理消息异常: {e}")

    async def _listen_messages(self):
        """监听Redis消息"""
        try:
            # 持续监听消息
            async for message in self.pubsub.listen():
                if message["type"] == "message":
                    try:
                        # 解析消息
                        data = json.loads(message["data"])

                        # 转发到WebSocket
                        await self.send(text_data=json.dumps(data))

                        # 如果是完成或错误消息，可以选择关闭连接
                        if data.get("type") in ["done", "error"]:
                            logger.info(f"任务结束，准备关闭连接: 项目 {self.project_id}")
                            # 等待1秒后关闭，确保消息已发送
                            await asyncio.sleep(1)
                            await self.close()
                            break

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
                await self.send(
                    text_data=json.dumps({"type": "error", "error": f"Redis连接失败: {e!s}"})
                )

            # Epic 3: 触发重连
            if self.reconnect_manager and self.reconnect_manager.should_retry():
                await self.reconnect_manager.start()

    # 抽象方法，由子类实现
    def _get_channels(self):
        """获取要订阅的Redis频道"""
        raise NotImplementedError("子类必须实现 _get_channels() 方法")

    def _get_stage_name(self):
        """获取阶段名称"""
        raise NotImplementedError("子类必须实现 _get_stage_name() 方法")

    def _get_connection_success_message(self):
        """获取连接成功消息"""
        return "已连接到实时流"


class WebSocketConnectionMetrics:
    """
    Story 3-1: WebSocket连接性能监控器

    职责:
    - 记录连接建立时间
    - 计算P95连接延迟
    - 统计连接成功率

    遵循单一职责原则(SRP)
    """

    @staticmethod
    def record_connection(project_id: str, stage: str, connection_time_ms: float, success: bool):
        """
        记录连接指标

        Args:
            project_id: 项目ID
            stage: 阶段名称
            connection_time_ms: 连接时间（毫秒）
            success: 是否成功
        """
        try:
            # 获取现有指标
            metrics = cache.get(CONNECTION_METRICS_KEY, {})

            # 更新指标
            key = f"{project_id}:{stage}"
            if key not in metrics:
                metrics[key] = {
                    "total_connections": 0,
                    "successful_connections": 0,
                    "connection_times_ms": [],
                }

            metrics[key]["total_connections"] += 1
            if success:
                metrics[key]["successful_connections"] += 1
                # 只保留最近MAX_METRICS_HISTORY条记录（避免内存溢出）
                metrics[key]["connection_times_ms"].append(connection_time_ms)
                if len(metrics[key]["connection_times_ms"]) > MAX_METRICS_HISTORY:
                    metrics[key]["connection_times_ms"].pop(0)

            # 缓存METRICS_CACHE_TIMEOUT秒
            cache.set(CONNECTION_METRICS_KEY, metrics, timeout=METRICS_CACHE_TIMEOUT)

        except Exception as e:
            logger.error(f"记录连接指标失败: {e}")

    @staticmethod
    def get_statistics(project_id: str = None, stage: str = None) -> Dict:
        """
        获取连接统计信息

        Args:
            project_id: 项目ID（可选）
            stage: 阶段名称（可选）

        Returns:
            包含P95、平均连接时间、成功率等统计信息的字典
        """
        try:
            metrics = cache.get(CONNECTION_METRICS_KEY, {})

            if project_id and stage:
                # 获取特定项目的统计
                key = f"{project_id}:{stage}"
                if key not in metrics:
                    return {}
                data = metrics[key]
            else:
                # 聚合所有项目的统计
                all_times = []
                total = 0
                successful = 0
                for data in metrics.values():
                    all_times.extend(data["connection_times_ms"])
                    total += data["total_connections"]
                    successful += data["successful_connections"]

                if not all_times:
                    return {}

                data = {
                    "connection_times_ms": all_times,
                    "total_connections": total,
                    "successful_connections": successful,
                }

            # 计算统计信息
            times = sorted(data["connection_times_ms"])
            n = len(times)

            if n == 0:
                return {}

            return {
                "total_connections": data["total_connections"],
                "successful_connections": data["successful_connections"],
                "success_rate": data["successful_connections"] / data["total_connections"] * 100,
                "avg_connection_time_ms": sum(times) / n,
                "p50_connection_time_ms": times[int(n * 0.5)],
                "p95_connection_time_ms": times[int(n * 0.95)] if n >= 20 else times[-1],
                "p99_connection_time_ms": times[int(n * 0.99)] if n >= 100 else times[-1],
                "min_connection_time_ms": min(times),
                "max_connection_time_ms": max(times),
            }

        except Exception as e:
            logger.error(f"获取连接统计失败: {e}")
            return {}


class ProjectStageConsumer(BaseProjectConsumer):
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
        self.stage_name = None

    async def connect(self):
        """WebSocket连接建立"""
        # 从URL获取参数
        self.stage_name = self.scope["url_route"]["kwargs"]["stage_name"]
        # 调用基类的connect
        await super().connect()

    def _get_channels(self):
        """返回单个Redis频道"""
        return f"ai_story:project:{self.project_id}:stage:{self.stage_name}"

    def _get_stage_name(self):
        """返回阶段名称"""
        return self.stage_name

    def _get_connection_success_message(self):
        """返回连接成功消息"""
        return f"已连接到阶段 {self.stage_name} 实时流"


class ProjectConsumer(BaseProjectConsumer):
    """
    项目级WebSocket消费者

    订阅整个项目的所有阶段更新

    WebSocket URL: ws://localhost:8000/ws/projects/{project_id}/

    可用于监控项目整体进度

    Epic 3: 集成自动重连机制
    """

    def _get_channels(self):
        """返回所有阶段的Redis频道列表"""
        return [
            f"ai_story:project:{self.project_id}:stage:rewrite",
            f"ai_story:project:{self.project_id}:stage:storyboard",
            f"ai_story:project:{self.project_id}:stage:image_generation",
            f"ai_story:project:{self.project_id}:stage:camera_movement",
            f"ai_story:project:{self.project_id}:stage:video_generation",
        ]

    def _get_stage_name(self):
        """返回阶段名称（所有阶段）"""
        return "all"

    def _get_connection_success_message(self):
        """返回连接成功消息"""
        return "已连接到项目实时流"


class ProjectProgressConsumer(BaseProjectConsumer):
    """
    Story 11.4.2: 项目进度WebSocket消费者

    专门用于前端进度组件的实时进度更新

    WebSocket URL: ws://localhost:8000/ws/projects/{project_id}/progress/

    事件格式:
    - progress: {"type": "progress", "stage": "llm", "percentage": 35, "current_step": 3, "total_steps": 10, "step_name": "生成场景描述"}
    - error: {"type": "error", "stage": "image_generation", "error_message": "API timeout", "error_type": "TimeoutException", "timestamp": "..."}
    - stage_complete: {"type": "stage_complete", "stage_name": "llm", "duration": 45, "output_count": 10, "next_stage": "image_generation"}

    Epic 3: 集成自动重连机制
    """

    def _get_channels(self):
        """返回所有阶段的Redis频道列表（用于进度追踪）"""
        return [
            f"ai_story:project:{self.project_id}:stage:rewrite",
            f"ai_story:project:{self.project_id}:stage:storyboard",
            f"ai_story:project:{self.project_id}:stage:image_generation",
            f"ai_story:project:{self.project_id}:stage:camera_movement",
            f"ai_story:project:{self.project_id}:stage:video_generation",
        ]

    def _get_stage_name(self):
        """返回阶段名称（用于进度追踪）"""
        return "progress"

    def _get_connection_success_message(self):
        """返回连接成功消息"""
        return "已连接到项目进度实时流"

    async def _listen_messages(self):
        """
        Story 11.4.2: 监听Redis消息并转换为进度事件格式

        将原有的消息格式转换为前端进度组件期望的格式:
        - stage_update → progress (带 percentage, current_step, total_steps, step_name)
        - error → error (带 error_message, error_type, timestamp)
        - done → stage_complete (带 duration, output_count, next_stage)
        """
        try:
            # 记录阶段开始时间（用于计算duration）
            stage_start_times = {}

            # 持续监听消息
            async for message in self.pubsub.listen():
                if message["type"] == "message":
                    try:
                        # 解析消息
                        data = json.loads(message["data"])
                        message_type = data.get("type")
                        stage = data.get("stage", "")

                        # 转换消息格式
                        if message_type == "stage_update":
                            # stage_update → progress 事件
                            progress_data = {
                                "type": "progress",
                                "stage": self._map_backend_stage_to_progress(stage),
                                "percentage": data.get("progress", 0),
                                "current_step": data.get("current", 0),
                                "total_steps": data.get("total", 1),
                                "step_name": data.get("message", data.get("item_name", "")),
                            }
                            await self.send(text_data=json.dumps(progress_data))

                        elif message_type == "progress":
                            # 进度消息 - 直接转发并补充字段
                            progress_data = {
                                "type": "progress",
                                "stage": self._map_backend_stage_to_progress(stage),
                                "percentage": data.get("progress", data.get("percentage", 0)),
                                "current_step": data.get("current_step", data.get("current", 0)),
                                "total_steps": data.get("total_steps", data.get("total", 1)),
                                "step_name": data.get("step_name", data.get("item_name", "")),
                            }
                            await self.send(text_data=json.dumps(progress_data))

                            # 记录阶段开始时间
                            if stage and stage not in stage_start_times:
                                stage_start_times[stage] = time.time()

                        elif message_type == "error":
                            # error 事件 - 增强格式
                            error_data = {
                                "type": "error",
                                "stage": self._map_backend_stage_to_progress(stage),
                                "error_message": data.get("error", "未知错误"),
                                "error_type": self._infer_error_type(data.get("error", "")),
                                "timestamp": data.get("timestamp", time.time()),
                            }
                            await self.send(text_data=json.dumps(error_data))

                        elif message_type == "done":
                            # done → stage_complete 事件
                            stage_key = stage
                            duration = 0
                            if stage_key in stage_start_times:
                                duration = time.time() - stage_start_times[stage_key]
                                del stage_start_times[stage_key]

                            # 计算输出数量（从 metadata 中获取）
                            metadata = data.get("metadata", {})
                            output_count = metadata.get("scene_count", metadata.get("count", 0))

                            # 确定下一阶段
                            next_stage = self._get_next_stage(stage)

                            complete_data = {
                                "type": "stage_complete",
                                "stage_name": self._map_backend_stage_to_progress(stage),
                                "duration": int(duration),
                                "output_count": output_count,
                                "next_stage": next_stage,
                            }
                            await self.send(text_data=json.dumps(complete_data))

                        # 其他消息类型直接转发
                        else:
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
                await self.send(
                    text_data=json.dumps({"type": "error", "error": f"Redis连接失败: {e!s}"})
                )

            # Epic 3: 触发重连
            if self.reconnect_manager and self.reconnect_manager.should_retry():
                await self.reconnect_manager.start()

    def _map_backend_stage_to_progress(self, backend_stage: str) -> str:
        """
        将后端阶段名称映射到前端进度组件使用的阶段key

        Args:
            backend_stage: 后端阶段名 (rewrite/storyboard/image_generation/camera_movement/video_generation)

        Returns:
            前端进度阶段key (llm/storyboard/image/camera/video)
        """
        stage_mapping = {
            "rewrite": "llm",
            "storyboard": "storyboard",
            "image_generation": "image",
            "camera_movement": "camera",
            "video_generation": "video",
        }
        return stage_mapping.get(backend_stage, backend_stage)

    def _get_next_stage(self, current_stage: str) -> str:
        """
        获取下一阶段名称（前端进度key）

        Args:
            current_stage: 当前阶段

        Returns:
            下一阶段的前端进度key，如果没有则返回空字符串
        """
        stage_order = [
            "rewrite",
            "storyboard",
            "image_generation",
            "camera_movement",
            "video_generation",
        ]
        try:
            current_index = stage_order.index(current_stage)
            if current_index < len(stage_order) - 1:
                next_backend = stage_order[current_index + 1]
                return self._map_backend_stage_to_progress(next_backend)
        except ValueError:
            pass
        return ""

    def _infer_error_type(self, error_message: str) -> str:
        """
        从错误消息推断错误类型

        Args:
            error_message: 错误消息

        Returns:
            错误类型 (TimeoutException/ApiException/ValidationException等)
        """
        error_lower = error_message.lower()
        if "timeout" in error_lower or "超时" in error_lower:
            return "TimeoutException"
        elif "api" in error_lower or "接口" in error_lower:
            return "ApiException"
        elif "validation" in error_lower or "验证" in error_lower:
            return "ValidationException"
        elif "connection" in error_lower or "连接" in error_lower:
            return "ConnectionException"
        else:
            return "GenericException"
