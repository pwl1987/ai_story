"""
内容生成域模型测试
测试ContentRewrite, Storyboard, GeneratedImage, CameraMovement, GeneratedVideo模型
遵循单一职责原则(SRP)
"""

import pytest
from django.db.utils import IntegrityError

from apps.content.models import (
    CameraMovement,
    ContentRewrite,
    GeneratedImage,
    GeneratedVideo,
    Storyboard,
)
from apps.content.tests.factories import (
    CameraMovementFactory,
    ContentRewriteFactory,
    GeneratedImageFactory,
    GeneratedVideoFactory,
    ProjectFactory,
    StoryboardFactory,
)


@pytest.mark.django_db
class TestContentRewriteModel:
    """
    测试ContentRewrite模型
    职责: 验证文案改写数据的创建、更新和关联
    遵循单一职责原则(SRP)
    """

    def test_create_content_rewrite_minimal(self):
        """测试创建最小文案改写"""
        project = ProjectFactory()
        rewrite = ContentRewrite.objects.create(
            project=project,
            original_text="原始文案",
            rewritten_text="改写后文案",
            prompt_used="测试提示词"
        )

        assert rewrite.id is not None
        assert rewrite.project == project
        assert rewrite.original_text == "原始文案"
        assert rewrite.rewritten_text == "改写后文案"

    def test_create_content_rewrite_full(self):
        """测试创建完整文案改写"""
        rewrite = ContentRewriteFactory()

        assert ContentRewrite.objects.filter(id=rewrite.id).exists()

    def test_rewrite_one_to_one_relationship(self):
        """测试项目与文案改写的一对一关系"""
        project = ProjectFactory()
        ContentRewriteFactory(project=project)

        # 尝试为同一项目创建第二个文案改写应该失败
        with pytest.raises(IntegrityError):
            ContentRewriteFactory(project=project)

    def test_rewrite_str_representation(self):
        """测试字符串表示"""
        rewrite = ContentRewriteFactory()
        expected = f"{rewrite.project.name} - 文案改写"
        assert str(rewrite) == expected

    def test_rewrite_json_fields(self):
        """测试JSON字段"""
        metadata = {
            'model': 'gpt-4',
            'temperature': 0.7,
            'tokens_used': 500
        }

        rewrite = ContentRewriteFactory(generation_metadata=metadata)

        assert rewrite.generation_metadata == metadata
        assert rewrite.generation_metadata['tokens_used'] == 500

    def test_rewrite_foreign_key_model_provider(self):
        """测试模型提供商外键"""
        # 创建带model_provider的rewrite
        from apps.models.tests.factories import ModelProviderFactory
        project = ProjectFactory()
        provider = ModelProviderFactory()
        rewrite = ContentRewriteFactory(project=project, model_provider=provider)

        assert rewrite.model_provider is not None
        assert rewrite.model_provider.is_active is True


@pytest.mark.django_db
class TestStoryboardModel:
    """
    测试Storyboard模型
    职责: 验证分镜数据的创建、排序和唯一约束
    遵循单一职责原则(SRP)
    """

    def test_create_storyboard_minimal(self):
        """测试创建最小分镜"""
        project = ProjectFactory()
        storyboard = Storyboard.objects.create(
            project=project,
            sequence_number=1,
            scene_description="开场画面",
            narration_text="这是旁白",
            image_prompt="画面提示"
        )

        assert storyboard.id is not None
        assert storyboard.project == project
        assert storyboard.sequence_number == 1

    def test_create_storyboard_full(self):
        """测试创建完整分镜"""
        storyboard = StoryboardFactory()

        assert Storyboard.objects.filter(id=storyboard.id).exists()

    def test_storyboard_unique_constraint(self):
        """测试项目+序号唯一约束"""
        project = ProjectFactory()
        StoryboardFactory(project=project, sequence_number=1)

        # 尝试创建相同序号的分镜应该失败
        with pytest.raises(IntegrityError):
            StoryboardFactory(project=project, sequence_number=1)

    def test_storyboard_ordering(self):
        """测试默认排序（按序号）"""
        project = ProjectFactory()
        storyboard1 = StoryboardFactory(project=project, sequence_number=3)
        storyboard2 = StoryboardFactory(project=project, sequence_number=1)
        storyboard3 = StoryboardFactory(project=project, sequence_number=2)

        storyboards = list(Storyboard.objects.filter(project=project))
        assert storyboards[0] == storyboard2
        assert storyboards[1] == storyboard3
        assert storyboards[2] == storyboard1

    def test_storyboard_str_representation(self):
        """测试字符串表示"""
        storyboard = StoryboardFactory(sequence_number=5)
        expected = f"{storyboard.project.name} - 分镜5"
        assert str(storyboard) == expected

    def test_storyboard_duration_default(self):
        """测试默认时长"""
        storyboard = StoryboardFactory()

        assert abs(storyboard.duration_seconds - 3.0) < 0.1  # 允许浮点误差

    def test_storyboard_foreign_key_cascade_delete(self):
        """测试项目删除级联到分镜"""
        project = ProjectFactory()
        storyboard = StoryboardFactory(project=project)

        storyboard_id = storyboard.id
        project.delete()

        assert not Storyboard.objects.filter(id=storyboard_id).exists()


