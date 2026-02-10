"""
Story 11.2.4: 单分镜重新生成 Celery 任务测试

测试 regenerate_shot_content 任务
"""

from unittest.mock import MagicMock, Mock, patch

import pytest

from apps.artworks.models import (
    Artwork,
    Chapter,
    CharacterPose,
    CharacterProfile,
    ScriptScene,
    Shot,
)
from apps.artworks.tasks import regenerate_shot_content
from apps.users.models import User


@pytest.mark.django_db
class RegenerateShotContentTaskTestCase:
    """regenerate_shot_content 任务测试"""

    def setup_method(self):
        """设置测试数据"""
        # 创建测试用户
        self.user = User.objects.create_user(
            username="testuser",
            password="testpass123",
        )

        # 创建作品
        self.artwork = Artwork.objects.create(
            title="测试作品",
            author="测试作者",
            artwork_type="manga",
        )

        # 创建角色
        self.character = CharacterProfile.objects.create(
            artwork=self.artwork,
            name="测试角色",
            display_name="测试角色",
        )

        # 创建角色造型
        self.pose = CharacterPose.objects.create(
            character=self.character,
            pose_name="默认造型",
            pose_type="full_body",
        )

        # 创建章节
        self.chapter = Chapter.objects.create(
            artwork=self.artwork,
            chapter_number=1,
            title="测试章节",
            original_text="测试章节内容",
        )

        # 创建场景
        self.scene = ScriptScene.objects.create(
            chapter=self.chapter,
            scene_number=1,
            scene_name="测试场景",
        )

        # 创建镜头
        self.shot = Shot.objects.create(
            scene=self.scene,
            shot_number=1,
            shot_type="standard",
            content="测试镜头内容",
            duration=3.0,
            character_pose=self.pose,
            is_generated=True,
            generation_retry_count=0,
        )

    @patch("apps.artworks.tasks.RedisStreamPublisher")
    def test_regenerate_shot_image_success(self, mock_publisher_class):
        """测试成功重新生成图像"""
        # 模拟 Redis 发布器
        mock_publisher = MagicMock()
        mock_publisher_class.return_value = mock_publisher

        # 执行任务
        result = regenerate_shot_content(
            shot_id=self.shot.id, regenerate_type="image", custom_prompt="测试提示词"
        )

        # 验证结果
        assert result["shot_id"] == self.shot.id
        assert result["regenerate_type"] == "image"
        assert "task_id" in result

        # 验证镜头状态更新
        self.shot.refresh_from_db()
        assert self.shot.generation_retry_count == 1
        assert self.shot.is_generated is True
        assert self.shot.generation_error == ""

        # 验证 Redis 调用
        mock_publisher.publish_stage_update.assert_called()
        mock_publisher.close.assert_called_once()

    @patch("apps.artworks.tasks.RedisStreamPublisher")
    def test_regenerate_shot_audio_success(self, mock_publisher_class):
        """测试成功重新生成音频"""
        mock_publisher = MagicMock()
        mock_publisher_class.return_value = mock_publisher

        result = regenerate_shot_content(
            shot_id=self.shot.id,
            regenerate_type="audio",
        )

        assert result["shot_id"] == self.shot.id
        assert result["regenerate_type"] == "audio"

    @patch("apps.artworks.tasks.RedisStreamPublisher")
    def test_regenerate_shot_both_success(self, mock_publisher_class):
        """测试同时重新生成图像和音频"""
        mock_publisher = MagicMock()
        mock_publisher_class.return_value = mock_publisher

        result = regenerate_shot_content(
            shot_id=self.shot.id,
            regenerate_type="both",
        )

        assert result["shot_id"] == self.shot.id
        assert result["regenerate_type"] == "both"

    @patch("apps.artworks.tasks.RedisStreamPublisher")
    def test_regenerate_shot_progress_messages(self, mock_publisher_class):
        """测试进度消息发布"""
        mock_publisher = MagicMock()
        mock_publisher_class.return_value = mock_publisher

        regenerate_shot_content(
            shot_id=self.shot.id,
            regenerate_type="both",
        )

        # 验证发布了多个进度消息
        assert mock_publisher.publish_stage_update.call_count >= 3

        # 验证初始进度消息
        initial_call = mock_publisher.publish_stage_update.call_args_list[0]
        assert initial_call[1]["status"] == "processing"
        assert initial_call[1]["progress"] == 0

        # 验证完成进度消息
        completion_calls = [
            call
            for call in mock_publisher.publish_stage_update.call_args_list
            if call[1].get("status") == "completed"
        ]
        assert len(completion_calls) > 0
        assert completion_calls[0][1]["progress"] == 100

    @patch("apps.artworks.tasks.RedisStreamPublisher")
    def test_regenerate_shot_error_handling(self, mock_publisher_class):
        """测试错误处理"""
        mock_publisher = MagicMock()
        mock_publisher_class.return_value = mock_publisher

        # 模拟镜头不存在
        result = regenerate_shot_content(
            shot_id=99999,
            regenerate_type="image",
        )

        assert result["shot_id"] == 99999
        assert "error" in result
        assert "不存在" in result["error"]

    @patch("apps.artworks.tasks.RedisStreamPublisher")
    def test_regenerate_shot_error_published(self, mock_publisher_class):
        """测试错误消息发布"""
        # 第一次调用返回 None（模拟镜头不存在）
        with patch("apps.artworks.tasks.Shot.objects.get", side_effect=Shot.DoesNotExist):
            mock_publisher = MagicMock()
            mock_publisher_class.return_value = mock_publisher

            regenerate_shot_content(
                shot_id=99999,
                regenerate_type="image",
            )

            # 验证发布了错误消息
            mock_publisher.publish_error.assert_called_once()
            error_call = mock_publisher.publish_error.call_args
            assert "error" in error_call[1]

    @patch("apps.artworks.tasks.RedisStreamPublisher")
    def test_regenerate_shot_custom_prompt(self, mock_publisher_class):
        """测试使用自定义提示词"""
        mock_publisher = MagicMock()
        mock_publisher_class.return_value = mock_publisher

        custom_prompt = "电影级光效、柔焦背景"

        result = regenerate_shot_content(
            shot_id=self.shot.id, regenerate_type="image", custom_prompt=custom_prompt
        )

        assert result["shot_id"] == self.shot.id

    def test_regenerate_shot_increment_retry_count(self):
        """测试重试计数增加"""
        initial_retry_count = self.shot.generation_retry_count

        with patch("apps.artworks.tasks.RedisStreamPublisher") as mock_publisher_class:
            mock_publisher = MagicMock()
            mock_publisher_class.return_value = mock_publisher

            regenerate_shot_content(
                shot_id=self.shot.id,
                regenerate_type="image",
            )

            self.shot.refresh_from_db()
            assert self.shot.generation_retry_count == initial_retry_count + 1

    @patch("apps.artworks.tasks.RedisStreamPublisher")
    def test_regenerate_shot_reset_error_on_success(self, mock_publisher_class):
        """测试成功时重置错误信息"""
        # 设置初始错误
        self.shot.generation_error = "之前的错误"
        self.shot.save()

        mock_publisher = MagicMock()
        mock_publisher_class.return_value = mock_publisher

        regenerate_shot_content(
            shot_id=self.shot.id,
            regenerate_type="image",
        )

        self.shot.refresh_from_db()
        assert self.shot.generation_error == ""
        assert self.shot.is_generated is True

    @patch("apps.artworks.tasks.RedisStreamPublisher")
    @patch("apps.artworks.tasks.regenerate_shot_content.retry")
    def test_regenerate_shot_retry_on_exception(self, mock_retry, mock_publisher_class):
        """测试异常时重试"""
        # 模拟任务实例
        task = Mock()
        task.request.id = "test-task-id"
        task.request.retries = 0
        task.max_retries = 2

        mock_publisher = MagicMock()
        mock_publisher_class.return_value = mock_publisher

        # 模拟发布器抛出异常
        mock_publisher.publish_stage_update.side_effect = Exception("测试异常")

        with pytest.raises(Exception):
            regenerate_shot_content.call(task, self.shot.id, "image")

        # 验证调用了重试
        task.retry.assert_called_once()

    def test_regenerate_shot_task_signature(self):
        """测试任务签名配置"""
        task = regenerate_shot_content

        # 验证任务配置
        assert task.max_retries == 2
        assert task.default_retry_delay == 60
        assert task.acks_late is True
        assert task.soft_time_limit == 300
        assert task.time_limit == 600


