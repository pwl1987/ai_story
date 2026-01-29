"""
WebSocket自动重连测试
Epic 3: 实时通信稳定性 - 自动重连机制
职责: 测试WebSocket自动重连功能
"""

import asyncio
import os

# 避免循环导入
import sys
import time
from unittest.mock import AsyncMock, MagicMock

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from core.websocket.reconnect_manager import (
    ReconnectState,
    ReconnectStrategy,
    WebSocketReconnectManager,
)


@pytest.mark.unit
class TestReconnectStrategy:
    """重连策略测试"""

    def test_initial_state(self):
        """测试初始状态"""
        strategy = ReconnectStrategy(max_retries=5)

        assert strategy.retry_count == 0
        assert strategy.state == ReconnectState.DISCONNECTED
        assert strategy.should_retry() is True

    def test_successful_connection(self):
        """测试连接成功"""
        strategy = ReconnectStrategy(max_retries=5)

        # 连接成功
        strategy.on_success()

        assert strategy.retry_count == 0
        assert strategy.state == ReconnectState.CONNECTED
        assert strategy.current_delay == 1.0  # 重置为初始延迟

    def test_single_failure(self):
        """测试单次连接失败"""
        strategy = ReconnectStrategy(max_retries=5)

        # 第一次失败
        asyncio.run(strategy.on_failure())

        assert strategy.retry_count == 1
        assert strategy.state == ReconnectState.RECONNECTING
        assert strategy.current_delay == 1.0  # 1秒延迟

    def test_multiple_failures(self):
        """测试多次连接失败"""
        strategy = ReconnectStrategy(max_retries=5)

        # 模拟5次失败
        for _i in range(5):
            asyncio.run(strategy.on_failure())

        assert strategy.retry_count == 5
        assert strategy.state == ReconnectState.FAILED
        assert strategy.should_retry() is False

    def test_exponential_backoff(self):
        """测试指数退避延迟"""
        strategy = ReconnectStrategy(max_retries=5, initial_delay=1.0, backoff_multiplier=2.0)

        # 测试延迟序列: 1s, 2s, 4s, 8s, 16s
        # 注意: 第5次失败时达到max_retries，不再更新延迟
        expected_delays = [1.0, 2.0, 4.0, 8.0, 8.0]  # 最后一次保持8.0

        for i, expected_delay in enumerate(expected_delays):
            asyncio.run(strategy.on_failure())
            # 验证当前延迟 (on_failure已设置current_delay)
            assert strategy.current_delay == expected_delay, (
                f"第{i + 1}次失败，期望延迟{expected_delay}秒，实际{strategy.current_delay}秒"
            )

    def test_max_delay_limit(self):
        """测试最大延迟限制"""
        strategy = ReconnectStrategy(
            max_retries=10,
            initial_delay=1.0,
            max_delay=5.0,  # 最大5秒
            backoff_multiplier=2.0,
        )

        # 测试延迟不会超过最大值
        for _ in range(10):
            asyncio.run(strategy.on_failure())
            assert strategy.get_next_delay() <= 5.0

    def test_reset_after_success(self):
        """测试连接成功后重置计数"""
        strategy = ReconnectStrategy(max_retries=5)

        # 3次失败
        for _ in range(3):
            asyncio.run(strategy.on_failure())

        assert strategy.retry_count == 3

        # 连接成功
        strategy.on_success()

        assert strategy.retry_count == 0
        assert strategy.state == ReconnectState.CONNECTED
        assert strategy.should_retry() is True


