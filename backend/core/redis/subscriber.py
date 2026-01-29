"""
Redis流式接收器
职责: 订阅Redis Pub/Sub频道并接收流式数据
遵循单一职责原则(SRP)
"""

import json
import logging
from typing import Any, AsyncGenerator, Dict, Optional

from django.conf import settings

import redis

logger = logging.getLogger(__name__)


class RedisStreamSubscriber:
    """
    Redis流式接收器

    负责订阅Redis Pub/Sub频道并接收实时流式数据
    支持异步迭代器模式,可用于SSE流式响应

    频道命名规范: ai_story:project:{project_id}:stage:{stage_name}
    """

    def __init__(self, project_id: str, stage_name: Optional[str] = None):
        """
        初始化接收器

        Args:
            project_id: 项目ID
            stage_name: 阶段名称 (可选,为None时订阅项目所有阶段)
        """
        self.project_id = project_id
        self.stage_name = stage_name

        # 构建频道模式
        if stage_name:
            self.channel = f"ai_story:project:{project_id}:stage:{stage_name}"
        else:
            # 订阅项目所有阶段
            self.channel = f"ai_story:project:{project_id}:stage:*"

        self.redis_client = None
        self.pubsub = None

        logger.info(f"初始化Redis接收器: {self.channel}")

    def _get_redis_client(self) -> redis.Redis:
        """
        获取Redis客户端
        使用连接池提高性能
        """
        try:
            # 从Django settings获取Redis Pub/Sub专用配置
            redis_url = getattr(settings, "REDIS_PUBSUB_URL", "redis://localhost:6379/2")

            # 解析Redis URL
            return redis.from_url(
                redis_url,
                decode_responses=True,  # 自动解码为字符串
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
                health_check_interval=30,
            )
        except Exception as e:
            logger.error(f"Redis连接失败: {e!s}")
            raise

    def subscribe(self):
        """
        订阅频道
        """
        try:
            if not self.redis_client:
                self.redis_client = self._get_redis_client()

            if not self.pubsub:
                self.pubsub = self.redis_client.pubsub()

            # 支持模式匹配订阅
            if "*" in self.channel:
                self.pubsub.psubscribe(self.channel)
                logger.info(f"模式订阅频道: {self.channel}")
            else:
                self.pubsub.subscribe(self.channel)
                logger.info(f"订阅频道: {self.channel}")

        except Exception as e:
            logger.error(f"订阅频道失败: {e!s}")
            raise

    def unsubscribe(self):
        """
        取消订阅
        """
        try:
            if self.pubsub:
                if "*" in self.channel:
                    self.pubsub.punsubscribe(self.channel)
                else:
                    self.pubsub.unsubscribe(self.channel)
                logger.info(f"取消订阅频道: {self.channel}")
        except Exception as e:
            logger.error(f"取消订阅失败: {e!s}")

    def listen(self, timeout: Optional[int] = None) -> AsyncGenerator[Dict[str, Any], None]:
        """
        监听消息 (同步生成器)

        Args:
            timeout: 超时时间(秒),None表示永不超时

        Yields:
            Dict[str, Any]: 解析后的消息字典
        """
        try:
            self.subscribe()

            # 设置超时
            if timeout:
                self.pubsub.connection_pool.connection_kwargs["socket_timeout"] = timeout

            for message in self.pubsub.listen():
                # 过滤订阅确认消息
                if message["type"] in ("subscribe", "psubscribe"):
                    logger.debug(f"订阅成功: {message}")
                    continue

                # 过滤取消订阅消息
                if message["type"] in ("unsubscribe", "punsubscribe"):
                    logger.debug(f"取消订阅: {message}")
                    break

                # 处理实际消息
                if message["type"] in ("message", "pmessage"):
                    try:
                        # 解析JSON数据
                        data = json.loads(message["data"])

                        # 添加频道信息
                        data["channel"] = message.get("channel", self.channel)

                        # logger.debug(f"接收消息: {data.get('type')} from {data['channel']}")

                        yield data

                        # 如果收到done或error消息,结束监听
                        if data.get("type") in ("done", "error"):
                            logger.info(f"收到结束消息: {data.get('type')}")
                            break

                    except json.JSONDecodeError as e:
                        logger.error(f"JSON解析失败: {e!s}, 原始数据: {message['data']}")
                        continue
                    except Exception as e:
                        logger.error(f"消息处理异常: {e!s}")
                        continue

        except redis.RedisError as e:
            logger.error(f"Redis监听失败: {e!s}")
            yield {"type": "error", "error": f"Redis连接错误: {e!s}", "project_id": self.project_id}
        except Exception as e:
            logger.error(f"监听异常: {e!s}")
            yield {"type": "error", "error": f"监听异常: {e!s}", "project_id": self.project_id}
        finally:
            self.close()

    def get_message(self, timeout: float = 1.0) -> Optional[Dict[str, Any]]:
        """
        获取单条消息 (非阻塞)

        Args:
            timeout: 超时时间(秒)

        Returns:
            Optional[Dict[str, Any]]: 消息字典,无消息返回None
        """
        try:
            if not self.pubsub:
                self.subscribe()

            message = self.pubsub.get_message(timeout=timeout)

            if not message:
                return None

            # 过滤订阅确认消息
            if message["type"] in ("subscribe", "psubscribe", "unsubscribe", "punsubscribe"):
                return None

            # 处理实际消息
            if message["type"] in ("message", "pmessage"):
                try:
                    data = json.loads(message["data"])
                    data["channel"] = message.get("channel", self.channel)
                    return data
                except json.JSONDecodeError as e:
                    logger.error(f"JSON解析失败: {e!s}")
                    return None

            return None

        except Exception as e:
            logger.error(f"获取消息失败: {e!s}")
            return None

    def close(self):
        """
        关闭连接
        """
        try:
            if self.pubsub:
                self.unsubscribe()
                self.pubsub.close()
                self.pubsub = None
                logger.info(f"关闭PubSub连接: {self.channel}")

            if self.redis_client:
                self.redis_client.close()
                self.redis_client = None
                logger.info(f"关闭Redis连接: {self.channel}")

        except Exception as e:
            logger.error(f"关闭连接失败: {e!s}")

    def __enter__(self):
        """上下文管理器入口"""
        self.subscribe()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器退出"""
        self.close()

    def __del__(self):
        """析构函数"""
        self.close()