@pytest.mark.django_db
class RegenerateShotIntegrationTestCase:
    """重新生成集成测试"""

    def setup_method(self):
        """设置测试数据"""
        self.user = User.objects.create_user(
            username="testuser",
            password="testpass123",
        )

        self.artwork = Artwork.objects.create(
            title="测试作品",
            author="测试作者",
            artwork_type="manga",
        )

        self.character = CharacterProfile.objects.create(
            artwork=self.artwork,
            name="测试角色",
            display_name="测试角色",
        )

        self.pose = CharacterPose.objects.create(
            character=self.character,
            pose_name="默认造型",
            pose_type="full_body",
        )

        # 创建章节
        self.chapter = Chapter.objects.create(
            artwork=self.artwork,
            chapter_number=1,
            title="测试章节",
            original_text="测试章节内容",
        )

        self.scene = ScriptScene.objects.create(
            chapter=self.chapter,
            scene_number=1,
            scene_name="测试场景",
        )

    @patch("apps.artworks.tasks.RedisStreamPublisher")
    def test_full_regenerate_workflow(self, mock_publisher_class):
        """测试完整的重新生成工作流"""
        mock_publisher = MagicMock()
        mock_publisher_class.return_value = mock_publisher

        # 创建镜头
        shot = Shot.objects.create(
            scene=self.scene,
            shot_number=1,
            shot_type="standard",
            content="测试内容",
            duration=3.0,
            character_pose=self.pose,
            is_generated=False,
            generation_retry_count=0,
        )

        # 执行重新生成任务
        result = regenerate_shot_content(
            shot_id=shot.id,
            regenerate_type="both",
        )

        # 验证结果
        assert result["shot_id"] == shot.id
        assert result["regenerate_type"] == "both"

        # 验证镜头状态更新
        shot.refresh_from_db()
        assert shot.is_generated is True
        assert shot.generation_retry_count == 1
        assert shot.generated_at is not None
