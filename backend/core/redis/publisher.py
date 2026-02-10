"""
Redis流式发布器
职责: 将流式数据发布到Redis Pub/Sub频道
遵循单一职责原则(SRP)
Epic 3: 集成进度历史记录功能
"""

import json
import logging
import time
from typing import Any, Dict, Optional

from django.conf import settings

import redis

logger = logging.getLogger(__name__)


class RedisStreamPublisher:
    """
    Redis流式发布器

    负责将AI生成的流式数据发布到Redis Pub/Sub频道
    前端可通过WebSocket订阅该频道接收实时数据

    频道命名规范: ai_story:project:{project_id}:stage:{stage_name}
    """

    def __init__(self, project_id: str, stage_name: str):
        """
        初始化发布器

        Args:
            project_id: 项目ID
            stage_name: 阶段名称 (rewrite/storyboard/image_generation等)
        """
        self.project_id = project_id
        self.stage_name = stage_name
        self.channel = f"ai_story:project:{project_id}:stage:{stage_name}"

        # 使用连接池
        self.redis_client = self._get_redis_client()

        logger.info(f"初始化Redis发布器: {self.channel}")

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

    def publish(self, message: Dict[str, Any]) -> bool:
        """
        发布消息到Redis频道

        Args:
            message: 消息字典

        Returns:
            bool: 是否发布成功
        """
        try:
            # 添加时间戳
            if "timestamp" not in message:
                message["timestamp"] = time.time()

            # 序列化为JSON
            message_json = json.dumps(message, ensure_ascii=False)

            # 发布到频道
            self.redis_client.publish(self.channel, message_json)

            # Epic 3: 记录关键消息到历史数据库
            self._record_to_history(message)

            # logger.debug(f"发布消息到 {self.channel}: {message.get('type')} (订阅者: {subscribers})")

            return True

        except redis.RedisError as e:
            logger.error(f"Redis发布失败: {e!s}")
            return False
        except Exception as e:
            logger.error(f"消息发布异常: {e!s}")
            return False

    def _record_to_history(self, message: Dict[str, Any]) -> bool:
        """
        Epic 3: 记录消息到历史数据库

        仅记录关键消息类型:
        - stage_update: 阶段状态更新
        - done: 任务完成
        - error: 错误
        - progress: 批量进度

        不记录高频token消息,避免数据库压力

        Args:
            message: 消息字典

        Returns:
            bool: 是否记录成功
        """
        message_type = message.get("type")

        # 仅记录关键消息类型
        if message_type not in ["stage_update", "done", "error", "progress"]:
            return True

        try:
            # 延迟导入,避免循环依赖
            from apps.projects.services import ProgressHistoryRecorder

            # 映射消息类型到历史记录类型
            if message_type == "stage_update":
                ProgressHistoryRecorder.record_stage_update(
                    project_id=self.project_id,
                    stage=self.stage_name,
                    status=message.get("status", "pending"),
                    progress=message.get("progress", 0),
                    message=message.get("message", ""),
                )
            elif message_type == "done":
                ProgressHistoryRecorder.record_done(
                    project_id=self.project_id,
                    stage=self.stage_name,
                    result=message.get("full_text", ""),
                    metadata=message.get("metadata"),
                )
            elif message_type == "error":
                ProgressHistoryRecorder.record_error(
                    project_id=self.project_id,
                    stage=self.stage_name,
                    error=message.get("error", ""),
                    retry_count=message.get("retry_count", 0),
                )
            elif message_type == "progress":
                # 批量进度消息,也记录为stage_update
                ProgressHistoryRecorder.record_stage_update(
                    project_id=self.project_id,
                    stage=self.stage_name,
                    status="processing",
                    progress=message.get("progress", 0),
                    message=f"处理进度: {message.get('current', 0)}/{message.get('total', 0)}",
                )

            return True

        except Exception as e:
            # 历史记录失败不应影响Redis发布
            logger.warning(f"记录历史失败: {e!s}")
            return False

    def publish_token(self, content: str, full_text: str = "") -> bool:
        """
        发布Token消息 (流式文本片段)

        Args:
            content: 文本片段
            full_text: 累积的完整文本

        Returns:
            bool: 是否发布成功
        """
        message = {
            "type": "token",
            "content": content,
            "full_text": full_text,
            "stage": self.stage_name,
            "project_id": self.project_id,
        }
        return self.publish(message)

    def publish_stage_update(
        self, status: str, progress: Optional[int] = None, message: Optional[str] = None
    ) -> bool:
        """
        发布阶段状态更新消息

        Args:
            status: 状态 (processing/completed/failed)
            progress: 进度百分比 (0-100)
            message: 状态描述

        Returns:
            bool: 是否发布成功
        """
        msg = {
            "type": "stage_update",
            "stage": self.stage_name,
            "status": status,
            "project_id": self.project_id,
        }

        if progress is not None:
            msg["progress"] = progress

        if message:
            msg["message"] = message

        return self.publish(msg)

    def publish_done(self, full_text: str = "", metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        发布完成消息

        Args:
            full_text: 完整生成结果
            metadata: 元数据 (tokens_used, latency_ms等)

        Returns:
            bool: 是否发布成功
        """
        message = {
            "type": "done",
            "stage": self.stage_name,
            "project_id": self.project_id,
            "full_text": full_text,
        }

        if metadata:
            message["metadata"] = metadata

        return self.publish(message)

    def publish_error(self, error: str, retry_count: int = 0) -> bool:
        """
        发布错误消息

        Args:
            error: 错误描述
            retry_count: 重试次数

        Returns:
            bool: 是否发布成功
        """
        message = {
            "type": "error",
            "stage": self.stage_name,
            "project_id": self.project_id,
            "error": error,
            "retry_count": retry_count,
        }
        return self.publish(message)

    def publish_progress(self, current: int, total: int, item_name: str = "") -> bool:
        """
        发布进度消息 (用于批量处理场景)

        Story 11.4.2: 增强格式，添加 current_step, total_steps, step_name 字段

        Args:
            current: 当前处理数量
            total: 总数量
            item_name: 当前处理项名称

        Returns:
            bool: 是否发布成功
        """
        progress = int((current / total) * 100) if total > 0 else 0

        message = {
            "type": "progress",
            "stage": self.stage_name,
            "project_id": self.project_id,
            "current": current,
            "total": total,
            "progress": progress,
            # Story 11.4.2: 添加前端进度组件期望的字段
            "current_step": current,
            "total_steps": total,
            "step_name": item_name,
        }

        if item_name:
            message["item_name"] = item_name

        return self.publish(message)

    def publish_stage_complete(
        self, duration: float, output_count: int = 0, next_stage: str = ""
    ) -> bool:
        """
        Story 11.4.2: 发布阶段完成事件

        Args:
            duration: 阶段耗时（秒）
            output_count: 输出数量
            next_stage: 下一阶段名称

        Returns:
            bool: 是否发布成功
        """
        message = {
            "type": "stage_complete",
            "stage_name": self.stage_name,
            "duration": duration,
            "output_count": output_count,
            "project_id": self.project_id,
        }

        if next_stage:
            message["next_stage"] = next_stage

        return self.publish(message)

    def publish_progress_detailed(
        self,
        percentage: float,
        current_step: int,
        total_steps: int,
        step_name: str = "",
    ) -> bool:
        """
        Story 11.4.2: 发布详细进度消息（匹配前端组件期望格式）

        Args:
            percentage: 进度百分比 (0-100)
            current_step: 当前步骤
            total_steps: 总步骤数
            step_name: 步骤名称

        Returns:
            bool: 是否发布成功
        """
        message = {
            "type": "progress",
            "stage": self.stage_name,
            "percentage": percentage,
            "current_step": current_step,
            "total_steps": total_steps,
            "step_name": step_name,
            "project_id": self.project_id,
        }

        return self.publish(message)

    def close(self):
        """
        关闭Redis连接
        """
        try:
            if self.redis_client:
                self.redis_client.close()
                logger.info(f"关闭Redis连接: {self.channel}")
        except Exception as e:
            logger.error(f"关闭Redis连接失败: {e!s}")

    def __enter__(self):
        """上下文管理器入口"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器退出"""
        self.close()
