"""
Story 11.5.1: 批量操作功能测试

测试:
- BatchOperationResult 数据类
- BatchOperationService 基础服务
- ShotBatchOperationService 镜头批量操作
- API 端点测试
"""

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIRequestFactory, force_authenticate

from apps.artworks.models import (
    Artwork,
    Chapter,
    CharacterPose,
    CharacterProfile,
    GenerationProgress,
    ScriptScene,
    Shot,
)
from apps.artworks.services import (
    BatchOperationResult,
    BatchOperationService,
    ShotBatchOperationService,
)
from apps.artworks.views import (
    GenerationProgressViewSet,
    ScriptSceneViewSet,
    ShotViewSet,
)

User = get_user_model()


@pytest.mark.django_db
class TestBatchOperationResult:
    """测试 BatchOperationResult 数据类"""

    def test_result_initialization(self):
        """测试结果初始化"""
        result = BatchOperationResult(operation_type="test_operation")

        assert result.operation_type == "test_operation"
        assert result.total_count == 0
        assert result.success_count == 0
        assert result.failed_count == 0
        assert result.errors == []
        assert result.success_ids == []
        assert result.progress_id is None

    def test_add_success(self):
        """测试添加成功项"""
        result = BatchOperationResult(operation_type="test")
        result.add_success(123)
        result.add_success(456)

        assert result.success_count == 2
        assert result.total_count == 2
        assert result.success_ids == [123, 456]

    def test_add_error(self):
        """测试添加错误项"""
        result = BatchOperationResult(operation_type="test")
        result.add_error(789, "Item not found", error_code="NOT_FOUND")

        assert result.failed_count == 1
        assert result.total_count == 1
        assert len(result.errors) == 1
        assert result.errors[0]["item_id"] == 789
        assert result.errors[0]["error_message"] == "Item not found"
        assert result.errors[0]["error_code"] == "NOT_FOUND"

    def test_mark_completed(self):
        """测试标记完成"""
        result = BatchOperationResult(operation_type="test")
        result.mark_completed()

        assert result.completed_at is not None

    def test_calculate_success_rate(self):
        """测试成功率计算"""
        result = BatchOperationResult(operation_type="test")
        result.add_success(1)
        result.add_success(2)
        result.add_success(3)
        result.add_error(4, "Error")

        assert result._calculate_success_rate() == 75.0

    def test_to_dict(self):
        """测试转换为字典"""
        result = BatchOperationResult(operation_type="bulk_delete")
        result.add_success(1)
        result.add_error(2, "Error", "DELETE_ERROR")
        result.mark_completed()

        data = result.to_dict()

        assert data["operation_type"] == "bulk_delete"
        assert data["total_count"] == 2
        assert data["success_count"] == 1
        assert data["failed_count"] == 1
        assert data["success_rate"] == 50.0
        assert len(data["errors"]) == 1
        assert data["success_ids"] == [1]
        assert data["duration_seconds"] is not None


