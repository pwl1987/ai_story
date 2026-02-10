"""
Story 11.5.2: 镜头版本管理测试

测试:
- ShotVersion 模型
- 版本自动创建
- 版本恢复
- 版本对比
- API 端点
"""

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIRequestFactory, force_authenticate

from apps.artworks.models import (
    Artwork,
    Chapter,
    CharacterPose,
    CharacterProfile,
    PhysicalScene,
    ScriptScene,
    Shot,
    ShotVersion,
)
from apps.artworks.serializers import ShotVersionSerializer
from rest_framework.test import APIRequestFactory
from apps.artworks.views import ShotVersionViewSet

User = get_user_model()


@pytest.mark.django_db
class TestShotVersionModel:
    """测试 ShotVersion 模型"""

    def test_create_version_basic(self, user, scene):
        """测试创建基本版本"""
        shot = Shot.objects.create(
            scene=scene,
            shot_number=1,
            shot_type="dialogue",
            content="Test content",
            speaker="Test Speaker",
            sort_order=0,
        )

        version = ShotVersion.create_version(
            shot=shot,
            change_description="Initial version",
            is_auto_created=True,
            user=user,
        )

        assert version.version_number == 1
        assert version.shot == shot
        assert version.change_description == "Initial version"
        assert version.is_auto_created is True
        assert version.created_by == user
        assert "content" in version.content_snapshot

    def test_version_number_increments(self, user, scene):
        """测试版本号递增"""
        shot = Shot.objects.create(
            scene=scene,
            shot_number=1,
            shot_type="dialogue",
            content="Test content",
            speaker="Test Speaker",
            sort_order=0,
        )

        version1 = ShotVersion.create_version(shot=shot, user=user)
        version2 = ShotVersion.create_version(shot=shot, user=user)
        version3 = ShotVersion.create_version(shot=shot, user=user)

        assert version1.version_number == 1
        assert version2.version_number == 2
        assert version3.version_number == 3

    def test_content_snapshot_captures_all_fields(self, user, scene, character):
        """测试内容快照捕获所有字段"""
        pose = CharacterPose.objects.create(
            character=character,
            pose_name="Test Pose",
            pose_type="casual",
            pose_image="test.jpg",
        )

        shot = Shot.objects.create(
            scene=scene,
            shot_number=1,
            shot_type="dialogue",
            content="Test content with camera movement",
            speaker="Test Speaker",
            camera_movement="zoom in",
            camera_angle="high angle",
            duration=5.0,
            sort_order=0,
            character_pose=pose,
            camera_movement_params={"zoom": "1.5x", "speed": "slow"},
            shot_composition="Close up shot",
        )

        version = ShotVersion.create_version(shot=shot, user=user)
        snapshot = version.content_snapshot

        assert snapshot["shot_number"] == 1
        assert snapshot["shot_type"] == "dialogue"
        assert snapshot["content"] == "Test content with camera movement"
        assert snapshot["speaker"] == "Test Speaker"
        assert snapshot["camera_movement"] == "zoom in"
        assert snapshot["camera_angle"] == "high angle"
        assert snapshot["duration"] == 5.0
        assert snapshot["character_pose_id"] == pose.id
        assert snapshot["camera_movement_params"]["zoom"] == "1.5x"
        assert snapshot["shot_composition"] == "Close up shot"

    def test_cleanup_old_versions(self, user, scene):
        """测试清理旧版本"""
        shot = Shot.objects.create(
            scene=scene,
            shot_number=1,
            shot_type="dialogue",
            content="Test content",
            speaker="Test Speaker",
            sort_order=0,
        )

        # 创建15个版本
        for i in range(15):
            ShotVersion.create_version(
                shot=shot,
                change_description=f"Version {i + 1}",
                user=user,
            )

        # 验证只保留最近10个
        versions_count = ShotVersion.objects.filter(shot=shot).count()
        assert versions_count == 10

        # 验证保留的是最新的版本
        latest_version = ShotVersion.objects.filter(shot=shot).order_by("-version_number").first()
        assert latest_version.version_number == 15

        oldest_version = ShotVersion.objects.filter(shot=shot).order_by("version_number").first()
        assert oldest_version.version_number == 6  # 15 - 10 + 1 = 6

    def test_restore_version(self, user, scene):
        """测试恢复版本"""
        shot = Shot.objects.create(
            scene=scene,
            shot_number=1,
            shot_type="dialogue",
            content="Original content",
            speaker="Original Speaker",
            sort_order=0,
        )

        # 创建第一个版本
        version1 = ShotVersion.create_version(
            shot=shot,
            change_description="Original version",
            user=user,
        )

        # 修改镜头
        shot.content = "Modified content"
        shot.speaker = "Modified Speaker"
        shot.camera_movement = "pan left"
        shot.save()

        # 创建第二个版本
        version2 = ShotVersion.create_version(
            shot=shot,
            change_description="Modified version",
            user=user,
        )

        # 恢复到第一个版本
        version1.restore()

        shot.refresh_from_db()
        assert shot.content == "Original content"
        assert shot.speaker == "Original Speaker"
        assert shot.camera_movement == ""

        # 验证创建了新的恢复版本
        versions_count = ShotVersion.objects.filter(shot=shot).count()
        assert versions_count == 3  # 原始2个 + 恢复时创建的1个

    def test_compare_versions(self, user, scene):
        """测试版本对比"""
        shot = Shot.objects.create(
            scene=scene,
            shot_number=1,
            shot_type="dialogue",
            content="Original content",
            speaker="Original Speaker",
            sort_order=0,
        )

        version1 = ShotVersion.create_version(
            shot=shot,
            change_description="Original version",
            user=user,
        )

        # 修改镜头
        shot.content = "Modified content"
        shot.camera_movement = "zoom in"
        shot.duration = 10.0
        shot.save()

        version2 = ShotVersion.create_version(
            shot=shot,
            change_description="Modified version",
            user=user,
        )

        # 对比两个版本
        differences = version2.compare_with(version1)

        assert "content" in differences
        assert differences["content"]["old"] == "Original content"
        assert differences["content"]["new"] == "Modified content"

        assert "camera_movement" in differences
        assert differences["camera_movement"]["old"] == ""
        assert differences["camera_movement"]["new"] == "zoom in"

        assert "duration" in differences
        assert differences["duration"]["old"] == 3.0  # 默认值
        assert differences["duration"]["new"] == 10.0

    def test_is_latest_property(self, user, scene):
        """测试 is_latest 属性"""
        shot = Shot.objects.create(
            scene=scene,
            shot_number=1,
            shot_type="dialogue",
            content="Test content",
            speaker="Test Speaker",
            sort_order=0,
        )

        version1 = ShotVersion.create_version(shot=shot, user=user)
        version2 = ShotVersion.create_version(shot=shot, user=user)

        assert version1.is_latest is False
        assert version2.is_latest is True

    def test_str_method(self, user, scene):
        """测试 __str__ 方法"""
        shot = Shot.objects.create(
            scene=scene,
            shot_number=1,
            shot_type="dialogue",
            content="This is a very long content that should be truncated in the string representation",
            speaker="Test Speaker",
            sort_order=0,
        )

        version = ShotVersion.create_version(shot=shot, user=user)

        str_repr = str(version)
        assert "v1" in str_repr
        # Shot 的 __str__ 只截取前30个字符，不添加 "..."
        assert "This is a very long content th" in str_repr  # 前30个字符