@pytest.mark.django_db
class TestGeneratedImageModel:
    """
    测试GeneratedImage模型
    职责: 验证生成图片数据的状态管理和文件信息
    遵循单一职责原则(SRP)
    """

    def test_create_generated_image_minimal(self):
        """测试创建最小生成图片"""
        storyboard = StoryboardFactory()
        image = GeneratedImage.objects.create(
            storyboard=storyboard,
            image_url="http://example.com/image.jpg"
        )

        assert image.id is not None
        assert image.storyboard == storyboard
        assert image.status == 'pending'

    def test_create_generated_image_full(self):
        """测试创建完整生成图片"""
        image = GeneratedImageFactory()

        assert GeneratedImage.objects.filter(id=image.id).exists()

    def test_image_status_choices(self):
        """测试图片状态选择"""
        storyboard = StoryboardFactory()

        for status in ['pending', 'processing', 'completed', 'failed']:
            image = GeneratedImageFactory(
                storyboard=storyboard,
                status=status
            )
            assert image.status == status

    def test_image_retry_count(self):
        """测试重试次数"""
        image = GeneratedImageFactory(retry_count=0)

        assert image.retry_count == 0

        # 模拟重试
        image.retry_count += 1
        image.save()

        image.refresh_from_db()
        assert image.retry_count == 1

    def test_image_file_properties(self):
        """测试文件属性"""
        image = GeneratedImageFactory(
            width=1024,
            height=1024,
            file_size=500000
        )

        assert image.width == 1024
        assert image.height == 1024
        assert image.file_size == 500000

    def test_image_str_representation(self):
        """测试字符串表示"""
        image = GeneratedImageFactory()
        expected = f"{image.storyboard} - 图片"
        assert str(image) == expected

    def test_image_foreign_key_cascade_delete(self):
        """测试分镜删除级联到图片"""
        image = GeneratedImageFactory()
        image_id = image.id

        image.storyboard.delete()

        assert not GeneratedImage.objects.filter(id=image_id).exists()


@pytest.mark.django_db
class TestCameraMovementModel:
    """
    测试CameraMovement模型
    职责: 验证运镜参数的类型和配置
    遵循单一职责原则(SRP)
    """

    def test_create_camera_movement_minimal(self):
        """测试创建最小运镜"""
        storyboard = StoryboardFactory()
        movement = CameraMovement.objects.create(
            storyboard=storyboard,
            movement_type='zoom_in',
            prompt_used="测试提示词"
        )

        assert movement.id is not None
        assert movement.storyboard == storyboard
        assert movement.movement_type == 'zoom_in'

    def test_create_camera_movement_full(self):
        """测试创建完整运镜"""
        movement = CameraMovementFactory()

        assert CameraMovement.objects.filter(id=movement.id).exists()

    def test_movement_type_choices(self):
        """测试运镜类型选择"""
        movement_types = [
            'static', 'zoom_in', 'zoom_out', 'pan_left',
            'pan_right', 'tilt_up', 'tilt_down', 'dolly_in', 'dolly_out'
        ]

        for movement_type in movement_types:
            # 每个movement_type需要不同的storyboard（一对一关系）
            storyboard = StoryboardFactory()
            movement = CameraMovementFactory(
                storyboard=storyboard,
                movement_type=movement_type
            )
            assert movement.movement_type == movement_type

    def test_movement_json_params(self):
        """测试运镜参数JSON字段"""
        params = {
            'intensity': 0.8,
            'duration': 3.0,
            'smoothness': 0.9
        }

        movement = CameraMovementFactory(movement_params=params)

        assert movement.movement_params == params
        assert movement.movement_params['intensity'] == 0.8

    def test_movement_one_to_one_relationship(self):
        """测试分镜与运镜的一对一关系"""
        storyboard = StoryboardFactory()
        CameraMovementFactory(storyboard=storyboard)

        # 尝试为同一分镜创建第二个运镜应该失败
        with pytest.raises(IntegrityError):
            CameraMovementFactory(storyboard=storyboard)

    def test_movement_str_representation(self):
        """测试字符串表示"""
        movement = CameraMovementFactory(movement_type='zoom_in')
        expected = f"{movement.storyboard} - 推进"
        assert str(movement) == expected


