"""
Redis Stream Publisher测试
测试RedisStreamPublisher的各种发布功能
"""

import json
import pytest
from unittest.mock import MagicMock, patch
from core.redis.publisher import RedisStreamPublisher


@pytest.mark.unit
class TestRedisStreamPublisher:
    """RedisStreamPublisher测试类"""

    @patch('core.redis.publisher.redis')
    def test_initialization(self, mock_redis):
        """测试发布器初始化"""
        mock_client = MagicMock()
        mock_redis.from_url.return_value = mock_client

        publisher = RedisStreamPublisher('proj-1', 'rewrite')

        assert publisher.project_id == 'proj-1'
        assert publisher.stage_name == 'rewrite'
        assert publisher.channel == 'ai_story:project:proj-1:stage:rewrite'
        assert publisher.redis_client == mock_client

        # 验证Redis客户端创建
        mock_redis.from_url.assert_called_once()

    @patch('core.redis.publisher.redis')
    def test_publish_token(self, mock_redis):
        """测试发布token消息"""
        mock_client = MagicMock()
        mock_redis.from_url.return_value = mock_client
        mock_client.publish.return_value = 1  # 1个订阅者

        publisher = RedisStreamPublisher('proj-1', 'rewrite')
        result = publisher.publish_token('Hello', 'Hello World')

        assert result is True
        mock_client.publish.assert_called_once()

        # 验证发布的消息
        call_args = mock_client.publish.call_args
        channel = call_args[0][0]
        message_json = call_args[0][1]

        assert channel == 'ai_story:project:proj-1:stage:rewrite'
        message = json.loads(message_json)
        assert message['type'] == 'token'
        assert message['content'] == 'Hello'
        assert message['full_text'] == 'Hello World'
        assert message['stage'] == 'rewrite'
        assert message['project_id'] == 'proj-1'
        assert 'timestamp' in message

    @patch('core.redis.publisher.redis')
    def test_publish_stage_update(self, mock_redis):
        """测试发布阶段更新消息"""
        mock_client = MagicMock()
        mock_redis.from_url.return_value = mock_client
        mock_client.publish.return_value = 1

        publisher = RedisStreamPublisher('proj-1', 'rewrite')
        result = publisher.publish_stage_update(
            status='processing',
            progress=50,
            message='正在生成...'
        )

        assert result is True

        # 验证消息格式
        call_args = mock_client.publish.call_args
        message_json = call_args[0][1]
        message = json.loads(message_json)

        assert message['type'] == 'stage_update'
        assert message['status'] == 'processing'
        assert message['progress'] == 50
        assert message['message'] == '正在生成...'

    @patch('core.redis.publisher.redis')
    def test_publish_stage_update_minimal(self, mock_redis):
        """测试发布最小阶段更新（无progress和message）"""
        mock_client = MagicMock()
        mock_redis.from_url.return_value = mock_client
        mock_client.publish.return_value = 1

        publisher = RedisStreamPublisher('proj-1', 'rewrite')
        result = publisher.publish_stage_update(status='completed')

        assert result is True

        # 验证消息格式
        call_args = mock_client.publish.call_args
        message_json = call_args[0][1]
        message = json.loads(message_json)

        assert message['type'] == 'stage_update'
        assert message['status'] == 'completed'
        assert 'progress' not in message
        assert 'message' not in message

    @patch('core.redis.publisher.redis')
    def test_publish_done(self, mock_redis):
        """测试发布完成消息"""
        mock_client = MagicMock()
        mock_redis.from_url.return_value = mock_client
        mock_client.publish.return_value = 1

        publisher = RedisStreamPublisher('proj-1', 'rewrite')
        result = publisher.publish_done(
            full_text='完整生成的文本',
            metadata={'tokens_used': 100, 'latency_ms': 500}
        )

        assert result is True

        # 验证消息格式
        call_args = mock_client.publish.call_args
        message_json = call_args[0][1]
        message = json.loads(message_json)

        assert message['type'] == 'done'
        assert message['full_text'] == '完整生成的文本'
        assert message['metadata']['tokens_used'] == 100
        assert message['metadata']['latency_ms'] == 500

    @patch('core.redis.publisher.redis')
    def test_publish_error(self, mock_redis):
        """测试发布错误消息"""
        mock_client = MagicMock()
        mock_redis.from_url.return_value = mock_client
        mock_client.publish.return_value = 1

        publisher = RedisStreamPublisher('proj-1', 'rewrite')
        result = publisher.publish_error('生成失败', retry_count=2)

        assert result is True

        # 验证消息格式
        call_args = mock_client.publish.call_args
        message_json = call_args[0][1]
        message = json.loads(message_json)

        assert message['type'] == 'error'
        assert message['error'] == '生成失败'
        assert message['retry_count'] == 2

    @patch('core.redis.publisher.redis')
    def test_publish_progress(self, mock_redis):
        """测试发布进度消息"""
        mock_client = MagicMock()
        mock_redis.from_url.return_value = mock_client
        mock_client.publish.return_value = 1

        publisher = RedisStreamPublisher('proj-1', 'rewrite')
        result = publisher.publish_progress(
            current=5,
            total=10,
            item_name='生成第5张图片'
        )

        assert result is True

        # 验证消息格式
        call_args = mock_client.publish.call_args
        message_json = call_args[0][1]
        message = json.loads(message_json)

        assert message['type'] == 'progress'
        assert message['current'] == 5
        assert message['total'] == 10
        assert message['progress'] == 50
        assert message['item_name'] == '生成第5张图片'

    @patch('core.redis.publisher.redis')
    def test_publish_progress_calculation(self, mock_redis):
        """测试进度计算逻辑"""
        mock_client = MagicMock()
        mock_redis.from_url.return_value = mock_client
        mock_client.publish.return_value = 1

        publisher = RedisStreamPublisher('proj-1', 'rewrite')

        # 测试边界情况
        publisher.publish_progress(current=0, total=10)
        call_args = mock_client.publish.call_args
        message = json.loads(call_args[0][1])
        assert message['progress'] == 0

        publisher.publish_progress(current=10, total=10)
        call_args = mock_client.publish.call_args
        message = json.loads(call_args[0][1])
        assert message['progress'] == 100

    @patch('core.redis.publisher.redis')
    def test_publish_adds_timestamp(self, mock_redis):
        """测试发布自动添加时间戳"""
        mock_client = MagicMock()
        mock_redis.from_url.return_value = mock_client
        mock_client.publish.return_value = 1

        publisher = RedisStreamPublisher('proj-1', 'rewrite')
        publisher.publish_token('test', 'test')

        call_args = mock_client.publish.call_args
        message_json = call_args[0][1]
        message = json.loads(message_json)

        assert 'timestamp' in message
        assert isinstance(message['timestamp'], float)

    @patch('core.redis.publisher.redis')
    def test_publish_with_custom_timestamp(self, mock_redis):
        """测试使用自定义时间戳"""
        mock_client = MagicMock()
        mock_redis.from_url.return_value = mock_client
        mock_client.publish.return_value = 1

        publisher = RedisStreamPublisher('proj-1', 'rewrite')

        # 直接调用publish方法，传入自定义时间戳
        custom_message = {
            'type': 'custom',
            'timestamp': 1234567890.0
        }
        publisher.publish(custom_message)

        call_args = mock_client.publish.call_args
        message_json = call_args[0][1]
        message = json.loads(message_json)

        assert message['timestamp'] == 1234567890.0

    @patch('core.redis.publisher.redis')
    @patch('core.redis.publisher.logger')
    def test_publish_failure_handling(self, mock_logger, mock_redis):
        """测试发布失败处理"""
        mock_client = MagicMock()
        mock_redis.from_url.return_value = mock_client
        # 模拟Redis发布失败（返回0表示没有订阅者）
        mock_client.publish.return_value = 0

        publisher = RedisStreamPublisher('proj-1', 'rewrite')
        # publish方法即使没有订阅者也返回True
        result = publisher.publish_token('test', 'test')

        # 实际实现中publish总是返回True（除非抛出异常）
        assert result is True

    @patch('core.redis.publisher.redis')
    def test_close_connection(self, mock_redis):
        """测试关闭Redis连接"""
        mock_client = MagicMock()
        mock_redis.from_url.return_value = mock_client

        publisher = RedisStreamPublisher('proj-1', 'rewrite')
        publisher.close()

        mock_client.close.assert_called_once()

    @patch('core.redis.publisher.redis')
    def test_context_manager(self, mock_redis):
        """测试上下文管理器"""
        mock_client = MagicMock()
        mock_redis.from_url.return_value = mock_client

        with RedisStreamPublisher('proj-1', 'rewrite') as publisher:
            assert publisher is not None
            publisher.publish_token('test', 'test')

        # 验证退出时关闭连接
        mock_client.close.assert_called_once()

    @patch('core.redis.publisher.redis')
    @patch('core.redis.publisher.settings')
    def test_redis_url_from_settings(self, mock_settings, mock_redis):
        """测试从settings获取Redis URL"""
        mock_settings.REDIS_PUBSUB_URL = 'redis://custom:6380/3'
        mock_client = MagicMock()
        mock_redis.from_url.return_value = mock_client

        publisher = RedisStreamPublisher('proj-1', 'rewrite')

        # 验证使用了自定义URL
        mock_redis.from_url.assert_called_once()
        call_args = mock_redis.from_url.call_args
        assert call_args[0][0] == 'redis://custom:6380/3'
