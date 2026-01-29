"""
core.redis.publisher 和 core.redis.subscriber 单元测试

使用Mock测试Redis Pub/Sub消息发布/订阅功能
"""

from unittest.mock import MagicMock, Mock, patch

import pytest

from core.redis.publisher import RedisStreamPublisher
from core.redis.subscriber import RedisStreamSubscriber


@pytest.mark.unit
class TestRedisStreamPublisher:
    """测试RedisStreamPublisher发布器"""

    @pytest.fixture
    def publisher(self):
        """创建发布器实例"""
        return RedisStreamPublisher(project_id="test-project-123", stage_name="rewrite")

    def test_publisher_initialization(self, publisher):
        """测试发布器初始化"""
        assert publisher.project_id == "test-project-123"
        assert publisher.stage_name == "rewrite"
        assert publisher.channel == "ai_story:project:test-project-123:stage:rewrite"

    def test_channel_format_with_different_stage(self):
        """测试不同阶段的频道命名"""
        publisher_rewrite = RedisStreamPublisher("proj-1", "rewrite")
        publisher_storyboard = RedisStreamPublisher("proj-1", "storyboard")
        publisher_image = RedisStreamPublisher("proj-1", "image_generation")

        assert "rewrite" in publisher_rewrite.channel
        assert "storyboard" in publisher_storyboard.channel
        assert "image_generation" in publisher_image.channel

    @patch("core.redis.publisher.redis")
    def test_publish_success(self, mock_redis, publisher):
        """测试成功发布消息"""
        # Mock Redis客户端
        mock_client = MagicMock()
        mock_redis.from_url.return_value = mock_client
        mock_client.publish.return_value = 1  # 1个订阅者

        # 重新初始化以使用Mock
        publisher.redis_client = mock_client

        # 发布消息
        message = {"type": "test", "data": "value"}
        result = publisher.publish(message)

        assert result is True
        mock_client.publish.assert_called_once()

    @patch("core.redis.publisher.redis")
    def test_publish_adds_timestamp(self, mock_redis, publisher):
        """测试发布消息自动添加时间戳"""
        import time

        mock_client = MagicMock()
        mock_redis.from_url.return_value = mock_client
        publisher.redis_client = mock_client

        # 发布不带时间戳的消息
        message = {"type": "test"}
        before_publish = time.time()
        publisher.publish(message)
        after_publish = time.time()

        # 验证时间戳被添加
        call_args = mock_client.publish.call_args
        published_message = call_args[0][1]  # 第二个参数是消息JSON
        import json

        parsed = json.loads(published_message)
        assert "timestamp" in parsed
        assert before_publish <= parsed["timestamp"] <= after_publish

    def test_publish_token(self):
        """测试发布Token消息"""
        publisher = RedisStreamPublisher("proj-1", "rewrite")

        # Mock publish方法
        publisher.publish = Mock(return_value=True)

        result = publisher.publish_token("content片段", "完整内容")

        assert result is True
        publisher.publish.assert_called_once()

        # 验证消息格式
        call_args = publisher.publish.call_args[0][0]
        assert call_args["type"] == "token"
        assert call_args["content"] == "content片段"
        assert call_args["full_text"] == "完整内容"
        assert call_args["stage"] == "rewrite"
        assert call_args["project_id"] == "proj-1"

    def test_publish_stage_update(self):
        """测试发布阶段更新消息"""
        publisher = RedisStreamPublisher("proj-1", "rewrite")
        publisher.publish = Mock(return_value=True)

        result = publisher.publish_stage_update(
            status="processing", progress=50, message="正在处理"
        )

        assert result is True

        call_args = publisher.publish.call_args[0][0]
        assert call_args["type"] == "stage_update"
        assert call_args["status"] == "processing"
        assert call_args["progress"] == 50
        assert call_args["message"] == "正在处理"

    def test_publish_done(self):
        """测试发布完成消息"""
        publisher = RedisStreamPublisher("proj-1", "rewrite")
        publisher.publish = Mock(return_value=True)

        result = publisher.publish_done(full_text="生成的完整文本", metadata={"tokens": 1000})

        assert result is True

        call_args = publisher.publish.call_args[0][0]
        assert call_args["type"] == "done"
        assert call_args["full_text"] == "生成的完整文本"
        assert call_args["metadata"] == {"tokens": 1000}

    def test_publish_error(self):
        """测试发布错误消息"""
        publisher = RedisStreamPublisher("proj-1", "rewrite")
        publisher.publish = Mock(return_value=True)

        result = publisher.publish_error("处理失败", retry_count=2)

        assert result is True

        call_args = publisher.publish.call_args[0][0]
        assert call_args["type"] == "error"
        assert call_args["error"] == "处理失败"
        assert call_args["retry_count"] == 2

    def test_publish_progress(self):
        """测试发布进度消息"""
        publisher = RedisStreamPublisher("proj-1", "rewrite")
        publisher.publish = Mock(return_value=True)

        result = publisher.publish_progress(current=5, total=10, item_name="image_5")

        assert result is True

        call_args = publisher.publish.call_args[0][0]
        assert call_args["type"] == "progress"
        assert call_args["current"] == 5
        assert call_args["total"] == 10
        assert call_args["progress"] == 50  # 5/10 * 100
        assert call_args["item_name"] == "image_5"

    @patch("core.redis.publisher.redis")
    def test_close_connection(self, mock_redis, publisher):
        """测试关闭Redis连接"""
        mock_client = MagicMock()
        publisher.redis_client = mock_client

        publisher.close()

        mock_client.close.assert_called_once()