@pytest.mark.django_db
class TestBatchOperationService:
    """测试 BatchOperationService 基础服务"""

    def test_create_progress(self, user):
        """测试创建进度追踪"""
        service = BatchOperationService(operation_type="test", user=user)
        progress = service._create_progress(10)

        assert progress.total_items == 10
        assert progress.completed_items == 0
        assert progress.status == "processing"
        assert progress.user == user

    def test_update_progress(self, user):
        """测试更新进度"""
        service = BatchOperationService(operation_type="test", user=user)
        progress = service._create_progress(10)

        service._update_progress(completed=5, failed=2)

        progress.refresh_from_db()
        assert progress.completed_items == 5
        assert progress.failed_items == 2

    def test_execute_batch_delete(self, user, artwork, chapter, scene):
        """测试批量删除操作"""
        # 创建多个镜头
        shots = []
        for i in range(3):
            shot = Shot.objects.create(
                scene=scene,
                shot_number=i + 1,
                shot_type="dialogue",
                content=f"Test content {i}",
                speaker="Test Speaker",
                sort_order=i,
            )
            shots.append(shot)

        service = BatchOperationService(operation_type="bulk_delete", user=user)
        shot_ids = [shots[0].id, shots[1].id]

        result = service.execute_batch_delete(Shot, shot_ids)

        assert result.total_count == 2
        assert result.success_count == 2
        assert result.failed_count == 0
        assert result.success_ids == shot_ids

        # 验证镜头已被删除
        assert Shot.objects.filter(id__in=shot_ids).count() == 0
        assert Shot.objects.filter(id=shots[2].id).exists()

    def test_execute_batch_delete_with_not_found(self, user, scene):
        """测试批量删除包含不存在的项目"""
        # 创建一个镜头
        shot = Shot.objects.create(
            scene=scene,
            shot_number=1,
            shot_type="dialogue",
            content="Test content",
            speaker="Test Speaker",
            sort_order=0,
        )

        service = BatchOperationService(operation_type="bulk_delete", user=user)
        # 包含存在的ID和不存在的ID
        shot_ids = [shot.id, 99999]

        result = service.execute_batch_delete(Shot, shot_ids)

        assert result.total_count == 2
        assert result.success_count == 1
        assert result.failed_count == 1
        assert len(result.errors) == 1
        assert result.errors[0]["error_code"] == "NOT_FOUND"

    def test_execute_batch_operation(self, user, scene):
        """测试通用批量操作"""
        # 创建多个场景
        scenes = []
        for i in range(3):
            s = ScriptScene.objects.create(
                chapter=scene.chapter,
                physical_scene=scene.physical_scene,
                scene_number=i + 10,
                scene_name=f"Test Scene {i}",
                description=f"Description {i}",
            )
            scenes.append(s)

        service = BatchOperationService(operation_type="bulk_update", user=user)

        def update_scene_name(scene):
            scene.scene_name = f"Updated {scene.scene_name}"
            scene.save(update_fields=["scene_name"])

        result = service.execute_batch_operation(scenes, update_scene_name, "UPDATE_ERROR")

        assert result.total_count == 3
        assert result.success_count == 3
        assert result.failed_count == 0

        # 验证场景名称已更新
        for scene in scenes:
            scene.refresh_from_db()
            assert scene.scene_name.startswith("Updated")