@pytest.mark.django_db
class TestShotVersionSerializer:
    """测试 ShotVersion 序列化器"""

    def test_serializer_includes_all_fields(self, user, scene):
        """测试序列化器包含所有字段"""
        shot = Shot.objects.create(
            scene=scene,
            shot_number=1,
            shot_type="dialogue",
            content="Test content",
            speaker="Test Speaker",
            sort_order=0,
        )

        version = ShotVersion.create_version(
            shot=shot,
            change_description="Test version",
            user=user,
        )

        serializer = ShotVersionSerializer(version)
        data = serializer.data

        assert data["id"] == version.id
        assert data["version_number"] == 1
        assert data["change_description"] == "Test version"
        assert data["is_auto_created"] is True
        assert data["is_latest"] is True
        assert "content_snapshot" in data
        assert "shot_content_preview" in data

    def test_shot_content_preview_truncates_long_content(self, user, scene):
        """测试内容预览截断长内容"""
        shot = Shot.objects.create(
            scene=scene,
            shot_number=1,
            shot_type="dialogue",
            content="a" * 200,  # 超过100字符的长内容
            speaker="Test Speaker",
            sort_order=0,
        )

        version = ShotVersion.create_version(shot=shot, user=user)
        serializer = ShotVersionSerializer(version)
        data = serializer.data

        assert len(data["shot_content_preview"]) == 103  # 100 + "..."
        assert data["shot_content_preview"].endswith("...")