@pytest.mark.unit
class TestRedisStreamSubscriber:
    """测试RedisStreamSubscriber订阅器"""

    def test_subscriber_initialization_with_stage(self):
        """测试订阅特定阶段的初始化"""
        subscriber = RedisStreamSubscriber(project_id="test-project-123", stage_name="rewrite")

        assert subscriber.project_id == "test-project-123"
        assert subscriber.stage_name == "rewrite"
        assert subscriber.channel == "ai_story:project:test-project-123:stage:rewrite"

    def test_subscriber_initialization_wildcard(self):
        """测试订阅项目所有阶段的初始化"""
        subscriber = RedisStreamSubscriber(project_id="test-project-123", stage_name=None)

        assert subscriber.channel == "ai_story:project:test-project-123:stage:*"

    @patch("core.redis.subscriber.redis")
    def test_subscribe_method(self, mock_redis):
        """测试subscribe方法"""
        mock_client = MagicMock()
        mock_redis.from_url.return_value = mock_client
        mock_pubsub = MagicMock()
        mock_client.pubsub.return_value = mock_pubsub

        subscriber = RedisStreamSubscriber("proj-1", "rewrite")
        subscriber.subscribe()

        # 验证订阅被调用
        mock_pubsub.subscribe.assert_called_once_with(subscriber.channel)

    @patch("core.redis.subscriber.redis")
    def test_subscribe_pattern_wildcard(self, mock_redis):
        """测试模式订阅(通配符)"""
        mock_client = MagicMock()
        mock_redis.from_url.return_value = mock_client
        mock_pubsub = MagicMock()
        mock_client.pubsub.return_value = mock_pubsub

        subscriber = RedisStreamSubscriber("proj-1", None)
        subscriber.subscribe()

        # 验证使用psubscribe(模式订阅)
        mock_pubsub.psubscribe.assert_called_once_with(subscriber.channel)

    @patch("core.redis.subscriber.redis")
    def test_unsubscribe(self, mock_redis):
        """测试取消订阅"""
        mock_client = MagicMock()
        mock_redis.from_url.return_value = mock_client
        mock_pubsub = MagicMock()
        mock_client.pubsub.return_value = mock_pubsub

        subscriber = RedisStreamSubscriber("proj-1", "rewrite")
        subscriber.pubsub = mock_pubsub

        subscriber.unsubscribe()

        # 验证取消订阅被调用
        mock_pubsub.unsubscribe.assert_called_once_with(subscriber.channel)

    @patch("core.redis.subscriber.redis")
    def test_unsubscribe_pattern_wildcard(self, mock_redis):
        """测试取消模式订阅"""
        mock_client = MagicMock()
        mock_redis.from_url.return_value = mock_client
        mock_pubsub = MagicMock()
        mock_client.pubsub.return_value = mock_pubsub

        subscriber = RedisStreamSubscriber("proj-1", None)
        subscriber.pubsub = mock_pubsub

        subscriber.unsubscribe()

        # 验证使用punsubscribe
        mock_pubsub.punsubscribe.assert_called_once_with(subscriber.channel)

    @patch("core.redis.subscriber.redis")
    def test_get_message_with_subscription(self, mock_redis):
        """测试获取消息"""

        mock_client = MagicMock()
        mock_redis.from_url.return_value = mock_client
        mock_pubsub = MagicMock()
        mock_client.pubsub.return_value = mock_pubsub

        # Mock订阅确认消息
        mock_pubsub.get_message.return_value = {"type": "subscribe", "data": None}

        subscriber = RedisStreamSubscriber("proj-1", "rewrite")
        subscriber.subscribe()

        # 第一次调用应返回None(订阅确认)
        message = subscriber.get_message(timeout=1.0)
        assert message is None

    @patch("core.redis.subscriber.redis")
    def test_get_message_with_data(self, mock_redis):
        """测试获取实际消息"""
        import json

        mock_client = MagicMock()
        mock_redis.from_url.return_value = mock_client
        mock_pubsub = MagicMock()
        mock_client.pubsub.return_value = mock_pubsub

        # Mock实际消息 - 直接返回消息数据
        test_message = {"type": "message", "data": json.dumps({"key": "value"})}
        mock_pubsub.get_message.return_value = test_message

        subscriber = RedisStreamSubscriber("proj-1", "rewrite")
        subscriber.pubsub = mock_pubsub

        message = subscriber.get_message(timeout=1.0)

        assert message is not None
        assert message["key"] == "value"  # JSON已解析
        assert "channel" in message

    @patch("core.redis.subscriber.redis")
    def test_close_connection(self, mock_redis):
        """测试关闭连接"""
        mock_client = MagicMock()
        mock_redis.from_url.return_value = mock_client
        mock_pubsub = MagicMock()
        mock_client.pubsub.return_value = mock_pubsub

        subscriber = RedisStreamSubscriber("proj-1", "rewrite")
        subscriber.redis_client = mock_client
        subscriber.pubsub = mock_pubsub

        subscriber.close()

        # 验证连接被关闭
        mock_pubsub.unsubscribe.assert_called_once()
        mock_pubsub.close.assert_called_once()
        mock_client.close.assert_called_once()