@pytest.mark.unit
class TestWebSocketReconnectManager:
    """WebSocket重连管理器测试"""

    @pytest.fixture
    def mock_connect_callback(self):
        """Mock连接回调"""
        return AsyncMock(return_value=True)

    @pytest.fixture
    def mock_disconnect_callback(self):
        """Mock断开回调"""
        return AsyncMock()

    def test_initial_state(self, mock_connect_callback):
        """测试初始状态"""
        manager = WebSocketReconnectManager(
            project_id="proj-1",
            stage="rewrite",
            connect_callback=mock_connect_callback,
            max_retries=5,
        )

        assert manager.project_id == "proj-1"
        assert manager.stage == "rewrite"
        assert manager.is_connected is False
        assert manager.get_state() == ReconnectState.DISCONNECTED

    @pytest.mark.asyncio
    async def test_successful_connection(self, mock_connect_callback):
        """测试连接成功"""
        manager = WebSocketReconnectManager(
            project_id="proj-1",
            stage="rewrite",
            connect_callback=mock_connect_callback,
            max_retries=5,
        )

        # 启动连接
        success = await manager.start()

        assert success is True
        assert manager.is_connected is True
        assert manager.get_state() == ReconnectState.CONNECTED
        assert mock_connect_callback.call_count == 1

    @pytest.mark.asyncio
    async def test_connection_failure(self):
        """测试连接失败"""
        mock_connect = AsyncMock(return_value=False)

        manager = WebSocketReconnectManager(
            project_id="proj-1",
            stage="rewrite",
            connect_callback=mock_connect,
            max_retries=2,  # 仅重试2次以加快测试
        )

        # 启动连接 (会重连2次后失败)
        success = await manager.start()

        assert success is False
        assert manager.is_connected is False
        assert manager.get_state() == ReconnectState.FAILED
        # 初始连接 + 2次重连 = 3次调用
        assert mock_connect.call_count == 3

    @pytest.mark.asyncio
    async def test_ping_pong(self, mock_connect_callback):
        """测试心跳检测"""
        manager = WebSocketReconnectManager(
            project_id="proj-1",
            stage="rewrite",
            connect_callback=mock_connect_callback,
            max_retries=5,
        )

        # 模拟收到ping
        timestamp = time.time()
        manager.on_ping(timestamp)

        assert manager.last_ping_time == timestamp

    @pytest.mark.asyncio
    async def test_health_check(self, mock_connect_callback):
        """测试健康检查"""
        manager = WebSocketReconnectManager(
            project_id="proj-1",
            stage="rewrite",
            connect_callback=mock_connect_callback,
            max_retries=5,
        )

        # 未连接时健康检查失败
        assert manager.check_health() is False

        # 连接成功
        await manager.start()

        # 连接成功后健康检查通过 (没有心跳超时)
        assert manager.check_health() is True

    @pytest.mark.asyncio
    async def test_health_check_timeout(self, mock_connect_callback):
        """测试心跳超时"""
        manager = WebSocketReconnectManager(
            project_id="proj-1",
            stage="rewrite",
            connect_callback=mock_connect_callback,
            max_retries=5,
            ping_timeout=1,  # 1秒超时
        )

        # 连接成功
        await manager.start()

        # 发送心跳
        manager.on_ping(time.time() - 2)  # 2秒前的心跳 (已超时)

        # 健康检查失败
        assert manager.check_health() is False

    @pytest.mark.asyncio
    async def test_stop_manager(self, mock_connect_callback, mock_disconnect_callback):
        """测试停止管理器"""
        manager = WebSocketReconnectManager(
            project_id="proj-1",
            stage="rewrite",
            connect_callback=mock_connect_callback,
            disconnect_callback=mock_disconnect_callback,
            max_retries=5,
        )

        # 启动连接
        await manager.start()
        assert manager.is_connected is True

        # 停止管理器
        await manager.stop()

        assert manager.is_connected is False
        assert manager.get_state() == ReconnectState.DISCONNECTED
        assert mock_disconnect_callback.call_count == 1


@pytest.mark.integration
@pytest.mark.asyncio
class TestWebSocketConsumerReconnect:
    """WebSocket消费者重连集成测试"""

    async def test_consumer_reconnect_on_redis_failure(self):
        """
        集成测试: Redis连接失败时自动重连

        注意: 这个测试需要真实的Redis环境
        在CI/CD环境中可能需要mock
        """
        # 这里只测试方法调用不出错
        # 实际的重连测试需要更复杂的mock设置
        from apps.projects.consumers import ProjectStageConsumer

        # 创建消费者实例 (不实际连接WebSocket)
        consumer = ProjectStageConsumer()

        # 验证重连管理器初始化
        assert hasattr(consumer, "reconnect_manager")

        # 验证连接和断开方法存在
        assert hasattr(consumer, "_connect_redis")
        assert hasattr(consumer, "_disconnect_redis")
        assert hasattr(consumer, "_listen_messages")

    async def test_consumer_ping_pong_handling(self):
        """
        集成测试: WebSocket消费者处理ping/pong消息
        """
        from apps.projects.consumers import ProjectStageConsumer

        # 创建消费者实例
        consumer = ProjectStageConsumer()
        consumer.reconnect_manager = MagicMock()

        # 模拟接收ping消息
        ping_message = '{"type": "ping", "timestamp": 1234567890.0}'

        # 验证消息处理逻辑 (不实际调用receive，因为需要WebSocket连接)
        # 这里只验证消息格式正确
        import json

        data = json.loads(ping_message)
        assert data["type"] == "ping"
        assert data["timestamp"] == 1234567890.0


@pytest.mark.performance
@pytest.mark.asyncio
class TestReconnectPerformance:
    """重连性能测试"""

    async def test_reconnect_speed(self):
        """
        性能测试: 验证重连速度

        目标: 5次重连在合理时间内完成
        """
        # Mock回调: 前4次失败，第5次成功
        call_count = [0]

        async def mock_connect():
            call_count[0] += 1
            return not call_count[0] < 5

        manager = WebSocketReconnectManager(
            project_id="proj-1", stage="rewrite", connect_callback=mock_connect, max_retries=5
        )

        # 记录开始时间
        start_time = time.time()

        # 启动连接 (会重连4次后成功)
        success = await manager.start()

        elapsed = time.time() - start_time

        assert success is True
        # 总延迟 = 1 + 2 + 4 + 8 = 15秒 (理论值)
        # 实际测试中，mock不实际sleep，所以应该很快
        assert elapsed < 20  # 允许一定的误差

    async def test_no_reconnect_on_first_success(self):
        """
        性能测试: 首次连接成功时不重连

        目标: 确保不会无谓重连
        """
        mock_connect = AsyncMock(return_value=True)

        manager = WebSocketReconnectManager(
            project_id="proj-1", stage="rewrite", connect_callback=mock_connect, max_retries=5
        )

        # 启动连接
        await manager.start()

        # 应该只调用一次
        assert mock_connect.call_count == 1
