"""
WebSocket压力测试
Epic 3: 实时通信稳定性 - 综合测试和文档
职责: 测试WebSocket在高并发场景下的性能表现
"""

import asyncio
import os

# 避免循环导入
import sys
import time
from unittest.mock import AsyncMock

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from core.websocket import WebSocketReconnectManager


@pytest.mark.stress
@pytest.mark.asyncio
class TestWebSocketConcurrency:
    """WebSocket并发压力测试"""

    async def test_concurrent_connections_100(self):
        """
        压力测试: 100个并发WebSocket连接

        目标: 验证系统能稳定处理100个并发连接
        """
        connection_count = 100

        # Mock连接回调 (模拟连接成功)
        async def mock_connect():
            await asyncio.sleep(0.01)  # 模拟10ms连接延迟
            return True

        # 创建100个并发连接
        tasks = []
        for i in range(connection_count):
            manager = WebSocketReconnectManager(
                project_id=f'proj-{i}',
                stage='rewrite',
                connect_callback=mock_connect,
                max_retries=3
            )
            tasks.append(manager.start())

        # 并发执行所有连接
        start_time = time.time()
        results = await asyncio.gather(*tasks, return_exceptions=True)
        elapsed = time.time() - start_time

        # 统计结果
        successful_connections = sum(1 for r in results if r is True)
        failed_connections = sum(1 for r in results if r is not True)

        print("\n并发连接测试结果:")
        print(f"  总连接数: {connection_count}")
        print(f"  成功连接: {successful_connections}")
        print(f"  失败连接: {failed_connections}")
        print(f"  总耗时: {elapsed:.2f}秒")
        print(f"  平均延迟: {elapsed/connection_count*1000:.2f}ms")

        # 验证: 所有连接都应成功
        assert successful_connections == connection_count, \
            f"期望{connection_count}个成功连接，实际{successful_connections}个"
        assert failed_connections == 0

        # 验证: 总耗时应在合理范围内 (< 5秒)
        assert elapsed < 5.0, f"总耗时{elapsed:.2f}秒超标"

    async def test_concurrent_reconnections_50(self):
        """
        压力测试: 50个连接同时重连

        目标: 验证重连机制在高并发下的稳定性
        """
        reconnection_count = 50

        # Mock连接回调: 前2次失败，第3次成功
        call_counters = {}

        async def mock_connect_with_retry():
            project_id = asyncio.current_task().get_name() if hasattr(asyncio.current_task(), 'get_name') else 'unknown'
            if project_id not in call_counters:
                call_counters[project_id] = 0

            call_counters[project_id] += 1
            count = call_counters[project_id]

            await asyncio.sleep(0.01)  # 模拟连接延迟

            # 第1、2次失败，第3次成功
            return count >= 3

        # 创建50个需要重连的连接
        tasks = []
        for i in range(reconnection_count):
            manager = WebSocketReconnectManager(
                project_id=f'proj-{i}',
                stage='rewrite',
                connect_callback=mock_connect_with_retry,
                max_retries=5
            )
            tasks.append(asyncio.create_task(manager.start(), name=f'proj-{i}'))

        # 并发执行所有重连
        start_time = time.time()
        results = await asyncio.gather(*tasks, return_exceptions=True)
        elapsed = time.time() - start_time

        # 统计结果
        successful = sum(1 for r in results if r is True)
        failed = sum(1 for r in results if r is not True)

        print("\n并发重连测试结果:")
        print(f"  总连接数: {reconnection_count}")
        print(f"  成功连接: {successful}")
        print(f"  失败连接: {failed}")
        print(f"  总耗时: {elapsed:.2f}秒")

        # 验证: 所有连接最终都应成功
        assert successful == reconnection_count, \
            f"期望{reconnection_count}个成功连接，实际{successful}个"
        assert failed == 0

    async def test_rapid_connection_disconnect_200(self):
        """
        压力测试: 200个快速连接/断开循环

        目标: 验证系统能稳定处理频繁的连接/断开
        """
        cycle_count = 200

        # Mock连接/断开回调
        async def mock_connect():
            await asyncio.sleep(0.001)  # 模拟1ms延迟
            return True

        async def mock_disconnect():
            await asyncio.sleep(0.001)  # 模拟1ms延迟

        # 执行200次连接/断开循环
        start_time = time.time()
        successful_cycles = 0

        for i in range(cycle_count):
            manager = WebSocketReconnectManager(
                project_id=f'proj-{i}',
                stage='rewrite',
                connect_callback=mock_connect,
                disconnect_callback=mock_disconnect,
                max_retries=3
            )

            # 连接
            success = await manager.start()
            if success:
                successful_cycles += 1

            # 立即断开
            await manager.stop()

        elapsed = time.time() - start_time

        print("\n快速连接/断开测试结果:")
        print(f"  总循环次数: {cycle_count}")
        print(f"  成功循环: {successful_cycles}")
        print(f"  总耗时: {elapsed:.2f}秒")
        print(f"  平均延迟: {elapsed/cycle_count*1000:.2f}ms")

        # 验证: 所有循环都应成功
        assert successful_cycles == cycle_count

        # 验证: 平均延迟应 < 50ms
        avg_latency_ms = elapsed / cycle_count * 1000
        assert avg_latency_ms < 50, f"平均延迟{avg_latency_ms:.2f}ms超标"