@pytest.mark.django_db
class TestShotBatchOperationService:
    """测试 ShotBatchOperationService 镜头批量操作"""

    def test_batch_update_character(self, user, artwork, chapter, scene, character):
        """测试批量更新角色造型"""
        # 创建造型
        pose = CharacterPose.objects.create(
            character=character,
            pose_name="Test Pose",
            pose_type="casual",
            pose_image="test.jpg",
        )

        # 创建多个镜头
        shots = []
        for i in range(3):
            shot = Shot.objects.create(
                scene=scene,
                shot_number=i + 1,
                shot_type="dialogue",
                content=f"Test content {i}",
                speaker="Test Speaker",
                sort_order=i,
            )
            shots.append(shot)

        service = ShotBatchOperationService(operation_type="bulk_update_character", user=user)
        shot_ids = [s.id for s in shots]

        result = service.batch_update_character(shot_ids, pose.id)

        assert result.total_count == 3
        assert result.success_count == 3
        assert result.failed_count == 0

        # 验证造型已更新
        for shot in shots:
            shot.refresh_from_db()
            assert shot.character_pose_id == pose.id

    def test_batch_update_character_clear(self, user, scene, character):
        """测试批量清除角色造型"""
        pose = CharacterPose.objects.create(
            character=character,
            pose_name="Test Pose",
            pose_type="casual",
            pose_image="test.jpg",
        )

        # 创建带有造型的镜头
        shots = []
        for i in range(2):
            shot = Shot.objects.create(
                scene=scene,
                shot_number=i + 1,
                shot_type="dialogue",
                content=f"Test content {i}",
                speaker="Test Speaker",
                character_pose=pose,
                sort_order=i,
            )
            shots.append(shot)

        service = ShotBatchOperationService(operation_type="bulk_update_character", user=user)
        shot_ids = [s.id for s in shots]

        # 传入 None 表示清除造型
        result = service.batch_update_character(shot_ids, None)

        assert result.total_count == 2
        assert result.success_count == 2

        # 验证造型已清除
        for shot in shots:
            shot.refresh_from_db()
            assert shot.character_pose_id is None

    def test_batch_update_character_invalid_pose(self, user, scene):
        """测试批量更新使用无效的造型ID"""
        shot = Shot.objects.create(
            scene=scene,
            shot_number=1,
            shot_type="dialogue",
            content="Test content",
            speaker="Test Speaker",
            sort_order=0,
        )

        service = ShotBatchOperationService(operation_type="bulk_update_character", user=user)

        result = service.batch_update_character([shot.id], 99999)

        # 应该失败，因为造型不存在 (失败快速返回，未处理任何镜头)
        assert result.total_count == 0  # 没有处理任何镜头
        assert result.success_count == 0
        assert result.failed_count == 1
        assert result.errors[0]["error_code"] == "POSE_NOT_FOUND"

    def test_batch_move(self, user, artwork, chapter, scene):
        """测试批量移动镜头"""
        # 创建目标场景
        target_scene = ScriptScene.objects.create(
            chapter=chapter,
            physical_scene=scene.physical_scene,
            scene_number=2,
            scene_name="Target Scene",
            description="Target description",
        )

        # 创建多个镜头在源场景
        shots = []
        for i in range(3):
            shot = Shot.objects.create(
                scene=scene,
                shot_number=i + 1,
                shot_type="dialogue",
                content=f"Test content {i}",
                speaker="Test Speaker",
                sort_order=i,
            )
            shots.append(shot)

        # 更新源场景的镜头计数
        scene.shot_count = 3
        scene.save()

        service = ShotBatchOperationService(operation_type="bulk_move", user=user)
        shot_ids = [s.id for s in shots]

        result = service.batch_move(shot_ids, target_scene.id, update_sort_order=True)

        assert result.total_count == 3
        assert result.success_count == 3
        assert result.failed_count == 0

        # 验证镜头已移动
        for shot in shots:
            shot.refresh_from_db()
            assert shot.scene_id == target_scene.id
            assert shot.sort_order > 0

        # 验证目标场景的镜头计数已更新
        target_scene.refresh_from_db()
        assert target_scene.shot_count == 3

    def test_batch_move_target_scene_not_found(self, user, scene):
        """测试批量移动到不存在的场景"""
        shot = Shot.objects.create(
            scene=scene,
            shot_number=1,
            shot_type="dialogue",
            content="Test content",
            speaker="Test Speaker",
            sort_order=0,
        )

        service = ShotBatchOperationService(operation_type="bulk_move", user=user)

        result = service.batch_move([shot.id], 99999)

        assert result.failed_count == 1
        assert result.errors[0]["error_code"] == "TARGET_SCENE_NOT_FOUND"


