"""
WebSocket性能监控服务
Epic 3: 实时通信稳定性 - 性能优化
职责: 监控WebSocket连接和消息推送性能
遵循单一职责原则(SRP)
"""

import logging
import time
from typing import Dict, Optional

from prometheus_client import Counter, Gauge, Histogram

logger = logging.getLogger(__name__)


class WebSocketMetrics:
    """
    WebSocket性能监控服务

    职责:
    - 记录WebSocket连接建立时间
    - 记录消息推送延迟
    - 记录Redis Pub/Sub延迟
    - 提供Prometheus指标

    使用示例:
    >>> WebSocketMetrics.record_connection_time(project_id, stage, duration_ms)
    >>> WebSocketMetrics.record_message_latency(project_id, stage, latency_ms)
    """

    # Prometheus指标

    # WebSocket连接时间(毫秒)
    connection_time_histogram = Histogram(
        "websocket_connection_time_milliseconds",
        "WebSocket连接建立时间",
        ["project_id", "stage"],
        buckets=[5, 10, 25, 50, 100, 250, 500, 1000, 2500, 5000, 10000],
    )

    # 消息推送延迟(毫秒)
    message_latency_histogram = Histogram(
        "websocket_message_latency_milliseconds",
        "WebSocket消息推送延迟",
        ["project_id", "stage", "message_type"],
        buckets=[1, 5, 10, 25, 50, 100, 250, 500, 1000, 2500, 5000],
    )

    # Redis Pub/Sub延迟(毫秒)
    redis_publish_latency_histogram = Histogram(
        "redis_publish_latency_milliseconds",
        "Redis消息发布延迟",
        ["project_id", "stage"],
        buckets=[0.1, 0.5, 1, 5, 10, 25, 50, 100, 250, 500],
    )

    # WebSocket连接计数
    active_connections_gauge = Gauge(
        "websocket_active_connections", "当前活跃WebSocket连接数", ["project_id", "stage"]
    )

    # 消息推送计数
    messages_sent_counter = Counter(
        "websocket_messages_sent_total",
        "WebSocket消息发送总数",
        ["project_id", "stage", "message_type", "status"],
    )

    # Redis消息发布计数
    redis_messages_published_counter = Counter(
        "redis_messages_published_total", "Redis消息发布总数", ["project_id", "stage", "status"]
    )

    @staticmethod
    def record_connection_time(project_id: str, stage: str, duration_ms: float) -> None:
        """
        记录WebSocket连接建立时间

        Args:
            project_id: 项目ID
            stage: 阶段名称
            duration_ms: 连接建立耗时(毫秒)
        """
        try:
            WebSocketMetrics.connection_time_histogram.labels(
                project_id=project_id, stage=stage
            ).observe(duration_ms)

            logger.debug(
                f"WebSocket连接时间: project={project_id}, stage={stage}, duration={duration_ms}ms"
            )
        except Exception as e:
            logger.error(f"记录连接时间失败: {e}")

    @staticmethod
    def record_message_latency(
        project_id: str, stage: str, message_type: str, latency_ms: float, status: str = "success"
    ) -> None:
        """
        记录消息推送延迟

        Args:
            project_id: 项目ID
            stage: 阶段名称
            message_type: 消息类型
            latency_ms: 推送延迟(毫秒)
            status: 状态(success/error)
        """
        try:
            # 记录延迟
            WebSocketMetrics.message_latency_histogram.labels(
                project_id=project_id, stage=stage, message_type=message_type
            ).observe(latency_ms)

            # 记录发送计数
            WebSocketMetrics.messages_sent_counter.labels(
                project_id=project_id, stage=stage, message_type=message_type, status=status
            ).inc()

            # NFR-P4: 推送延迟应<500ms
            if latency_ms > 500:
                logger.warning(
                    f"消息推送延迟超标: project={project_id}, stage={stage}, "
                    f"latency={latency_ms}ms, threshold=500ms"
                )
        except Exception as e:
            logger.error(f"记录消息延迟失败: {e}")

    @staticmethod
    def record_redis_publish_latency(
        project_id: str, stage: str, latency_ms: float, status: str = "success"
    ) -> None:
        """
        记录Redis消息发布延迟

        Args:
            project_id: 项目ID
            stage: 阶段名称
            latency_ms: 发布延迟(毫秒)
            status: 状态(success/error)
        """
        try:
            # 记录延迟
            WebSocketMetrics.redis_publish_latency_histogram.labels(
                project_id=project_id, stage=stage
            ).observe(latency_ms)

            # 记录发布计数
            WebSocketMetrics.redis_messages_published_counter.labels(
                project_id=project_id, stage=stage, status=status
            ).inc()

            # NFR-I5: Redis延迟应<100ms
            if latency_ms > 100:
                logger.warning(
                    f"Redis发布延迟超标: project={project_id}, stage={stage}, "
                    f"latency={latency_ms}ms, threshold=100ms"
                )
        except Exception as e:
            logger.error(f"记录Redis发布延迟失败: {e}")

    @staticmethod
    def increment_active_connections(project_id: str, stage: str) -> None:
        """
        增加活跃连接计数

        Args:
            project_id: 项目ID
            stage: 阶段名称
        """
        try:
            WebSocketMetrics.active_connections_gauge.labels(
                project_id=project_id, stage=stage
            ).inc()
        except Exception as e:
            logger.error(f"增加连接计数失败: {e}")

    @staticmethod
    def decrement_active_connections(project_id: str, stage: str) -> None:
        """
        减少活跃连接计数

        Args:
            project_id: 项目ID
            stage: 阶段名称
        """
        try:
            WebSocketMetrics.active_connections_gauge.labels(
                project_id=project_id, stage=stage
            ).dec()
        except Exception as e:
            logger.error(f"减少连接计数失败: {e}")

    @staticmethod
    def get_metrics_summary(project_id: Optional[str] = None) -> Dict:
        """
        获取性能指标摘要

        Args:
            project_id: 项目ID(可选,不指定则返回所有项目)

        Returns:
            Dict: 性能指标摘要
            {
                'total_connections': int,
                'average_connection_time': float,
                'average_message_latency': float,
                'p95_message_latency': float,
                'p99_message_latency': float,
                'active_connections': int
            }
        """
        # 收集连接时间样本
        connection_samples = []
        for sample in WebSocketMetrics.connection_time_histogram.collect():
            for _name, labels, samples in sample.samples:
                if project_id is None or labels.get("project_id") == project_id:
                    connection_samples.extend(samples)

        # 收集消息延迟样本
        message_samples = []
        for sample in WebSocketMetrics.message_latency_histogram.collect():
            for _name, labels, samples in sample.samples:
                if project_id is None or labels.get("project_id") == project_id:
                    message_samples.extend(samples)

        # 计算统计信息
        summary = {
            "total_connections": sum(connection_samples),
            "average_connection_time": sum(connection_samples) / len(connection_samples)
            if connection_samples
            else 0,
            "average_message_latency": sum(message_samples) / len(message_samples)
            if message_samples
            else 0,
            "active_connections": 0,  # 需要从Gauge获取
        }

        # 计算百分位数
        if message_samples:
            sorted_samples = sorted(message_samples)
            n = len(sorted_samples)
            summary["p95_message_latency"] = sorted_samples[int(n * 0.95)] if n > 0 else 0
            summary["p99_message_latency"] = sorted_samples[int(n * 0.99)] if n > 0 else 0

        return summary


