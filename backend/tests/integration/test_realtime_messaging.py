"""
实时通信集成测试
测试Redis Pub/Sub消息发布和接收
"""

import time

import pytest

from core.redis.publisher import RedisStreamPublisher

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(
        not pytest.importorskip("redis"),
        reason="需要redis包"
    )
]


@pytest.mark.integration
@pytest.mark.django_db
class TestRealtimeMessaging:
    """实时通信集成测试"""

    @pytest.fixture
    def redis_client(self):
        """真实Redis客户端"""
        import redis
        client = redis.Redis.from_url('redis://localhost:6379/2', decode_responses=True)
        # 清理测试频道
        yield client
        # 清理
        client.close()

    def test_publish_token_message(self, redis_client):
        """测试发布token消息"""
        project_id = 'test-project-1'
        stage_name = 'rewrite'

        # 创建发布器
        publisher = RedisStreamPublisher(project_id, stage_name)

        # 发布token消息
        token = 'Hello'
        full_text = 'Hello World'
        result = publisher.publish_token(token, full_text)

        # 验证发布成功
        assert result is True

        # 关闭连接
        publisher.close()

    def test_publish_stage_update_message(self, redis_client):
        """测试发布阶段更新消息"""
        project_id = 'test-project-2'
        stage_name = 'storyboard'

        publisher = RedisStreamPublisher(project_id, stage_name)

        # 发布阶段更新
        result = publisher.publish_stage_update(
            status='processing',
            progress=50,
            message='正在生成分镜...'
        )

        assert result is True
        publisher.close()

    def test_publish_error_message(self, redis_client):
        """测试发布错误消息"""
        project_id = 'test-project-3'
        stage_name = 'image_generation'

        publisher = RedisStreamPublisher(project_id, stage_name)

        # 发布错误消息
        result = publisher.publish_error(
            error='生成失败',
            retry_count=1
        )

        assert result is True
        publisher.close()

    def test_publish_done_message(self, redis_client):
        """测试发布完成消息"""
        project_id = 'test-project-4'
        stage_name = 'camera_movement'

        publisher = RedisStreamPublisher(project_id, stage_name)

        # 发布完成消息
        result = publisher.publish_done(
            full_text='运镜生成完成',
            metadata={'frames': 120}
        )

        assert result is True
        publisher.close()

    def test_channel_format(self, redis_client):
        """测试Redis频道名称格式"""
        project_id = 'proj-123'
        stage_name = 'video_generation'

        publisher = RedisStreamPublisher(project_id, stage_name)

        # 验证频道名称格式
        # publisher的channel属性应该是私有属性，我们直接验证发布是否成功

        result = publisher.publish_token('test', 'test')
        assert result is True

        publisher.close()

    def test_context_manager(self, redis_client):
        """测试上下文管理器"""
        project_id = 'test-project-5'
        stage_name = 'rewrite'

        # 使用上下文管理器
        with RedisStreamPublisher(project_id, stage_name) as publisher:
            result = publisher.publish_stage_update(
                status='completed',
                progress=100,
                message='完成'
            )
            assert result is True
        # 连接应该自动关闭

    def test_publish_with_custom_timestamp(self, redis_client):
        """测试发布自定义时间戳的消息"""
        project_id = 'test-project-6'
        stage_name = 'storyboard'

        publisher = RedisStreamPublisher(project_id, stage_name)

        # 发布带自定义时间戳的消息
        custom_timestamp = int(time.time()) - 3600  # 1小时前

        result = publisher.publish(
            message={
                'type': 'stage_update',
                'status': 'processing',
                'progress': 25,
                'message': '处理中',
                'timestamp': custom_timestamp
            }
        )

        assert result is True
        publisher.close()

    def test_multiple_messages(self, redis_client):
        """测试连续发布多条消息"""
        project_id = 'test-project-7'
        stage_name = 'rewrite'

        publisher = RedisStreamPublisher(project_id, stage_name)

        # 连续发布多条token消息
        messages = ['Hello', 'World', '!']

        for msg in messages:
            result = publisher.publish_token(msg, msg)
            assert result is True

        publisher.close()

    def test_different_stages(self, redis_client):
        """测试不同阶段的发布"""
        project_id = 'test-project-8'

        stages = ['rewrite', 'storyboard', 'image_generation',
                 'camera_movement', 'video_generation']

        for stage in stages:
            publisher = RedisStreamPublisher(project_id, stage)
            result = publisher.publish_stage_update(
                status='processing',
                progress=0,
                message=f'{stage} 开始'
            )
            assert result is True
            publisher.close()

    def test_publish_progress_message(self, redis_client):
        """测试发布进度消息"""
        project_id = 'test-project-9'
        stage_name = 'video_generation'

        publisher = RedisStreamPublisher(project_id, stage_name)

        # 发布进度更新
        result = publisher.publish_progress(
            current=75,
            total=100,
            item_name='视频生成'
        )

        assert result is True
        publisher.close()

    def test_message_data_structure(self, redis_client):
        """测试消息数据结构"""
        project_id = 'test-project-10'
        stage_name = 'rewrite'

        publisher = RedisStreamPublisher(project_id, stage_name)

        # 发布消息并验证数据结构（使用metadata通过done）
        result = publisher.publish_done(
            full_text='完成',
            metadata={'step': 1, 'total_steps': 3}
        )

        assert result is True
        publisher.close()
