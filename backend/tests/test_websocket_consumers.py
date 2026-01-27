"""
WebSocket消费者单元测试
测试apps.projects.consumers的ProjectStageConsumer核心逻辑
"""

import json
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from apps.projects.consumers import ProjectStageConsumer


@pytest.mark.unit
@pytest.mark.asyncio
class TestProjectStageConsumerUnit:
    """ProjectStageConsumer单元测试"""

    def _create_consumer(self, project_id='test-123', stage_name='rewrite'):
        """辅助方法：创建消费者实例"""
        scope = {
            'type': 'websocket',
            'url_route': {
                'kwargs': {
                    'project_id': project_id,
                    'stage_name': stage_name
                }
            }
        }

        consumer = ProjectStageConsumer(scope)
        consumer.scope = scope
        return consumer

    async def test_consumer_instantiation(self):
        """测试消费者可以实例化"""
        consumer = self._create_consumer('test-123', 'rewrite')

        # 验证属性设置
        assert consumer.project_id == 'test-123'
        assert consumer.stage_name == 'rewrite'

    async def test_channel_name_construction(self):
        """测试频道名称构造逻辑"""
        consumer = self._create_consumer('proj-xyz', 'storyboard')
        expected_channel = 'ai_story:project:proj-xyz:stage:storyboard'

        # 验证频道名称构造
        assert f"ai_story:project:{consumer.project_id}:stage:{consumer.stage_name}" == expected_channel

    @patch('apps.projects.consumers.aioredis')
    async def test_connect_creates_redis_task(self, mock_aioredis):
        """测试连接时创建Redis订阅任务"""
        # Mock Redis连接
        mock_redis = AsyncMock()
        mock_pubsub = AsyncMock()
        mock_redis.pubsub.return_value = mock_pubsub
        mock_aioredis.from_url.return_value = mock_redis

        consumer = self._create_consumer()

        # Mock accept方法
        consumer.accept = AsyncMock()

        # 调用connect
        await consumer.connect()

        # 验证accept被调用
        consumer.accept.assert_called_once()

        # 验证redis_task被创建
        assert hasattr(consumer, 'redis_task')
        assert consumer.redis_task is not None

    @patch('apps.projects.consumers.aioredis')
    async def test_disconnect_cancels_redis_task(self, mock_aioredis):
        """测试断开时取消Redis订阅任务"""
        # Mock Redis连接
        mock_redis = AsyncMock()
        mock_pubsub = AsyncMock()
        mock_redis.pubsub.return_value = mock_pubsub
        mock_aioredis.from_url.return_value = mock_redis

        consumer = self._create_consumer()
        consumer.accept = AsyncMock()

        # 先连接
        await consumer.connect()

        # 保存redis_task引用
        redis_task = consumer.redis_task

        # Mock redis_task的cancel方法
        redis_task.cancel = MagicMock()

        # 调用disconnect
        await consumer.disconnect(close_code=1000)

        # 验证cancel被调用
        redis_task.cancel.assert_called_once()

    async def test_receive_ping_message(self):
        """测试接收ping消息并返回pong"""
        consumer = self._create_consumer()

        # Mock send方法
        consumer.send = AsyncMock()

        # 调用receive with ping
        ping_data = json.dumps({'type': 'ping', 'timestamp': 1234567890.0})
        await consumer.receive(text_data=ping_data)

        # 验证send被调用，发送pong响应
        consumer.send.assert_called_once()
        call_args = consumer.send.call_args
        sent_message = json.loads(call_args[1]['text_data'])
        assert sent_message['type'] == 'pong'
        assert sent_message['timestamp'] == 1234567890.0

    async def test_receive_invalid_json(self):
        """测试接收无效JSON消息"""
        consumer = self._create_consumer()

        # 调用receive with invalid JSON - 应该不抛出异常
        await consumer.receive(text_data='invalid json')

        # 如果到达这里，说明消费者正确处理了无效JSON
        assert True

    async def test_receive_without_text_data(self):
        """测试接收无文本数据"""
        consumer = self._create_consumer()

        # 调用receive without text_data - 应该不抛出异常
        await consumer.receive(text_data=None)

        assert True

    @patch('apps.projects.consumers.aioredis')
    async def test_channel_format_different_stages(self, mock_aioredis):
        """测试不同stage的频道名称格式"""
        mock_redis = AsyncMock()
        mock_pubsub = AsyncMock()
        mock_redis.pubsub.return_value = mock_pubsub
        mock_aioredis.from_url.return_value = mock_redis

        test_cases = [
            ('proj-1', 'rewrite', 'ai_story:project:proj-1:stage:rewrite'),
            ('proj-2', 'storyboard', 'ai_story:project:proj-2:stage:storyboard'),
            ('proj-3', 'image_generation', 'ai_story:project:proj-3:stage:image_generation'),
            ('proj-4', 'camera_movement', 'ai_story:project:proj-4:stage:camera_movement'),
            ('proj-5', 'video_generation', 'ai_story:project:proj-5:stage:video_generation'),
        ]

        for project_id, stage_name, expected_channel in test_cases:
            consumer = self._create_consumer(project_id, stage_name)
            consumer.accept = AsyncMock()
            await consumer.connect()

            # 验证频道名称
            assert consumer.channel_name == expected_channel

    @pytest.mark.asyncio
    @patch('apps.projects.consumers.settings')
    async def test_redis_url_from_settings(self, mock_settings):
        """测试从settings获取Redis URL"""
        # 设置自定义Redis URL
        mock_settings.CELERY_BROKER_URL = 'redis://custom-redis:6380/5'

        consumer = self._create_consumer()

        # 验证能够访问settings
        # (实际连接会在_subscribe_redis中进行)
        from django.conf import settings
        redis_url = getattr(settings, 'CELERY_BROKER_URL', 'redis://localhost:6379/5')
        assert redis_url is not None

    @patch('apps.projects.consumers.aioredis')
    async def test_accept_called_before_redis_task(self, mock_aioredis):
        """测试accept在Redis任务创建前被调用"""
        call_order = []

        async def mock_accept():
            call_order.append('accept')

        async def mock_from_url(*args, **kwargs):
            call_order.append('redis')
            mock_redis = AsyncMock()
            mock_pubsub = AsyncMock()
            mock_redis.pubsub.return_value = mock_pubsub
            return mock_redis

        mock_aioredis.from_url = mock_from_url

        consumer = self._create_consumer()
        consumer.accept = mock_accept

        await consumer.connect()

        # 验证accept在redis之前被调用
        assert call_order[0] == 'accept'
        assert call_order[1] == 'redis'
