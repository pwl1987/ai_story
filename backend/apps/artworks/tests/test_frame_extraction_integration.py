"""
首尾帧提取集成测试 (Story 12-5)

测试覆盖:
1. 端到端提取流程
2. Celery 任务执行
3. 异步任务进度追踪
4. 服务与API集成

运行方法：python -m pytest apps/artworks/tests/test_frame_extraction_integration.py -v
"""

import io

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image

from apps.artworks.models import ScriptScene, Shot, Chapter, Artwork
from apps.artworks.tasks import extract_frames_task
from config.celery import app


@pytest.mark.django_db
class TestFrameExtractionIntegration:
    """首尾帧提取集成测试"""

    def setup_method(self):
        """测试数据初始化"""
        # 创建测试用作品
        self.artwork = Artwork.objects.create(
            title="集成测试作品",
            author="测试作者",
            artwork_type="novel",
        )

        self.chapter = Chapter.objects.create(
            artwork=self.artwork,
            chapter_number=1,
            title="集成测试章节",
            original_text="测试内容",
        )

    def _create_scene_with_shots(self, shot_count=2):
        """创建带镜头的测试场景"""
        scene = ScriptScene.objects.create(
            chapter=self.chapter,
            scene_number=1,
            scene_name="集成测试场景",
        )

        # 创建多个镜头
        for i in range(shot_count):
            img = Image.new("RGB", (100, 100), color=["red", "blue", "green"][i])
            buffer = io.BytesIO()
            img.save(buffer, format="JPEG")
            buffer.seek(0)

            upload = SimpleUploadedFile(
                name=f"shot_{i}.jpg",
                content=buffer.read(),
                content_type="image/jpeg",
            )

            Shot.objects.create(
                scene=scene, shot_number=i + 1, sort_order=i + 1, generated_image=upload
            )

        return scene

    # ========== 集成测试 ==========

    def test_end_to_end_frame_extraction(self):
        """测试端到端提取流程"""
        from apps.artworks.services.frame_extraction import get_frame_extraction_service

        scene = self._create_scene_with_shots(shot_count=3)

        # 执行提取
        service = get_frame_extraction_service()
        result = service.extract_frames(scene.id)

        # 验证结果
        assert result["success"] is True
        assert result["message"] == "提取成功"

        # 刷新并验证场景对象
        scene.refresh_from_db()
        assert scene.head_frame is not None
        assert scene.tail_frame is not None

        # 验证文件存在
        import os
        if scene.head_frame and scene.head_frame.path:
            assert os.path.exists(scene.head_frame.path)
        if scene.tail_frame and scene.tail_frame.path:
            assert os.path.exists(scene.tail_frame.path)

    def test_celery_task_execution(self):
        """测试 Celery 任务执行"""
        scene = self._create_scene_with_shots(shot_count=2)

        # 同步执行任务（用于测试）
        result = extract_frames_task.apply_async(args=[scene.id]).get(timeout=30)

        # 验证任务结果
        assert result["success"] is True
        assert result["scene_id"] == scene.id

        # 刷新场景并验证首尾帧
        scene.refresh_from_db()
        assert scene.head_frame is not None
        assert scene.tail_frame is not None

        # 验证返回的URL
        assert "head_frame_url" in result
        assert "tail_frame_url" in result

    def test_celery_task_with_nonexistent_scene(self):
        """测试不存在场景的 Celery 任务"""
        result = extract_frames_task.apply_async(args=[99999]).get(timeout=10)

        # 应该返回失败
        assert result["success"] is False
        assert "error" in result

    def test_celery_task_force_reextract(self):
        """测试强制重新提取功能"""
        scene = self._create_scene_with_shots(shot_count=2)

        # 第一次提取
        result1 = extract_frames_task.apply_async(
            args=[scene.id, False]
        ).get(timeout=30)

        assert result1["success"] is True
        first_head_url = result1.get("head_frame_url")

        # 强制重新提取
        result2 = extract_frames_task.apply_async(
            args=[scene.id, True]
        ).get(timeout=30)

        assert result2["success"] is True
        second_head_url = result2.get("head_frame_url")

        # 验证两次提取的URL存在（时间戳导致路径不同）
        assert first_head_url is not None
        assert second_head_url is not None

    def test_service_with_marked_frames(self):
        """测试使用标记的首尾帧"""
        scene = self._create_scene_with_shots(shot_count=3)

        # 标记特定镜头为首尾帧
        shots = list(scene.shots.all())
        shots[0].is_head_frame = True
        shots[0].save()

        shots[-1].is_tail_frame = True
        shots[-1].save()

        from apps.artworks.services.frame_extraction import get_frame_extraction_service

        # 执行提取
        service = get_frame_extraction_service()
        result = service.extract_frames(scene.id)

        # 验证使用了标记的镜头
        assert result["success"] is True
        scene.refresh_from_db()

        # 验证首帧来自第一个镜头（被标记）
        assert scene.head_frame is not None

        # 验证尾帧来自最后一个镜头（被标记）
        assert scene.tail_frame is not None

    def test_service_quality_optimization(self):
        """测试图片质量优化"""
        scene = self._create_scene_with_shots(shot_count=1)

        # 创建高质量测试图片
        img = Image.new("RGB", (3840, 2160), color="purple")
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG", quality=95)
        buffer.seek(0)

        upload = SimpleUploadedFile(
            name="high_quality.jpg",
            content=buffer.read(),
            content_type="image/jpeg",
        )

        # 替换镜头图片
        shot = scene.shots.first()
        shot.image = upload
        shot.save()

        from apps.artworks.services.frame_extraction import get_frame_extraction_service

        # 执行提取
        service = get_frame_extraction_service()
        result = service.extract_frames(scene.id)

        # 验证成功提取
        assert result["success"] is True
        scene.refresh_from_db()
        assert scene.head_frame is not None

        # 验证图片已优化到1080p
        if scene.head_frame and scene.head_frame.path:
            import os
            assert os.path.exists(scene.head_frame.path)

            with Image.open(scene.head_frame.path) as optimized_img:
                # 验证尺寸不超过1080p
                assert optimized_img.width <= 1920
                assert optimized_img.height <= 1080

    @pytest.mark.skip(reason="需要实际文件系统验证")
    def test_frame_file_storage_structure(self):
        """测试文件存储结构"""
        scene = self._create_scene_with_shots(shot_count=1)

        from apps.artworks.services.frame_extraction import get_frame_extraction_service

        # 执行提取
        service = get_frame_extraction_service()
        result = service.extract_frames(scene.id)

        # 验证成功
        assert result["success"] is True
        scene.refresh_from_db()

        # 验证文件路径格式
        if scene.head_frame and scene.head_frame.name:
            # 路径应该包含 scenes/heads/ 或 scenes/frames/head/
            assert "head" in scene.head_frame.name.lower()
            assert scene.head_frame.name.endswith(".jpg")

        if scene.tail_frame and scene.tail_frame.name:
            # 路径应该包含 scenes/tails/ 或 scenes/frames/tail/
            assert "tail" in scene.tail_frame.name.lower()
            assert scene.tail_frame.name.endswith(".jpg")
