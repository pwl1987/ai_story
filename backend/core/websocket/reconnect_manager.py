"""
WebSocket自动重连管理器
Epic 3: 实时通信稳定性 - 自动重连机制
职责: 管理WebSocket重连逻辑和策略
遵循单一职责原则(SRP)
"""

import asyncio
import contextlib
import logging
from enum import Enum
from typing import Callable, Optional

logger = logging.getLogger(__name__)


class ReconnectState(Enum):
    """重连状态枚举"""

    DISCONNECTED = "disconnected"  # 已断开
    CONNECTING = "connecting"  # 连接中
    CONNECTED = "connected"  # 已连接
    RECONNECTING = "reconnecting"  # 重连中
    FAILED = "failed"  # 重连失败


class ReconnectStrategy:
    """
    重连策略管理器

    职责:
    - 管理重连次数和间隔
    - 指数退避策略 (1s, 2s, 4s, 8s, 16s)
    - 最大重连次数限制

    使用示例:
    >>> strategy = ReconnectStrategy(max_retries=5)
    >>> async for attempt in strategy:
    >>>     # 尝试连接
    >>>     success = await connect()
    >>>     if success:
    >>>         strategy.on_success()
    >>>         break
    >>>     else:
    >>>         await strategy.on_failure()
    """

    def __init__(
        self,
        max_retries: int = 5,
        initial_delay: float = 1.0,
        max_delay: float = 16.0,
        backoff_multiplier: float = 2.0,
    ):
        """
        初始化重连策略

        Args:
            max_retries: 最大重连次数 (默认5次)
            initial_delay: 初始重连延迟(秒) (默认1秒)
            max_delay: 最大重连延迟(秒) (默认16秒)
            backoff_multiplier: 退避倍数 (默认2倍)
        """
        self.max_retries = max_retries
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.backoff_multiplier = backoff_multiplier

        self.retry_count = 0
        self.current_delay = initial_delay
        self.state = ReconnectState.DISCONNECTED

    def should_retry(self) -> bool:
        """
        判断是否应该继续重试

        Returns:
            bool: 是否可以继续重试
        """
        return self.retry_count < self.max_retries

    async def on_failure(self) -> None:
        """
        连接失败时的处理

        - 增加重连计数
        - 计算下次重连延迟
        - 更新状态
        """
        self.retry_count += 1
        self.state = ReconnectState.RECONNECTING

        if self.should_retry():
            # 指数退避: 1s, 2s, 4s, 8s, 16s
            delay = min(
                self.initial_delay * (self.backoff_multiplier ** (self.retry_count - 1)),
                self.max_delay,
            )
            self.current_delay = delay

            logger.warning(
                f"连接失败，{delay:.1f}秒后进行第{self.retry_count}次重连 "
                f"(最多{self.max_retries}次)"
            )

            # 等待延迟时间
            await asyncio.sleep(delay)
        else:
            # 重连次数耗尽
            self.state = ReconnectState.FAILED
            logger.error(f"重连失败: 已达到最大重连次数({self.max_retries}次)")

    def on_success(self) -> None:
        """
        连接成功时的处理

        - 重置重连计数
        - 重置延迟
        - 更新状态
        """
        self.retry_count = 0
        self.current_delay = self.initial_delay
        self.state = ReconnectState.CONNECTED

        logger.info("连接成功，重置重连计数")

    def get_state(self) -> ReconnectState:
        """获取当前重连状态"""
        return self.state

    def get_retry_count(self) -> int:
        """获取当前重连次数"""
        return self.retry_count

    def get_next_delay(self) -> float:
        """获取下次重连延迟"""
        return self.current_delay