@pytest.mark.django_db
class TestGeneratedVideoModel:
    """
    测试GeneratedVideo模型
    职责: 验证生成视频的属性和关联关系
    遵循单一职责原则(SRP)
    """

    def test_create_generated_video_minimal(self):
        """测试创建最小生成视频"""
        # 先创建image和camera_movement（必需的外键）
        storyboard = StoryboardFactory()
        from apps.content.tests.factories import CameraMovementFactory, GeneratedImageFactory
        image = GeneratedImageFactory(storyboard=storyboard)
        movement = CameraMovementFactory(storyboard=storyboard)

        video = GeneratedVideo.objects.create(
            storyboard=storyboard,
            image=image,
            camera_movement=movement,
            video_url="http://example.com/video.mp4"
        )

        assert video.id is not None
        assert video.storyboard == storyboard
        assert video.status == 'pending'

    def test_create_generated_video_full(self):
        """测试创建完整生成视频"""
        video = GeneratedVideoFactory()

        assert GeneratedVideo.objects.filter(id=video.id).exists()

    def test_video_status_choices(self):
        """测试视频状态选择"""
        storyboard = StoryboardFactory()

        for status in ['pending', 'processing', 'completed', 'failed']:
            video = GeneratedVideoFactory(
                storyboard=storyboard,
                status=status
            )
            assert video.status == status

    def test_video_properties(self):
        """测试视频属性"""
        video = GeneratedVideoFactory(
            duration=5.0,
            width=1080,
            height=1920,
            fps=24,
            file_size=10000000
        )

        assert video.duration == 5.0
        assert video.width == 1080
        assert video.height == 1920
        assert video.fps == 24
        assert video.file_size == 10000000

    def test_video_foreign_keys(self):
        """测试外键关联"""
        # 手动创建确保关联正确
        storyboard = StoryboardFactory()
        image = GeneratedImageFactory(storyboard=storyboard)
        movement = CameraMovementFactory(storyboard=storyboard)
        video = GeneratedVideoFactory(
            storyboard=storyboard,
            image=image,
            camera_movement=movement
        )

        assert video.image is not None
        assert video.camera_movement is not None
        assert video.storyboard == video.image.storyboard

    def test_video_str_representation(self):
        """测试字符串表示"""
        video = GeneratedVideoFactory()
        expected = f"{video.storyboard} - 视频"
        assert str(video) == expected

    def test_video_generation_params(self):
        """测试生成参数JSON字段"""
        params = {
            'duration': 3.0,
            'fps': 24,
            'quality': 'high',
            'motion_scale': 1.0
        }

        video = GeneratedVideoFactory(generation_params=params)

        assert video.generation_params == params


@pytest.mark.django_db
class TestRelationships:
    """
    测试模型间关系
    职责: 验证内容生成域各模型间的关联关系
    遵循单一职责原则(SRP)
    """

    def test_project_to_content_rewrite_one_to_one(self):
        """测试项目与文案改写一对一关系"""
        project = ProjectFactory()
        rewrite = ContentRewriteFactory(project=project)

        assert project.content_rewrite == rewrite
        assert rewrite.project == project

    def test_project_to_storyboards_one_to_many(self):
        """测试项目与分镜一对多关系"""
        project = ProjectFactory()
        storyboard1 = StoryboardFactory(project=project, sequence_number=1)
        storyboard2 = StoryboardFactory(project=project, sequence_number=2)

        assert project.storyboards.count() == 2
        assert storyboard1 in project.storyboards.all()
        assert storyboard2 in project.storyboards.all()

    def test_storyboard_to_images_one_to_many(self):
        """测试分镜与图片一对多关系"""
        storyboard = StoryboardFactory()
        image1 = GeneratedImageFactory(storyboard=storyboard)
        image2 = GeneratedImageFactory(storyboard=storyboard)

        assert storyboard.images.count() == 2
        assert image1 in storyboard.images.all()
        assert image2 in storyboard.images.all()

    def test_storyboard_to_camera_movement_one_to_one(self):
        """测试分镜与运镜一对一关系"""
        storyboard = StoryboardFactory()
        movement = CameraMovementFactory(storyboard=storyboard)

        assert storyboard.camera_movement == movement
        assert movement.storyboard == storyboard

    def test_storyboard_to_videos_one_to_many(self):
        """测试分镜与视频一对多关系"""
        storyboard = StoryboardFactory()
        video1 = GeneratedVideoFactory(storyboard=storyboard)
        video2 = GeneratedVideoFactory(storyboard=storyboard)

        assert storyboard.videos.count() == 2
        assert video1 in storyboard.videos.all()
        assert video2 in storyboard.videos.all()

    def test_complete_content_chain(self):
        """测试完整的内容生成链"""
        # 项目 → 分镜 → 图片 + 运镜 → 视频
        project = ProjectFactory()
        storyboard = StoryboardFactory(project=project, sequence_number=1)
        image = GeneratedImageFactory(storyboard=storyboard)
        movement = CameraMovementFactory(storyboard=storyboard)
        video = GeneratedVideoFactory(
            storyboard=storyboard,
            image=image,
            camera_movement=movement
        )

        # 验证完整链路
        assert video.storyboard.project == project
        assert video.image.storyboard == storyboard
        assert video.camera_movement.storyboard == storyboard