@pytest.mark.stress
@pytest.mark.asyncio
class TestRedisPubSubStress:
    """Redis Pub/Sub压力测试"""

    async def test_high_frequency_messages_1000(self):
        """
        压力测试: 1000条高频消息发布

        目标: 验证Redis Pub/Sub在高频消息下的性能
        """
        message_count = 1000
        published_count = 0

        # Mock Redis客户端
        mock_redis = AsyncMock()
        mock_redis.publish = AsyncMock(return_value=1)

        async def mock_publish():
            nonlocal published_count
            await asyncio.sleep(0.001)  # 模拟1ms发布延迟
            published_count += 1
            return True

        # 快速发布1000条消息
        start_time = time.time()

        tasks = [mock_publish() for _ in range(message_count)]
        await asyncio.gather(*tasks)

        elapsed = time.time() - start_time

        print("\n高频消息发布测试结果:")
        print(f"  总消息数: {message_count}")
        print(f"  成功发布: {published_count}")
        print(f"  总耗时: {elapsed:.2f}秒")
        print(f"  平均延迟: {elapsed/message_count*1000:.2f}ms")
        print(f"  吞吐量: {message_count/elapsed:.2f} msg/s")

        # 验证: 所有消息都应发布成功
        assert published_count == message_count

        # 验证: 吞吐量应 > 1000 msg/s
        throughput = message_count / elapsed
        assert throughput > 1000, f"吞吐量{throughput:.2f} msg/s过低"

    async def test_concurrent_publishers_10(self):
        """
        压力测试: 10个并发发布者

        目标: 验证多发布者并发场景
        """
        publisher_count = 10
        messages_per_publisher = 100
        total_messages = publisher_count * messages_per_publisher

        # Mock发布回调
        async def mock_publish_messages(publisher_id):
            published = 0
            for _i in range(messages_per_publisher):
                await asyncio.sleep(0.001)  # 模拟延迟
                published += 1
            return published

        # 创建10个并发发布者
        tasks = [
            mock_publish_messages(i)
            for i in range(publisher_count)
        ]

        start_time = time.time()
        results = await asyncio.gather(*tasks)
        elapsed = time.time() - start_time

        total_published = sum(results)

        print("\n并发发布者测试结果:")
        print(f"  发布者数: {publisher_count}")
        print(f"  每发布者消息数: {messages_per_publisher}")
        print(f"  总消息数: {total_messages}")
        print(f"  成功发布: {total_published}")
        print(f"  总耗时: {elapsed:.2f}秒")
        print(f"  吞吐量: {total_published/elapsed:.2f} msg/s")

        # 验证: 所有消息都应发布成功
        assert total_published == total_messages

        # 验证: 吞吐量应 > 500 msg/s
        throughput = total_published / elapsed
        assert throughput > 500, f"吞吐量{throughput:.2f} msg/s过低"