@pytest.mark.unit
class TestRedisPubSubIntegration:
    """Redis Pub/Sub集成测试"""

    def test_publisher_subscriber_channel_format(self):
        """测试发布器和订阅器使用相同的频道格式"""
        project_id = "test-project"
        stage_name = "rewrite"

        publisher = RedisStreamPublisher(project_id, stage_name)
        subscriber = RedisStreamSubscriber(project_id, stage_name)

        # 验证频道格式一致
        assert publisher.channel == subscriber.channel

    def test_wildcard_subscriber_matches_multiple_publishers(self):
        """测试通配符订阅匹配多个发布器"""
        project_id = "test-project"

        # 创建多个阶段的发布器
        publisher1 = RedisStreamPublisher(project_id, "rewrite")
        publisher2 = RedisStreamPublisher(project_id, "storyboard")
        publisher3 = RedisStreamPublisher(project_id, "image_generation")

        # 创建通配符订阅器
        subscriber = RedisStreamSubscriber(project_id, None)

        # 验证频道格式
        assert publisher1.channel == "ai_story:project:test-project:stage:rewrite"
        assert publisher2.channel == "ai_story:project:test-project:stage:storyboard"
        assert publisher3.channel == "ai_story:project:test-project:stage:image_generation"
        assert subscriber.channel == "ai_story:project:test-project:stage:*"

    def test_context_manager_usage(self):
        """测试上下文管理器用法"""
        publisher = RedisStreamPublisher("proj-1", "rewrite")
        publisher.close = Mock()

        with publisher:
            pass

        # 验证退出时调用close
        publisher.close.assert_called_once()
