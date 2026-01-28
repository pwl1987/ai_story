"""
Redis连接池管理
Epic 3: 实时通信稳定性 - 性能优化
职责: 复用Redis连接,提高性能
遵循单一职责原则(SRP)
"""

import logging
import redis.asyncio as aioredis
from typing import Optional
from django.conf import settings

logger = logging.getLogger(__name__)


class RedisConnectionPool:
    """
    Redis连接池管理器

    职责:
    - 管理Redis连接池
    - 复用连接,提高性能
    - 自动重连
    - 连接健康检查

    使用示例:
    >>> async with RedisConnectionPool.get_connection() as redis:
    >>>     await redis.publish('channel', 'message')
    """

    _pools = {}  # {(host, port, db): pool}

    @classmethod
    async def get_connection(
        cls,
        redis_url: Optional[str] = None
    ) -> aioredis.Redis:
        """
        获取Redis连接(从连接池)

        Args:
            redis_url: Redis URL(可选,默认使用settings配置)

        Returns:
            aioredis.Redis: Redis连接实例
        """
        if redis_url is None:
            redis_url = getattr(settings, 'CELERY_BROKER_URL', 'redis://localhost:6379/2')

        # 解析Redis URL
        import re
        match = re.match(r'redis://([^:]+):(\d+)/(\d+)', redis_url)
        if match:
            host, port, db = match.groups()
            pool_key = (host, int(port), int(db))
        else:
            pool_key = redis_url

        # 获取或创建连接池
        if pool_key not in cls._pools:
            logger.info(f"创建新的Redis连接池: {pool_key}")
            cls._pools[pool_key] = await aioredis.from_url(
                redis_url,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                socket_keepalive=True,
                health_check_interval=30,
                max_connections=50,  # 最大连接数
                retry_on_timeout=True
            )

        return cls._pools[pool_key]

    @classmethod
    async def close_all(cls) -> None:
        """
        关闭所有连接池

        用于应用关闭时清理资源
        """
        for pool_key, pool in cls._pools.items():
            try:
                await pool.close()
                logger.info(f"已关闭Redis连接池: {pool_key}")
            except Exception as e:
                logger.error(f"关闭Redis连接池失败: {pool_key}, error={e}")

        cls._pools.clear()

    @classmethod
    async def health_check(cls, redis_url: Optional[str] = None) -> bool:
        """
        健康检查

        Args:
            redis_url: Redis URL(可选)

        Returns:
            bool: 连接是否健康
        """
        try:
            redis_client = await cls.get_connection(redis_url)
            await redis_client.ping()
            return True
        except Exception as e:
            logger.error(f"Redis健康检查失败: {e}")
            return False


class RedisPublisherWithContext:
    """
    带性能监控的Redis发布器

    职责:
    - 发布消息到Redis Pub/Sub
    - 自动记录性能指标
    - 使用连接池提高性能

    使用示例:
    >>> async with RedisPublisherWithContext(project_id, stage) as publisher:
    >>>     await publisher.publish(message)
    """

    def __init__(self, project_id: str, stage: str):
        """
        初始化发布器

        Args:
            project_id: 项目ID
            stage: 阶段名称
        """
        self.project_id = project_id
        self.stage = stage
        self.channel = f"ai_story:project:{project_id}:stage:{stage}"
        self.redis_client = None

    async def __aenter__(self):
        """进入上下文: 获取Redis连接"""
        self.redis_client = await RedisConnectionPool.get_connection()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """退出上下文: 清理资源"""
        # 连接池管理,不需要手动关闭
        return False

    async def publish(self, message: dict) -> bool:
        """
        发布消息到Redis(带性能监控)

        Args:
            message: 消息字典

        Returns:
            bool: 是否发布成功
        """
        import json
        import time
        from core.metrics.websocket_metrics import WebSocketMetrics

        start_time = time.time()

        try:
            # 序列化消息
            message_json = json.dumps(message, ensure_ascii=False)

            # 发布到Redis
            subscribers = await self.redis_client.publish(self.channel, message_json)

            # 记录发布延迟
            latency_ms = (time.time() - start_time) * 1000
            WebSocketMetrics.record_redis_publish_latency(
                self.project_id,
                self.stage,
                latency_ms,
                status='success'
            )

            logger.debug(
                f"Redis发布成功: channel={self.channel}, "
                f"subscribers={subscribers}, latency={latency_ms:.2f}ms"
            )

            return True

        except Exception as e:
            # 记录失败
            latency_ms = (time.time() - start_time) * 1000
            WebSocketMetrics.record_redis_publish_latency(
                self.project_id,
                self.stage,
                latency_ms,
                status='error'
            )

            logger.error(f"Redis发布失败: {e}")
            return False