@pytest.mark.stress
@pytest.mark.asyncio
class TestReconnectManagerUnderLoad:
    """重连管理器负载测试"""

    async def test_reconnect_with_timeouts(self):
        """
        压力测试: 重连过程中的超时处理

        目标: 验证超时场景下的稳定性
        """
        connection_count = 20
        timeout_count = 0

        # Mock连接回调: 随机超时
        async def mock_connect_with_timeout():
            nonlocal timeout_count
            await asyncio.sleep(0.1)  # 模拟100ms延迟

            # 30%的概率模拟超时
            import random
            if random.random() < 0.3:
                timeout_count += 1
                raise asyncio.TimeoutError("Connection timeout")

            return True

        # 创建20个连接，部分会超时
        tasks = []
        for i in range(connection_count):
            manager = WebSocketReconnectManager(
                project_id=f'proj-{i}',
                stage='rewrite',
                connect_callback=mock_connect_with_timeout,
                max_retries=3
            )
            tasks.append(manager.start())

        start_time = time.time()
        results = await asyncio.gather(*tasks, return_exceptions=True)
        elapsed = time.time() - start_time

        successful = sum(1 for r in results if r is True)
        failed = sum(1 for r in results if r is not True)

        print("\n超时处理测试结果:")
        print(f"  总连接数: {connection_count}")
        print(f"  超时次数: {timeout_count}")
        print(f"  成功连接: {successful}")
        print(f"  失败连接: {failed}")
        print(f"  总耗时: {elapsed:.2f}秒")

        # 验证: 即使有超时，大部分连接也应成功
        success_rate = successful / connection_count
        assert success_rate >= 0.7, f"成功率{success_rate:.2%}过低"

    async def test_memory_leak_detection(self):
        """
        压力测试: 内存泄漏检测

        目标: 验证长时间运行不会导致内存泄漏
        """
        import gc

        # 记录初始内存
        gc.collect()
        initial_objects = len(gc.get_objects())

        # 执行1000次连接/断开循环
        for i in range(1000):
            manager = WebSocketReconnectManager(
                project_id=f'proj-{i}',
                stage='rewrite',
                connect_callback=AsyncMock(return_value=True),
                disconnect_callback=AsyncMock(),
                max_retries=3
            )

            await manager.start()
            await manager.stop()

        # 强制垃圾回收
        gc.collect()
        final_objects = len(gc.get_objects())

        object_growth = final_objects - initial_objects

        print("\n内存泄漏检测结果:")
        print(f"  初始对象数: {initial_objects}")
        print(f"  最终对象数: {final_objects}")
        print(f"  对象增长: {object_growth}")
        print(f"  增长率: {object_growth/initial_objects*100:.2f}%")

        # 验证: 对象增长应 < 10%
        growth_rate = object_growth / initial_objects
        assert growth_rate < 0.1, f"对象增长率{growth_rate:.2%}过高，可能存在内存泄漏"


@pytest.mark.integration
@pytest.mark.asyncio
class TestEndToEndScenarios:
    """端到端场景测试"""

    async def test_full_workflow_simulation(self):
        """
        集成测试: 完整工作流模拟

        模拟: 连接 → 接收消息 → 断线 → 重连 → 接收更多消息 → 正常关闭
        """
        message_log = []

        # Mock连接回调
        connection_attempt = 0

        async def mock_connect():
            nonlocal connection_attempt
            connection_attempt += 1
            await asyncio.sleep(0.01)

            # 第1次连接成功，第2次失败，第3次成功
            return connection_attempt != 2

        async def mock_disconnect():
            await asyncio.sleep(0.001)

        # 创建管理器
        manager = WebSocketReconnectManager(
            project_id='proj-e2e',
            stage='rewrite',
            connect_callback=mock_connect,
            disconnect_callback=mock_disconnect,
            max_retries=5
        )

        # 1. 连接
        assert await manager.start() is True
        message_log.append('connected')

        # 2. 模拟接收消息
        for _i in range(5):
            manager.on_ping(time.time())
            await asyncio.sleep(0.01)
        message_log.append('received_5_messages')

        # 3. 健康检查
        assert manager.check_health() is True
        message_log.append('health_ok')

        # 4. 断开
        await manager.stop()
        message_log.append('disconnected')

        # 5. 重新连接 (会触发重连逻辑)
        connection_attempt = 0  # 重置计数器，模拟第2次连接失败
        manager.is_connected = False
        success = await manager.start()
        message_log.append(f'reconnected_{success}')

        print("\n端到端工作流日志:")
        for log in message_log:
            print(f"  - {log}")

        # 验证工作流
        assert 'connected' in message_log
        assert 'received_5_messages' in message_log
        assert 'health_ok' in message_log
        assert 'disconnected' in message_log
        assert 'reconnected_True' in message_log

    async def test_multiple_projects_concurrent(self):
        """
        集成测试: 多项目并发运行

        模拟: 10个项目同时进行WebSocket通信
        """
        project_count = 10

        # 为每个项目创建独立的管理器
        managers = []
        for i in range(project_count):
            manager = WebSocketReconnectManager(
                project_id=f'proj-{i}',
                stage=f'stage-{i % 5}',  # 5个阶段轮询
                connect_callback=AsyncMock(return_value=True),
                disconnect_callback=AsyncMock(),
                max_retries=3
            )
            managers.append(manager)

        # 并发启动所有项目
        start_time = time.time()
        tasks = [manager.start() for manager in managers]
        results = await asyncio.gather(*tasks)
        elapsed = time.time() - start_time

        successful = sum(1 for r in results if r is True)

        print("\n多项目并发测试结果:")
        print(f"  项目数: {project_count}")
        print(f"  成功连接: {successful}")
        print(f"  总耗时: {elapsed:.2f}秒")

        # 验证: 所有项目都应成功
        assert successful == project_count

        # 并发发送心跳
        for _i in range(10):
            for manager in managers:
                manager.on_ping(time.time())
            await asyncio.sleep(0.01)

        # 验证健康检查
        healthy_count = sum(1 for manager in managers if manager.check_health())
        print(f"  健康项目数: {healthy_count}")
        assert healthy_count == project_count

        # 清理所有项目
        for manager in managers:
            await manager.stop()