class WebSocketReconnectManager:
    """
    WebSocket自动重连管理器

    职责:
    - 管理WebSocket重连生命周期
    - 集成ReconnectStrategy
    - 提供重连回调接口
    - 监控连接健康状态

    使用示例:
    >>> manager = WebSocketReconnectManager(
    >>>     project_id='proj-1',
    >>>     stage='rewrite',
    >>>     connect_callback=lambda: connect_to_redis()
    >>> )
    >>> await manager.start()
    """

    def __init__(
        self,
        project_id: str,
        stage: str,
        connect_callback: Callable,
        disconnect_callback: Optional[Callable] = None,
        max_retries: int = 5,
        ping_interval: int = 30,
        ping_timeout: int = 60,
    ):
        """
        初始化重连管理器

        Args:
            project_id: 项目ID
            stage: 阶段名称
            connect_callback: 连接回调函数 (返回bool表示成功/失败)
            disconnect_callback: 断开回调函数 (可选)
            max_retries: 最大重连次数
            ping_interval: 心跳间隔(秒) (默认30秒)
            ping_timeout: 心跳超时(秒) (默认60秒)
        """
        self.project_id = project_id
        self.stage = stage
        self.connect_callback = connect_callback
        self.disconnect_callback = disconnect_callback

        # 重连策略
        self.strategy = ReconnectStrategy(max_retries=max_retries)

        # 心跳检测
        self.last_ping_time = None
        self.ping_interval = ping_interval
        self.ping_timeout = ping_timeout

        # 连接状态
        self.is_connected = False
        self.reconnect_task = None

    async def start(self) -> bool:
        """
        启动自动重连管理器

        Returns:
            bool: 连接是否成功
        """
        self.strategy.state = ReconnectState.CONNECTING

        # 尝试连接
        success = await self._attempt_connect()

        if success:
            self.strategy.on_success()
            self.is_connected = True
            return True
        else:
            # 启动重连任务
            await self._start_reconnect_loop()
            return self.strategy.state == ReconnectState.CONNECTED

    async def _attempt_connect(self) -> bool:
        """
        尝试建立连接

        Returns:
            bool: 连接是否成功
        """
        try:
            logger.info(
                f"尝试连接: project={self.project_id}, stage={self.stage}, "
                f"attempt={self.strategy.retry_count + 1}"
            )

            # 调用连接回调
            success = await self.connect_callback()

            if success:
                logger.info(f"连接成功: project={self.project_id}, stage={self.stage}")
                return True
            else:
                logger.warning(f"连接失败: project={self.project_id}, stage={self.stage}")
                return False

        except Exception as e:
            logger.error(f"连接异常: {e}")
            return False

    async def _start_reconnect_loop(self) -> None:
        """启动重连循环"""
        while self.strategy.should_retry():
            # 等待重连延迟
            await self.strategy.on_failure()

            # 尝试重连
            success = await self._attempt_connect()

            if success:
                self.strategy.on_success()
                self.is_connected = True
                break

        # 检查最终状态
        if not self.strategy.should_retry():
            self.strategy.state = ReconnectState.FAILED
            logger.error(
                f"重连失败: project={self.project_id}, stage={self.stage}, "
                f"retries={self.strategy.retry_count}"
            )

    async def stop(self) -> None:
        """停止重连管理器"""
        self.is_connected = False
        self.strategy.state = ReconnectState.DISCONNECTED

        # 取消重连任务
        if self.reconnect_task and not self.reconnect_task.done():
            self.reconnect_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self.reconnect_task

        # 调用断开回调
        if self.disconnect_callback:
            await self.disconnect_callback()

        logger.info(f"重连管理器已停止: project={self.project_id}, stage={self.stage}")

    def on_ping(self, timestamp: float) -> None:
        """
        收到心跳ping消息

        Args:
            timestamp: ping时间戳
        """
        self.last_ping_time = timestamp
        logger.debug(
            f"收到ping: project={self.project_id}, stage={self.stage}, timestamp={timestamp}"
        )

    def check_health(self) -> bool:
        """
        检查连接健康状态

        Returns:
            bool: 连接是否健康
        """
        import time

        if not self.is_connected:
            return False

        # 检查心跳超时
        if self.last_ping_time:
            elapsed = time.time() - self.last_ping_time
            if elapsed > self.ping_timeout:
                logger.warning(
                    f"心跳超时: project={self.project_id}, stage={self.stage}, "
                    f"elapsed={elapsed:.1f}s"
                )
                return False

        return True

    def get_state(self) -> ReconnectState:
        """获取当前状态"""
        return self.strategy.get_state()

    def get_retry_count(self) -> int:
        """获取重连次数"""
        return self.strategy.get_retry_count()

    def is_reconnecting(self) -> bool:
        """是否正在重连"""
        return self.strategy.state == ReconnectState.RECONNECTING