class ConnectionTimer:
    """
    连接时间计时器(上下文管理器)

    用于自动测量WebSocket连接建立时间

    使用示例:
    >>> with ConnectionTimer(project_id, stage) as timer:
    >>>     # 建立WebSocket连接
    >>>     await websocket.connect()
    >>> # 自动记录连接时间
    """

    def __init__(self, project_id: str, stage: str):
        """
        初始化计时器

        Args:
            project_id: 项目ID
            stage: 阶段名称
        """
        self.project_id = project_id
        self.stage = stage
        self.start_time = None

    def __enter__(self):
        """开始计时"""
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """结束计时并记录"""
        if self.start_time:
            duration_ms = (time.time() - self.start_time) * 1000
            WebSocketMetrics.record_connection_time(self.project_id, self.stage, duration_ms)

            # NFR-P2: 连接建立应<1秒
            if duration_ms > 1000:
                logger.warning(
                    f"WebSocket连接时间超标: project={self.project_id}, "
                    f"stage={self.stage}, duration={duration_ms}ms, threshold=1000ms"
                )

        return False


class MessageLatencyTimer:
    """
    消息延迟计时器(上下文管理器)

    用于自动测量消息推送延迟

    使用示例:
    >>> with MessageLatencyTimer(project_id, stage, 'stage_update') as timer:
    >>>     await websocket.send(text_data=json.dumps(message))
    >>> # 自动记录消息延迟
    """

    def __init__(self, project_id: str, stage: str, message_type: str):
        """
        初始化计时器

        Args:
            project_id: 项目ID
            stage: 阶段名称
            message_type: 消息类型
        """
        self.project_id = project_id
        self.stage = stage
        self.message_type = message_type
        self.start_time = None

    def __enter__(self):
        """开始计时"""
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """结束计时并记录"""
        if self.start_time:
            latency_ms = (time.time() - self.start_time) * 1000
            status = "error" if exc_type else "success"
            WebSocketMetrics.record_message_latency(
                self.project_id, self.stage, self.message_type, latency_ms, status
            )

        return False
