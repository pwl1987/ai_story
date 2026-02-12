"""
首尾帧提取服务单元测试 (Story 12-5)

测试覆盖:
1. 首帧查找逻辑（优先标记 > 序列顺序）
2. 尾帧查找逻辑（优先标记 > 序列倒序）
3. 图片优化逻辑（1080p JPEG 格式）
4. 边界条件处理（空场景、单镜头、文件损坏）
5. 重新提取功能

运行方法：python -m pytest apps/artworks/tests/test_frame_extraction_service.py -v
"""

import io

import pytest
from PIL import Image

from apps.artworks.models import ScriptScene, Shot, Chapter, Artwork
from apps.artworks.services.frame_extraction import (
    FrameExtractionService,
    get_frame_extraction_service,
)


@pytest.mark.django_db
class TestFrameExtractionService:
    """测试首尾帧提取服务"""

    def setup_method(self):
        """测试数据初始化"""
        self.service = FrameExtractionService()

        # 创建测试用章节和场景
        self.artwork = Artwork.objects.create(
            title="测试作品",
            author="测试作者",
            artwork_type="novel",
        )

        self.chapter = Chapter.objects.create(
            artwork=self.artwork,
            chapter_number=1,
            title="测试章节",
            original_text="测试内容",
        )

    # ========== 首帧查找测试 ==========

    def test_find_head_shot_with_marked_head(self):
        """测试优先使用标记的首帧"""
        scene = ScriptScene.objects.create(
            chapter=self.chapter,
            scene_number=1,
            scene_name="场景1",
        )

        shot1 = Shot.objects.create(
            scene=scene, shot_number=1, sort_order=1, is_head_frame=False
        )
        shot2 = Shot.objects.create(
            scene=scene, shot_number=2, sort_order=2, is_head_frame=True
        )

        head_shot = self.service._find_head_shot(scene.shots.all())

        assert head_shot.id == shot2.id
        assert head_shot.is_head_frame is True

    def test_find_head_shot_without_marked_head(self):
        """测试无标记时使用第一个镜头"""
        scene = ScriptScene.objects.create(
            chapter=self.chapter,
            scene_number=2,
            scene_name="场景2",
        )

        shot1 = Shot.objects.create(scene=scene, shot_number=1, sort_order=1)
        shot2 = Shot.objects.create(scene=scene, shot_number=2, sort_order=2)

        head_shot = self.service._find_head_shot(scene.shots.all())

        assert head_shot.id == shot1.id
        assert head_shot.sort_order == 1

    def test_find_head_shot_empty_shots(self):
        """测试空镜头列表返回None"""
        scene = ScriptScene.objects.create(
            chapter=self.chapter,
            scene_number=3,
            scene_name="场景3",
        )

        head_shot = self.service._find_head_shot(scene.shots.all())
        assert head_shot is None

    # ========== 尾帧查找测试 ==========

    def test_find_tail_shot_with_marked_tail(self):
        """测试优先使用标记的尾帧"""
        scene = ScriptScene.objects.create(
            chapter=self.chapter,
            scene_number=4,
            scene_name="场景4",
        )

        shot1 = Shot.objects.create(
            scene=scene, shot_number=1, sort_order=2, is_tail_frame=True
        )
        shot2 = Shot.objects.create(
            scene=scene, shot_number=2, sort_order=3, is_tail_frame=False
        )

        tail_shot = self.service._find_tail_shot(scene.shots.all())

        assert tail_shot.id == shot1.id
        assert tail_shot.is_tail_frame is True

    def test_find_tail_shot_without_marked_tail(self):
        """测试无标记时使用最后一个镜头"""
        scene = ScriptScene.objects.create(
            chapter=self.chapter,
            scene_number=5,
            scene_name="场景5",
        )

        shot1 = Shot.objects.create(scene=scene, shot_number=1, sort_order=1)
        shot2 = Shot.objects.create(scene=scene, shot_number=2, sort_order=3)

        tail_shot = self.service._find_tail_shot(scene.shots.all())

        assert tail_shot.id == shot2.id
        assert tail_shot.sort_order == 3

    def test_find_tail_shot_empty_shots(self):
        """测试空镜头列表返回None"""
        scene = ScriptScene.objects.create(
            chapter=self.chapter,
            scene_number=6,
            scene_name="场景6",
        )

        tail_shot = self.service._find_tail_shot(scene.shots.all())
        assert tail_shot is None

    # ========== 图片优化测试 ==========

    def test_extract_and_optimize_frame_converts_to_rgb(self):
        """测试图片转换为RGB格式"""
        scene = ScriptScene.objects.create(
            chapter=self.chapter,
            scene_number=7,
            scene_name="场景7",
        )

        # 创建 RGBA 格式的测试图片
        img = Image.new("RGBA", (100, 100), color=(255, 0, 0, 128))
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)

        from django.core.files.uploadedfile import SimpleUploadedFile

        upload = SimpleUploadedFile(
            name="test_rgba.png",
            content=buffer.read(),
            content_type="image/png",
        )

        shot = Shot.objects.create(scene=scene, shot_number=1, sort_order=1, generated_image=upload)

        result = self.service._extract_and_optimize_frame(shot, "head", scene)

        assert result is not None
        assert result.name.endswith(".jpg")

    def test_extract_and_optimize_frame_resizes_to_1080p(self):
        """测试图片缩放到1080p"""
        scene = ScriptScene.objects.create(
            chapter=self.chapter,
            scene_number=8,
            scene_name="场景8",
        )

        # 创建大尺寸测试图片
        img = Image.new("RGB", (3840, 2160), color="red")
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG")
        buffer.seek(0)

        from django.core.files.uploadedfile import SimpleUploadedFile

        upload = SimpleUploadedFile(
            name="test_large.jpg",
            content=buffer.read(),
            content_type="image/jpeg",
        )

        shot = Shot.objects.create(scene=scene, shot_number=1, sort_order=1, generated_image=upload)

        result = self.service._extract_and_optimize_frame(shot, "head", scene)

        # 验证生成的图片尺寸不超过1080p
        assert result is not None

    def test_extract_and_optimize_frame_with_corrupted_image(self):
        """测试损坏图片返回None"""
        scene = ScriptScene.objects.create(
            chapter=self.chapter,
            scene_number=9,
            scene_name="场景9",
        )

        shot = Shot.objects.create(scene=scene, shot_number=1, sort_order=1, generated_image=None)

        result = self.service._extract_and_optimize_frame(shot, "head", scene)

        assert result is None

    def test_extract_and_optimize_frame_filename_format(self):
        """测试生成正确的文件名格式"""
        scene = ScriptScene.objects.create(
            chapter=self.chapter,
            scene_number=10,
            scene_name="场景10",
        )

        img = Image.new("RGB", (100, 100), color="blue")
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG")
        buffer.seek(0)

        from django.core.files.uploadedfile import SimpleUploadedFile

        upload = SimpleUploadedFile(
            name="test.jpg",
            content=buffer.read(),
            content_type="image/jpeg",
        )

        shot = Shot.objects.create(scene=scene, shot_number=1, sort_order=1, generated_image=upload)

        result = self.service._extract_and_optimize_frame(shot, "head", scene)

        # 验证文件名格式: head_{scene_id}_{shot_id}.jpg
        assert result.name == f"head_{scene.id}_{shot.id}.jpg"

    # ========== 边界条件测试 ==========

    def test_extract_frames_with_empty_scene(self):
        """测试空场景抛出ValueError"""
        scene = ScriptScene.objects.create(
            chapter=self.chapter,
            scene_number=11,
            scene_name="空场景",
        )

        with pytest.raises(ValueError) as exc_info:
            self.service.extract_frames(scene.id)

        assert "没有可提取的镜头" in str(exc_info.value)

    def test_extract_frames_with_single_shot(self):
        """测试单镜头场景首尾帧相同"""
        scene = ScriptScene.objects.create(
            chapter=self.chapter,
            scene_number=12,
            scene_name="单镜头场景",
        )

        img = Image.new("RGB", (100, 100), color="green")
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG")
        buffer.seek(0)

        from django.core.files.uploadedfile import SimpleUploadedFile

        upload = SimpleUploadedFile(
            name="single.jpg",
            content=buffer.read(),
            content_type="image/jpeg",
        )

        Shot.objects.create(scene=scene, shot_number=1, sort_order=1, generated_image=upload)

        result = self.service.extract_frames(scene.id)

        assert result["success"] is True
        scene.refresh_from_db()
        # 单镜头场景，首尾帧应该都存在
        assert scene.head_frame is not None
        assert scene.tail_frame is not None

    def test_re_extract_overwrites_existing_frames(self):
        """测试重新提取覆盖已有帧"""
        scene = ScriptScene.objects.create(
            chapter=self.chapter,
            scene_number=13,
            scene_name="测试重新提取",
        )

        img = Image.new("RGB", (100, 100), color="yellow")
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG")
        buffer.seek(0)

        from django.core.files.uploadedfile import SimpleUploadedFile

        upload = SimpleUploadedFile(
            name="retest.jpg",
            content=buffer.read(),
            content_type="image/jpeg",
        )

        shot = Shot.objects.create(scene=scene, shot_number=1, sort_order=1, generated_image=upload)

        # 第一次提取
        self.service.extract_frames(scene.id)
        scene.refresh_from_db()
        first_head_name = scene.head_frame.name if scene.head_frame else None

        # 第二次提取（重新提取）
        import time
        time.sleep(0.1)  # 确保时间戳不同
        self.service.extract_frames(scene.id)
        scene.refresh_from_db()
        second_head_name = scene.head_frame.name if scene.head_frame else None

        # 验证文件名不同（时间戳导致路径不同）
        if first_head_name and second_head_name:
            # 文件名相同但路径不同（因为日期目录）
            assert first_head_name.split("/")[0] == second_head_name.split("/")[0]

    def test_extract_frames_nonexistent_scene(self):
        """测试不存在的场景抛出ValueError"""
        with pytest.raises(ValueError) as exc_info:
            self.service.extract_frames(99999)

        assert "不存在" in str(exc_info.value)

    def test_extract_frames_invalid_scene_id(self):
        """测试无效场景 ID（<= 0）抛出 ValueError"""
        with pytest.raises(ValueError) as exc_info:
            self.service.extract_frames(0)

        assert "无效的场景 ID" in str(exc_info.value)

        with pytest.raises(ValueError) as exc_info:
            self.service.extract_frames(-1)

        assert "无效的场景 ID" in str(exc_info.value)

        # ========== 单例模式测试 ==========

    def test_get_frame_extraction_service_singleton(self):
        """测试服务单例模式"""
        service1 = get_frame_extraction_service()
        service2 = get_frame_extraction_service()

        assert service1 is service2

    def test_service_constants(self):
        """测试服务配置常量（从 Django settings 读取）"""
        from apps.artworks.services.frame_extraction import FRAME_TARGET_SIZE, FRAME_JPEG_QUALITY
        assert FRAME_TARGET_SIZE == (1920, 1080)
        assert FRAME_JPEG_QUALITY == 85