@pytest.mark.django_db
class TestBatchOperationAPI:
    """测试批量操作 API 端点"""

    def test_api_bulk_update_character(self, user, artwork, chapter, scene, character):
        """测试批量更新角色造型 API"""
        pose = CharacterPose.objects.create(
            character=character,
            pose_name="Test Pose",
            pose_type="casual",
            pose_image="test.jpg",
        )

        shots = []
        for i in range(3):
            shot = Shot.objects.create(
                scene=scene,
                shot_number=i + 1,
                shot_type="dialogue",
                content=f"Test content {i}",
                speaker="Test Speaker",
                sort_order=i,
            )
            shots.append(shot)

        factory = APIRequestFactory()
        viewset = ShotViewSet.as_view({"post": "bulk_update_character"})

        request = factory.post(
            "/api/v1/artworks/shots/bulk_update_character/",
            {
                "shot_ids": [s.id for s in shots],
                "character_pose_id": pose.id,
            },
            format="json",
        )
        force_authenticate(request, user=user)

        response = viewset(request)

        assert response.status_code == 200
        data = response.data
        assert data["success_count"] == 3
        assert data["failed_count"] == 0
        assert data["progress_id"] is not None

    def test_api_bulk_move(self, user, chapter, scene):
        """测试批量移动镜头 API"""
        target_scene = ScriptScene.objects.create(
            chapter=chapter,
            physical_scene=scene.physical_scene,
            scene_number=2,
            scene_name="Target Scene",
            description="Target description",
        )

        shots = []
        for i in range(3):
            shot = Shot.objects.create(
                scene=scene,
                shot_number=i + 1,
                shot_type="dialogue",
                content=f"Test content {i}",
                speaker="Test Speaker",
                sort_order=i,
            )
            shots.append(shot)

        factory = APIRequestFactory()
        viewset = ShotViewSet.as_view({"post": "bulk_move"})

        request = factory.post(
            "/api/v1/artworks/shots/bulk_move/",
            {
                "shot_ids": [s.id for s in shots],
                "target_scene_id": target_scene.id,
                "update_sort_order": True,
            },
            format="json",
        )
        force_authenticate(request, user=user)

        response = viewset(request)

        assert response.status_code == 200
        data = response.data
        assert data["success_count"] == 3
        assert data["operation_type"] == "bulk_move"

    def test_api_bulk_delete_enhanced(self, user, scene):
        """测试批量删除镜头 API (增强版)"""
        shots = []
        for i in range(3):
            shot = Shot.objects.create(
                scene=scene,
                shot_number=i + 1,
                shot_type="dialogue",
                content=f"Test content {i}",
                speaker="Test Speaker",
                sort_order=i,
            )
            shots.append(shot)

        factory = APIRequestFactory()
        viewset = ShotViewSet.as_view({"post": "bulk_delete_enhanced"})

        request = factory.post(
            "/api/v1/artworks/shots/bulk_delete_enhanced/",
            {"shot_ids": [shots[0].id, shots[1].id]},
            format="json",
        )
        force_authenticate(request, user=user)

        response = viewset(request)

        assert response.status_code == 200
        data = response.data
        assert data["success_count"] == 2
        assert data["operation_type"] == "bulk_delete"

    def test_api_progress_list(self, user, scene):
        """测试获取进度列表 API"""
        # 创建一些进度记录
        for i in range(3):
            GenerationProgress.objects.create(
                user=user,
                generation_type="batch",
                status="processing",
                total_items=10,
                completed_items=i,
                failed_items=0,
            )

        factory = APIRequestFactory()
        viewset = GenerationProgressViewSet.as_view({"get": "list"})

        request = factory.get("/api/v1/artworks/progress/")
        force_authenticate(request, user=user)

        response = viewset(request)

        assert response.status_code == 200
        data = response.data
        assert len(data) >= 3

    def test_api_progress_detail(self, user):
        """测试获取进度详情 API"""
        progress = GenerationProgress.objects.create(
            user=user,
            generation_type="batch",
            status="processing",
            total_items=10,
            completed_items=5,
            failed_items=1,
        )

        factory = APIRequestFactory()
        viewset = GenerationProgressViewSet.as_view({"get": "retrieve"})

        request = factory.get(f"/api/v1/artworks/progress/{progress.id}/")
        force_authenticate(request, user=user)

        response = viewset(request, pk=progress.id)

        assert response.status_code == 200
        data = response.data
        assert data["id"] == progress.id
        assert data["progress_percentage"] == 50.0


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
    from apps.artworks.models import PhysicalScene

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