@pytest.mark.django_db
class TestShotVersionAPI:
    """测试 ShotVersion API 端点"""

    def test_list_versions_for_shot(self, user, scene):
        """测试获取镜头的版本列表"""
        shot = Shot.objects.create(
            scene=scene,
            shot_number=1,
            shot_type="dialogue",
            content="Test content",
            speaker="Test Speaker",
            sort_order=0,
        )

        # 创建多个版本
        for i in range(5):
            ShotVersion.create_version(
                shot=shot,
                change_description=f"Version {i + 1}",
                user=user,
            )

        factory = APIRequestFactory()
        viewset = ShotVersionViewSet.as_view({"get": "list"})

        request = factory.get(f"/api/v1/artworks/shot-versions/?shot_id={shot.id}")
        force_authenticate(request, user=user)

        response = viewset(request)

        assert response.status_code == 200
        data = response.data
        # 注意: 由于分页，实际返回的结构可能不同
        assert "results" in data or len(data) >= 5

    def test_restore_version(self, user, scene):
        """测试恢复版本 API"""
        shot = Shot.objects.create(
            scene=scene,
            shot_number=1,
            shot_type="dialogue",
            content="Original content",
            speaker="Original Speaker",
            sort_order=0,
        )

        version1 = ShotVersion.create_version(shot=shot, user=user)

        # 修改镜头
        shot.content = "Modified content"
        shot.save()

        factory = APIRequestFactory()
        viewset = ShotVersionViewSet.as_view({"post": "restore"})

        request = factory.post(f"/api/v1/artworks/shot-versions/{version1.id}/restore/")
        force_authenticate(request, user=user)

        response = viewset(request, pk=version1.id)

        assert response.status_code == 200
        data = response.data
        assert "detail" in data
        assert "restored" in data["detail"].lower() or "恢复" in data["detail"]
        assert "shot" in data

        # 验证镜头已恢复
        shot.refresh_from_db()
        assert shot.content == "Original content"

    def test_compare_versions(self, user, scene):
        """测试版本对比 API"""
        shot = Shot.objects.create(
            scene=scene,
            shot_number=1,
            shot_type="dialogue",
            content="Original content",
            speaker="Original Speaker",
            sort_order=0,
        )

        version1 = ShotVersion.create_version(shot=shot, user=user)

        shot.content = "Modified content"
        shot.camera_movement = "zoom in"
        shot.save()

        version2 = ShotVersion.create_version(shot=shot, user=user)

        factory = APIRequestFactory()
        viewset = ShotVersionViewSet.as_view({"get": "compare"})

        request = factory.get(
            f"/api/v1/artworks/shot-versions/{version2.id}/compare/?compare_version_id={version1.id}"
        )
        force_authenticate(request, user=user)

        response = viewset(request, pk=version2.id)

        assert response.status_code == 200
        data = response.data
        assert "current_version" in data
        assert "compare_version" in data
        assert "differences" in data
        assert "content" in data["differences"]

    def test_create_snapshot(self, user, scene):
        """测试手动创建快照 API"""
        shot = Shot.objects.create(
            scene=scene,
            shot_number=1,
            shot_type="dialogue",
            content="Test content",
            speaker="Test Speaker",
            sort_order=0,
        )

        factory = APIRequestFactory()
        viewset = ShotVersionViewSet.as_view({"post": "create_snapshot"})

        request = factory.post(
            "/api/v1/artworks/shot-versions/create_snapshot/",
            {
                "shot_id": shot.id,
                "change_description": "手动创建的版本",
            },
            format="json",
        )
        force_authenticate(request, user=user)

        response = viewset(request)

        assert response.status_code == 201
        data = response.data
        assert "detail" in data
        assert "version" in data
        assert data["version"]["change_description"] == "手动创建的版本"
        assert data["version"]["is_auto_created"] is False

        # 验证版本已创建
        versions_count = ShotVersion.objects.filter(shot=shot).count()
        assert versions_count == 1


# ===== Fixtures =====


@pytest.fixture
def user(db):
    """创建测试用户"""
    return User.objects.create_user(
        username="testuser",
        email="test@example.com",
        password="testpass123",
    )


@pytest.fixture
def artwork(db):
    """创建测试作品"""
    return Artwork.objects.create(
        title="Test Artwork",
        author="Test Author",
        artwork_type="novel",
    )


@pytest.fixture
def chapter(db, artwork):
    """创建测试章节"""
    return Chapter.objects.create(
        artwork=artwork,
        chapter_number=1,
        title="Chapter 1",
        original_text="This is a test chapter content.",
    )


@pytest.fixture
def physical_scene(db):
    """创建测试物理场景"""
    return PhysicalScene.objects.create(
        name="Test Scene",
        category="indoor",
    )


@pytest.fixture
def scene(db, chapter, physical_scene):
    """创建测试剧本场景"""
    return ScriptScene.objects.create(
        chapter=chapter,
        physical_scene=physical_scene,
        scene_number=1,
        scene_name="Scene 1",
        description="Test scene description",
    )


@pytest.fixture
def character(db, artwork):
    """创建测试角色"""
    return CharacterProfile.objects.create(
        artwork=artwork,
        name="Test Character",
        display_name="Test Character Display",
    )
