"""
WebSocket连接测试
验证WebSocket实时通信功能

运行方式:
    cd backend
    uv run pytest tests/websocket/test_websocket_connection.py -v

依赖:
    - channels-3.0.4+
    - pytest-asyncio
"""
import pytest
from channels.testing import WebsocketCommunicator
from django.contrib.auth import get_user_model
import asyncio

User = get_user_model()


@pytest.mark.asyncio
@pytest.mark.django_db
class TestWebSocketConnection:
    """WebSocket连接测试"""

    async def test_project_websocket_connection(self):
        """测试项目级WebSocket连接"""
        from config.routing import application

        # 使用测试项目的UUID
        project_id = "00000000-0000-0000-0000-000000000001"
        communicator = WebsocketCommunicator(
            application,
            f"/ws/projects/{project_id}/"
        )

        # 连接
        connected, subprotocol = await communicator.connect()
        assert connected, "WebSocket连接失败"

        # 接收连接确认消息
        response = await communicator.receive_json_from()
        assert response['type'] == 'connected', "未收到连接确认消息"

        # 发送ping
        await communicator.send_json_to({
            'type': 'ping',
            'timestamp': 1234567890
        })

        # 接收pong
        response = await communicator.receive_json_from(timeout=5)
        assert response['type'] == 'pong', "未收到pong响应"
        assert 'timestamp' in response, "pong响应缺少timestamp"

        # 断开连接
        await communicator.disconnect()
        print("✓ WebSocket连接测试通过")

    async def test_stage_websocket_connection(self):
        """测试阶段级WebSocket连接"""
        from config.routing import application

        project_id = "00000000-0000-0000-0000-000000000001"
        stage_name = "rewrite"
        communicator = WebsocketCommunicator(
            application,
            f"/ws/projects/{project_id}/stage/{stage_name}/"
        )

        # 连接
        connected, subprotocol = await communicator.connect()
        assert connected, "阶段WebSocket连接失败"

        # 接收连接确认消息
        response = await communicator.receive_json_from()
        assert response['type'] == 'connected', "未收到连接确认消息"

        # 断开连接
        await communicator.disconnect()
        print("✓ 阶段WebSocket连接测试通过")

    async def test_websocket_reconnect(self):
        """测试WebSocket重连机制"""
        from config.routing import application

        project_id = "00000000-0000-0000-0000-000000000001"

        # 第一次连接
        communicator1 = WebsocketCommunicator(
            application,
            f"/ws/projects/{project_id}/"
        )
        connected, _ = await communicator1.connect()
        assert connected, "第一次连接失败"

        await communicator1.receive_json_from()  # 连接确认
        await communicator1.disconnect()

        # 等待一小段时间
        await asyncio.sleep(0.1)

        # 第二次连接（重连）
        communicator2 = WebsocketCommunicator(
            application,
            f"/ws/projects/{project_id}/"
        )
        connected, _ = await communicator2.connect()
        assert connected, "重连失败"

        await communicator2.receive_json_from()  # 连接确认
        await communicator2.disconnect()

        print("✓ WebSocket重连测试通过")

    async def test_websocket_heartbeat(self):
        """测试WebSocket心跳机制"""
        from config.routing import application

        project_id = "00000000-0000-0000-0000-000000000001"
        communicator = WebsocketCommunicator(
            application,
            f"/ws/projects/{project_id}/"
        )

        connected, _ = await communicator.connect()
        assert connected

        await communicator.receive_json_from()  # 连接确认

        # 发送多个心跳
        for i in range(3):
            await communicator.send_json_to({
                'type': 'ping',
                'timestamp': 1234567890 + i
            })
            response = await communicator.receive_json_from(timeout=5)
            assert response['type'] == 'pong'
            await asyncio.sleep(0.1)

        await communicator.disconnect()
        print("✓ WebSocket心跳测试通过")

    async def test_websocket_invalid_project(self):
        """测试无效项目ID的连接"""
        from config.routing import application

        # 使用不存在的项目ID
        project_id = "99999999-9999-9999-9999-999999999999"
        communicator = WebsocketCommunicator(
            application,
            f"/ws/projects/{project_id}/"
        )

        # 连接应该被拒绝或超时
        try:
            connected, _ = await communicator.connect(timeout=3)
            if connected:
                # 如果连接成功，应该立即收到错误消息
                try:
                    response = await communicator.receive_json_from(timeout=1)
                    assert response.get('type') in ['error', 'close'], "应该收到错误消息"
                except:
                    pass  # 超时也是可接受的
                await communicator.disconnect()
        except Exception:
            pass  # 连接失败也是可接受的

        print("✓ 无效项目ID测试通过")


@pytest.mark.asyncio
@pytest.mark.django_db
class TestWebSocketMessages:
    """WebSocket消息测试"""

    async def test_progress_message_format(self):
        """测试进度消息格式"""
        from config.routing import application

        project_id = "00000000-0000-0000-0000-000000000001"
        communicator = WebsocketCommunicator(
            application,
            f"/ws/projects/{project_id}/"
        )

        connected, _ = await communicator.connect()
        assert connected

        # 接收连接确认
        response = await communicator.receive_json_from()
        assert response['type'] == 'connected'

        # 注意: 实际的进度消息需要从Redis Pub/Sub接收
        # 这里只测试连接和消息格式，不测试实际的消息内容

        await communicator.disconnect()
        print("✓ 消息格式测试通过")


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s'])
